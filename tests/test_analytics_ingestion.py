import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analytics_ingestion import persist_events
from analytics_schema import normalize_metric_event
from persistence.repository import SQLiteRepository


def test_ingestion_creates_deterministic_event_id(tmp_path):
    repo = SQLiteRepository(str(tmp_path / "ingest.db"))
    repo.init_schema()
    event = normalize_metric_event(
        "tiktok", "tt1", "2026-09-21T21:00:00+00:00",
        {"views": 50, "likes": 5}
    )
    assert persist_events(repo, [event]) == 1
    assert persist_events(repo, [event]) == 1
    rows = repo.list_analytics_events(video_id="tt1")
    assert len(rows) == 1
    assert rows[0]["metrics"]["views"] == 50
    repo.close()


if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        test_ingestion_creates_deterministic_event_id(Path(d))
    print("ANALYTICS INGESTION AUDIT: 1 PASS")
