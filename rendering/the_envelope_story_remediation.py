#!/usr/bin/env python3
"""Story-specific, deterministic visual remediation for THE ENVELOPE.

Produces real 60s H.264/AAC MP4s, measured QA JSON, and contact sheets.
This is motion-designed 2D media, not diffusion/AI-generated video.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from rendering.the_envelope_fallback import EPISODES as SOURCE_EPISODES

OUT = ROOT / "build" / "the-envelope-story-remediation"
WIDTH, HEIGHT, FPS = 720, 1280, 30
SCENES_PER_EPISODE = 6
TRANSITION = 0.6
CLIP_SECONDS = 60.0 / SCENES_PER_EPISODE + TRANSITION * (SCENES_PER_EPISODE - 1) / SCENES_PER_EPISODE
STEP_SECONDS = CLIP_SECONDS - TRANSITION
CLASSIFICATION = "DETERMINISTIC_MOTION_TEXT_FALLBACK"

# Each profile changes location geometry, props, and framing—not just the palette.
PROFILES = {
    "front_door": {"place": "FRONT DOOR / MORNING", "place_id": "front_door",
                   "objects": ["brass_mailbox", "door_handle", "wooden_porch", "envelope"],
                   "palette": (24, 39, 59), "accent": (210, 174, 105)},
    "kitchen": {"place": "KITCHEN / NIGHT", "place_id": "kitchen",
                "objects": ["coffee_mug", "night_window", "stained_envelope", "counter"],
                "palette": (67, 43, 32), "accent": (222, 159, 86)},
    "photo_archive": {"place": "PHOTO ARCHIVE", "place_id": "photo_archive",
                      "objects": ["old_photo", "date_card", "file_box", "envelope"],
                      "palette": (57, 48, 38), "accent": (203, 183, 139)},
    "hallway_mirror": {"place": "HALLWAY / MIRROR", "place_id": "hallway_mirror",
                       "objects": ["wall_mirror", "portrait", "door_shadow", "envelope"],
                       "palette": (35, 39, 48), "accent": (169, 179, 190)},
    "locked_room": {"place": "LOCKED ROOM", "place_id": "locked_room",
                    "objects": ["brass_key", "childhood_drawings", "locked_door", "envelope"],
                    "palette": (39, 34, 40), "accent": (194, 157, 106)},
    "records_room": {"place": "RECORDS ROOM", "place_id": "records_room",
                     "objects": ["birth_certificate", "labelled_box", "paper_stack", "envelope"],
                     "palette": (51, 48, 42), "accent": (197, 178, 132)},
    "apartment": {"place": "APARTMENT / NIGHT", "place_id": "apartment",
                  "objects": ["phone", "window_reflection", "two_shadows", "envelope"],
                  "palette": (25, 31, 43), "accent": (186, 150, 105)},
    "office": {"place": "OFFICE / TWIST", "place_id": "office",
               "objects": ["scattered_letters", "wall_map", "scissors", "torn_envelope"],
               "palette": (36, 38, 44), "accent": (201, 164, 101)},
    "attic_archive": {"place": "ATTIC ARCHIVE / FINALE", "place_id": "attic_archive",
                      "objects": ["archive_chest", "wax_seal", "burned_edges", "old_photo", "keys"],
                      "palette": (47, 37, 30), "accent": (211, 171, 91)},
    "bedroom": {"place": "BEDROOM / LATE NIGHT", "place_id": "bedroom",
                "objects": ["phone_glow", "open_drawer", "creased_letter", "window"],
                "palette": (29, 34, 49), "accent": (172, 169, 158)},
    "stairwell": {"place": "STAIRWELL", "place_id": "stairwell",
                  "objects": ["stair_rail", "doorway", "long_shadow", "envelope"],
                  "palette": (32, 34, 38), "accent": (194, 163, 113)},
    "courthouse": {"place": "PUBLIC RECORDS HALL", "place_id": "courthouse",
                   "objects": ["record_folder", "bench", "number_ticket", "letter"],
                   "palette": (53, 54, 50), "accent": (190, 175, 145)},
}

# Episode-specific anchors follow the source story beats. Other episodes are selected
# from title/hook/body keywords, with a deterministic episode-number fallback.
EXPLICIT_PROFILES = {"EP01": "front_door", "EP02": "kitchen", "EP15": "office", "EP30": "attic_archive"}
KEYWORD_PROFILES = [
    (("attic", "archive", "final", "closure", "last truth"), "attic_archive"),
    (("torn", "twist", "scissors", "map", "investigated", "betrayal", "betrayed"), "office"),
    (("birth certificate", "mother's name", "name", "officially dead", "dead"), "records_room"),
    (("locked room", "drawings", "key", "room"), "locked_room"),
    (("photo", "photograph", "date", "tomorrow", "picture"), "photo_archive"),
    (("phone", "caller", "calls", "live photo", "rings"), "bedroom"),
    (("shadow", "watching", "protect", "adam"), "apartment"),
    (("door", "arrives", "arrives", "mailbox", "envelope arrives"), "front_door"),
    (("mother", "woman", "memory", "childhood"), "hallway_mirror"),
    (("letter", "second envelope", "another envelope", "envelope"), "stairwell"),
]

BEATS = [
    ("WIDE ESTABLISHING", "wide"),
    ("THE OBJECT", "detail"),
    ("THE CLUE", "clue"),
    ("THE REACTION", "reaction"),
    ("THE REVEAL", "reveal"),
    ("THE DECISION", "decision"),
]
CAMERAS = ["zoom_in", "pan_left", "zoom_shake", "pan_vertical", "dolly_in", "zoom_out"]
EPISODES = [
    {"episode": f"EP{i:02d}", "scenes": [{"name": BEATS[j][0], "camera": CAMERAS[j]} for j in range(SCENES_PER_EPISODE)]}
    for i in range(1, 31)
]


def classify_artifact() -> str:
    return CLASSIFICATION


def episode_profile(episode_id: str) -> dict:
    if episode_id not in {f"EP{i:02d}" for i in range(1, 31)}:
        raise ValueError(f"Unknown episode: {episode_id}")
    source = SOURCE_EPISODES[int(episode_id[2:]) - 1]
    text = " ".join(str(v).lower() for v in source)
    key = EXPLICIT_PROFILES.get(episode_id)
    if key is None:
        key = next((profile for words, profile in KEYWORD_PROFILES if any(word in text for word in words)), None)
    if key is None:
        # Deterministic rotation across physically distinct locations, not color-only variation.
        candidates = ["courthouse", "bedroom", "stairwell", "photo_archive", "locked_room", "hallway_mirror"]
        key = candidates[(int(episode_id[2:]) - 1) % len(candidates)]
    profile = dict(PROFILES[key])
    profile["episode"] = episode_id
    profile["title"], profile["hook"], profile["body"] = source
    profile["profile_key"] = key
    return profile


def motion_gate(scene_diffs: list[list[float]]) -> bool:
    return len(scene_diffs) == SCENES_PER_EPISODE and all(
        len(pair) == 2 and all(math.isfinite(v) and 3.0 < v < 85.0 for v in pair)
        for pair in scene_diffs
    )


def run(command: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=True, text=True, capture_output=True)


def load_font(size: int):
    for name in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                 "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"):
        if Path(name).exists():
            return ImageFont.truetype(name, size=size)
    return ImageFont.load_default()


def draw_scene(profile: dict, beat_index: int, output: Path, include_text: bool = True) -> None:
    """Draw location-specific geometry and story props for one beat."""
    base = profile["palette"]
    accent = profile["accent"]
    im = Image.new("RGB", (WIDTH, HEIGHT))
    pixels = im.load()
    for y in range(HEIGHT):
        fy = 1.0 - 0.25 * y / HEIGHT
        for x in range(WIDTH):
            edge = min(x / WIDTH, 1 - x / WIDTH, y / HEIGHT, 1 - y / HEIGHT)
            shade = max(0.56, min(1.0, edge * 3.4 + 0.59))
            grain = ((x * 17 + y * 31 + beat_index * 19) % 7) - 3
            pixels[x, y] = tuple(max(0, min(255, int(c * fy * shade) + grain)) for c in base)
    d = ImageDraw.Draw(im, "RGBA")
    gold = (*accent, 225)
    # Ground plane and location-specific structural elements.
    d.rectangle((0, 835, WIDTH, HEIGHT), fill=(13, 14, 18, 100))
    key = profile["profile_key"]
    if key == "front_door":
        d.rectangle((95, 210, 625, 1000), fill=(75, 53, 38, 245), outline=gold, width=6)
        d.rectangle((128, 245, 592, 965), outline=(18, 23, 30, 255), width=8)
        d.ellipse((540, 575, 565, 600), fill=gold)
        d.rectangle((500, 290, 612, 415), fill=(18, 22, 27, 255), outline=gold, width=4)
        d.text((556, 350), "12", font=load_font(30), fill=gold, anchor="mm")
        d.rectangle((235, 360, 485, 490), fill=(31, 34, 38, 255), outline=gold, width=4)
    elif key == "kitchen":
        d.rectangle((0, 665, WIDTH, 790), fill=(98, 68, 45, 255), outline=gold, width=3)
        d.rectangle((70, 175, 650, 555), fill=(15, 20, 28, 255), outline=(170, 155, 125, 200), width=8)
        d.line((360, 180, 360, 550), fill=gold, width=4)
        d.ellipse((130, 555, 255, 690), fill=(26, 30, 34, 255), outline=gold, width=5)
        d.arc((205, 575, 275, 655), 270, 90, fill=gold, width=7)
        d.ellipse((390, 590, 540, 620), fill=(18, 19, 22, 220))
    elif key == "office":
        d.rectangle((50, 620, 670, 790), fill=(88, 61, 42, 255), outline=gold, width=4)
        for i in range(5):
            x, y = 80 + i * 103, 540 + (i % 2) * 60
            d.polygon([(x, y), (x + 90, y - 18), (x + 130, y + 90), (x + 30, y + 110)],
                      fill=(225 - i * 7, 216 - i * 5, 191 - i * 3, 245), outline=gold)
        d.rectangle((470, 160, 655, 440), fill=(37, 43, 48, 245), outline=gold, width=4)
        for i in range(4):
            d.line((490, 200 + i * 50, 635, 220 + i * 42), fill=(170, 157, 132, 220), width=3)
        d.line((120, 650, 225, 570), fill=(175, 175, 180, 255), width=8)
        d.line((225, 570, 250, 590), fill=(175, 175, 180, 255), width=8)
    elif key == "attic_archive":
        d.polygon([(30, 400), (360, 150), (690, 400)], fill=(66, 48, 36, 245), outline=gold)
        d.rectangle((55, 400, 665, 960), fill=(48, 39, 33, 240), outline=gold, width=5)
        d.rectangle((135, 570, 585, 865), fill=(96, 64, 39, 255), outline=(201, 157, 86, 255), width=8)
        d.line((135, 650, 585, 650), fill=(36, 26, 20, 255), width=8)
        d.ellipse((330, 635, 390, 695), fill=(125, 35, 38, 255), outline=gold, width=5)
        d.polygon([(460, 735), (520, 710), (560, 790), (490, 810)], fill=(218, 204, 177, 245))
    elif key in ("photo_archive", "records_room", "courthouse"):
        d.rectangle((70, 190, 650, 1030), fill=(42, 40, 37, 220), outline=gold, width=4)
        for i in range(4):
            y = 290 + i * 160
            d.rectangle((100, y, 620, y + 115), fill=(105, 81, 55, 230), outline=gold, width=3)
            for j in range(4):
                x = 125 + j * 120
                d.rectangle((x, y + 20, x + 72, y + 90), fill=(218, 205, 178, 230), outline=(82, 68, 50, 255), width=2)
    elif key == "locked_room":
        d.rectangle((100, 190, 620, 1050), fill=(30, 31, 36, 255), outline=gold, width=6)
        d.ellipse((535, 565, 560, 590), fill=gold)
        for i in range(4):
            d.rectangle((130 + i * 110, 350, 220 + i * 110, 470), fill=(216, 206, 183, 230), outline=gold, width=3)
            d.line((140 + i * 110, 370, 208 + i * 110, 445), fill=(120, 65, 57, 220), width=4)
    elif key in ("bedroom", "apartment"):
        d.rectangle((70, 190, 650, 570), fill=(12, 17, 27, 255), outline=gold, width=5)
        d.line((360, 195, 360, 565), fill=gold, width=3)
        d.rectangle((90, 720, 630, 850), fill=(57, 48, 43, 255), outline=gold, width=4)
        d.ellipse((300, 625, 420, 745), fill=(15, 18, 23, 255), outline=gold, width=5)
        d.rectangle((345, 650, 375, 720), fill=(118, 175, 205, 200))
    else:  # hallway mirror / stairwell
        d.polygon([(0, 900), (720, 540), (720, 620), (0, 1000)], fill=(15, 17, 22, 190))
        d.rectangle((235, 190, 485, 610), fill=(14, 18, 24, 240), outline=gold, width=5)
        d.ellipse((300, 270, 420, 480), fill=(3, 4, 7, 200), outline=(180, 175, 160, 170), width=3)
        d.line((0, 650, 720, 920), fill=(180, 170, 151, 70), width=3)

    # Story object foreground changes position/scale per beat for composition variation.
    cx = [360, 360, 500, 235, 470, 360][beat_index]
    cy = [670, 735, 630, 760, 690, 750][beat_index]
    scale = [0.72, 1.0, 0.86, 0.76, 1.08, 0.92][beat_index]
    w, h = int(250 * scale), int(160 * scale)
    paper = (232, 222, 198, 250)
    d.rounded_rectangle((cx - w//2, cy - h//2, cx + w//2, cy + h//2),
                        radius=10, fill=paper, outline=gold, width=5)
    d.line((cx - w//2 + 8, cy - h//2 + 10, cx, cy + h//2 - 8,
            cx + w//2 - 8, cy - h//2 + 10), fill=(132, 101, 72, 255), width=4)
    if beat_index in (2, 4):
        d.ellipse((cx - 24, cy - 18, cx + 24, cy + 30), fill=(124, 35, 40, 255), outline=gold, width=3)
    if beat_index == 3:
        # Reaction beat: two human-like silhouettes as visual shorthand, not real people.
        d.ellipse((95, 390, 200, 500), fill=(0, 0, 0, 210))
        d.polygon([(80, 500), (215, 500), (245, 720), (55, 720)], fill=(0, 0, 0, 190))
        d.ellipse((520, 390, 625, 500), fill=(0, 0, 0, 225))
        d.polygon([(505, 500), (640, 500), (665, 720), (480, 720)], fill=(0, 0, 0, 205))

    # Text is rendered on a separate transparent layer after background crossfades.
    if include_text:
        small = load_font(21)
        title_font = load_font(34)
        body_font = load_font(24)
        d.text((WIDTH // 2, 95), f'{profile["episode"]}  •  {profile["place"]}',
               font=small, fill=(239, 224, 190, 255), anchor="mm")
        d.text((WIDTH // 2, 170), BEATS[beat_index][0], font=title_font,
               fill=(255, 248, 226, 255), anchor="mm", stroke_width=2, stroke_fill=(0, 0, 0, 220))
        story_line = [profile["title"], profile["hook"], profile["body"],
                      "A clue changes the scene.", "The pieces finally connect.", "One choice remains."][beat_index]
        story_line = re.sub(r"\s+", " ", story_line).strip()[:100]
        d.multiline_text((60, 1030), story_line, font=body_font,
                         fill=(246, 239, 220, 255), spacing=7, stroke_width=1, stroke_fill=(0, 0, 0, 220))
    d.rounded_rectangle((32, 32, WIDTH - 32, HEIGHT - 32), radius=24, outline=gold, width=2)
    im.save(output)


def draw_text_overlay(profile: dict, beat_index: int, output: Path) -> None:
    """Render captions separately so xfade never blends outgoing and incoming text."""
    im = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    small, title_font, body_font = load_font(21), load_font(34), load_font(24)
    d.text((WIDTH // 2, 95), f'{profile["episode"]}  •  {profile["place"]}',
           font=small, fill=(239, 224, 190, 255), anchor="mm",
           stroke_width=1, stroke_fill=(0, 0, 0, 220))
    d.text((WIDTH // 2, 170), BEATS[beat_index][0], font=title_font,
           fill=(255, 248, 226, 255), anchor="mm", stroke_width=2,
           stroke_fill=(0, 0, 0, 220))
    story_line = [profile["title"], profile["hook"], profile["body"],
                  "A clue changes the scene.", "The pieces finally connect.", "One choice remains."][beat_index]
    story_line = textwrap.fill(re.sub(r"\s+", " ", story_line).strip()[:100], width=34)
    d.multiline_text((60, 1030), story_line, font=body_font,
                     fill=(246, 239, 220, 255), spacing=7, stroke_width=1,
                     stroke_fill=(0, 0, 0, 220))
    im.save(output)


def camera_filter(camera: str) -> str:
    if camera == "zoom_in":
        z, x, y = "min(zoom+0.0006,1.18)", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif camera == "pan_left":
        z, x, y = "1.10", "iw/2-(iw/zoom/2)+18*sin(on/35)", "ih/2-(ih/zoom/2)"
    elif camera == "zoom_shake":
        z, x, y = "max(1.18-0.0005*on,1.02)", "iw/2-(iw/zoom/2)+2*sin(on*1.7)", "ih/2-(ih/zoom/2)+2*cos(on*1.9)"
    elif camera == "pan_vertical":
        z, x, y = "1.10", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)+18*sin(on/35)"
    elif camera == "dolly_in":
        z, x, y = "min(zoom+0.0008,1.25)", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    else:
        z, x, y = "max(1.22-0.00065*on,1.02)", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    return f"zoompan=z='{z}':x='{x}':y='{y}':d=320:s={WIDTH}x{HEIGHT}:fps={FPS},format=yuv420p"


def build_xfade_filter() -> str:
    parts = [f"[{i}:v]settb=AVTB,setpts=PTS-STARTPTS,fps={FPS},format=yuv420p[v{i}]"
             for i in range(SCENES_PER_EPISODE)]
    previous = "[v0]"
    for i in range(1, SCENES_PER_EPISODE):
        out = "[vout]" if i == SCENES_PER_EPISODE - 1 else f"[x{i}]"
        parts.append(f"{previous}[v{i}]xfade=transition=fade:duration={TRANSITION:.1f}:offset={i * STEP_SECONDS:.6f}{out}")
        previous = out
    return ";".join(parts)


def build_text_overlay_filter() -> str:
    """Overlay one independently timed text layer per beat after background-only xfade."""
    parts = []
    previous = "[vout]"
    for i in range(SCENES_PER_EPISODE):
        start = i * STEP_SECONDS
        text_duration = STEP_SECONDS if i < SCENES_PER_EPISODE - 1 else CLIP_SECONDS
        end = start + text_duration
        fade_out_start = max(0.0, text_duration - 0.3)
        parts.append(
            f"[{SCENES_PER_EPISODE + i}:v]format=rgba,"
            f"fade=t=in:st=0:d=0.3:alpha=1,"
            f"fade=t=out:st={fade_out_start:.6f}:d=0.3:alpha=1,"
            f"setpts=PTS-STARTPTS+{start:.6f}/TB[txt{i}]"
        )
        out = "[vfinal]" if i == SCENES_PER_EPISODE - 1 else f"[vt{i}]"
        parts.append(
            f"{previous}[txt{i}]overlay=eof_action=pass:shortest=0:format=auto:"
            f"enable='gte(t,{start:.6f})*lt(t,{end:.6f})'{out}"
        )
        previous = out
    return ";".join(parts)


def image_diff(left: Image.Image, right: Image.Image) -> float:
    a = left.convert("L").resize((180, 320))
    b = right.convert("L").resize((180, 320))
    return float(ImageStat.Stat(ImageChops.difference(a, b)).mean[0])


def extract_frame(path: Path, at: float, output: Path) -> None:
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{at:.3f}",
                    "-i", str(path), "-frames:v", "1", str(output)],
                   check=True, capture_output=True)


def quality_gates(path: Path, profile: dict) -> dict:
    meta = json.loads(run(["ffprobe", "-v", "error", "-show_format", "-show_streams",
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
        audio_pass = volume not in ("-inf", "NOT_FOUND") and math.isfinite(float(volume)) and float(volume) > -60
    except ValueError:
        audio_pass = False
    frame_means = []
    scene_diffs = []
    with tempfile.TemporaryDirectory(prefix="envelope-story-qa-") as temp:
        temp_path = Path(temp)
        for pct in (10, 50, 90):
            frame = temp_path / f"frame{pct}.png"
            extract_frame(path, duration * pct / 100, frame)
            with Image.open(frame) as im:
                frame_means.append(float(ImageStat.Stat(im.convert("L")).mean[0]))
        # Two within-beat diffs for every 10-second beat. This prevents transitions
        # between scenes from masking a static scene.
        for i in range(SCENES_PER_EPISODE):
            times = [min(duration - 0.05, i * STEP_SECONDS + t) for t in (1.2, 4.8, 8.2)]
            frames = []
            for j, at in enumerate(times):
                frame = temp_path / f"motion_{i}_{j}.png"
                extract_frame(path, at, frame)
                with Image.open(frame) as im:
                    frames.append(im.copy())
            scene_diffs.append([image_diff(frames[0], frames[1]), image_diff(frames[1], frames[2])])
        # Contact sheet from six actual frames extracted from the encoded MP4.
        thumbs = []
        for i, at in enumerate((5, 15, 25, 35, 45, 55)):
            frame = temp_path / f"contact_{i}.png"
            extract_frame(path, at, frame)
            with Image.open(frame) as im:
                thumb = im.convert("RGB")
                thumb.thumbnail((180, 320))
                thumbs.append(thumb.copy())
        sheet = Image.new("RGB", (3 * 180, 2 * 320), (20, 20, 24))
        for i, thumb in enumerate(thumbs):
            sheet.paste(thumb, ((i % 3) * 180, (i // 3) * 320))
        sheet_path = path.with_name(f"{profile['episode']}_contact_sheet.png")
        sheet.save(sheet_path)
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    checks = {
        "duration_60s": 59.9 <= duration <= 60.1,
        "resolution_720x1280": (video.get("width"), video.get("height")) == (720, 1280),
        "video_h264": video.get("codec_name") == "h264",
        "audio_aac": audio.get("codec_name") == "aac",
        "full_decode": decode.returncode == 0,
        "sha256": len(sha) == 64,
        "audio_mean_volume_above_minus60db": audio_pass,
        "frames_10_50_90_not_black": len(frame_means) == 3 and all(v > 10 for v in frame_means),
        "within_scene_motion_all_six_beats": motion_gate(scene_diffs),
        "contact_sheet_created": (path.with_name(f"{profile['episode']}_contact_sheet.png")).exists(),
    }
    return {
        "episode": profile["episode"], "title": profile["title"], "place": profile["place"],
        "place_id": profile["place_id"], "objects": profile["objects"],
        "duration_sec": duration, "width": video.get("width"), "height": video.get("height"),
        "video_codec": video.get("codec_name"), "audio_codec": audio.get("codec_name"),
        "mean_volume_db": volume, "frame_mean_luminance_10_50_90": frame_means,
        "within_scene_motion_mean_diffs": scene_diffs, "sha256": sha,
        "size_bytes": path.stat().st_size, "artifact_class": classify_artifact(),
        "checks": checks, "all_pass": all(checks.values()),
        "contact_sheet": f"{profile['episode']}_contact_sheet.png",
    }


def render_episode(episode_id: str) -> dict:
    profile = episode_profile(episode_id)
    for executable in ("ffmpeg", "ffprobe", "espeak-ng"):
        if not shutil.which(executable):
            raise RuntimeError(f"Missing required free executable: {executable}")
    OUT.mkdir(parents=True, exist_ok=True)
    video_path = OUT / f"{episode_id}_60s_STORY_REMEDIATED.mp4"
    with tempfile.TemporaryDirectory(prefix="envelope-story-render-") as temp:
        tmp = Path(temp)
        clips, overlays = [], []
        for i, camera in enumerate(CAMERAS):
            still = tmp / f"scene_{i}.png"
            overlay = tmp / f"text_{i}.png"
            clip = tmp / f"scene_{i}.mp4"
            draw_scene(profile, i, still, include_text=False)
            draw_text_overlay(profile, i, overlay)
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                            "-loop", "1", "-framerate", str(FPS), "-i", str(still),
                            "-vf", camera_filter(camera), "-frames:v", "320", "-an",
                            "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                            "-pix_fmt", "yuv420p", "-r", str(FPS), str(clip)],
                           check=True, capture_output=True)
            clips.append(clip)
            overlays.append(overlay)
        audio = tmp / "narration.wav"
        narration = f'{profile["title"]}. {profile["hook"]} {profile["body"]}'
        subprocess.run(["espeak-ng", "-s", "145", "-w", str(audio), narration],
                       check=True, capture_output=True)
        command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
        for clip in clips:
            command += ["-i", str(clip)]
        for i, overlay in enumerate(overlays):
            text_duration = STEP_SECONDS if i < SCENES_PER_EPISODE - 1 else CLIP_SECONDS
            command += ["-loop", "1", "-framerate", str(FPS), "-t",
                        f"{text_duration:.6f}", "-i", str(overlay)]
        command += ["-i", str(audio), "-filter_complex",
                    build_xfade_filter() + ";" + build_text_overlay_filter() + ";[12:a]apad=pad_dur=60[aout]",
                    "-map", "[vfinal]", "-map", "[aout]", "-t", "60",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                    "-pix_fmt", "yuv420p", "-r", str(FPS),
                    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
                    str(video_path)]
        subprocess.run(command, check=True, capture_output=True)
    qa = quality_gates(video_path, profile)
    qa_path = OUT / f"{episode_id}_qa.json"
    qa_path.write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
    if not qa["all_pass"]:
        raise RuntimeError(f"QUALITY_GATES_FAILED: {episode_id}: {json.dumps(qa, ensure_ascii=False)}")
    return {"video": str(video_path), "qa": str(qa_path), "contact_sheet": str(OUT / qa["contact_sheet"]),
            "artifact_class": classify_artifact(), "all_pass": True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ep", default="EP01")
    parser.add_argument("--qa", type=Path, help="Re-run measured QA on an existing MP4")
    args = parser.parse_args()
    if args.qa:
        profile = episode_profile(args.qa.name[:4])
        result = quality_gates(args.qa, profile)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if not result["all_pass"]:
            raise SystemExit(1)
    else:
        print(json.dumps(render_episode(args.ep), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
