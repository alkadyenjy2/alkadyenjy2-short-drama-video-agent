#!/usr/bin/env python3
"""Frame-level OCR gate for THE ENVELOPE story-specific scene transitions."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path

from PIL import Image
import pytesseract

TRANSITION = 0.6
SCENES_PER_EPISODE = 6
CLIP_SECONDS = 60.0 / SCENES_PER_EPISODE + TRANSITION * (SCENES_PER_EPISODE - 1) / SCENES_PER_EPISODE
STEP_SECONDS = CLIP_SECONDS - TRANSITION
BEAT_NAMES = [
    "WIDE ESTABLISHING",
    "THE OBJECT",
    "THE CLUE",
    "THE REACTION",
    "THE REVEAL",
    "THE DECISION",
]


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def transition_text_pass(ocr_text: str, previous_scene: str, current_scene: str) -> bool:
    observed = normalize(ocr_text)
    previous = normalize(previous_scene)
    current = normalize(current_scene)
    return bool(current and current in observed and previous not in observed)


def inspect_transitions(video: Path) -> dict:
    results = []
    with tempfile.TemporaryDirectory(prefix="story-transition-qa-") as temp:
        for idx in range(1, SCENES_PER_EPISODE):
            # Sample after the incoming title's 0.3s fade-in has completed.
            timestamp = idx * STEP_SECONDS + 0.4
            frame_path = Path(temp) / f"transition-{idx}.png"
            proc = subprocess.run(
                ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                 "-ss", f"{timestamp:.6f}", "-i", str(video), "-frames:v", "1", str(frame_path)],
                capture_output=True, text=True,
            )
            if proc.returncode != 0 or not frame_path.exists():
                results.append({"transition": idx, "timestamp_sec": round(timestamp, 3),
                                "pass": False, "error": (proc.stderr or "frame extraction failed")[-500:]})
                continue
            with Image.open(frame_path) as image:
                # Beat title is centered near y=170; exclude the episode/place header at y=95.
                crop = image.crop((70, 105, 650, 245))
                text = pytesseract.image_to_string(crop, config="--psm 11")
            previous, current = BEAT_NAMES[idx - 1], BEAT_NAMES[idx]
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
    result = inspect_transitions(args.video)
    report_path = args.video.with_name(f"{args.video.stem}_transition_qa.json")
    report_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    print(f"TRANSITION_QA_REPORT: {report_path}")
    if not result["all_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
