import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cloudinary_storage import store_video_artifact


class CloudinaryStorageTests(unittest.TestCase):
    def test_missing_cloudinary_credentials_fails_closed(self):
        with patch.dict(os.environ, {"CLOUDINARY_URL": ""}, clear=False), patch(
            "cloudinary_storage.cloudinary.uploader.upload"
        ) as upload:
            with self.assertRaises(RuntimeError):
                store_video_artifact(
                    artifact_url="https://provider.example/episode.mp4",
                    video_id="video_test",
                    story_id="story_test",
                )
        upload.assert_not_called()

    def test_provider_url_is_copied_to_cloudinary_and_stable_asset_url_returned(self):
        upload_result = {
            "secure_url": "https://res.cloudinary.com/demo/video/upload/v1/short-drama/video_test.mp4",
            "public_id": "short-drama/video_test",
            "asset_id": "asset-123",
            "bytes": 123456,
            "resource_type": "video",
        }
        with patch.dict(os.environ, {"CLOUDINARY_URL": "cloudinary://key:secret@demo"}, clear=False), patch(
            "cloudinary_storage.cloudinary.uploader.upload", return_value=upload_result
        ) as upload:
            result = store_video_artifact(
                artifact_url="https://provider.example/temporary/episode.mp4?token=temporary",
                video_id="video_test",
                story_id="story_test",
            )
        self.assertEqual(result["artifact_url"], upload_result["secure_url"])
        self.assertEqual(result["storage_provider"], "cloudinary")
        self.assertEqual(result["storage_public_id"], upload_result["public_id"])
        self.assertEqual(result["storage_asset_id"], upload_result["asset_id"])
        self.assertEqual(result["storage_bytes"], 123456)
        upload.assert_called_once()
        self.assertEqual(upload.call_args.args[0], "https://provider.example/temporary/episode.mp4?token=temporary")
        self.assertEqual(upload.call_args.kwargs["resource_type"], "video")
        self.assertEqual(upload.call_args.kwargs["type"], "authenticated")
        self.assertEqual(upload.call_args.kwargs["overwrite"], False)

    def test_incomplete_cloudinary_response_is_rejected(self):
        with patch.dict(os.environ, {"CLOUDINARY_URL": "cloudinary://key:secret@demo"}, clear=False), patch(
            "cloudinary_storage.cloudinary.uploader.upload",
            return_value={"secure_url": "http://not-secure.example/video.mp4"},
        ):
            with self.assertRaises(RuntimeError):
                store_video_artifact(
                    artifact_url="https://provider.example/episode.mp4",
                    video_id="video_test",
                    story_id="story_test",
                )


if __name__ == "__main__":
    unittest.main()
