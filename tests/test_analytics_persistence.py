import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from persistence.repository import SQLiteRepository
from analytics_schema import normalize_metric_event


def test_analytics_persistence(tmp_path):
    repo = SQLiteRepository(str(tmp_path / "analytics.db"))
    repo.init_schema()
    event = normalize_metric_event(
        "youtube", "vid1", "2026-09-21T21:00:00+00:00",
        {"views": 1000, "likes": 100, "comments": 5, "revenue": 1.25, "currency": "USD"},
        "https://youtube.com/watch?v=vid1",
    )
    event["event_id"] = "evt1"
    event["video_id"] = "vid1"
    repo.create_analytics_event(event)
    rows = repo.list_analytics_events(video_id="vid1", platform="youtube")
    assert len(rows) == 1
    assert rows[0]["metrics"]["views"] == 1000
    assert rows[0]["metrics"]["revenue"] == 1.25
    assert rows[0]["evidence_status"] == "OBSERVED"
    repo.close()


if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        from pathlib import Path
        test_analytics_persistence(Path(d))
    print("ANALYTICS PERSISTENCE AUDIT: 1 PASS")
