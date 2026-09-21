import os, tempfile, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

for key in [
    "TIKTOK_CLIENT_KEY","TIKTOK_CLIENT_SECRET","TIKTOK_ACCESS_TOKEN","TIKTOK_REFRESH_TOKEN",
    "YOUTUBE_CLIENT_ID","YOUTUBE_CLIENT_SECRET","YOUTUBE_REFRESH_TOKEN","YOUTUBE_ACCESS_TOKEN"
]:
    os.environ.pop(key, None)

from publisher import (
    TikTokPublisher, YouTubePublisher, PublicationState, publications,
    _classify_tiktok_error, _classify_youtube_error, _platform_idempotency_key,
    _safe_error_text,
)

passed = 0
failed = 0

def test(name, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"[PASS] {name}")
    else:
        failed += 1
        print(f"[FAIL] {name}")
        raise AssertionError(name)

print("=== Fresh TikTok + YouTube Audit ===")

tt = TikTokPublisher()
r = tt.publish_direct_post("https://example.com/video.mp4", "test", [], "pub_tt_blocked")
test("TikTok blocked without creds -> state=FAILED", r["state"] == PublicationState.FAILED)
test("TikTok no fake PUBLISHED on missing creds", r["state"] != PublicationState.PUBLISHED and r["receipt"] is None)
test("TikTok evidence record has BLOCKED_CREDENTIALS", r["evidence_record"]["evidence_status"] == "BLOCKED_CREDENTIALS")
test("TikTok auth error not retryable", _classify_tiktok_error(401, "access_token_invalid", "") == ("authentication_failure", False))
test("TikTok scope error not retryable", _classify_tiktok_error(401, "scope_not_authorized", "") == ("authorization_failure", False))
test("TikTok rate limit retryable", _classify_tiktok_error(429, "rate_limit_exceeded", "") == ("rate_limit", True))
test("TikTok spam cap retryable", _classify_tiktok_error(403, "spam_risk_too_many_posts", "") == ("rate_limit", True))
test("TikTok flow uses official INIT/STATUS/CREATOR URLs",
     tt.INIT_URL.endswith("/v2/post/publish/video/init/") and
     tt.STATUS_URL.endswith("/v2/post/publish/status/fetch/") and
     tt.CREATOR_INFO_URL.endswith("/v2/post/publish/creator_info/query/"))
test("TikTok scopes declared", set(("video.publish","video.upload")).issubset(set(tt.REQUIRED_SCOPES)))

publications["pub_idem"] = {"video_id":"video-7","story_id":"story-3"}
k1 = _platform_idempotency_key("pub_idem", "tiktok")
k2 = _platform_idempotency_key("pub_idem", "tiktok")
k3 = _platform_idempotency_key("pub_idem", "youtube")
test("Idempotency key deterministic per video/story/platform", k1 == k2 and k1 != k3 and len(k1) == 64)

os.environ.update({
    "TIKTOK_CLIENT_KEY":"client",
    "TIKTOK_CLIENT_SECRET":"secret",
    "TIKTOK_ACCESS_TOKEN":"token",
    "TIKTOK_STATUS_POLL_SECONDS":"0",
    "TIKTOK_MAX_STATUS_POLLS":"3",
})
import requests
real_post, real_put = requests.post, requests.put

class FakeResponse:
    def __init__(self, status_code=200, body=None, headers=None):
        self.status_code = status_code
        self._body = body or {}
        self.headers = headers or {}
    def json(self):
        return self._body

calls = {"post":0, "put":0, "status":0}
def tt_post(url, **kwargs):
    calls["post"] += 1
    if url.endswith("/creator_info/query/"):
        return FakeResponse(body={"data":{"privacy_level_options":["SELF_ONLY","PUBLIC_TO_EVERYONE"]},"error":{"code":"ok"}})
    if url.endswith("/video/init/"):
        return FakeResponse(body={"data":{"publish_id":"pub123","upload_url":"https://upload.invalid/u"},"error":{"code":"ok"}})
    calls["status"] += 1
    return FakeResponse(body={"data":{"status":"PUBLISH_COMPLETE","publicaly_available_post_id":[123456789]},"error":{"code":"ok"}})
def tt_put(url, **kwargs):
    calls["put"] += 1
    return FakeResponse(201)

requests.post, requests.put = tt_post, tt_put
with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
    f.write(b"x" * (5 * 1024 * 1024))
    tt_path = f.name
try:
    r = TikTokPublisher().publish_direct_post(tt_path, "caption", [], "pub_tt_realshape")
    test("TikTok mocked provider receipt -> PUBLISHED", r["state"] == PublicationState.PUBLISHED and r["receipt"] == "123456789")
    test("TikTok mocked flow performed INIT/STATUS/PUT", calls["post"] >= 3 and calls["put"] == 1)
    er = r["evidence_record"]
    test("TikTok evidence record has required fields", all(k in er for k in [
        "operation_id","video_id","platform","request_timestamp","provider_object_id",
        "publish_id","status_code","terminal_status","evidence_status","retry_count","idempotency_key"
    ]))
    test("TikTok evidence is VERIFIED only after receipt", er["evidence_status"] == "VERIFIED" and er["provider_object_id"] == "123456789")
finally:
    os.unlink(tt_path)
requests.post, requests.put = real_post, real_put

real_post = requests.post
def tt_200_no_receipt(url, **kwargs):
    if url.endswith("/creator_info/query/"):
        return FakeResponse(body={"data":{"privacy_level_options":["SELF_ONLY"]},"error":{"code":"ok"}})
    return FakeResponse(body={"data":{},"error":{"code":"ok"}})
requests.post = tt_200_no_receipt
r = TikTokPublisher().publish_direct_post("https://example.com/video.mp4","caption",[],"pub_tt_fake")
test("TikTok HTTP 200 alone is NOT proof", r["state"] != PublicationState.PUBLISHED and r["receipt"] is None)
requests.post = real_post

secret_text = "Bearer act.secret123 access_token=act.secret456 refresh_token=ref.secret client_secret=supersecret"
sanitized = _safe_error_text(secret_text)
test("No TikTok secrets in sanitized logs", "act.secret123" not in sanitized and "act.secret456" not in sanitized and "ref.secret" not in sanitized and "supersecret" not in sanitized)

yt = YouTubePublisher()
r = yt.publish("/missing/video.mp4","test","",[],"pub_yt_blocked")
test("YouTube blocked without creds -> state=FAILED", r["state"] == PublicationState.FAILED)
test("YouTube no fake PUBLISHED", r["state"] != PublicationState.PUBLISHED and r["receipt"] is None)
test("YouTube evidence record has BLOCKED_CREDENTIALS", r["evidence_record"]["evidence_status"] == "BLOCKED_CREDENTIALS")
test("YouTube quotaExceeded retryable", _classify_youtube_error(403,"quotaExceeded","") == ("quota_exceeded", True))
test("YouTube uploadLimitExceeded retryable", _classify_youtube_error(400,"uploadLimitExceeded","") == ("upload_limit_exceeded", True))
test("YouTube forbidden not retryable", _classify_youtube_error(403,"forbidden","") == ("authentication_or_authorization_failure", False))
test("YouTube invalidVideo not retryable", _classify_youtube_error(400,"invalidVideo","") == ("invalid_request_or_media", False))
test("YouTube resumable INIT endpoint", yt.INIT_URL == "https://www.googleapis.com/upload/youtube/v3/videos")
test("YouTube required OAuth scope declared", yt.REQUIRED_SCOPE == "https://www.googleapis.com/auth/youtube.upload")

os.environ.update({"YOUTUBE_CLIENT_ID":"client","YOUTUBE_CLIENT_SECRET":"secret","YOUTUBE_ACCESS_TOKEN":"token","YOUTUBE_PRIVACY_STATUS":"private","YOUTUBE_POLL_SECONDS":"0","YOUTUBE_MAX_STATUS_POLLS":"3"})
real_post, real_put, real_get = requests.post, requests.put, requests.get
yt_calls = {"post":0,"put":0,"get":0}
def yt_post(url, **kwargs):
    yt_calls["post"] += 1
    return FakeResponse(200, headers={"Location":"https://upload.invalid/session"})
def yt_put(url, **kwargs):
    yt_calls["put"] += 1
    return FakeResponse(201, body={"id":"yt123"})
def yt_get(url, **kwargs):
    yt_calls["get"] += 1
    return FakeResponse(200, body={"items":[{"id":"yt123","status":{"uploadStatus":"processed","privacyStatus":"private"},"processingDetails":{"processingStatus":"succeeded"}}]})
requests.post, requests.put, requests.get = yt_post, yt_put, yt_get
with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
    f.write(b"y" * 1024)
    yt_path = f.name
try:
    r = YouTubePublisher().publish(yt_path,"title","description",["drama"],"pub_yt_realshape")
    test("YouTube mocked videoId receipt -> PUBLISHED", r["state"] == PublicationState.PUBLISHED and r["receipt"] == "yt123")
    test("YouTube flow performed resumable POST/PUT/verification", yt_calls["post"] == 1 and yt_calls["put"] == 1 and yt_calls["get"] == 1)
    test("YouTube evidence record has required fields", all(k in r["evidence_record"] for k in [
        "operation_id","video_id","platform","request_timestamp","provider_object_id",
        "publish_id","status_code","terminal_status","evidence_status","retry_count","idempotency_key"
    ]))
    test("YouTube evidence is VERIFIED only after processing + privacy verification", r["evidence_record"]["evidence_status"] == "VERIFIED")
finally:
    os.unlink(yt_path)
requests.post, requests.put, requests.get = real_post, real_put, real_get

real_post = requests.post
requests.post = lambda url, **kwargs: FakeResponse(200, body={})
with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
    f.write(b"z" * 1024)
    bad_path = f.name
try:
    r = YouTubePublisher().publish(bad_path,"title","description",[],"pub_yt_fake")
    test("YouTube HTTP 200 alone is NOT proof", r["state"] != PublicationState.PUBLISHED and r["receipt"] is None)
finally:
    os.unlink(bad_path)
requests.post = real_post

print(f"=== Summary: {passed} PASS / {failed} FAIL ===")
assert failed == 0

# Fresh CI trigger: no production behavior change.
