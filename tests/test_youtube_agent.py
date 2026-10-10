import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

from youtube_agent import MAX_EPISODES, build_release_record, episode_id, publish_if_approved, verify_mp4, artifact_publish_classification

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

    fallback = Path(d) / "THE_LAST_VOICEMAIL_EP02_Fallback_Recut.mp4"
    fallback.write_bytes(b"placeholder")
    fallback_manifest = fallback.with_suffix(".manifest.json")
    fallback_manifest.write_text(
        '{"episode":"EP02","mode":"DETERMINISTIC_MOTION_FALLBACK_RECUT","content_note":"not a canonical story episode"}',
        encoding="utf-8",
    )
    classified = artifact_publish_classification(str(fallback))
    assert classified["status"] == "BLOCKED"
    assert "release candidate only" in classified["reason"]
    approval = Path(d) / "approval.json"
    approval.write_text(
        '{"approved":true,"approved_by":"ci-test","approved_at":"2026-09-27T00:00:00Z"}',
        encoding="utf-8",
    )
    fallback_publish = publish_if_approved(
        2, str(fallback), "Fallback", "Fallback", [], str(approval)
    )
    assert fallback_publish["status"] == "BLOCKED"
    assert fallback_publish["stage"] == "RENDER"

    canonical = Path(d) / "THE_LAST_VOICEMAIL_EP02.mp4"
    canonical.write_bytes(b"placeholder")
    canonical.with_suffix(".manifest.json").write_text(
        '{"episode":"EP02","artifact_class":"CANONICAL_STORY_EPISODE","mode":"AI_GENERATED_STORY"}',
        encoding="utf-8",
    )
    assert artifact_publish_classification(str(canonical))["status"] == "READY"

    canonical_fallback = Path(d) / "THE_LAST_VOICEMAIL_EP02_Canonical_Fallback.mp4"
    canonical_fallback.write_bytes(b"placeholder")
    canonical_fallback.with_suffix(".manifest.json").write_text(
        '{"episode":"EP02","artifact_class":"CANONICAL_STORY_EPISODE","mode":"DETERMINISTIC_MOTION_RENDER"}',
        encoding="utf-8",
    )
    assert artifact_publish_classification(str(canonical_fallback))["status"] == "READY"

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

with tempfile.TemporaryDirectory() as d:
    p = Path(d) / "corrupt-media.mp4"
    p.write_bytes(b"placeholder bytes, not a valid decoded video")
    probe_result = subprocess.CompletedProcess(
        args=["ffprobe"], returncode=0,
        stdout=json.dumps({
            "format": {"format_name": "mov,mp4,m4a,3gp,3g2,mj2", "duration": "1.0", "size": str(p.stat().st_size)},
            "streams": [{"codec_type": "video", "codec_name": "h264", "width": 720, "height": 1280}],
        }),
        stderr="",
    )
    decode_result = subprocess.CompletedProcess(
        args=["ffmpeg"], returncode=1, stdout="", stderr="decode failure",
    )
    with patch("youtube_agent.shutil.which", side_effect=lambda name: f"/usr/bin/{name}" if name in ("ffprobe", "ffmpeg") else None):
        with patch("youtube_agent.subprocess.run", side_effect=[probe_result, decode_result]):
            rejected = verify_mp4(str(p))
    assert rejected["status"] == "NOT_VERIFIED", rejected
    assert "decode" in rejected["reason"].lower(), rejected

print("YOUTUBE AGENT AUDIT: real-media validation + approval gate PASS")

# CI regression sentinel: ensure the repaired PYTHONPATH workflow is exercised on main.
# CI sentinel: trigger combined fallback artifact verification.
