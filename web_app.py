# web_app.py - Application Layer - Dashboard for Drama AI
import os
from datetime import datetime
from typing import List, Dict
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests

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
<h3 class="gold">🔁 Production Loop</h3>
<p>Discovery → Rights Review → Generation → Approval → Publish → Analytics → Learning.</p>
<p>لا يتم اعتبار أي فيديو مولداً أو منشوراً بدون artifact/receipt حقيقي.</p>
</div>

<div class="card">
<h3 class="gold">🧭 Platform Fit</h3>
<p>المنصة لا يتم اختيارها بنسبة ROI ثابتة. الاختيار يعتمد على البيانات المرصودة، صلاحيات الحساب، ومتطلبات النشر.</p>
</div>

<div class="card">
<h3 class="gold">🧭 Platform Fit</h3>
<p>المنصة لا يتم اختيارها بنسبة ROI ثابتة. الاختيار يعتمد على البيانات المرصودة، صلاحيات الحساب، ومتطلبات النشر.</p>
</div>

<div class="card">
<h3 class="gold">📦 آخر فيديوهات مولدة</h3>
<div id="videos">جاري التحميل...</div>
</div>

<script>
fetch('/videos').then(r=>{
  if (!r.ok) throw new Error('inventory unavailable');
  return r.json();
}).then(data=>{
  document.getElementById('videos').innerHTML = data.videos.map(v=>`<p>🎬 ${v.video_id} - ${v.current_version} - ${v.story_id || '—'}</p>`).join('') || 'لا يوجد فيديوهات مسجلة بعد';
}).catch(()=>{
  document.getElementById('videos').textContent = 'تعذر تحميل سجل الفيديوهات الدائم؛ حاول لاحقًا.';
});
</script>
</body>
</html>
"""

@app.get("/health")
def health():
    # Prefer the configured durable PostgreSQL store. The former Railway URL
    # may still exist in Vercel settings after that service has been removed.
    database_url = os.getenv("DATABASE_URL", "").strip()
    api_base = os.getenv("VIDEO_AGENT_API_URL", "").strip().rstrip("/")
    db_healthy = False
    if database_url:
        repo = None
        try:
            repo = get_repository()
            repo.init_schema()
            db_healthy = bool(repo.health_check())
        except Exception:
            db_healthy = False
        finally:
            if repo is not None:
                try:
                    repo.close()
                except Exception:
                    pass
        persistence_source = "postgres"
    else:
        if api_base:
            try:
                response = requests.get(f"{api_base}/health", timeout=5)
                if response.status_code == 200:
                    payload = response.json()
                    db_healthy = (
                        isinstance(payload, dict)
                        and payload.get("status") == "ok"
                        and payload.get("persistence") == "ok"
                    )
            except (requests.RequestException, ValueError):
                db_healthy = False
        persistence_source = "railway" if api_base else "unconfigured"

    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "db": db_healthy,
        "persistence_source": persistence_source,
        "agent": get_agent_status(),
        "publisher": get_adapter_status(),
    }

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

@app.get("/release-assets")
def list_release_assets():
    """Return real MP4 assets attached to the verified GitHub release.

    Release availability is not platform-publication evidence. Each item stays
    marked release_asset_only until a platform receipt/permalink is recorded.
    """
    import json
    manifest_path = os.path.join(os.path.dirname(__file__), "evidence", "the-envelope-release-assets.json")
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=503, detail="Release asset catalog is unavailable") from exc
    assets = manifest.get("assets") if isinstance(manifest, dict) else None
    if not isinstance(assets, list):
        raise HTTPException(status_code=502, detail="Release asset catalog is invalid")
    return {
        "count": len(assets),
        "assets": assets,
        "release_url": manifest.get("release_url"),
        "publication_status": "release_asset_only",
        "platform_published": False,
    }


@app.get("/videos")
def list_videos():
    # Prefer durable PostgreSQL when configured; never silently fall back to
    # Vercel's ephemeral SQLite file when DATABASE_URL is present.
    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url:
        repo = None
        try:
            repo = get_repository()
            repo.init_schema()
            return {"videos": repo.list_video_versions(), "storage": "postgres"}
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Persistent video inventory is unavailable") from exc
        finally:
            if repo is not None:
                try:
                    repo.close()
                except Exception:
                    pass

    # Legacy persistent Railway API remains available as a fallback for existing
    # deployments that have not yet been migrated to DATABASE_URL.
    api_base = os.getenv("VIDEO_AGENT_API_URL", "").strip().rstrip("/")
    if api_base:
        api_token = os.getenv("VIDEO_API_TOKEN", "").strip()
        if not api_token:
            raise HTTPException(status_code=503, detail="Persistent video inventory is not configured")
        try:
            response = requests.get(
                f"{api_base}/videos",
                headers={"Authorization": f"Bearer {api_token}"},
                timeout=8,
            )
            if response.status_code != 200:
                raise HTTPException(status_code=503, detail="Persistent video inventory is unavailable")
            payload = response.json()
            videos = payload.get("videos") if isinstance(payload, dict) else None
            if not isinstance(videos, list):
                raise HTTPException(status_code=502, detail="Persistent video inventory returned an invalid response")
            return {"videos": videos, "storage": "persistent"}
        except requests.RequestException as exc:
            raise HTTPException(status_code=503, detail="Persistent video inventory is unavailable") from exc
        except ValueError as exc:
            raise HTTPException(status_code=502, detail="Persistent video inventory returned invalid JSON") from exc

    # Local/dev fallback only. Schema creation is idempotent; production should
    # configure DATABASE_URL or VIDEO_AGENT_API_URL.
    try:
        repo = get_repository()
        repo.init_schema()
        return {"videos": repo.list_video_versions(), "storage": "local"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Video inventory is unavailable") from exc
    finally:
        if "repo" in locals():
            try:
                repo.close()
            except Exception:
                pass

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
