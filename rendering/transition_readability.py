#!/usr/bin/env python3
"""Frame-level OCR gate for THE ENVELOPE scene transitions.

Checks actual rendered MP4 frames, not just the FFmpeg filter graph. The title
must switch cleanly to the incoming scene, with no readable previous title.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path

from PIL import Image
import pytesseract

WIDTH, HEIGHT = 720, 1280
FPS = 30
TRANSITION = 0.8
SCENES_PER_EPISODE = 6
SCENE_DURATION = 60.0 / SCENES_PER_EPISODE + TRANSITION * (SCENES_PER_EPISODE - 1) / SCENES_PER_EPISODE
STEP = SCENE_DURATION - TRANSITION
SCENE_NAMES = [
    "THE ENVELOPE",
    "A MEMORY RETURNS",
    "THE WARNING",
    "THE LETTER OPENS",
    "TWO SHADOWS",
    "SEALED IN SECRET",
]


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def transition_text_pass(ocr_text: str, previous_scene: str, current_scene: str) -> bool:
    """Require the incoming scene title and reject the previous title."""
    observed = normalize(ocr_text)
    previous = normalize(previous_scene)
    current = normalize(current_scene)
    return bool(current and current in observed and previous not in observed)


def inspect_video(video: Path) -> dict:
    results = []
    with tempfile.TemporaryDirectory(prefix="envelope-transition-qa-") as temp:
        for idx in range(1, SCENES_PER_EPISODE):
            timestamp = idx * STEP + 0.15
            frame_path = Path(temp) / f"transition-{idx}.png"
            cmd = [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-ss", f"{timestamp:.6f}", "-i", str(video),
                "-frames:v", "1", str(frame_path),
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode != 0 or not frame_path.exists():
                results.append({
                    "transition": idx,
                    "timestamp_sec": round(timestamp, 3),
                    "pass": False,
                    "error": (proc.stderr or "frame extraction failed")[-500:],
                })
                continue
            with Image.open(frame_path) as image:
                # The scene title is centered near y=190 in the 720x1280 frame.
                crop = image.crop((70, 120, 650, 270))
                text = pytesseract.image_to_string(crop, config="--psm 6")
            previous, current = SCENE_NAMES[idx - 1], SCENE_NAMES[idx]
            passed = transition_text_pass(text, previous, current)
            results.append({
                "transition": idx,
                "timestamp_sec": round(timestamp, 3),
                "previous_scene": previous,
                "expected_scene": current,
                "ocr_text": text.strip(),
                "previous_title_absent": normalize(previous) not in normalize(text),
                "expected_title_present": normalize(current) in normalize(text),
                "pass": passed,
            })
    return {
        "video": video.name,
        "method": "TESSERACT_OCR_ON_RENDERED_TRANSITION_FRAMES",
        "sample_count": len(results),
        "passed_count": sum(item.get("pass", False) for item in results),
        "all_pass": len(results) == SCENES_PER_EPISODE - 1 and all(item.get("pass", False) for item in results),
        "transitions": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True, type=Path)
    args = parser.parse_args()
    if not args.video.is_file():
        raise SystemExit(f"VIDEO_NOT_FOUND: {args.video}")
    result = inspect_video(args.video)
    print(json.dumps(result, indent=2))
    if not result["all_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
