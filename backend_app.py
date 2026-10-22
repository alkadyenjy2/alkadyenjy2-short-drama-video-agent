"""Authenticated persistent API for the Short Drama dashboard."""
import hmac
import os
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from persistence.postgres_repository import PostgresRepository

app = FastAPI(title="Short Drama Persistent API", version="1.0.0")


def repository():
    try:
        return PostgresRepository(initialize_schema=False)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Persistent database unavailable") from exc


def require_token(authorization: str | None):
    expected = os.getenv("VIDEO_API_TOKEN", "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="API authentication is not configured")
    supplied = (authorization or "").removeprefix("Bearer ").strip()
    if not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")


class VideoVersionInput(BaseModel):
    video_id: str
    current_version: str
    story_id: str | None = None


@app.get("/health")
def health():
    try:
        repo = repository()
        healthy = repo.health_check()
        repo.close()
        if not healthy:
            raise HTTPException(status_code=503, detail="Database schema is incomplete")
        return {"status": "ok", "persistence": "ok"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Persistent database unhealthy") from exc


@app.get("/videos")
def list_videos(authorization: str | None = Header(default=None)):
    require_token(authorization)
    repo = repository()
    try:
        return {"videos": repo.list_video_versions(), "storage": "persistent"}
    finally:
        repo.close()


@app.post("/videos")
def upsert_video(body: VideoVersionInput, authorization: str | None = Header(default=None)):
    require_token(authorization)
    repo = repository()
    try:
        saved = repo.create_or_update_video_version(
            body.video_id, body.current_version, body.story_id
        )
        readback = repo.get_video_version(body.video_id)
        if not readback or readback.get("current_version") != body.current_version:
            raise HTTPException(status_code=500, detail="Persistence readback verification failed")
        return {"video": saved, "readback_verified": True, "storage": "persistent"}
    finally:
        repo.close()


@app.get("/videos/{video_id}")
def get_video(video_id: str, authorization: str | None = Header(default=None)):
    require_token(authorization)
    repo = repository()
    try:
        item = repo.get_video_version(video_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Video not found")
        return {"video": item, "storage": "persistent"}
    finally:
        repo.close()
