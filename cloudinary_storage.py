"""Copy provider-generated MP4s into durable Cloudinary video storage.

Requires CLOUDINARY_URL to be configured securely in the application environment.
Uploads are private to this adapter's configuration; no upload is attempted when
credentials are absent. The provider URL is used only as the upload source and
is not returned to the client or persisted as the canonical artifact URL.
"""
import os
from urllib.parse import urlparse

import cloudinary
import cloudinary.uploader


def store_video_artifact(*, artifact_url: str, video_id: str, story_id: str) -> dict:
    if not os.getenv("CLOUDINARY_URL", "").strip():
        raise RuntimeError("CLOUDINARY_URL is required for durable video storage")

    source = urlparse(artifact_url or "")
    if source.scheme != "https" or not source.hostname or source.username is not None or source.password is not None:
        raise RuntimeError("Provider artifact URL must be HTTPS without embedded credentials")

    cloudinary.config(secure=True)
    result = cloudinary.uploader.upload(
        artifact_url,
        resource_type="video",
        type="upload",
        folder="short-drama",
        public_id=video_id,
        overwrite=False,
        unique_filename=False,
        use_filename=False,
        context=f"story_id={story_id}|video_id={video_id}",
    )
    if not isinstance(result, dict):
        raise RuntimeError("Cloudinary returned an invalid upload response")

    secure_url = result.get("secure_url")
    parsed_result = urlparse(secure_url or "")
    public_id = result.get("public_id")
    asset_id = result.get("asset_id")
    byte_count = result.get("bytes")
    if (
        parsed_result.scheme != "https"
        or not parsed_result.hostname
        or not public_id
        or not asset_id
        or not isinstance(byte_count, int)
        or byte_count <= 0
        or result.get("resource_type") != "video"
    ):
        raise RuntimeError("Cloudinary did not confirm a durable video asset")

    return {
        "artifact_url": secure_url,
        "storage_provider": "cloudinary",
        "storage_public_id": public_id,
        "storage_asset_id": asset_id,
        "storage_bytes": byte_count,
    }
