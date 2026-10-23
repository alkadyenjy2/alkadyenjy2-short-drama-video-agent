import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.responses import Response

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cloudinary_playback import create_temporary_playback_url
import web_app


class CloudinaryPlaybackTests(unittest.TestCase):
    def test_missing_credentials_fails_closed_without_signing(self):
        with patch.dict(os.environ, {"CLOUDINARY_URL": ""}, clear=False), patch(
            "cloudinary_playback.cloudinary.utils.private_download_url"
        ) as sign:
            with self.assertRaises(RuntimeError):
                create_temporary_playback_url("short-drama/video_test")
        sign.assert_not_called()

    def test_signed_authenticated_video_url_has_short_expiry(self):
        with patch.dict(os.environ, {"CLOUDINARY_URL": "cloudinary://key:secret@demo"}, clear=False), patch(
            "cloudinary_playback.time.time", return_value=1_800_000_000
        ), patch(
            "cloudinary_playback.cloudinary.utils.private_download_url",
            return_value="https://res.cloudinary.com/demo/video/authenticated/s--signature--/short-drama/video_test.mp4",
        ) as sign:
            result = create_temporary_playback_url("short-drama/video_test", ttl_seconds=300)

        self.assertEqual(
            result["url"],
            "https://res.cloudinary.com/demo/video/authenticated/s--signature--/short-drama/video_test.mp4",
        )
        self.assertEqual(result["expires_at"], 1_800_000_300)
        sign.assert_called_once_with(
            "short-drama/video_test",
            "mp4",
            {"resource_type": "video", "type": "authenticated", "expires_at": 1_800_000_300},
        )

    def test_invalid_public_id_is_rejected_before_signing(self):
        with patch.dict(os.environ, {"CLOUDINARY_URL": "cloudinary://key:secret@demo"}, clear=False), patch(
            "cloudinary_playback.cloudinary.utils.private_download_url"
        ) as sign:
            with self.assertRaises(ValueError):
                create_temporary_playback_url("../outside/video")
        sign.assert_not_called()

    def test_lookalike_cloudinary_hostname_is_rejected(self):
        with patch.dict(os.environ, {"CLOUDINARY_URL": "cloudinary://key:secret@demo"}, clear=False), patch(
            "cloudinary_playback.cloudinary.utils.private_download_url",
            return_value="https://res.cloudinary.com.evil.example/video/authenticated/file.mp4",
        ):
            with self.assertRaises(RuntimeError):
                create_temporary_playback_url("short-drama/video_test")

    def test_non_https_signed_url_is_rejected(self):
        with patch.dict(os.environ, {"CLOUDINARY_URL": "cloudinary://key:secret@demo"}, clear=False), patch(
            "cloudinary_playback.cloudinary.utils.private_download_url",
            return_value="http://evil.example/video.mp4",
        ):
            with self.assertRaises(RuntimeError):
                create_temporary_playback_url("short-drama/video_test")


class ArtifactPlaybackEndpointTests(unittest.TestCase):
    def setUp(self):
        self.artifact = {
            "artifact_id": "artifact_test123",
            "video_id": "video_test123",
            "evidence_status": "OBSERVED",
            "storage_provider": "cloudinary",
            "storage_public_id": "short-drama/video_test123",
            "storage_asset_id": "asset-test123",
        }

    def test_playback_requires_service_authorization_before_database_read(self):
        with patch.dict(os.environ, {"VIDEO_API_TOKEN": "expected-token"}, clear=False), patch(
            "web_app.get_generated_artifact"
        ) as lookup:
            with self.assertRaises(HTTPException) as exc:
                web_app.artifact_playback("artifact_test123", Response(), authorization="Bearer wrong")
        self.assertEqual(exc.exception.status_code, 401)
        lookup.assert_not_called()

    def test_playback_returns_short_lived_url_and_disables_caching(self):
        with patch.dict(os.environ, {"VIDEO_API_TOKEN": "expected-token"}, clear=False), patch(
            "web_app.get_generated_artifact", return_value=self.artifact
        ), patch(
            "web_app.create_temporary_playback_url",
            return_value={"url": "https://res.cloudinary.com/demo/video/authenticated/s--sig--/short-drama/video_test123.mp4", "expires_at": 1_800_000_300},
        ) as sign:
            response = Response()
            result = web_app.artifact_playback("artifact_test123", response, authorization="Bearer expected-token")

        self.assertEqual(result["artifact_id"], "artifact_test123")
        self.assertEqual(result["playback_url"], "https://res.cloudinary.com/demo/video/authenticated/s--sig--/short-drama/video_test123.mp4")
        self.assertEqual(result["expires_in_seconds"], 300)
        self.assertEqual(result["publication_status"], "NOT_PUBLISHED")
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        sign.assert_called_once_with("short-drama/video_test123", ttl_seconds=300)

    def test_missing_artifact_returns_not_found(self):
        with patch.dict(os.environ, {"VIDEO_API_TOKEN": "expected-token"}, clear=False), patch(
            "web_app.get_generated_artifact", return_value=None
        ):
            with self.assertRaises(HTTPException) as exc:
                web_app.artifact_playback("artifact_missing", Response(), authorization="Bearer expected-token")
        self.assertEqual(exc.exception.status_code, 404)

    def test_unverified_or_non_cloudinary_artifact_is_not_playable(self):
        bad_artifact = dict(self.artifact, storage_provider="unknown")
        with patch.dict(os.environ, {"VIDEO_API_TOKEN": "expected-token"}, clear=False), patch(
            "web_app.get_generated_artifact", return_value=bad_artifact
        ), patch("web_app.create_temporary_playback_url") as sign:
            with self.assertRaises(HTTPException) as exc:
                web_app.artifact_playback("artifact_test123", Response(), authorization="Bearer expected-token")
        self.assertEqual(exc.exception.status_code, 409)
        sign.assert_not_called()

    def test_database_error_fails_closed(self):
        with patch.dict(os.environ, {"VIDEO_API_TOKEN": "expected-token"}, clear=False), patch(
            "web_app.get_generated_artifact", side_effect=RuntimeError("database unavailable")
        ):
            with self.assertRaises(HTTPException) as exc:
                web_app.artifact_playback("artifact_test123", Response(), authorization="Bearer expected-token")
        self.assertEqual(exc.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
