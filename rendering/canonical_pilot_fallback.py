#!/usr/bin/env python3
"""Render the canonical Pilot 001 story spine as real deterministic motion episodes.
This is a canonical story render, not AI video generation.
"""
from __future__ import annotations
import hashlib, json, shutil, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/"assets"/"pilot001"
OUT=ROOT/"build"/"canonical_pilot"
W,H,FPS=720,1280,24
STORY_SOURCE="https://app.notion.com/p/3e00199a7db0811cb15af6dcf5ab5752"
EPISODES={
2:("8:17",["8:16 AM. Maya watches the clock.","Daniel asks her to leave exactly as predicted.","He says there is a gas leak, but Maya sees no evidence.","The phone vibrates.","LOOK UNDER THE KITCHEN FLOORBOARD."]),
3:("The Photo",["Maya finds an old photo under the floorboard.","Daniel is standing beside a woman tied to the old accident.","The woman died one year before Maya met Daniel.","Maya turns the photo over.","The handwritten date matches the future voicemail."]),
4:("The Lie",["Daniel notices the photo is missing.","He says the woman was an old colleague.","He says the accident was investigated.","Maya checks the official story.","One witness statement is missing. The witness is Maya's mother."]),
5:("The Source",["The voicemail uses a private childhood phrase.","Maya realizes the caller knows her family history.","Daniel did not cause the original accident.","But Daniel knows who did.","Tomorrow, ask Daniel who paid for the funeral."]),
6:("The Last Voicemail",["Maya asks Daniel about the funeral payment.","Daniel admits he has been protecting someone.","The voice on the phone is someone Maya believed died.","The accident was staged.","Maya was the real intended target. A second unknown number calls."]),
}
PATTERNS={
2:["maya","phone","apartment","daniel","maya","phone","daniel","phone","maya","apartment"],
3:["maya","apartment","phone","maya","daniel","phone","maya","apartment","phone","maya"],
4:["daniel","maya","phone","daniel","apartment","maya","phone","daniel","maya","phone"],
5:["maya","phone","apartment","maya","phone","daniel","maya","phone","apartment","maya"],
6:["maya","daniel","phone","maya","apartment","phone","maya","daniel","phone","maya"],
}
DURS=[9,10,9,10,9,10,9,10,9,10]
VOICE_POS=[2,4,6,8,10]

def run(cmd):
    subprocess.run(cmd,check=True)
def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest().upper()
def probe(p):
    r=subprocess.run(["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(p)],check=True,capture_output=True,text=True)
    return json.loads(r.stdout)
def render(ep,title,lines):
    epdir=OUT/f"EP{ep:02d}"; seg=epdir/"segments"; aud=epdir/"audio"
    seg.mkdir(parents=True,exist_ok=True); aud.mkdir(parents=True,exist_ok=True)
    assets={"maya":"Maya.jpg","daniel":"Daniel.jpg","phone":"Phone.jpg","apartment":"Apartment.jpg"}
    for i,(name,dur) in enumerate(zip(PATTERNS[ep],DURS),1):
        vf=(f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,"
            f"crop={W*2}:{H*2},zoompan=z='min(zoom+0.0008,1.08)':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={dur*FPS}:s={W}x{H}:fps={FPS},format=yuv420p")
        run(["ffmpeg","-y","-v","error","-loop","1","-i",str(ASSETS/assets[name]),
             "-t",str(dur),"-vf",vf,"-an","-c:v","libx264","-preset","veryfast","-crf","22",
             "-movflags","+faststart",str(seg/f"{i:02d}.mp4")])
        wav=aud/f"{i:02d}.wav"
        if i in VOICE_POS and shutil.which("espeak-ng"):
            raw=aud/f"{i:02d}_raw.wav"; line=lines[VOICE_POS.index(i)]
            voice="en-us+f3" if i in (2,6,10) else "en-us+m3"
            run(["espeak-ng","-v",voice,"-s","150","-p","45","-w",str(raw),line])
            run(["ffmpeg","-y","-v","error","-i",str(raw),"-af",f"apad=pad_dur={dur}",
                 "-t",str(dur),"-ar","48000","-ac","2","-c:a","pcm_s16le",str(wav)])
        else:
            run(["ffmpeg","-y","-v","error","-f","lavfi","-i","anullsrc=r=48000:cl=stereo",
                 "-t",str(dur),"-ar","48000","-ac","2","-c:a","pcm_s16le",str(wav)])
    vl=epdir/"video.txt"; al=epdir/"audio.txt"
    vl.write_text("".join(f"file '{seg/f'{i:02d}.mp4'}'\n" for i in range(1,11)))
    al.write_text("".join(f"file '{aud/f'{i:02d}.wav'}'\n" for i in range(1,11)))
    vcat=epdir/"vcat.mp4"; acat=epdir/"acat.wav"
    run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(vl),"-c","copy",str(vcat)])
    run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(al),"-c:a","pcm_s16le",str(acat)])
    out=epdir/f"THE_LAST_VOICEMAIL_EP{ep:02d}_Canonical_Fallback.mp4"
    safe=title.replace("'","").replace(":","-")
    vf=f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='THE LAST VOICEMAIL - EP {ep:02d} - {safe}':fontcolor=white:fontsize=24:x=(w-text_w)/2:y=80"
    run(["ffmpeg","-y","-v","error","-i",str(vcat),"-i",str(acat),"-vf",vf,"-map","0:v:0","-map","1:a:0",
         "-t","95","-c:v","libx264","-preset","medium","-crf","21","-c:a","aac","-b:a","128k","-movflags","+faststart",str(out)])
    p=probe(out)
    dec=subprocess.run(["ffmpeg","-v","error","-i",str(out),"-f","null","-"],capture_output=True,text=True)
    if dec.returncode: raise RuntimeError(dec.stderr[-2000:])
    duration=float(p["format"].get("duration","0"))
    if not 94.5<=duration<=95.5: raise RuntimeError(f"bad duration {duration}")
    manifest={"episode":f"EP{ep:02d}","title":title,"artifact":str(out),
      "artifact_class":"CANONICAL_STORY_EPISODE","mode":"DETERMINISTIC_MOTION_RENDER",
      "story_source":STORY_SOURCE,"content_note":"Canonical Pilot 001 story episode rendered with deterministic motion fallback; not AI video generation.",
      "evidence_status":"GENERATED","publication":"NOT_PERFORMED","duration_sec":duration,
      "size_bytes":out.stat().st_size,"sha256":sha256(out),"decode":"FFMPEG_DECODE_PASS","probe":p}
    (epdir/f"EP{ep:02d}.manifest.json").write_text(json.dumps(manifest,indent=2))
    print(json.dumps({"episode":f"EP{ep:02d}","title":title,"sha256":manifest["sha256"],"size_bytes":manifest["size_bytes"]}))
def main():
    missing=[p for p in ("Maya.jpg","Daniel.jpg","Apartment.jpg","Phone.jpg") if not (ASSETS/p).exists()]
    if missing: raise SystemExit("missing assets: "+",".join(missing))
    for ep,(title,lines) in EPISODES.items(): render(ep,title,lines)
if __name__=="__main__": main()
