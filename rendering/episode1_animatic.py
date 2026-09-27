#!/usr/bin/env python3
"""Deterministic, evidence-first fallback renderer for THE LAST VOICEMAIL.

This is NOT AI video generation. It is a free production fallback that converts
verified still references plus the verified Shot 1 MP4 into a real 9:16 MP4
using FFmpeg, Ken-Burns motion, captions, and local espeak-ng speech.
It is intentionally isolated from the external video-generation adapter.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

W = 720
H = 1280
FPS = 24
ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "build" / "episode1"
ASSETS = WORK / "assets"
SEGMENTS = WORK / "segments"
AUDIO = WORK / "audio"
OUT = ROOT / "build" / "THE_LAST_VOICEMAIL_Episode1_Fallback_Animatic.mp4"
MANIFEST = ROOT / "build" / "THE_LAST_VOICEMAIL_Episode1_Fallback_Animatic.manifest.json"

URLS = {
    "shot1": "https://d8j0ntlcm91z4.cloudfront.net/user_3HbVmnPxO34s5Uv14BNfdNSi1VZ/hf_20260927_021445_3378447b-f005-48db-aeb0-382714cd43b1.mp4",
    "maya": "https://cdn.creativeclaw.co/u/9ed00843/images/e83041d3-c03b-4104-89a2-1988d077763c.jpg",
    "daniel": "https://cdn.creativeclaw.co/u/9ed00843/images/8dfda36b-da6a-452a-8798-f63088cf7959.jpg",
    "phone": "https://cdn.creativeclaw.co/u/9ed00843/images/f8c0a0b5-1c33-49ef-8547-ae642e49bc59.jpg",
    "apartment": "https://cdn.creativeclaw.co/u/9ed00843/images/0227258c-f72d-4231-a83e-14f6fdd38da9.jpg",
}

SCENES = [
    (1, 5, "shot1", None, "Maya", "Hello?"),
    (2, 13, "maya", "maya", "Maya", "Hello?"),
    (3, 4, "phone", None, None, None),
    (4, 20, "maya", "maya", "Maya", "If you're hearing this, it's already started. Tomorrow at eight seventeen, Daniel will ask you to leave the house. Do not go."),
    (5, 8, "phone", "maya", "Maya", "That's impossible."),
    (6, 8, "daniel", "daniel", "Daniel", "Who were you talking to?"),
    (7, 18, "daniel", "maya", "Maya", "Nobody."),
    (8, 10, "maya", None, None, None),
    (9, 6, "phone", None, None, None),
    (10, 3, "title", None, None, None),
]

CAPTIONS = [
    (0.0, 5.0, "Hello?"),
    (22.0, 42.0, "If you're hearing this, it's already started.\nTomorrow at 8:17, Daniel will ask you to leave the house. Do not go."),
    (42.0, 50.0, "That's impossible."),
    (50.0, 58.0, "Who were you talking to?"),
    (58.0, 76.0, "Nobody."),
]

def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)

def download(name: str, url: str) -> Path:
    dest = ASSETS / name
    if not dest.exists() or dest.stat().st_size == 0:
        print(f"Downloading {name}")
        urllib.request.urlretrieve(url, dest)
    if dest.stat().st_size == 0:
        raise RuntimeError(f"Downloaded empty asset: {name}")
    return dest

def ffprobe_json(path: Path) -> dict:
    p = subprocess.run(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    )
    return json.loads(p.stdout)

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def seconds_for_scene(duration: int) -> int:
    return duration * FPS

def make_srt(path: Path) -> None:
    def stamp(t: float) -> str:
        ms = int(round(t * 1000))
        h, ms = divmod(ms, 3600000)
        m, ms = divmod(ms, 60000)
        s, ms = divmod(ms, 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    lines = []
    for i, (a, b, text) in enumerate(CAPTIONS, 1):
        lines += [str(i), f"{stamp(a)} --> {stamp(b)}", text, ""]
    path.write_text("\n".join(lines), encoding="utf-8")

def make_still_segment(image: Path, duration: int, out: Path, reverse: bool = False) -> None:
    frames = seconds_for_scene(duration)
    if reverse:
        zoom = "max(zoom-0.0008,1.0)"
    else:
        zoom = "min(zoom+0.0008,1.08)"
    vf = (
        f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,"
        f"crop={W*2}:{H*2},"
        f"zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={frames}:s={W}x{H}:fps={FPS},format=yuv420p"
    )
    run(["ffmpeg","-y","-v","error","-loop","1","-i",str(image),"-t",str(duration),
         "-vf",vf,"-an","-c:v","libx264","-preset","veryfast","-crf","22","-movflags","+faststart",str(out)])

def make_shot1_segment(src: Path, out: Path) -> None:
    vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},format=yuv420p"
    run(["ffmpeg","-y","-v","error","-i",str(src),"-t","5","-vf",vf,
         "-c:v","libx264","-preset","veryfast","-crf","22","-c:a","aac","-b:a","96k",str(out)])

def make_title(out: Path) -> None:
    vf = (
        "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
        "text='THE LAST VOICEMAIL':fontcolor=white:fontsize=42:x=(w-text_w)/2:y=(h-text_h)/2-20,"
        "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
        "text='EPISODE 1 — THE CALL':fontcolor=white:fontsize=22:x=(w-text_w)/2:y=(h-text_h)/2+45"
    )
    run(["ffmpeg","-y","-v","error","-f","lavfi","-i",f"color=c=black:s={W}x{H}:d=3:r={FPS}",
         "-vf",vf,"-an","-c:v","libx264","-preset","veryfast","-crf","22","-pix_fmt","yuv420p",str(out)])

def make_voice(text: str, voice: str, out: Path) -> None:
    if not text:
        run(["ffmpeg","-y","-v","error","-f","lavfi","-i","anullsrc=r=48000:cl=stereo",
             "-t","0.1","-c:a","pcm_s16le",str(out)])
        return
    run(["espeak-ng","-v",voice,"-s","150","-p","45","-w",str(out),text])

def pad_audio(src: Path, duration: int, out: Path) -> None:
    run(["ffmpeg","-y","-v","error","-i",str(src),"-af",f"apad=pad_dur={duration}",
         "-t",str(duration),"-ar","48000","-ac","2","-c:a","pcm_s16le",str(out)])

def main() -> None:
    for d in (WORK, ASSETS, SEGMENTS, AUDIO, OUT.parent):
        d.mkdir(parents=True, exist_ok=True)

    for key, url in URLS.items():
        download(f"{key}{'.mp4' if key=='shot1' else '.jpg'}", url)

    # Segment video.
    for n, duration, asset, voice, _, _ in SCENES:
        out = SEGMENTS / f"{n:02d}.mp4"
        if asset == "shot1":
            make_shot1_segment(ASSETS / "shot1.mp4", out)
        elif asset == "title":
            make_title(out)
        else:
            make_still_segment(ASSETS / f"{asset}.jpg", duration, out, reverse=(n % 2 == 0))

    # Segment audio, preserving Shot 1's observed source audio and adding dialogue.
    for n, duration, asset, voice, speaker, text in SCENES:
        out = AUDIO / f"{n:02d}.wav"
        if n == 1:
            spoken = AUDIO / "01_voice.wav"
            make_voice(text or "", "en-us+f3", spoken)
            run(["ffmpeg","-y","-v","error","-i",str(ASSETS/"shot1.mp4"),"-t","5",
                 "-i",str(spoken),"-filter_complex",
                 "[0:a]volume=0.65[a0];[1:a]volume=1.2[a1];[a0][a1]amix=inputs=2:duration=longest:dropout_transition=0[a]",
                 "-map","[a]","-ar","48000","-ac","2","-c:a","pcm_s16le",str(out)])
        elif text:
            spoken = AUDIO / f"{n:02d}_voice.wav"
            make_voice(text, "en-us+f3" if speaker == "Maya" else "en-us+m3", spoken)
            pad_audio(spoken, duration, out)
        else:
            run(["ffmpeg","-y","-v","error","-f","lavfi","-i","anullsrc=r=48000:cl=stereo",
                 "-t",str(duration),"-ar","48000","-ac","2","-c:a","pcm_s16le",str(out)])

    # Concat video and audio independently, then mux.
    vlist = WORK / "video_concat.txt"
    alist = WORK / "audio_concat.txt"
    vlist.write_text("".join(f"file '{SEGMENTS/f'{n:02d}.mp4'}'\n" for n, *_ in SCENES), encoding="utf-8")
    alist.write_text("".join(f"file '{AUDIO/f'{n:02d}.wav'}'\n" for n, *_ in SCENES), encoding="utf-8")

    vcat = WORK / "video_cat.mp4"
    acat = WORK / "audio_cat.wav"
    run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(vlist),
         "-c","copy",str(vcat)])
    run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(alist),
         "-c:a","pcm_s16le",str(acat)])

    srt = WORK / "episode1.srt"
    make_srt(srt)

    # Burn captions and mux final audio.
    caption_vf = (
        f"subtitles={srt}:force_style='FontName=DejaVu Sans,FontSize=18,"
        "Outline=2,Shadow=0,Alignment=2,MarginV=80'"
    )
    run(["ffmpeg","-y","-v","error","-i",str(vcat),"-i",str(acat),
         "-vf",caption_vf,"-map","0:v:0","-map","1:a:0","-t","95",
         "-c:v","libx264","-preset","medium","-crf","21","-c:a","aac","-b:a","128k",
         "-movflags","+faststart",str(OUT)])

    # Evidence: probe + full decode + hash.
    probe = ffprobe_json(OUT)
    decode = subprocess.run(["ffmpeg","-v","error","-i",str(OUT),"-f","null","-"],
                            capture_output=True, text=True)
    if decode.returncode != 0:
        raise RuntimeError("FINAL_DECODE_FAILED: " + decode.stderr[-2000:])
    duration = float(probe["format"].get("duration", "0"))
    streams = probe.get("streams", [])
    if duration < 94.5 or duration > 95.5:
        raise RuntimeError(f"Unexpected final duration: {duration}")
    if not any(s.get("codec_type") == "video" for s in streams):
        raise RuntimeError("No video stream")
    if not any(s.get("codec_type") == "audio" for s in streams):
        raise RuntimeError("No audio stream")

    manifest = {
        "artifact": str(OUT),
        "mode": "DETERMINISTIC_MOTION_FALLBACK",
        "evidence_status": "OBSERVED",
        "episode": "THE LAST VOICEMAIL / Episode 1",
        "duration_sec": duration,
        "sha256": sha256(OUT),
        "size_bytes": OUT.stat().st_size,
        "probe": probe,
        "decode": "FFMPEG_DECODE_PASS",
        "source_shot1_sha256": sha256(ASSETS / "shot1.mp4"),
        "source_assets": URLS,
        "ai_video_generation_used_for_fallback": False,
        "publication": "NOT_PERFORMED",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    main()
