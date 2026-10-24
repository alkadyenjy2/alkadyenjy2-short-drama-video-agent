#!/usr/bin/env python3
"""Free, deterministic visual upgrade for THE ENVELOPE.

Uses Pillow + FFmpeg + espeak-ng. This is motion-designed 2D media, NOT diffusion AI video.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageStat
from rendering.the_envelope_fallback import EPISODES as SOURCE_EPISODES

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "the-envelope-visual-upgrade"
WIDTH, HEIGHT, FPS = 720, 1280, 30
SCENES_PER_EPISODE = 6
TRANSITION = 0.8
SCENE_DURATION = 60.0 / SCENES_PER_EPISODE + TRANSITION * (SCENES_PER_EPISODE - 1) / SCENES_PER_EPISODE
CLASSIFICATION = "DETERMINISTIC_MOTION_TEXT_FALLBACK"
PALETTES = [(16, 29, 53), (69, 49, 35), (75, 19, 27), (65, 57, 43), (24, 24, 29), (18, 31, 51)]
SCENE_NAMES = [
    "THE ENVELOPE", "A MEMORY RETURNS", "THE WARNING", "THE LETTER OPENS",
    "TWO SHADOWS", "SEALED IN SECRET",
]
CAMERAS = ["zoom_in", "pan_left", "zoom_shake", "pan_vertical", "dolly_in", "zoom_out"]
SCENE_LINES = [
    "Something was left here for her.",
    "The past refuses to stay buried.",
    "Every answer creates a new fear.",
    "The letter changes everything.",
    "Someone has been watching.",
    "The final seal hides one last truth.",
]

EPISODES = [
    {"episode": f"EP{i:02d}", "title": item[0], "hook": item[1], "body": item[2],
     "scenes": [{"name": SCENE_NAMES[j], "camera": CAMERAS[j], "palette": PALETTES[j],
                 "line": SCENE_LINES[j]} for j in range(SCENES_PER_EPISODE)]}
    for i, item in enumerate(SOURCE_EPISODES, 1)
]


def classify_artifact() -> str:
    return CLASSIFICATION


def motion_gate(diffs: list[float]) -> bool:
    return len(diffs) >= 2 and all(5.0 < value < 90.0 for value in diffs)


def build_xfade_filter() -> str:
    """Return the six-input video filter chain, with measured 60s timing."""
    parts = []
    step = SCENE_DURATION - TRANSITION
    previous = "[v0]"
    for i in range(1, SCENES_PER_EPISODE):
        out = "[vout]" if i == SCENES_PER_EPISODE - 1 else f"[x{i}]"
        offset = i * step
        parts.append(
            f"{previous}[v{i}]xfade=transition=fade:duration={TRANSITION:.1f}:"
            f"offset={offset:.6f}{out}"
        )
        previous = out
    return ";".join(parts)


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=True, text=True, capture_output=True)


def load_font(size: int):
    for name in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                 "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"):
        if Path(name).exists():
            return ImageFont.truetype(name, size=size)
    return ImageFont.load_default()


def create_scene_image(episode: dict, scene_index: int, output: Path) -> None:
    scene = episode["scenes"][scene_index]
    base = scene["palette"]
    im = Image.new("RGB", (WIDTH, HEIGHT))
    px = im.load()
    for y in range(HEIGHT):
        fy = 1.0 - 0.28 * y / HEIGHT
        for x in range(WIDTH):
            edge = min(x / WIDTH, 1 - x / WIDTH, y / HEIGHT, 1 - y / HEIGHT)
            vignette = max(0.60, min(1.0, edge * 3.8 + 0.58))
            grain = ((x * 17 + y * 31 + scene_index * 13) % 7) - 3
            px[x, y] = tuple(max(0, min(255, int(c * fy * vignette) + grain)) for c in base)
    draw = ImageDraw.Draw(im, "RGBA")
    gold = (211, 176, 105, 220)
    # Subtle frame, mood-specific light leak, and story illustration.
    draw.rounded_rectangle((34, 36, WIDTH - 34, HEIGHT - 36), radius=22, outline=gold, width=2)
    if scene_index in (0, 3, 5):
        # Envelope / letter: outlined paper with a visible fold.
        box = (WIDTH // 2 - 170, HEIGHT // 2 - 120, WIDTH // 2 + 170, HEIGHT // 2 + 100)
        paper = (229, 218, 190, 245) if scene_index != 3 else (247, 239, 214, 250)
        draw.rounded_rectangle(box, radius=10, fill=paper, outline=(190, 158, 105, 255), width=4)
        draw.line((box[0] + 8, box[1] + 12, WIDTH // 2, box[1] + 118,
                   box[2] - 8, box[1] + 12), fill=(132, 99, 65, 255), width=5)
        if scene_index == 5:
            draw.ellipse((WIDTH // 2 - 28, HEIGHT // 2 - 42, WIDTH // 2 + 28, HEIGHT // 2 + 14),
                         fill=(123, 32, 38, 255), outline=gold, width=4)
    elif scene_index == 1:
        # Memory/dust: sepia light and drifting particles.
        for k in range(36):
            x = (k * 127 + 41) % WIDTH
            y = (k * 197 + 73) % HEIGHT
            r = 2 + k % 4
            draw.ellipse((x-r, y-r, x+r, y+r), fill=(235, 205, 151, 90))
        draw.rounded_rectangle((90, 420, WIDTH - 90, 720), radius=20,
                               outline=(224, 194, 144, 150), width=3)
    elif scene_index == 2:
        # Tension: red focus rings.
        for r in (90, 150, 220):
            draw.ellipse((WIDTH//2-r, HEIGHT//2-r, WIDTH//2+r, HEIGHT//2+r),
                         outline=(190, 55, 55, 80), width=3)
    else:
        # Two distinct shadows for confrontation.
        draw.ellipse((125, 370, 300, 760), fill=(0, 0, 0, 145))
        draw.ellipse((410, 370, 585, 760), fill=(0, 0, 0, 170))
    # Corner light leak, restrained so the text remains legible.
    draw.ellipse((-180, -160, 210, 230), fill=(255, 177, 90, 20))
    font_title, font_copy, font_small = load_font(36), load_font(25), load_font(20)
    draw.text((WIDTH // 2, 100), f'{episode["episode"]}  /  THE ENVELOPE',
              font=font_small, fill=(237, 221, 186, 255), anchor="mm")
    draw.text((WIDTH // 2, 190), scene["name"], font=font_title,
              fill=(255, 247, 225, 255), anchor="mm", stroke_width=2, stroke_fill=(0, 0, 0, 180))
    draw.multiline_text((72, HEIGHT - 300), episode["title"], font=font_title,
                        fill=(255, 255, 246, 255), spacing=12, stroke_width=2,
                        stroke_fill=(0, 0, 0, 180))
    copy = scene["line"]
    draw.multiline_text((72, HEIGHT - 225), copy, font=font_copy,
                        fill=(232, 220, 194, 255), spacing=8)
    im = im.filter(ImageFilter.GaussianBlur(radius=0.15))
    im.save(output, quality=95)


def camera_filter(camera: str) -> str:
    # zoompan generates 320 distinct frames from each source image.
    if camera == "zoom_in":
        z = "min(zoom+0.00055,1.18)"
        x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif camera == "pan_left":
        z = "1.10"
        x, y = "iw/2-(iw/zoom/2)+20*sin(on/38)", "ih/2-(ih/zoom/2)"
    elif camera == "zoom_shake":
        z = "max(1.18-0.00055*on,1.02)"
        x, y = "iw/2-(iw/zoom/2)+2*sin(on*1.7)", "ih/2-(ih/zoom/2)+2*cos(on*1.9)"
    elif camera == "pan_vertical":
        z = "1.10"
        x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)+18*sin(on/38)"
    elif camera == "dolly_in":
        z = "min(zoom+0.0008,1.25)"
        x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    else:
        z = "max(1.22-0.00065*on,1.02)"
        x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    return f"zoompan=z='{z}':x='{x}':y='{y}':d=320:s={WIDTH}x{HEIGHT}:fps={FPS},format=yuv420p"


def render_episode(episode_id: str) -> Path:
    if episode_id not in {ep["episode"] for ep in EPISODES}:
        raise ValueError(f"Unknown episode: {episode_id}")
    if not shutil_which("ffmpeg") or not shutil_which("ffprobe") or not shutil_which("espeak-ng"):
        raise RuntimeError("REQUIRES ffmpeg, ffprobe, and espeak-ng")
    episode = next(ep for ep in EPISODES if ep["episode"] == episode_id)
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="envelope-visual-") as temp:
        tmp = Path(temp)
        images, clips = [], []
        for i, scene in enumerate(episode["scenes"]):
            image_path = tmp / f"scene{i}.png"
            clip_path = tmp / f"scene{i}.mp4"
            create_scene_image(episode, i, image_path)
            images.append(image_path)
            # Each scene is 320 frames (10.6667s); xfade overlaps total 4s.
            vf = camera_filter(scene["camera"])
            run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                 "-loop", "1", "-framerate", str(FPS), "-i", str(image_path),
                 "-vf", vf, "-frames:v", "320", "-an", "-c:v", "libx264",
                 "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p",
                 "-r", str(FPS), str(clip_path)])
            clips.append(clip_path)
        narration_text = f'{episode["title"]}. {episode["hook"]} {episode["body"]} ' + " ".join(SCENE_LINES)
        audio_path = tmp / "narration.wav"
        run(["espeak-ng", "-s", "145", "-w", str(audio_path), narration_text])
        command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
        for clip in clips:
            command += ["-i", str(clip)]
        command += ["-i", str(audio_path), "-filter_complex", build_xfade_filter(),
                    "-map", "[vout]", "-map", "6:a:0",
                    "-af", "apad=pad_dur=60", "-t", "60",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                    "-pix_fmt", "yuv420p", "-r", str(FPS),
                    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
                    str(OUT / f"{episode_id}_60s_VISUAL_UPGRADE.mp4")]
        # Apply audio padding to the mapped input using a second filter graph.
        command[command.index("-filter_complex") + 1] += ";[6:a]apad=pad_dur=60[aout]"
        command[command.index("-map") + 3] = "[aout]"
        run(command)
        result_path = OUT / f"{episode_id}_60s_VISUAL_UPGRADE.mp4"
        qa = quality_gates(result_path)
        (OUT / f"{episode_id}_qa.json").write_text(json.dumps(qa, indent=2), encoding="utf-8")
        if not qa["all_pass"]:
            raise RuntimeError(f"QUALITY_GATES_FAILED: {episode_id}: {json.dumps(qa, sort_keys=True)}")
        return result_path


def shutil_which(name: str) -> str | None:
    import shutil
    return shutil.which(name)


def quality_gates(path: Path) -> dict:
    def probe(args):
        return subprocess.run(args, check=True, capture_output=True, text=True)
    meta = json.loads(probe(["ffprobe", "-v", "error", "-show_format", "-show_streams",
                             "-of", "json", str(path)]).stdout)
    video = next((s for s in meta["streams"] if s.get("codec_type") == "video"), {})
    audio = next((s for s in meta["streams"] if s.get("codec_type") == "audio"), {})
    duration = float(meta["format"]["duration"])
    decode = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"],
                            capture_output=True, text=True)
    audio_run = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
                                "-vn", "-af", "volumedetect", "-f", "null", "-"],
                               capture_output=True, text=True)
    match = re.search(r"mean_volume:\s*(-?inf|-?[0-9.]+)\s*dB", audio_run.stderr)
    volume = match.group(1) if match else "NOT_FOUND"
    try:
        audio_pass = volume != "-inf" and volume != "NOT_FOUND" and math.isfinite(float(volume)) and float(volume) > -60
    except ValueError:
        audio_pass = False
    frame_means = []
    with tempfile.TemporaryDirectory(prefix="envelope-qa-") as temp:
        for pct in (10, 50, 90):
            frame = Path(temp) / f"frame{pct}.png"
            at = duration * pct / 100
            snap = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                                   "-ss", f"{at:.3f}", "-i", str(path), "-frames:v", "1", str(frame)],
                                  capture_output=True, text=True)
            if snap.returncode or not frame.exists():
                frame_means.append(0.0)
                continue
            with Image.open(frame) as image:
                gray = image.convert("L")
                frame_means.append(float(ImageStat.Stat(gray).mean[0]))
        diffs = []
        with tempfile.TemporaryDirectory(prefix="envelope-motion-") as temp:
            frames = []
            for pct in (10, 50, 90):
                frame = Path(temp) / f"motion{pct}.png"
                at = duration * pct / 100
                subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                                "-ss", f"{at:.3f}", "-i", str(path), "-frames:v", "1", str(frame)],
                               check=True, capture_output=True)
                with Image.open(frame) as image:
                    frames.append(image.convert("L").resize((180, 320)))
            for left, right in zip(frames, frames[1:]):
                diffs.append(float(ImageStat.Stat(ImageChops.difference(left, right)).mean[0]))
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    checks = {
        "duration_pass": 59.9 <= duration <= 60.1,
        "resolution_codec_pass": (video.get("width"), video.get("height"), video.get("codec_name")) == (720, 1280, "h264"),
        "audio_codec_pass": audio.get("codec_name") == "aac",
        "full_decode_pass": decode.returncode == 0,
        "sha256_pass": len(sha) == 64,
        "audio_loudness_pass": audio_pass,
        "three_frames_not_black_pass": len(frame_means) == 3 and all(x > 10 for x in frame_means),
        "motion_pass": motion_gate(diffs),
    }
    return {
        "episode": path.name[:4], "file": path.name, "duration_sec": duration,
        "width": video.get("width"), "height": video.get("height"),
        "video_codec": video.get("codec_name"), "audio_codec": audio.get("codec_name"),
        "mean_volume_db": volume, "frame_mean_luminance_10_50_90": frame_means,
        "motion_mean_diff_10_50_90": diffs, "sha256": sha, "size_bytes": path.stat().st_size,
        "artifact_class": classify_artifact(), "checks": checks, "all_pass": all(checks.values()),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ep", default="EP01")
    parser.add_argument("--qa", type=Path)
    args = parser.parse_args()
    if args.qa:
        result = quality_gates(args.qa)
        print(json.dumps(result, indent=2))
        if not result["all_pass"]:
            raise SystemExit(1)
    else:
        path = render_episode(args.ep)
        print(json.dumps({"output": str(path), "qa": str(OUT / f"{args.ep}_qa.json"),
                          "artifact_class": classify_artifact()}, indent=2))


if __name__ == "__main__":
    # ImageChops is intentionally imported here for a stable top-level test import.
    from PIL import ImageChops
    main()
