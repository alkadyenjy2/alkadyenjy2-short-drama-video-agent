import sys
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from http_video_generation import HTTPVideoGenerationAdapter
from video_generation_adapter import VideoGenerationAccessError


def test_polling_url_must_share_provider_origin_before_auth_token_is_sent():
    accepted = Mock(status_code=202)
    accepted.json.return_value = {
        "job_id": "job-1",
        "status_url": "https://attacker.example/steal-token",
    }
    with patch("http_video_generation.requests.post", return_value=accepted), patch(
        "http_video_generation.requests.get"
    ) as get:
        adapter = HTTPVideoGenerationAdapter(
            endpoint="https://provider.example/generate",
            api_key="do-not-leak",
            max_polls=1,
            poll_seconds=0,
        )
        try:
            adapter.generate("script", {})
        except VideoGenerationAccessError as exc:
            assert "status_url" in str(exc)
        else:
            raise AssertionError("cross-origin status_url must be rejected")
    get.assert_not_called()


def test_same_origin_polling_can_return_artifact():
    accepted = Mock(status_code=202)
    accepted.json.return_value = {
        "job_id": "job-1",
        "status_url": "https://provider.example/jobs/job-1",
    }
    done = Mock(status_code=200)
    done.json.return_value = {"artifact_url": "https://media.example/episode.mp4", "duration_sec": 8}
    with patch("http_video_generation.requests.post", return_value=accepted), patch(
        "http_video_generation.requests.get", return_value=done
    ) as get:
        adapter = HTTPVideoGenerationAdapter(
            endpoint="https://provider.example/generate",
            api_key="secret",
            max_polls=1,
            poll_seconds=0,
        )
        artifact = adapter.generate("script", {})
    assert artifact.artifact_url == "https://media.example/episode.mp4"
    assert get.call_args.kwargs["headers"]["Authorization"] == "Bearer secret"


if __name__ == "__main__":
    test_polling_url_must_share_provider_origin_before_auth_token_is_sent()
    test_same_origin_polling_can_return_artifact()
    print("HTTP VIDEO GENERATION SECURITY: 2 PASS")
