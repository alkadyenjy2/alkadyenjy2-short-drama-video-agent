"""PostgreSQL implementation of the drama video persistence contract.

Uses psycopg v3 and DATABASE_URL. JSON-shaped fields remain JSON-encoded text
for compatibility with the existing SQLite repository contract.
"""
import json
import os
import threading
from typing import Dict, List, Optional

import psycopg
from psycopg.rows import dict_row

from .repository import PersistenceRepository


class PostgresRepository(PersistenceRepository):
    def __init__(self, database_url: Optional[str] = None, initialize_schema: bool = True):
        self.database_url = (database_url or os.getenv("DATABASE_URL", "")).strip()
        if not self.database_url:
            raise ValueError("DATABASE_URL is required for PostgreSQL persistence")
        self._lock = threading.RLock()
        self._conn = psycopg.connect(self.database_url, row_factory=dict_row, autocommit=True)
        if initialize_schema:
            self.init_schema()

    def init_schema(self):
        statements = [
            """CREATE TABLE IF NOT EXISTS operation_logs (
                operation_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, video_id TEXT NOT NULL,
                timestamp TEXT NOT NULL, parent_version TEXT, new_version TEXT NOT NULL,
                operation_type TEXT NOT NULL, parsed_value TEXT, generated_prompt TEXT,
                preview_reference TEXT NOT NULL, status TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
            "CREATE INDEX IF NOT EXISTS idx_operation_logs_video_id ON operation_logs(video_id)",
            "CREATE INDEX IF NOT EXISTS idx_operation_logs_timestamp ON operation_logs(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_operation_logs_user_id ON operation_logs(user_id)",
            """CREATE TABLE IF NOT EXISTS video_versions (
                video_id TEXT PRIMARY KEY, story_id TEXT, current_version TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
            "CREATE INDEX IF NOT EXISTS idx_video_versions_story_id ON video_versions(story_id)",
            """CREATE TABLE IF NOT EXISTS publications (
                publication_id TEXT PRIMARY KEY, video_id TEXT NOT NULL, story_id TEXT NOT NULL,
                platforms TEXT NOT NULL, state TEXT NOT NULL, receipts TEXT, attempts TEXT,
                created_at TEXT NOT NULL, updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
            "CREATE INDEX IF NOT EXISTS idx_publications_video_id ON publications(video_id)",
            "CREATE INDEX IF NOT EXISTS idx_publications_state ON publications(state)",
            "CREATE INDEX IF NOT EXISTS idx_publications_created_at ON publications(created_at)",
            """CREATE TABLE IF NOT EXISTS analytics_events (
                event_id TEXT PRIMARY KEY, video_id TEXT NOT NULL, publication_id TEXT,
                platform TEXT NOT NULL, observed_at TEXT NOT NULL, source_url TEXT,
                metrics TEXT NOT NULL, currency TEXT, attribution_window TEXT,
                evidence_status TEXT NOT NULL)""",
            "CREATE INDEX IF NOT EXISTS idx_analytics_video_id ON analytics_events(video_id)",
            "CREATE INDEX IF NOT EXISTS idx_analytics_platform ON analytics_events(platform)",
            "CREATE INDEX IF NOT EXISTS idx_analytics_observed_at ON analytics_events(observed_at)",
        ]
        with self._lock, self._conn.cursor() as cur:
            for statement in statements:
                cur.execute(statement)

    def _one(self, sql, params=()):
        with self._lock, self._conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return dict(row) if row else None

    def _all(self, sql, params=()):
        with self._lock, self._conn.cursor() as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]

    @staticmethod
    def _decode(row, fields):
        if row:
            for field, fallback in fields.items():
                try:
                    row[field] = json.loads(row[field]) if row.get(field) else fallback
                except (TypeError, ValueError):
                    row[field] = fallback
        return row

    def create_operation_log(self, log: Dict) -> Dict:
        with self._lock, self._conn.cursor() as cur:
            cur.execute("""INSERT INTO operation_logs
                (operation_id,user_id,video_id,timestamp,parent_version,new_version,operation_type,
                 parsed_value,generated_prompt,preview_reference,status)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT(operation_id) DO UPDATE SET user_id=EXCLUDED.user_id,
                video_id=EXCLUDED.video_id,timestamp=EXCLUDED.timestamp,parent_version=EXCLUDED.parent_version,
                new_version=EXCLUDED.new_version,operation_type=EXCLUDED.operation_type,
                parsed_value=EXCLUDED.parsed_value,generated_prompt=EXCLUDED.generated_prompt,
                preview_reference=EXCLUDED.preview_reference,status=EXCLUDED.status""",
                (log["operation_id"], log["user_id"], log["video_id"], log["timestamp"],
                 log.get("parent_version"), log["new_version"], log["operation_type"],
                 log.get("parsed_value"), log.get("generated_prompt"), log["preview_reference"],
                 log.get("status", "PENDING_PREVIEW")))
        return log

    def list_operation_history(self, video_id: str) -> List[Dict]:
        return self._all("SELECT * FROM operation_logs WHERE video_id=%s ORDER BY timestamp ASC", (video_id,))

    def get_operation_log(self, operation_id: str) -> Optional[Dict]:
        return self._one("SELECT * FROM operation_logs WHERE operation_id=%s", (operation_id,))

    def create_or_update_video_version(self, video_id: str, current_version: str, story_id: Optional[str] = None) -> Dict:
        self._one("""INSERT INTO video_versions(video_id,story_id,current_version)
            VALUES(%s,%s,%s) ON CONFLICT(video_id) DO UPDATE SET
            current_version=EXCLUDED.current_version,
            story_id=COALESCE(EXCLUDED.story_id,video_versions.story_id),
            updated_at=CURRENT_TIMESTAMP RETURNING video_id""", (video_id, story_id, current_version))
        return self.get_video_version(video_id)

    def get_video_version(self, video_id: str) -> Optional[Dict]:
        row = self._one("SELECT * FROM video_versions WHERE video_id=%s", (video_id,))
        if row:
            row["history_count"] = self._one("SELECT COUNT(*) AS cnt FROM operation_logs WHERE video_id=%s", (video_id,))["cnt"]
        return row

    def list_video_versions(self) -> List[Dict]:
        return self._all("SELECT * FROM video_versions ORDER BY updated_at DESC")

    def create_publication(self, publication: Dict) -> Dict:
        with self._lock, self._conn.cursor() as cur:
            cur.execute("""INSERT INTO publications
                (publication_id,video_id,story_id,platforms,state,receipts,attempts,created_at)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT(publication_id) DO UPDATE SET video_id=EXCLUDED.video_id,
                story_id=EXCLUDED.story_id,platforms=EXCLUDED.platforms,state=EXCLUDED.state,
                receipts=EXCLUDED.receipts,attempts=EXCLUDED.attempts,updated_at=CURRENT_TIMESTAMP""",
                (publication["publication_id"], publication["video_id"], publication["story_id"],
                 json.dumps(publication["platforms"]), publication["state"],
                 json.dumps(publication.get("receipts", {})), json.dumps(publication.get("attempts", [])),
                 publication["created_at"]))
        return publication

    def update_publication(self, publication_id: str, updates: Dict) -> Optional[Dict]:
        allowed = {"platforms", "receipts", "attempts", "state", "video_id", "story_id"}
        clauses, values = [], []
        for key, value in updates.items():
            if key in allowed:
                clauses.append(f"{key}=%s")
                values.append(json.dumps(value) if key in {"platforms", "receipts", "attempts"} else value)
        if clauses:
            clauses.append("updated_at=CURRENT_TIMESTAMP")
            values.append(publication_id)
            with self._lock, self._conn.cursor() as cur:
                cur.execute(f"UPDATE publications SET {', '.join(clauses)} WHERE publication_id=%s", values)
        return self.get_publication(publication_id)

    def get_publication(self, publication_id: str) -> Optional[Dict]:
        return self._decode(self._one("SELECT * FROM publications WHERE publication_id=%s", (publication_id,)),
                            {"platforms": [], "receipts": {}, "attempts": []})

    def list_publications(self, video_id: Optional[str] = None) -> List[Dict]:
        sql, params = ("SELECT * FROM publications ORDER BY created_at DESC", ())
        if video_id:
            sql, params = ("SELECT * FROM publications WHERE video_id=%s ORDER BY created_at DESC", (video_id,))
        return [self._decode(row, {"platforms": [], "receipts": {}, "attempts": []}) for row in self._all(sql, params)]

    def create_analytics_event(self, event: Dict) -> Dict:
        with self._lock, self._conn.cursor() as cur:
            cur.execute("""INSERT INTO analytics_events
                (event_id,video_id,publication_id,platform,observed_at,source_url,metrics,currency,attribution_window,evidence_status)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT(event_id) DO UPDATE SET video_id=EXCLUDED.video_id,
                publication_id=EXCLUDED.publication_id,platform=EXCLUDED.platform,
                observed_at=EXCLUDED.observed_at,source_url=EXCLUDED.source_url,metrics=EXCLUDED.metrics,
                currency=EXCLUDED.currency,attribution_window=EXCLUDED.attribution_window,
                evidence_status=EXCLUDED.evidence_status""",
                (event["event_id"], event["video_id"], event.get("publication_id"), event["platform"],
                 event["observed_at"], event.get("source_url", ""), json.dumps(event.get("metrics", {})),
                 event.get("currency"), event.get("attribution_window"), event.get("evidence_status", "UNKNOWN")))
        return event

    def list_analytics_events(self, video_id: Optional[str] = None, platform: Optional[str] = None) -> List[Dict]:
        clauses, values = [], []
        if video_id:
            clauses.append("video_id=%s"); values.append(video_id)
        if platform:
            clauses.append("platform=%s"); values.append(platform)
        sql = "SELECT * FROM analytics_events"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        rows = self._all(sql + " ORDER BY observed_at DESC", tuple(values))
        return [self._decode(row, {"metrics": {}}) for row in rows]

    def close(self):
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def health_check(self) -> bool:
        try:
            with self._lock, self._conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS cnt FROM information_schema.tables WHERE table_schema='public' AND table_name = ANY(%s)",
                            (["operation_logs", "video_versions", "publications", "analytics_events"],))
                return cur.fetchone()["cnt"] == 4
        except Exception:
            return False
