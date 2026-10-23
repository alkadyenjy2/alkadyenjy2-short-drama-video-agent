import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import web_app
from video_generation_adapter import VideoArtifact


def request_body():
    return web_app.GenerateRequest(story_id="the-last-voicemail-ep1", user_id="provider-test-user")


class ProviderGenerationPersistenceTests(unittest.TestCase):
    def test_plan_only_when_provider_is_not_configured(self):
        with patch.dict(os.environ, {"VIDEO_GENERATION_API_URL": "", "VIDEO_GENERATION_API_KEY": ""}, clear=False):
            result = web_app.generate_video(request_body(), authorization=None)
        self.assertEqual(result["status"], "PLAN_ONLY")
        self.assertEqual(result["generation_evidence"], "NOT_AVAILABLE")
        self.assertNotIn("artifact_url", result)

    def test_configured_generation_requires_authenticated_request(self):
        with patch.dict(os.environ, {
            "VIDEO_GENERATION_API_URL": "https://provider.example/generate",
            "VIDEO_GENERATION_API_KEY": "provider-secret",
            "VIDEO_API_TOKEN": "request-secret",
        }, clear=False):
            with self.assertRaises(HTTPException) as exc:
                web_app.generate_video(request_body(), authorization="Bearer wrong")
        self.assertEqual(exc.exception.status_code, 401)

    def test_http_provider_endpoint_is_rejected_before_calling_provider(self):
        with patch.dict(os.environ, {
            "VIDEO_GENERATION_API_URL": "http://provider.example/generate",
            "VIDEO_GENERATION_API_KEY": "provider-secret",
            "VIDEO_API_TOKEN": "request-secret",
        }, clear=False), patch("web_app.HTTPVideoGenerationAdapter") as adapter:
            with self.assertRaises(HTTPException) as exc:
                web_app.generate_video(request_body(), authorization="Bearer request-secret")
        self.assertEqual(exc.exception.status_code, 503)
        adapter.assert_not_called()

    def test_missing_database_fails_before_provider_call(self):
        with patch.dict(os.environ, {
            "VIDEO_GENERATION_API_URL": "https://provider.example/generate",
            "VIDEO_GENERATION_API_KEY": "provider-secret",
            "VIDEO_API_TOKEN": "request-secret",
            "DATABASE_URL": "",
        }, clear=False), patch("web_app.HTTPVideoGenerationAdapter") as adapter:
            with self.assertRaises(HTTPException) as exc:
                web_app.generate_video(request_body(), authorization="Bearer request-secret")
        self.assertEqual(exc.exception.status_code, 503)
        adapter.assert_not_called()

    def test_provider_artifact_is_persisted_before_generated_status(self):
        artifact = VideoArtifact("https://media.example/episode.mp4", "generic_http", 8, "OBSERVED")
        with patch.dict(os.environ, {
            "VIDEO_GENERATION_API_URL": "https://provider.example/generate",
            "VIDEO_GENERATION_API_KEY": "provider-secret",
            "VIDEO_API_TOKEN": "request-secret",
            "DATABASE_URL": "postgresql://test:test@localhost/test",
        }, clear=False), patch("web_app.HTTPVideoGenerationAdapter") as adapter, patch(
            "web_app.store_video_artifact",
            return_value={
                "artifact_url": "https://res.cloudinary.com/demo/video/upload/short-drama/video_test.mp4",
                "storage_provider": "cloudinary",
                "storage_public_id": "short-drama/video_test",
                "storage_asset_id": "asset_test",
                "storage_bytes": 123456,
            },
        ) as store, patch(
            "web_app.persist_generated_artifact",
            return_value={"artifact_id": "artifact_test", "readback_verified": True},
        ) as persist:
            adapter.return_value.generate.return_value = artifact
            result = web_app.generate_video(request_body(), authorization="Bearer request-secret")
        self.assertEqual(result["status"], "GENERATED")
        self.assertEqual(result["generation_evidence"], "CLOUDINARY_COPY_AND_DB_READBACK_VERIFIED")
        self.assertEqual(result["artifact_url"], "https://res.cloudinary.com/demo/video/upload/short-drama/video_test.mp4")
        self.assertEqual(result["artifact_id"], "artifact_test")
        store.assert_called_once()
        persist.assert_called_once()
        self.assertEqual(persist.call_args.kwargs["storage_provider"], "cloudinary")
        self.assertEqual(persist.call_args.kwargs["storage_asset_id"], "asset_test")

    def test_non_https_artifact_is_rejected(self):
        artifact = VideoArtifact("http://media.example/episode.mp4", "generic_http", 8, "OBSERVED")
        with patch.dict(os.environ, {
            "VIDEO_GENERATION_API_URL": "https://provider.example/generate",
            "VIDEO_GENERATION_API_KEY": "provider-secret",
            "VIDEO_API_TOKEN": "request-secret",
            "DATABASE_URL": "postgresql://test:test@localhost/test",
        }, clear=False), patch("web_app.HTTPVideoGenerationAdapter") as adapter:
            adapter.return_value.generate.return_value = artifact
            with self.assertRaises(HTTPException) as exc:
                web_app.generate_video(request_body(), authorization="Bearer request-secret")
        self.assertEqual(exc.exception.status_code, 502)


if __name__ == "__main__":
    unittest.main()
