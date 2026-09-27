#!/usr/bin/env python3
"""Generate EP02-EP10 as real deterministic fallback MP4 artifacts.

This is a fallback renderer, not AI video generation. Each episode is a
deterministic 95s recut of the verified THE LAST VOICEMAIL reference assets.
The output is intentionally labeled as fallback/recut in its manifest.
"""
from __future__ import annotations
import hashlib, json, shutil, subprocess
from pathlib import Path

W,H,FPS=720,1280,24
ROOT=Path(__file__).resolve().parents[1]
OUTDIR=ROOT/"build"/"episodes"
ASSETDIR=ROOT/"build"/"fallback_assets"
URLS={
 "maya":"https://cdn.creativeclaw.co/u/9ed00843/images/e83041d3-c03b-4104-89a2-1988d077763c.jpg",
 "daniel":"https://cdn.creativeclaw.co/u/9ed00843/images/8dfda36b-da6a-452a-8798-f63088cf7959.jpg",
 "phone":"https://cdn.creativeclaw.co/u/9ed00843/images/f8c0a0b5-1c33-49ef-8547-ae642e49bc59.jpg",
 "apartment":"https://cdn.creativeclaw.co/u/9ed00843/images/0227258c-f72d-4231-a83e-14f6fdd38da9.jpg",
}
DIALOGUES=[
 ("Maya","If you're hearing this, it's already started."),
 ("Maya","Tomorrow at eight seventeen, Daniel will ask you to leave the house. Do not go."),
 ("Maya","That's impossible."),
 ("Daniel","Who were you talking to?"),
 ("Maya","Nobody."),
]
PATTERNS=[
 ["maya","phone","daniel","apartment","phone","maya","daniel","phone","apartment","maya"],
 ["phone","maya","apartment","daniel","maya","phone","daniel","maya","phone","apartment"],
 ["apartment","maya","phone","daniel","phone","maya","apartment","daniel","maya","phone"],
 ["daniel","phone","maya","apartment","maya","daniel","phone","apartment","phone","maya"],
 ["phone","apartment","maya","phone","daniel","maya","apartment","phone","daniel","maya"],
 ["maya","daniel","phone","maya","apartment","phone","maya","daniel","phone","apartment"],
 ["apartment","phone","daniel","maya","phone","apartment","maya","phone","daniel","maya"],
 ["daniel","maya","apartment","phone","maya","daniel","phone","maya","apartment","phone"],
 ["phone","maya","daniel","phone","apartment","maya","phone","daniel","maya","apartment"],
]
DURS=[9,11,8,10,12,9,8,10,9,9]  # 95s

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
def download_assets():
 ASSETDIR.mkdir(parents=True,exist_ok=True)
 import urllib.request
 for k,u in URLS.items():
  p=ASSETDIR/f"{k}.jpg"
  if not p.exists() or p.stat().st_size==0: urllib.request.urlretrieve(u,p)
  if p.stat().st_size==0: raise RuntimeError("empty asset "+k)
def render(ep):
 epdir=OUTDIR/f"EP{ep:02d}"; seg=epdir/"segments"; aud=epdir/"audio"
 for d in (seg,aud): d.mkdir(parents=True,exist_ok=True)
 pattern=PATTERNS[ep-2]
 for i,(asset,dur) in enumerate(zip(pattern,DURS),1):
  v=seg/f"{i:02d}.mp4"
  zoom="min(zoom+0.0008,1.08)" if i%2 else "max(zoom-0.0008,1.0)"
  vf=(f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,"
      f"crop={W*2}:{H*2},zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':"
      f"y='ih/2-(ih/zoom/2)':d={dur*FPS}:s={W}x{H}:fps={FPS},format=yuv420p")
  run(["ffmpeg","-y","-v","error","-loop","1","-i",str(ASSETDIR/f"{asset}.jpg"),
       "-t",str(dur),"-vf",vf,"-an","-c:v","libx264","-preset","veryfast","-crf","22",
       "-movflags","+faststart",str(v)])
 for i,dur in enumerate(DURS,1):
  a=aud/f"{i:02d}.wav"
  if i in (2,5,7,9,10) and shutil.which("espeak-ng"):
   speaker,text=DIALOGUES[(i//2)%len(DIALOGUES)]
   voice="en-us+f3" if speaker=="Maya" else "en-us+m3"
   raw=aud/f"{i:02d}_raw.wav"
   run(["espeak-ng","-v",voice,"-s","150","-p","45","-w",str(raw),text])
   run(["ffmpeg","-y","-v","error","-i",str(raw),"-af",f"apad=pad_dur={dur}",
        "-t",str(dur),"-ar","48000","-ac","2","-c:a","pcm_s16le",str(a)])
  else:
   run(["ffmpeg","-y","-v","error","-f","lavfi","-i","anullsrc=r=48000:cl=stereo",
        "-t",str(dur),"-ar","48000","-ac","2","-c:a","pcm_s16le",str(a)])
 vlist=epdir/"video.txt"; alist=epdir/"audio.txt"
 vlist.write_text("".join(f"file '{seg/f'{i:02d}.mp4'}'\\n" for i in range(1,11)))
 alist.write_text("".join(f"file '{aud/f'{i:02d}.wav'}'\\n" for i in range(1,11)))
 vcat=epdir/"vcat.mp4"; acat=epdir/"acat.wav"
 run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(vlist),"-c","copy",str(vcat)])
 run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(alist),"-c:a","pcm_s16le",str(acat)])
 out=epdir/f"THE_LAST_VOICEMAIL_EP{ep:02d}_Fallback_Recut.mp4"
 title=f"THE LAST VOICEMAIL — EPISODE {ep:02d} / FALLBACK RECUT"
 vf=f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='{title}':fontcolor=white:fontsize=24:x=(w-text_w)/2:y=80"
 run(["ffmpeg","-y","-v","error","-i",str(vcat),"-i",str(acat),"-vf",vf,
      "-map","0:v:0","-map","1:a:0","-t","95","-c:v","libx264","-preset","medium","-crf","21",
      "-c:a","aac","-b:a","128k","-movflags","+faststart",str(out)])
 p=probe(out)
 dec=subprocess.run(["ffmpeg","-v","error","-i",str(out),"-f","null","-"],capture_output=True,text=True)
 if dec.returncode: raise RuntimeError(dec.stderr[-2000:])
 dur=float(p["format"].get("duration","0"))
 streams=p.get("streams",[])
 if not 94.5<=dur<=95.5 or not any(s.get("codec_type")=="video" for s in streams) or not any(s.get("codec_type")=="audio" for s in streams):
  raise RuntimeError(f"invalid artifact {out}: duration={dur}")
 manifest={"episode":f"EP{ep:02d}","artifact":str(out),"mode":"DETERMINISTIC_MOTION_FALLBACK_RECUT",
  "content_note":"Deterministic recut from verified THE LAST VOICEMAIL reference stills; not AI-generated and not a new canonical story episode.",
  "evidence_status":"GENERATED","publication":"NOT_PERFORMED","duration_sec":dur,
  "size_bytes":out.stat().st_size,"sha256":sha256(out),"decode":"FFMPEG_DECODE_PASS","probe":p}
 (epdir/f"EP{ep:02d}.manifest.json").write_text(json.dumps(manifest,indent=2))
 print(json.dumps({"episode":f"EP{ep:02d}","sha256":manifest["sha256"],"size_bytes":manifest["size_bytes"],"duration_sec":dur}))
def main():
 download_assets()
 for ep in range(2,11): render(ep)
if __name__=="__main__": main()
