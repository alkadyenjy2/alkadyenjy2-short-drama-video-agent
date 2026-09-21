"""Provider-neutral transcription boundary.

No network call is made by this module. A provider implementation can be plugged in
without changing Idea Inbox or rights logic. Missing provider access stays explicit.
"""
from dataclasses import dataclass
from typing import Optional


class TranscriptionAccessError(RuntimeError):
    pass


@dataclass
class TranscriptResult:
    text: str
    provider: str
    evidence_status: str = "OBSERVED"


class TranscriptionAdapter:
    provider = "abstract"

    def transcribe(self, media_url: str) -> TranscriptResult:
        raise NotImplementedError


class ProviderUnavailableTranscriptionAdapter(TranscriptionAdapter):
    provider = "unconfigured"

    def transcribe(self, media_url: str) -> TranscriptResult:
        raise TranscriptionAccessError(
            "No transcription provider configured; transcript remains NOT_AVAILABLE"
        )
