import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cloudinary_playback import create_temporary_playback_url


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

    def test_non_https_signed_url_is_rejected(self):
        with patch.dict(os.environ, {"CLOUDINARY_URL": "cloudinary://key:secret@demo"}, clear=False), patch(
            "cloudinary_playback.cloudinary.utils.private_download_url",
            return_value="http://evil.example/video.mp4",
        ):
            with self.assertRaises(RuntimeError):
                create_temporary_playback_url("short-drama/video_test")


if __name__ == "__main__":
    unittest.main()
