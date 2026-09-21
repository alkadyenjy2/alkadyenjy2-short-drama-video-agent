"""Evidence-first URL ingestion for Idea Inbox.

Fetches public HTML metadata/text only. It does not download or republish third-party media.
Transcript is never fabricated: callers must provide a transcript or connect a dedicated
transcription provider.
"""
from html.parser import HTMLParser
from typing import Dict
import requests
from urllib.parse import urlparse

from rights_engine import validate_source_url


class URLFetchError(RuntimeError):
    pass


class _TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.description = ""
        self._in_title = False
        self._in_body = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title":
            self._in_title = True
        if tag == "meta":
            name = (attrs.get("name") or attrs.get("property") or "").lower()
            if name in {"description", "og:description", "twitter:description"}:
                self.description = attrs.get("content", "")[:2000]
        if tag == "body":
            self._in_body = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag == "body":
            self._in_body = False

    def handle_data(self, data):
        text = " ".join(data.split())
        if not text:
            return
        if self._in_title:
            self.title += text
        elif self._in_body and len(self.parts) < 200:
            self.parts.append(text)


def fetch_public_url(url: str, timeout: int = 20, max_text_chars: int = 12000) -> Dict:
    if not validate_source_url(url):
        raise ValueError("invalid source URL")
    response = requests.get(
        url,
        headers={"User-Agent": "ShortDramaEvidenceFetcher/1.0"},
        timeout=timeout,
        allow_redirects=True,
    )
    if response.status_code >= 400:
        raise URLFetchError(f"source fetch failed: HTTP {response.status_code}")
    content_type = response.headers.get("content-type", "").lower()
    parser = _TextParser()
    if "text/html" in content_type:
        parser.feed(response.text)
    else:
        parser.title = urlparse(response.url).netloc
    text = " ".join(parser.parts)[:max_text_chars]
    return {
        "source_url": url,
        "final_url": response.url,
        "status": "FETCHED",
        "http_status": response.status_code,
        "content_type": content_type,
        "title": parser.title[:500],
        "description": parser.description,
        "text": text,
        "transcript_status": "NOT_AVAILABLE",
        "evidence_status": "OBSERVED",
    }


def attach_transcript(document: Dict, transcript: str, provider: str) -> Dict:
    if not transcript or not transcript.strip():
        raise ValueError("transcript is empty")
    result = dict(document)
    result["transcript"] = transcript
    result["transcript_provider"] = provider
    result["transcript_status"] = "OBSERVED"
    return result
