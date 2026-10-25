#!/usr/bin/env python3
"""Frame-level OCR gate for THE ENVELOPE story-specific scene transitions."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from difflib import SequenceMatcher
from pathlib import Path

from PIL import Image, ImageEnhance
import pytesseract

TRANSITION = 0.6
SCENES_PER_EPISODE = 6
CLIP_SECONDS = 60.0 / SCENES_PER_EPISODE + TRANSITION * (SCENES_PER_EPISODE - 1) / SCENES_PER_EPISODE
STEP_SECONDS = CLIP_SECONDS - TRANSITION
POST_TRANSITION_SETTLE = 3.0
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


def compact(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def approximately_contains(expected: str, observed: str, threshold: float = 0.75) -> bool:
    """Match full titles or distinctive words despite OCR dropping/misreading characters."""
    target = compact(expected)
    source = compact(observed)
    if not target or not source:
        return False
    expected_words = re.findall(r"[a-z0-9]+", expected.lower())
    observed_words = re.findall(r"[a-z0-9]+", observed.lower())
    if not expected_words or not observed_words:
        return False

    # Compare complete token windows, never arbitrary substrings. This avoids
    # accepting a different title because a few letters happen to overlap.
    phrase_threshold = max(threshold, 0.75)
    for start in range(len(observed_words)):
        for count in range(1, min(len(expected_words) + 1, len(observed_words) - start) + 1):
            observed_phrase = compact(" ".join(observed_words[start:start + count]))
            if SequenceMatcher(None, target, observed_phrase).ratio() >= phrase_threshold:
                return True

    # OCR can sometimes lose the prefix ("THE") and misread a distinctive word
    # (REVEAL -> REVEAR). Whole-word matching allows that while rejecting
    # neighboring titles such as REACTION -> REVEAL.
    for word in expected_words:
        if len(word) < 4:
            continue
        for observed_word in observed_words:
            if abs(len(word) - len(observed_word)) > 2:
                continue
            if SequenceMatcher(None, word, observed_word).ratio() >= max(threshold, 0.82):
                return True
    return False


def transition_text_pass(ocr_text: str, previous_scene: str, current_scene: str) -> bool:
    """Require the incoming title and reject a confidently detected previous title."""
    current_present = approximately_contains(current_scene, ocr_text, threshold=0.75)
    # Be stricter for absence checks: a weak OCR fragment should not be mistaken
    # for a previous title and block an otherwise readable incoming scene.
    previous_present = approximately_contains(previous_scene, ocr_text, threshold=0.82)
    return current_present and not previous_present


def transition_sample_timestamp(index: int) -> float:
    """Sample after the 0.6s crossfade plus a 2s settling window for robust OCR."""
    if not 1 <= index < SCENES_PER_EPISODE:
        raise ValueError(f"Transition index must be in 1..{SCENES_PER_EPISODE - 1}, got {index}")
    return index * STEP_SECONDS + TRANSITION + POST_TRANSITION_SETTLE


def inspect_transitions(video: Path) -> dict:
    results = []
    with tempfile.TemporaryDirectory(prefix="story-transition-qa-") as temp:
        for idx in range(1, SCENES_PER_EPISODE):
            # Inspect the incoming title once the visual transition is stable;
            # OCR during a crossfade is unreliable even when the title is legible.
            timestamp = transition_sample_timestamp(idx)
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
                # Crop the title, upscale, and combine two OCR layouts to reduce false negatives.
                crop = image.crop((130, 125, 590, 215)).convert("L")
                crop = ImageEnhance.Contrast(crop.resize((crop.width * 4, crop.height * 4))).enhance(2.0)
                text_block = pytesseract.image_to_string(crop, config="--psm 6")
                text_sparse = pytesseract.image_to_string(crop, config="--psm 11")
                text = text_block + "\n" + text_sparse
            previous, current = BEAT_NAMES[idx - 1], BEAT_NAMES[idx]
            current_present = approximately_contains(current, text, threshold=0.75)
            previous_present = approximately_contains(previous, text, threshold=0.82)
            passed = current_present and not previous_present
            results.append({
                "transition": idx,
                "timestamp_sec": round(timestamp, 3),
                "previous_scene": previous,
                "expected_scene": current,
                "ocr_text": text.strip(),
                "previous_title_absent": not previous_present,
                "expected_title_present": current_present,
                "pass": passed,
            })
    return {
        "video": video.name,
        "method": "TESSERACT_OCR_ON_STABLE_POST_TRANSITION_FRAMES_MULTI_CONFIG_FUZZY_MATCH",
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
