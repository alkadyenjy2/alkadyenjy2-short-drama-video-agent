"""Provider-neutral video generation boundary.

The publisher remains downstream. Generation must return a real artifact path/URL
before publishing can start; no fake render is accepted.
"""
from dataclasses import dataclass
from typing import Dict, Optional


class VideoGenerationAccessError(RuntimeError):
    pass


@dataclass
class VideoArtifact:
    artifact_url: str
    provider: str
    duration_sec: Optional[int] = None
    evidence_status: str = "OBSERVED"


class VideoGenerationAdapter:
    provider = "abstract"

    def generate(self, script: str, scene_plan: Dict, output_format: str = "mp4") -> VideoArtifact:
        raise NotImplementedError


class ProviderUnavailableVideoGenerationAdapter(VideoGenerationAdapter):
    provider = "unconfigured"

    def generate(self, script: str, scene_plan: Dict, output_format: str = "mp4") -> VideoArtifact:
        raise VideoGenerationAccessError(
            "No video-generation provider configured; generation cannot be marked successful"
        )
