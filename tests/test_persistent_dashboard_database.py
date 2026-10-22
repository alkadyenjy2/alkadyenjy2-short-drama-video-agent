import os
import unittest
from unittest.mock import Mock, patch

import web_app


class PersistentDashboardDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.repo = Mock()
        self.repo.health_check.return_value = True
        self.repo.list_video_versions.return_value = [
            {"video_id": "smoke-test", "current_version": "v1", "story_id": "test-story"}
        ]

    @patch.dict(
        os.environ,
        {
            "DATABASE_URL": "postgresql://test:secret@localhost/testdb",
            "VIDEO_AGENT_API_URL": "https://retired-railway.example",
        },
        clear=True,
    )
    @patch("web_app.get_repository")
    @patch("web_app.requests.get")
    def test_health_prefers_postgres_over_retired_railway(self, http_get, get_repository):
        get_repository.return_value = self.repo

        result = web_app.health()

        self.assertTrue(result["db"])
        self.assertEqual(result["persistence_source"], "postgres")
        http_get.assert_not_called()
        self.repo.health_check.assert_called_once()
        self.repo.close.assert_called_once()

    @patch.dict(
        os.environ,
        {
            "DATABASE_URL": "postgresql://test:secret@localhost/testdb",
            "VIDEO_AGENT_API_URL": "https://retired-railway.example",
        },
        clear=True,
    )
    @patch("web_app.get_repository")
    @patch("web_app.requests.get")
    def test_video_inventory_reads_postgres_before_legacy_api(self, http_get, get_repository):
        get_repository.return_value = self.repo

        result = web_app.list_videos()

        self.assertEqual(result["storage"], "postgres")
        self.assertEqual(result["videos"][0]["video_id"], "smoke-test")
        http_get.assert_not_called()
        self.repo.init_schema.assert_called_once()
        self.repo.list_video_versions.assert_called_once()
        self.repo.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
