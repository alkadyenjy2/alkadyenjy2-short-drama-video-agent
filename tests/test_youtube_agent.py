import tempfile
from pathlib import Path

from youtube_agent import MAX_EPISODES, build_release_record, episode_id, publish_if_approved

assert MAX_EPISODES == 10
assert episode_id(1) == "EP01"
assert episode_id(10) == "EP10"

with tempfile.TemporaryDirectory() as d:
    p = Path(d) / "shot.mp4"
    p.write_bytes(b"real-test-artifact")
    rec = build_release_record(
        1,
        {"ready": True},
        {"ready": True},
        {"mp4_path": str(p)},
        {"ready": True},
    )
    assert rec["stages"]["MP4_EVIDENCE"] == "GENERATED"
    assert len(rec["mp4_evidence"]["sha256"]) == 64
    assert rec["stages"]["APPROVAL"] == "BLOCKED"
    assert rec["publish_allowed"] is False

    blocked = publish_if_approved(1, str(p), "Test", "Test", [], str(Path(d) / "missing.json"))
    assert blocked["status"] == "BLOCKED"
    assert blocked["stage"] == "APPROVAL"

print("YOUTUBE AGENT AUDIT: 7 PASS")
