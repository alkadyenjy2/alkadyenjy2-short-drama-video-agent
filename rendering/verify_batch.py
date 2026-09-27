#!/usr/bin/env python3
"""Verify deterministic fallback episode artifacts produced by batch_fallback.py."""
from __future__ import annotations
import json
import subprocess
from pathlib import Path

root = Path("build/episodes")
manifests = sorted(root.glob("EP*/EP*.manifest.json"))
mp4s = sorted(root.glob("EP*/*.mp4"))
assert len(manifests) == 9, f"expected 9 manifests, got {len(manifests)}"
assert len(mp4s) == 9, f"expected 9 mp4s, got {len(mp4s)}"

for manifest_path in manifests:
    manifest = json.loads(manifest_path.read_text())
    artifact = Path(manifest["artifact"])
    assert artifact.exists() and artifact.stat().st_size > 0, artifact
    probe = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(artifact)
    ]))
    video = next(s for s in probe["streams"] if s.get("codec_type") == "video")
    audio = next(s for s in probe["streams"] if s.get("codec_type") == "audio")
    assert video.get("codec_name") == "h264", (artifact, video)
    assert int(video.get("width", 0)) == 720 and int(video.get("height", 0)) == 1280, (artifact, video)
    assert 94.5 <= float(probe["format"].get("duration", "0")) <= 95.5, (artifact, probe["format"])
    assert audio.get("codec_name") == "aac", (artifact, audio)
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(artifact), "-f", "null", "-"], check=True)
    print("verified", artifact, manifest["sha256"])
