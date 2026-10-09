"""Regression tests for the video inventory API.

These tests intentionally use a small repository fake and mocked HTTP transport;
they do not call a video-generation provider or publish any media.
"""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import health
import web_app


class FakeRepository:
    def __init__(self, versions):
        self.versions = versions
        self.initialized = False

    def init_schema(self):
        self.initialized = True

    def list_video_versions(self):
        if not self.initialized:
            raise RuntimeError("schema not initialized")
        return self.versions


class VideoInventoryTests(unittest.TestCase):
    def test_local_inventory_uses_persistent_repository_interface(self):
        versions = [
            {
                "video_id": "video-1",
                "story_id": "story-1",
                "current_version": "v1",
                "created_at": "2026-10-09 00:00:00",
                "updated_at": "2026-10-09 00:00:00",
            }
        ]
        repo = FakeRepository(versions)
        with patch.object(web_app, "get_repository", return_value=repo), patch.dict(
            os.environ, {"VIDEO_AGENT_API_URL": ""}, clear=False
        ):
            result = web_app.list_videos()
        self.assertEqual(result["videos"], versions)
        self.assertTrue(repo.initialized)

    def test_inventory_authentication_fails_closed(self):
        self.assertFalse(health.is_video_inventory_authorized("Bearer test-token", ""))
        self.assertFalse(health.is_video_inventory_authorized("Bearer wrong", "test-token"))
        self.assertTrue(health.is_video_inventory_authorized("Bearer test-token", "test-token"))

    def test_inventory_uses_configured_persistent_service(self):
        payload = {
            "videos": [
                {
                    "video_id": "video-2",
                    "story_id": "story-2",
                    "current_version": "v2",
                    "created_at": "2026-10-09 00:00:00",
                    "updated_at": "2026-10-09 00:00:00",
                }
            ]
        }
        response = Mock()
        response.status_code = 200
        response.json.return_value = payload
        with patch.dict(
            os.environ,
            {
                "VIDEO_AGENT_API_URL": "https://persistent-video-service.example",
                "VIDEO_API_TOKEN": "test-token",
            },
            clear=False,
        ), patch.object(web_app, "requests", create=True) as requests:
            requests.get.return_value = response
            result = web_app.list_videos()
        self.assertEqual(result["videos"], payload["videos"])
        requests.get.assert_called_once_with(
            "https://persistent-video-service.example/videos",
            headers={"Authorization": "Bearer test-token"},
            timeout=8,
        )


if __name__ == "__main__":
    unittest.main()
