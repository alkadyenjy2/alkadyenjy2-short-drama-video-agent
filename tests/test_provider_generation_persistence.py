import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import web_app
from video_generation_adapter import VideoArtifact


def _request():
    return web_app.GenerateRequest(
        story_id="the-last-voicemail-ep1",
        user_id="provider-test-user",
    )


def test_generate_stays_plan_only_when_provider_is_not_configured():
    with patch.dict(os.environ, {"VIDEO_GENERATION_API_URL": "", "VIDEO_GENERATION_API_KEY": ""}, clear=False):
        result = web_app.generate_video(_request(), authorization=None)

    assert result["status"] == "PLAN_ONLY"
    assert result["generation_evidence"] == "NOT_AVAILABLE"
    assert "artifact_url" not in result


def test_configured_generation_requires_authenticated_request():
    with patch.dict(
        os.environ,
        {
            "VIDEO_GENERATION_API_URL": "https://provider.example/generate",
            "VIDEO_GENERATION_API_KEY": "provider-secret",
            "VIDEO_API_TOKEN": "request-secret",
        },
        clear=False,
    ):
        with pytest.raises(HTTPException) as exc:
            web_app.generate_video(_request(), authorization="Bearer wrong")

    assert exc.value.status_code == 401


def test_provider_artifact_is_persisted_and_only_then_marked_generated():
    artifact = VideoArtifact(
        artifact_url="https://media.example/episode.mp4",
        provider="generic_http",
        duration_sec=8,
        evidence_status="OBSERVED",
    )
    with patch.dict(
        os.environ,
        {
            "VIDEO_GENERATION_API_URL": "https://provider.example/generate",
            "VIDEO_GENERATION_API_KEY": "provider-secret",
            "VIDEO_API_TOKEN": "request-secret",
        },
        clear=False,
    ), patch("web_app.HTTPVideoGenerationAdapter") as adapter, patch(
        "web_app.persist_generated_artifact",
        return_value={"artifact_id": "artifact_test", "readback_verified": True},
    ) as persist:
        adapter.return_value.generate.return_value = artifact
        result = web_app.generate_video(_request(), authorization="Bearer request-secret")

    assert result["status"] == "GENERATED"
    assert result["generation_evidence"] == "PERSISTED_READBACK_VERIFIED"
    assert result["artifact_url"] == artifact.artifact_url
    assert result["artifact_id"] == "artifact_test"
    persist.assert_called_once()


def test_provider_artifact_without_https_url_is_not_accepted():
    artifact = VideoArtifact(
        artifact_url="http://media.example/episode.mp4",
        provider="generic_http",
        duration_sec=8,
        evidence_status="OBSERVED",
    )
    with patch.dict(
        os.environ,
        {
            "VIDEO_GENERATION_API_URL": "https://provider.example/generate",
            "VIDEO_GENERATION_API_KEY": "provider-secret",
            "VIDEO_API_TOKEN": "request-secret",
        },
        clear=False,
    ), patch("web_app.HTTPVideoGenerationAdapter") as adapter:
        adapter.return_value.generate.return_value = artifact
        with pytest.raises(HTTPException) as exc:
            web_app.generate_video(_request(), authorization="Bearer request-secret")

    assert exc.value.status_code == 502
