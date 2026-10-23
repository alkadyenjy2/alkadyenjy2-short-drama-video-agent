"""Regression coverage for the public Hugging Face video adapter.

No live provider requests are made by these tests.
"""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import hf_gradio_video_generation as adapter


class HuggingFaceVideoGenerationTests(unittest.TestCase):
    @patch.object(adapter, "_call_gradio")
    @patch.object(adapter.requests, "get")
    def test_generation_requests_portrait_video_and_hashes_download(self, get, call_gradio):
        call_gradio.side_effect = [
            {"url": "https://provider.invalid/frame.webp"},
            {"video": "https://provider.invalid/clip.mp4"},
        ]
        response = Mock()
        response.status_code = 200
        response.iter_content.return_value = [b"fake-mp4-bytes"]
        response.__enter__ = lambda self: self
        response.__exit__ = lambda self, *args: False
        get.return_value = response

        with tempfile.TemporaryDirectory() as output_dir:
            artifact = adapter.generate_story_video("A mysterious voicemail", output_dir=output_dir)

        video_call = call_gradio.call_args_list[1]
        self.assertEqual(video_call.args[2][2:4], [512, 896])
        self.assertEqual(artifact.size_bytes, len(b"fake-mp4-bytes"))
        self.assertEqual(len(artifact.sha256), 64)
        self.assertTrue(Path(artifact.local_path).is_file())


if __name__ == "__main__":
    unittest.main()
