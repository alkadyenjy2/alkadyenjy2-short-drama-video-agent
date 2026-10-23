"""Short-lived signed delivery URLs for authenticated Cloudinary videos.

The Cloudinary API secret is used only server-side. Returned links are temporary
bearer links, so callers must authenticate before requesting one and must not
log or persist the returned URL.
"""
import os
import re
import time
from urllib.parse import urlparse

import cloudinary
import cloudinary.utils


_PUBLIC_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9/_-]{0,254}$")


def create_temporary_playback_url(public_id: str, ttl_seconds: int = 300) -> dict:
    if not os.getenv("CLOUDINARY_URL", "").strip():
        raise RuntimeError("CLOUDINARY_URL is required to sign authenticated playback URLs")
    if (
        not isinstance(public_id, str)
        or not _PUBLIC_ID_RE.fullmatch(public_id)
        or any(part in ("", ".", "..") for part in public_id.split("/"))
    ):
        raise ValueError("A valid Cloudinary public ID is required")
    if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, int) or not 30 <= ttl_seconds <= 900:
        raise ValueError("Playback URL lifetime must be between 30 and 900 seconds")

    expires_at = int(time.time()) + ttl_seconds
    cloudinary.config(secure=True)
    url = cloudinary.utils.private_download_url(
        public_id,
        "mp4",
        {"resource_type": "video", "type": "authenticated", "expires_at": expires_at},
    )
    parsed = urlparse(url or "")
    if parsed.scheme != "https" or not parsed.hostname or not (parsed.hostname == "cloudinary.com" or parsed.hostname.endswith(".cloudinary.com")):
        raise RuntimeError("Cloudinary did not return a valid HTTPS playback URL")
    return {"url": url, "expires_at": expires_at}
