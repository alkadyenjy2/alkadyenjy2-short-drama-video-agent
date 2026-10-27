#!/usr/bin/env python3
"""Manual, evidence-first YouTube trend scan for GitHub Actions.

Requires YOUTUBE_DATA_API_KEY in the repository Actions secrets.
Writes JSON and PASS/FAIL logs only; does not publish content or schedule runs.
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from source_adapters import AdapterAccessError, YouTubeDiscoveryAdapter
from trend_intelligence import rank_trends

OUT = Path("build/trend-scan")
OUT.mkdir(parents=True, exist_ok=True)
log_path = OUT / "trend_scanner.log"
fail_path = OUT / "trend_scanner_FAIL.log"


def log(message: str) -> None:
    stamp = datetime.now(timezone.utc).isoformat()
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"{stamp} {message}\n")


def fail(message: str) -> int:
    stamp = datetime.now(timezone.utc).isoformat()
    fail_path.write_text(f"{stamp} FAIL {message}\n", encoding="utf-8")
    log(f"FAIL {message}")
    print(message, file=sys.stderr)
    return 1


def main() -> int:
    if not os.getenv("YOUTUBE_DATA_API_KEY"):
        return fail("YOUTUBE_DATA_API_KEY secret is missing")
    now = datetime.now(timezone.utc)
    published_after = (now - timedelta(days=7)).isoformat().replace("+00:00", "Z")
    adapter = YouTubeDiscoveryAdapter()
    queries = ["short drama", "vertical drama", "micro drama"]
    observations = []
    try:
        for query in queries:
            observations.extend(adapter.discover(
                query=query, published_after=published_after,
                region_code="US", max_results=25,
            ))
    except Exception as exc:
        return fail(f"source request failed: {type(exc).__name__}: {exc}")

    cutoff = now - timedelta(days=7)
    valid = []
    for item in observations:
        try:
            published = datetime.fromisoformat(item.observed_at.replace("Z", "+00:00"))
            # observed_at is fetch time, so use age_hours for the publication window.
            if item.title.strip() and item.source_url.startswith("https://www.youtube.com/watch?v=") and item.age_hours <= 168:
                valid.append(item)
        except Exception:
            continue

    ranked = rank_trends(valid, limit=50)
    if not ranked:
        return fail("No qualifying YouTube videos returned in the seven-day window")

    payload = {
        "status": "PASS",
        "source": "YouTube Data API v3",
        "generatedAt": now.isoformat(),
        "windowDays": 7,
        "count": len(ranked),
        "items": ranked,
        "evidence_status": "OBSERVED",
        "note": "Ranking is a heuristic; not a guarantee of future performance.",
    }
    output = OUT / "trending_stories.json"
    temp = output.with_suffix(".json.tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    json.loads(temp.read_text(encoding="utf-8"))
    temp.replace(output)
    reread = json.loads(output.read_text(encoding="utf-8"))
    if reread.get("status") != "PASS" or reread.get("count", 0) != len(reread.get("items", [])) or not reread.get("items"):
        return fail("Read-back verification failed")
    log(f"PASS count={reread['count']} output={output.as_posix()}")
    print(json.dumps({"status": "PASS", "count": reread["count"], "output": output.as_posix(), "generatedAt": reread["generatedAt"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
