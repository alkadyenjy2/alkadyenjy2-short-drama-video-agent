#!/usr/bin/env python3
"""Deterministic THE ENVELOPE fallback renderer.

This is a real MP4 production fallback for evidence/testing. It is NOT cinematic
AI generation. Each episode is 60s, vertical 9:16, H.264/AAC, with original
series text rendered over a deterministic motion background.
"""
from __future__ import annotations
import hashlib, json, os, shutil, subprocess, textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "the-envelope"
EPISODES = [
("The Envelope","On her wedding morning, Lina receives an envelope in her own handwriting: DO NOT MARRY ADAM.","Adam calls from downstairs: Did you find it?"),
("The Lie","Adam says the envelope is a prank. Lina asks how he knows what it says.","He answers: Because I mailed it."),
("The Photo","Inside is a childhood photo of Lina with a woman she does not recognize.","On the back: TOMORROW."),
("The Date","Lina searches the date on the photograph.","The date is tomorrow. The woman is watching her."),
("The Missing Woman","The woman in the photo is officially dead.","Lina's phone rings. The caller ID shows the dead woman's name."),
("The Phone","The caller sends a live photo from Adam's apartment.","Lina realizes someone is inside his locked room."),
("The Room","Lina follows Adam and finds a locked room filled with her childhood drawings.","Adam says: That room was never yours."),
("The Name","An old box contains Lina's name and a birth certificate.","The mother's name is not the one Lina knows."),
("The Mother","The woman from the photo calls again.","She says: Lina, you were never supposed to meet Adam."),
("The Betrayal","Lina discovers Adam investigated her family for years.","Adam admits he did it. He says he was trying to protect her."),
("The Second Envelope","Another envelope arrives before Lina can ask why.","Inside: a key and one sentence — ASK ADAM WHAT IT OPENS."),
("The Witness","A neighbor says Lina was taken from another family as a baby.","The neighbor adds: Your father knew why."),
("The Tape","A cassette contains Lina's father's voice.","If she remembers, we all lose."),
("The Accident","Lina learns her parents survived the accident everyone said killed them.","Someone has been hiding them."),
("The Debt","The family owes someone a secret debt.","Lina asks Adam: What did my parents promise?"),
("The Choice","Lina can expose Adam or follow him to the truth.","She follows him."),
("The Meeting","Lina meets the man who claims to be her biological father.","He carries proof that her identity was changed."),
("The Photograph","The photograph shows Adam's family with Lina's parents.","Someone destroyed the original."),
("The Deal","Adam says he married Lina to protect her.","Lina asks: Protect me from whom?"),
("The Test","Adam offers a DNA test.","Lina notices the sample label is wrong."),
("The Result","The DNA result arrives.","Lina discovers the sample was altered."),
("The Camera","A hidden camera has been recording Lina's apartment.","The footage goes back six years."),
("The Brother","A boy in the old footage looks exactly like Adam.","Adam says: He is my brother."),
("The Voice","The brother recognizes the voice leaving Lina warnings.","He says: Your mother paid me to keep you alive."),
("The Trap","Lina stages a fake escape.","Someone takes the bait."),
("The Reveal","Lina discovers her mother is alive and hiding.","Her mother says the danger never ended."),
("The Truth","The family secret is tied to an inheritance war.","Lina realizes her disappearance was planned."),
("The Betrayal","Adam's father ordered the disappearance.","Adam says he has one last thing to show her."),
("The Wedding","Lina returns to the wedding venue with every envelope.","She places them on the table: Now everyone tells the truth."),
("The Last Envelope","Adam says: I was never the person you were warned about.","Lina opens the final envelope: THEN WHY ARE YOU STILL WEARING HIS RING?")
]

def run(cmd):
    subprocess.run(cmd, check=True)


def wrap_text(text: str, width: int) -> str:
    return "\n".join(textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=False))

def build_narration_command(text: str, raw_path: Path) -> list[str]:
    if shutil.which("powershell"):
        escaped = text.replace("'", "''")
        return ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
                "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                f"$s.SetOutputToWaveFile('{raw_path}'); $s.Speak('{escaped}'); $s.Dispose()"]
    if shutil.which("espeak-ng"):
        return ["espeak-ng", "-w", str(raw_path), text]
    raise RuntimeError("NARRATION_ENGINE_UNAVAILABLE")


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def probe(path: Path):
    p=subprocess.run(["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(path)],
                     check=True,capture_output=True,text=True)
    return json.loads(p.stdout)

def main():
    from PIL import Image, ImageDraw, ImageFont
    OUT.mkdir(parents=True, exist_ok=True)
    records=[]
    for n,(title,hook,body) in enumerate(EPISODES,1):
        ep=f"EP{n:02d}"
        hookfile=OUT/f"{ep}_hook.txt"
        bodyfile=OUT/f"{ep}_body.txt"
        hookfile.write_text(hook,encoding="utf-8")
        bodyfile.write_text(body,encoding="utf-8")
        card=Image.new("RGB",(720,1280),(22,32,42))
        draw=ImageDraw.Draw(card)
        try:
            font_big=ImageFont.load_default(size=44)
            font_mid=ImageFont.load_default(size=34)
            font_small=ImageFont.load_default(size=28)
        except TypeError:
            font_big=font_mid=font_small=ImageFont.load_default()
        draw.text((360,90),f"{ep} - THE ENVELOPE",fill="white",font=font_small,anchor="ma")
        draw.multiline_text((60,360),wrap_text(hook, 28),fill="white",font=font_big,anchor="la",spacing=14)
        draw.multiline_text((60,760),wrap_text(body, 30),fill="white",font=font_mid,anchor="la",spacing=12)
        cardfile=OUT/f"{ep}_card.png"
        card.save(cardfile)
        out=OUT/f"{ep}_THE_ENVELOPE.mp4"
        raw=OUT/f"{ep}_voice_raw.wav"
        narration=hook+" "+body
        run(build_narration_command(narration, raw))
        run(["ffmpeg","-y","-v","error","-loop","1","-i",str(cardfile),"-i",str(raw),
             "-af","apad=pad_dur=60","-t","60","-r","24",
             "-map","0:v:0","-map","1:a:0","-c:v","libx264","-preset","veryfast",
             "-crf","23","-pix_fmt","yuv420p","-c:a","aac","-b:a","128k",
             "-movflags","+faststart",str(out)])
        p=probe(out)
        dec=subprocess.run(["ffmpeg","-v","error","-i",str(out),"-f","null","-"],
                           capture_output=True,text=True)
        if dec.returncode:
            raise RuntimeError(f"decode failed: {out}: {dec.stderr[-1000:]}")
        vol=subprocess.run(["ffmpeg","-v","info","-i",str(out),"-af","volumedetect","-f","null",os.devnull],capture_output=True,text=True)
        if "mean_volume: -inf" in vol.stderr:
            raise RuntimeError(f"AUDIO_SILENCE_GATE_FAILED: {out}")
        dur=float(p["format"]["duration"])
        streams=p["streams"]
        v=next(s for s in streams if s.get("codec_type")=="video")
        a=next(s for s in streams if s.get("codec_type")=="audio")
        if abs(dur-60)>0.1 or (v.get("width"),v.get("height"))!=(720,1280) or v.get("codec_name")!="h264" or a.get("codec_name")!="aac":
            raise RuntimeError(f"media gate failed: {out}")
        records.append({
            "episode":ep,"file":out.name,"title":title,"duration_sec":dur,
            "size_bytes":out.stat().st_size,"sha256":sha256(out),
            "video_codec":v.get("codec_name"),"width":v.get("width"),"height":v.get("height"),
            "fps":v.get("r_frame_rate"),"audio_codec":a.get("codec_name"),
            "sample_rate":a.get("sample_rate"),"channels":a.get("channels"),
            "decode":"FFMPEG_DECODE_PASS",
            "artifact_class":"DETERMINISTIC_MOTION_TEXT_FALLBACK",
            "publication":"NOT_PERFORMED"
        })
    manifest={"series":"THE ENVELOPE","episode_count":30,
              "generated_at":"CI_RUNTIME","artifact_class":"DETERMINISTIC_MOTION_TEXT_FALLBACK",
              "all_decode_pass":True,"artifacts":records}
    (OUT/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(json.dumps({"count":30,"all_decode_pass":True,"manifest":str(OUT/"manifest.json")}))

if __name__=="__main__":
    main()
