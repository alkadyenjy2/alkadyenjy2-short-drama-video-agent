# web_app.py - Application Layer - Dashboard for Drama AI
import os
from datetime import datetime
from typing import List, Dict
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests
import hmac
import uuid
from urllib.parse import urlparse

from http_video_generation import HTTPVideoGenerationAdapter
from generated_artifact_store import persist_generated_artifact, get_generated_artifact
from cloudinary_playback import create_temporary_playback_url
from cloudinary_storage import store_video_artifact
from video_generation_adapter import VideoGenerationAccessError
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
            repo = get_repository(initialize_schema=False)
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
            repo = get_repository(initialize_schema=False)
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
def generate_video(req: GenerateRequest, authorization: str | None = Header(default=None)):
    import json
    with open(os.path.join(os.path.dirname(__file__), "trending_stories.json"), "r", encoding="utf-8") as f:
        stories = json.load(f)
    story = next((s for s in stories if s["id"] == req.story_id), None)
    if not story:
        raise HTTPException(404, "Story not found")
    beats = parse_story_to_beats(story)

    endpoint = os.getenv("VIDEO_GENERATION_API_URL", "").strip()
    provider_key = os.getenv("VIDEO_GENERATION_API_KEY", "").strip()
    if not endpoint or not provider_key:
        return {
            "story_id": req.story_id,
            "beats": beats,
            "status": "PLAN_ONLY",
            "generation_evidence": "NOT_AVAILABLE",
            "character_bible_required": True,
            "reason": "VIDEO_GENERATION_API_URL and VIDEO_GENERATION_API_KEY must both be configured",
        }

    expected_token = os.getenv("VIDEO_API_TOKEN", "").strip()
    supplied_token = (authorization or "").removeprefix("Bearer ").strip()
    if not expected_token:
        raise HTTPException(503, "Generation request authentication is not configured")
    if not supplied_token or not hmac.compare_digest(supplied_token, expected_token):
        raise HTTPException(401, "Unauthorized")

    # The provider API key is sent as a bearer token; never send it to plain HTTP
    # or a URL containing embedded credentials.
    provider_url = urlparse(endpoint)
    if (
        provider_url.scheme != "https"
        or not provider_url.hostname
        or provider_url.username is not None
        or provider_url.password is not None
    ):
        raise HTTPException(503, "Video provider endpoint must be a valid HTTPS URL without embedded credentials")
    if not os.getenv("DATABASE_URL", "").strip():
        # Do not spend provider credits or upload a durable asset unless the
        # canonical database is configured to record the artifact receipt.
        raise HTTPException(503, "Durable artifact database is not configured")

    video_id = f"video_{req.story_id}_{uuid.uuid4().hex[:12]}"
    try:
        artifact = HTTPVideoGenerationAdapter().generate(
            script=story.get("story_outline", ""),
            scene_plan={"story_id": req.story_id, "beats": beats, "aspect_ratio": "9:16"},
            output_format="mp4",
        )
    except (VideoGenerationAccessError, requests.RequestException, ValueError) as exc:
        # Do not expose provider responses, credentials, or request headers.
        raise HTTPException(502, "Video provider did not return a verified artifact") from exc

    parsed_url = urlparse(artifact.artifact_url or "")
    if parsed_url.scheme != "https" or not parsed_url.hostname:
        raise HTTPException(502, "Provider artifact URL must be HTTPS")
    if artifact.evidence_status != "OBSERVED":
        raise HTTPException(502, "Provider artifact lacks observed generation evidence")

    try:
        durable_asset = store_video_artifact(
            artifact_url=artifact.artifact_url,
            video_id=video_id,
            story_id=req.story_id,
        )
    except Exception as exc:
        # Fail closed: a temporary provider URL must never be reported as durable.
        raise HTTPException(503, "Generated video could not be copied to durable storage") from exc

    try:
        stored = persist_generated_artifact(
            video_id=video_id,
            story_id=req.story_id,
            provider=artifact.provider,
            artifact_url=durable_asset["artifact_url"],
            duration_sec=artifact.duration_sec,
            evidence_status=artifact.evidence_status,
            storage_provider=durable_asset["storage_provider"],
            storage_public_id=durable_asset["storage_public_id"],
            storage_asset_id=durable_asset["storage_asset_id"],
            storage_bytes=durable_asset["storage_bytes"],
        )
    except Exception as exc:
        raise HTTPException(503, "Generated artifact could not be durably persisted and verified") from exc

    if not stored.get("readback_verified"):
        raise HTTPException(503, "Generated artifact persistence readback failed")
    return {
        "story_id": req.story_id,
        "video_id": video_id,
        "beats": beats,
        "status": "GENERATED",
        "generation_evidence": "CLOUDINARY_COPY_AND_DB_READBACK_VERIFIED",
        "artifact_id": stored["artifact_id"],
        "artifact_url": durable_asset["artifact_url"],
        "storage_provider": durable_asset["storage_provider"],
        "storage_public_id": durable_asset["storage_public_id"],
        "storage_bytes": durable_asset["storage_bytes"],
        "provider": artifact.provider,
        "duration_sec": artifact.duration_sec,
        "character_bible_required": True,
        "publication_status": "NOT_PUBLISHED",
    }


@app.get("/artifacts/{artifact_id}/playback")
def artifact_playback(
    artifact_id: str,
    response: Response,
    authorization: str | None = Header(default=None),
):
    """Issue a short-lived signed URL only to an authenticated service caller."""
    expected_token = os.getenv("VIDEO_API_TOKEN", "").strip()
    supplied_token = (authorization or "").removeprefix("Bearer ").strip()
    if not expected_token:
        raise HTTPException(503, "Playback authorization is not configured")
    if not supplied_token or not hmac.compare_digest(supplied_token, expected_token):
        raise HTTPException(401, "Unauthorized")

    try:
        artifact = get_generated_artifact(artifact_id)
    except Exception as exc:
        raise HTTPException(503, "Generated artifact metadata is unavailable") from exc
    if artifact is None:
        raise HTTPException(404, "Generated artifact not found")
    if (
        artifact.get("evidence_status") != "OBSERVED"
        or artifact.get("storage_provider") != "cloudinary"
        or not artifact.get("storage_public_id")
        or not artifact.get("storage_asset_id")
    ):
        raise HTTPException(409, "Artifact is not verified for playback")

    try:
        playback = create_temporary_playback_url(artifact["storage_public_id"], ttl_seconds=300)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(503, "Secure playback URL could not be created") from exc

    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return {
        "artifact_id": artifact["artifact_id"],
        "video_id": artifact["video_id"],
        "playback_url": playback["url"],
        "expires_at": playback["expires_at"],
        "expires_in_seconds": 300,
        "publication_status": "NOT_PUBLISHED",
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
