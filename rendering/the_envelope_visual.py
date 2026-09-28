#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"build"/"the-envelope-visual"
ASSETS=OUT/"assets"
W,H,FPS=720,1280,24
URLS={
 "lina":"https://cdn.creativeclaw.co/u/9ed00843/images/e83041d3-c03b-4104-89a2-1988d077763c.jpg",
 "adam":"https://cdn.creativeclaw.co/u/9ed00843/images/8dfda36b-da6a-452a-8798-f63088cf7959.jpg",
 "phone":"https://cdn.creativeclaw.co/u/9ed00843/images/f8c0a0b5-1c33-49ef-8547-ae642e49bc59.jpg",
 "home":"https://cdn.creativeclaw.co/u/9ed00843/images/0227258c-f72d-4231-a83e-14f6fdd38da9.jpg",
}
EPS=[
("The Envelope",["lina","phone","home","lina","phone"],["On my wedding morning, an envelope arrives in my own handwriting.","DO NOT MARRY ADAM.","Adam! Did you send this?","He says no. But he already knows what is inside."]),
("The Lie",["adam","lina","phone","adam","lina"],["Adam says the envelope is a prank.","I ask how he knows the message.","He answers: Because I mailed it.","Then my phone shows a photo I have never seen before."]),
("The Photo",["lina","phone","home","lina","phone"],["Inside the envelope is a childhood photo.","The woman beside me is a stranger.","On the back, one word: TOMORROW.","My phone rings before I can ask who she is."]),
("The Date",["phone","lina","home","phone","adam"],["I search the date printed on the photo.","It is tomorrow.","The woman in the picture should be dead.","Adam walks in and sees the photo.","He asks: Who gave you that?"]),
("The Missing Woman",["lina","phone","adam","home","lina"],["The woman is officially listed as dead.","Then her name appears on my caller ID.","She says: Lina, do not trust Adam.","I look at Adam. He is already holding another envelope."]),
("The Phone",["phone","lina","home","adam","phone"],["The caller sends a live photo from Adam's apartment.","I recognize the locked door behind him.","Adam says nobody has been inside.","Then the phone sends another photo.","This time, the door is open."]),
("The Room",["home","adam","lina","phone","home"],["I follow Adam to the apartment.","Behind the locked door are my childhood drawings.","Adam says the room was never mine.","I find a box with my name on it.","Inside is a birth certificate."]),
("The Name",["lina","phone","home","lina","adam"],["The birth certificate has my name.","But the mother's name is different.","I call the woman from the photo.","She says: You were taken as a baby.","Adam hears everything.","Then he finally tells me why."]),
("The Mother",["phone","lina","adam","home","phone"],["The woman says she is my real mother.","She says Adam's family hid the truth.","Adam says he was trying to protect me.","I ask: From whom?","The answer arrives in a new envelope."]),
("The Betrayal",["lina","adam","phone","home","lina"],["The final envelope contains one sentence.","ASK ADAM WHAT HE DID TO YOUR FAMILY.","Adam admits he investigated my past for years.","He says my parents are not dead.","Then someone knocks downstairs."]),
]
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
    ASSETS.mkdir(parents=True,exist_ok=True)
    for k,u in URLS.items():
        p=ASSETS/f"{k}.jpg"
        if not p.exists() or p.stat().st_size<1000: urllib.request.urlretrieve(u,p)
        if p.stat().st_size<1000: raise RuntimeError("bad asset "+k)
def make_segment(img,dur,out,reverse=False):
    zoom="max(zoom-0.0007,1.0)" if reverse else "min(zoom+0.0007,1.08)"
    vf=(f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,"
        f"crop={W*2}:{H*2},zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':"
        f"y='ih/2-(ih/zoom/2)':d={dur*FPS}:s={W}x{H}:fps={FPS},format=yuv420p")
    run(["ffmpeg","-y","-v","error","-loop","1","-i",str(img),"-t",str(dur),
         "-vf",vf,"-an","-c:v","libx264","-preset","veryfast","-crf","22","-movflags","+faststart",str(out)])
def make_voice(text,out):
    ps=out.with_suffix(".ps1")
    ps.write_text(
        'Add-Type -AssemblyName System.Speech\n'
        '$s=New-Object System.Speech.Synthesis.SpeechSynthesizer\n'
        f'$s.SetOutputToWaveFile("{str(out).replace(chr(92),chr(92)+chr(92))}")\n'
        f'$s.Speak("{text.replace(chr(34),chr(34)+chr(34))}")\n'
        '$s.Dispose()\n',encoding="utf-8")
    run(["powershell","-NoProfile","-ExecutionPolicy","Bypass","-File",str(ps)])
    ps.unlink(missing_ok=True)
def main():
    download_assets()
    records=[]
    for n,(title,images,lines) in enumerate(EPS,1):
        ep=f"EP{n:02d}"; epdir=OUT/ep; seg=epdir/"segments"; aud=epdir/"audio"
        seg.mkdir(parents=True,exist_ok=True); aud.mkdir(parents=True,exist_ok=True)
        durs=[12,12,12,12,12]
        for i,(asset,dur) in enumerate(zip(images,durs),1):
            make_segment(ASSETS/f"{asset}.jpg",dur,seg/f"{i:02d}.mp4",reverse=i%2==0)
        for i,dur in enumerate(durs,1):
            wav=aud/f"{i:02d}.wav"
            if i<=len(lines):
                raw=aud/f"{i:02d}_raw.wav"; make_voice(lines[i-1],raw)
                run(["ffmpeg","-y","-v","error","-i",str(raw),"-af",f"apad=pad_dur={dur}",
                     "-t",str(dur),"-ar","48000","-ac","2","-c:a","pcm_s16le",str(wav)])
            else:
                run(["ffmpeg","-y","-v","error","-f","lavfi","-i","anullsrc=r=48000:cl=stereo",
                     "-t",str(dur),"-ar","48000","-ac","2","-c:a","pcm_s16le",str(wav)])
        vl=epdir/"video.txt"; al=epdir/"audio.txt"
        vl.write_text("".join(f"file '{seg/f'{i:02d}.mp4'}'\n" for i in range(1,6)),encoding="utf-8")
        al.write_text("".join(f"file '{aud/f'{i:02d}.wav'}'\n" for i in range(1,6)),encoding="utf-8")
        vcat=epdir/"vcat.mp4"; acat=epdir/"acat.wav"
        run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(vl),"-c","copy",str(vcat)])
        run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(al),"-c:a","pcm_s16le",str(acat)])
        out=epdir/f"{ep}_THE_ENVELOPE_VISUAL.mp4"
        # Keep the master visual-first; episode identity is stored in the manifest.
        run(["ffmpeg","-y","-v","error","-i",str(vcat),"-i",str(acat),
             "-map","0:v:0","-map","1:a:0","-t","60",
             "-c:v","libx264","-preset","medium","-crf","21",
             "-c:a","aac","-b:a","128k","-movflags","+faststart",str(out)])
        p=probe(out); streams=p.get("streams",[])
        dec=subprocess.run(["ffmpeg","-v","error","-i",str(out),"-f","null","-"],capture_output=True,text=True)
        if dec.returncode: raise RuntimeError("decode failed: "+dec.stderr[-1000:])
        dur=float(p["format"]["duration"])
        v=next(s for s in streams if s.get("codec_type")=="video")
        a=next(s for s in streams if s.get("codec_type")=="audio")
        if not (59.8<=dur<=60.2 and v.get("width")==720 and v.get("height")==1280 and v.get("codec_name")=="h264" and a.get("codec_name")=="aac"):
            raise RuntimeError("media gate failed "+str(out))
        # Audible-content gate: reject silent masters.
        vol=subprocess.run(["ffmpeg","-v","info","-i",str(out),"-af","volumedetect","-f","null","NUL"],capture_output=True,text=True)
        if "mean_volume: -inf" in vol.stderr: raise RuntimeError("AUDIO_SILENCE_GATE_FAILED "+str(out))
        rec={"episode":ep,"title":title,"artifact":str(out),"duration_sec":dur,
             "size_bytes":out.stat().st_size,"sha256":sha256(out),
             "video_codec":v.get("codec_name"),"width":v.get("width"),"height":v.get("height"),
             "audio_codec":a.get("codec_name"),"sample_rate":a.get("sample_rate"),
             "channels":a.get("channels"),"decode":"FFMPEG_DECODE_PASS",
             "visual_gate":"PASS","audio_gate":"PASS","publication":"NOT_PERFORMED"}
        (epdir/f"{ep}.manifest.json").write_text(json.dumps(rec,indent=2),encoding="utf-8")
        records.append(rec); print(json.dumps(rec))
    (OUT/"manifest.json").write_text(json.dumps({"series":"THE ENVELOPE","count":10,"artifacts":records},indent=2),encoding="utf-8")
if __name__=="__main__": main()
