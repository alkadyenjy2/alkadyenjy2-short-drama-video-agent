# web_app.py - Application Layer - Dashboard for Drama AI
import os
from datetime import datetime
from typing import List, Dict
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from persistence.repository import get_repository
from visual_factory import get_agent_status, parse_story_to_beats
from publisher import get_adapter_status, PublicationState

app = FastAPI(title="DRAMA AI - Short Drama Video Agent", version="1.2")

class GenerateRequest(BaseModel):
    story_id: str
    user_id: str

@app.get("/", response_class=HTMLResponse)
def dashboard():
    return """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DRAMA AI Dashboard</title>
<style>
body { background:#0A0A0F; color:#F5F5F7; font-family: Tajawal, sans-serif; margin:0; padding:20px; }
.header { background: linear-gradient(135deg, #0A0A0F 0%, #1a1a2e 100%); padding:30px; border-radius:20px; border:1px solid #D4AF37; }
.logo { font-size:32px; font-weight:900; color:#D4AF37; }
.card { background:#1a1a2e; padding:20px; border-radius:15px; margin:15px 0; border:1px solid #333; }
.gold { color:#D4AF37; }
.red { color:#E50914; }
button { background:#D4AF37; color:#000; border:none; padding:12px 24px; border-radius:10px; font-weight:bold; cursor:pointer; }
button:hover { background:#E50914; color:#fff; }
</style>
</head>
<body>
<div class="header">
<div class="logo">🎬 DRAMA AI</div>
<p>قصص تريندينج.. بتتولد في ثواني - 9:16 Vertical Drama Agent</p>
<p>Bot: @YourBot | API: /health | Docs: /docs</p>
</div>

<div class="card">
<h3 class="gold">📊 حالة الايجنت (Agent Core)</h3>
<p>Visual Factory: READY | Character Bible: Consistent Face | Arabic Parser: اضاءة اغمق قص كابشن</p>
<p>Beats: 3-5 per story, 40-60 sec each, 1080x1920, 9:16</p>
<a href="/agent/status"><button>عرض حالة الايجنت</button></a>
<a href="/publisher/status"><button>حالة النشر (Publisher)</button></a>
<a href="/stories"><button>القصص التريندينج</button></a>
</div>

<div class="card">
<h3 class="gold">🚀 أهم 3 منصات للعملاء (حسب تحليلنا)</h3>
<p><b>1. TikTok (70%)</b> - أسرع نمو + Creativity Program $0.50-$1/1k views - هتجيب 100k متابع أول شهر</p>
<p><b>2. YouTube Shorts (20%)</b> - أرباح طويلة المدى 45% + ثقة العملاء B2B</p>
<p><b>3. Instagram Reels (10%)</b> - للبراندينج وشركات الإنتاج اللي هتدفع اشتراكات</p>
</div>

<div class="card">
<h3 class="gold">🎯 خطة أول 3 شهور (كشركة دعاية)</h3>
<p><b>شهر 1 - Proof:</b> 30 فيديو (2 يومياً) + إعلان ممول $5/يوم على أفضل فيديو</p>
<p><b>شهر 2 - Community:</b> سلسلة "اطلب قصتك" UGC + مقارنة v1 vs v2 vs v3</p>
<p><b>شهر 3 - Monetization:</b> 3 باقات Free/Creator $19/Agency $99 + Webinar</p>
</div>

<div class="card">
<h3 class="gold">📦 آخر فيديوهات مولدة</h3>
<div id="videos">جاري التحميل...</div>
</div>

<script>
fetch('/videos').then(r=>r.json()).then(data=>{
  document.getElementById('videos').innerHTML = data.videos.map(v=>`<p>🎬 ${v.video_id} - ${v.current_version} - ${v.status}</p>`).join('') || 'لا يوجد فيديوهات بعد';
});
</script>
</body>
</html>
"""

@app.get("/health")
def health():
    repo = get_repository()
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()+"Z", "db": repo.health_check(), "agent": get_agent_status(), "publisher": get_adapter_status()}

@app.get("/agent/status")
def agent_status():
    return get_agent_status()

@app.get("/publisher/status")
def publisher_status():
    return get_adapter_status()

@app.get("/stories")
def get_stories():
    import json
    with open(os.path.join(os.path.dirname(__file__), "trending_stories.json"), "r", encoding="utf-8") as f:
        stories = json.load(f)
    return {"count": len(stories), "stories": stories}

@app.get("/videos")
def list_videos():
    try:
        repo = get_repository()
        # Try to list from DB
        vids = repo.list_videos() if hasattr(repo, 'list_videos') else []
        return {"videos": vids}
    except Exception as e:
        return {"videos": [], "note": str(e)}

@app.post("/generate")
def generate_video(req: GenerateRequest):
    import json
    with open(os.path.join(os.path.dirname(__file__), "trending_stories.json"), "r", encoding="utf-8") as f:
        stories = json.load(f)
    story = next((s for s in stories if s["id"] == req.story_id), None)
    if not story:
        raise HTTPException(404, "Story not found")
    beats = parse_story_to_beats(story)
    return {"story_id": req.story_id, "beats": beats, "status": "PLAN_ONLY", "generation_evidence": "NOT_AVAILABLE", "character_bible_required": True}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
