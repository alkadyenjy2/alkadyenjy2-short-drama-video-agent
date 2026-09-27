import shutil
import subprocess
import tempfile
from pathlib import Path

from youtube_agent import MAX_EPISODES, build_release_record, episode_id, publish_if_approved, verify_mp4

assert MAX_EPISODES == 10
assert episode_id(1) == "EP01"
assert episode_id(10) == "EP10"

with tempfile.TemporaryDirectory() as d:
    p = Path(d) / "not-an-mp4.mp4"
    p.write_bytes(b"real-test-artifact")
    assert verify_mp4(str(Path(d) / "missing.mp4"))["status"] == "NOT_VERIFIED"

    rec = build_release_record(
        1,
        {"ready": True},
        {"ready": True},
        {"mp4_path": str(p)},
        {"ready": True},
    )
    assert rec["stages"]["MP4_EVIDENCE"] == "NOT_VERIFIED"
    assert rec["stages"]["APPROVAL"] == "BLOCKED"
    assert rec["publish_allowed"] is False

    blocked = publish_if_approved(1, str(p), "Test", "Test", [], str(Path(d) / "missing.json"))
    assert blocked["status"] == "BLOCKED"
    assert blocked["stage"] == "APPROVAL"

    if shutil.which("ffmpeg"):
        real = Path(d) / "real.mp4"
        subprocess.run(
            [
                "ffmpeg", "-y", "-v", "error",
                "-f", "lavfi", "-i", "color=c=black:s=160x284:r=24",
                "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                "-t", "0.25",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-c:a", "aac", str(real),
            ],
            check=True,
        )
        evidence = verify_mp4(str(real))
        assert evidence["status"] == "GENERATED"
        assert evidence["video_verified"] is True
        assert evidence["duration_sec"] > 0
        assert len(evidence["sha256"]) == 64

print("YOUTUBE AGENT AUDIT: real-media validation + approval gate PASS")
