import os
import unittest
from unittest.mock import Mock, patch

from fastapi import HTTPException

import backend_app


class PersistentApiTests(unittest.TestCase):
    def setUp(self):
        self.repo = Mock()
        self.repo.health_check.return_value = True
        self.repo.create_or_update_video_version.return_value = {
            "video_id": "api-smoke",
            "current_version": "v1",
            "story_id": "test-story",
        }
        self.repo.get_video_version.return_value = {
            "video_id": "api-smoke",
            "current_version": "v1",
            "story_id": "test-story",
        }

    @patch.dict(os.environ, {"VIDEO_API_TOKEN": "test-token"}, clear=True)
    @patch("backend_app.repository")
    def test_authenticated_upsert_requires_and_verifies_readback(self, repository):
        repository.return_value = self.repo
        body = backend_app.VideoVersionInput(
            video_id="api-smoke", current_version="v1", story_id="test-story"
        )

        result = backend_app.upsert_video(body, authorization="Bearer test-token")

        self.assertTrue(result["readback_verified"])
        self.assertEqual(result["video"]["video_id"], "api-smoke")
        self.repo.create_or_update_video_version.assert_called_once_with(
            "api-smoke", "v1", "test-story"
        )
        self.repo.get_video_version.assert_called_once_with("api-smoke")
        self.repo.close.assert_called_once()

    @patch.dict(os.environ, {"VIDEO_API_TOKEN": "test-token"}, clear=True)
    def test_upsert_rejects_missing_or_wrong_bearer_token(self):
        body = backend_app.VideoVersionInput(
            video_id="api-smoke", current_version="v1", story_id="test-story"
        )

        with self.assertRaises(HTTPException) as missing:
            backend_app.upsert_video(body, authorization=None)
        self.assertEqual(missing.exception.status_code, 401)

        with self.assertRaises(HTTPException) as wrong:
            backend_app.upsert_video(body, authorization="Bearer wrong-token")
        self.assertEqual(wrong.exception.status_code, 401)

    @patch.dict(os.environ, {"VIDEO_API_TOKEN": ""}, clear=True)
    def test_upsert_fails_closed_when_token_is_not_configured(self):
        body = backend_app.VideoVersionInput(
            video_id="api-smoke", current_version="v1", story_id="test-story"
        )

        with self.assertRaises(HTTPException) as missing_config:
            backend_app.upsert_video(body, authorization="Bearer test-token")
        self.assertEqual(missing_config.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
