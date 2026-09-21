"""Generic authenticated HTTP video-generation adapter.

Supports providers whose contract is:
POST JSON -> {artifact_url} or {job_id}; optional status URL polling.
The provider contract remains explicit, so unsupported APIs cannot be marked complete.
"""
import os
import time
from typing import Dict, Optional
import requests

from video_generation_adapter import VideoArtifact, VideoGenerationAccessError, VideoGenerationAdapter


class HTTPVideoGenerationAdapter(VideoGenerationAdapter):
    provider = "generic_http"

    def __init__(self, endpoint: Optional[str] = None, api_key: Optional[str] = None,
                 timeout: int = 60, max_polls: int = 20, poll_seconds: float = 3.0):
        self.endpoint = endpoint or os.getenv("VIDEO_GENERATION_API_URL")
        self.api_key = api_key or os.getenv("VIDEO_GENERATION_API_KEY")
        self.timeout = timeout
        self.max_polls = max_polls
        self.poll_seconds = poll_seconds

    def generate(self, script: str, scene_plan: Dict, output_format: str = "mp4") -> VideoArtifact:
        if not self.endpoint:
            raise VideoGenerationAccessError("VIDEO_GENERATION_API_URL is required")
        if not self.api_key:
            raise VideoGenerationAccessError("VIDEO_GENERATION_API_KEY is required")
        if not script.strip():
            raise ValueError("script is required")
        response = requests.post(
            self.endpoint,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={"script": script, "scene_plan": scene_plan, "output_format": output_format},
            timeout=self.timeout,
        )
        if response.status_code not in (200, 201, 202):
            raise VideoGenerationAccessError(f"video generation failed: HTTP {response.status_code}")
        payload = response.json()
        if payload.get("artifact_url"):
            return VideoArtifact(payload["artifact_url"], self.provider, payload.get("duration_sec"), "OBSERVED")
        job_id = payload.get("job_id")
        status_url = payload.get("status_url")
        if not job_id or not status_url:
            raise VideoGenerationAccessError("provider response has neither artifact_url nor job_id+status_url")
        for _ in range(self.max_polls):
            time.sleep(self.poll_seconds)
            poll = requests.get(
                status_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout,
            )
            if poll.status_code != 200:
                continue
            data = poll.json()
            if data.get("artifact_url"):
                return VideoArtifact(data["artifact_url"], self.provider, data.get("duration_sec"), "OBSERVED")
            if data.get("status") in {"FAILED", "CANCELLED"}:
                raise VideoGenerationAccessError(f"video generation terminal status: {data.get('status')}")
        raise VideoGenerationAccessError("video generation polling timeout; no artifact evidence")
