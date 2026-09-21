import os, tempfile, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
for key in ["TIKTOK_CLIENT_KEY","TIKTOK_CLIENT_SECRET","TIKTOK_ACCESS_TOKEN","YOUTUBE_CLIENT_ID","YOUTUBE_CLIENT_SECRET","YOUTUBE_REFRESH_TOKEN","YOUTUBE_ACCESS_TOKEN"]: os.environ.pop(key, None)
from publisher import TikTokPublisher, YouTubePublisher, PublicationState, _classify_tiktok_error, _classify_youtube_error
def test(name, condition):
    print("[PASS]" if condition else "[FAIL]", name)
    assert condition, name
print("=== TikTok + YouTube Audit Tests ===")
tt=TikTokPublisher(); r=tt.publish_direct_post("https://example.com/video.mp4","test",[],"pub_tt_1")
test("TikTok missing credentials -> FAILED", r["state"]==PublicationState.FAILED and r["receipt"] is None)
test("TikTok missing credentials -> no PUBLISHED", r["state"]!=PublicationState.PUBLISHED)
yt=YouTubePublisher(); r=yt.publish("/missing/video.mp4","test","",[],"pub_yt_1")
test("YouTube missing credentials -> FAILED", r["state"]==PublicationState.FAILED and r["receipt"] is None)
test("TikTok 401 not retryable", _classify_tiktok_error(401,"access_token_invalid","invalid")==("authentication_failure",False))
test("TikTok 429 retryable", _classify_tiktok_error(429,"rate_limit_exceeded","")==("rate_limit",True))
test("TikTok 500 retryable", _classify_tiktok_error(500,"internal_error","")==("temporary_provider_failure",True))
test("YouTube 403 quota not retryable", _classify_youtube_error(403,"quotaExceeded","quota")==("quota_exceeded",False))
test("YouTube 500 retryable", _classify_youtube_error(500,"backendError","")==("temporary_provider_failure",True))
class FakeResponse:
    def __init__(self,status_code=200,body=None,headers=None): self.status_code=status_code; self._body=body or {}; self.headers=headers or {}
    def json(self): return self._body
os.environ.update({"TIKTOK_CLIENT_KEY":"client","TIKTOK_CLIENT_SECRET":"secret","TIKTOK_ACCESS_TOKEN":"token","TIKTOK_STATUS_POLL_SECONDS":"0"})
import requests
real_post,real_put=requests.post,requests.put
calls={"post":0,"put":0}
def fake_post(url,**kwargs):
    calls["post"]+=1
    if url.endswith("/creator_info/query/"): return FakeResponse(body={"data":{"privacy_level_options":["SELF_ONLY","PUBLIC_TO_EVERYONE"]},"error":{"code":"ok"}})
    if url.endswith("/video/init/"): return FakeResponse(body={"data":{"publish_id":"pub123","upload_url":"https://upload.invalid/u"},"error":{"code":"ok"}})
    return FakeResponse(body={"data":{"status":"PUBLISH_COMPLETE","publicaly_available_post_id":[123456789]},"error":{"code":"ok"}})
def fake_put(url,**kwargs): calls["put"]+=1; return FakeResponse(201)
requests.post,requests.put=fake_post,fake_put
with tempfile.NamedTemporaryFile(suffix=".mp4",delete=False) as f: f.write(b"x"*(5*1024*1024)); video_path=f.name
try:
    r=TikTokPublisher().publish_direct_post(video_path,"caption",[],"pub_tt_e2e")
    test("TikTok mocked receipt -> PUBLISHED",r["state"]==PublicationState.PUBLISHED and r["receipt"]=="123456789")
    test("TikTok mocked upload used PUT",calls["put"]==1)
    test("TikTok evidence verified",r["evidence_record"]["evidence_status"]=="VERIFIED")
finally: os.unlink(video_path)
requests.post,requests.put=real_post,real_put
real_post=requests.post
def fake_200_no_receipt(url,**kwargs):
    if url.endswith("/creator_info/query/"): return FakeResponse(body={"data":{"privacy_level_options":["SELF_ONLY"]},"error":{"code":"ok"}})
    if url.endswith("/video/init/"): return FakeResponse(body={"data":{},"error":{"code":"ok"}})
    return FakeResponse(body={})
requests.post=fake_200_no_receipt
r=TikTokPublisher().publish_direct_post("https://example.com/video.mp4","caption",[],"pub_tt_fake")
test("TikTok HTTP 200 without publish_id -> FAILED",r["state"]==PublicationState.FAILED)
test("TikTok HTTP 200 without receipt -> not PUBLISHED",r["receipt"] is None and r["state"]!=PublicationState.PUBLISHED)
requests.post=real_post
os.environ.update({"YOUTUBE_CLIENT_ID":"client","YOUTUBE_CLIENT_SECRET":"secret","YOUTUBE_ACCESS_TOKEN":"token"})
real_post,real_put,real_get=requests.post,requests.put,requests.get
def yt_post(url,**kwargs): return FakeResponse(200,headers={"Location":"https://upload.invalid/session"})
def yt_put(url,**kwargs): return FakeResponse(200,body={"id":"yt123"})
def yt_get(url,**kwargs): return FakeResponse(200,body={"items":[{"id":"yt123"}]})
requests.post,requests.put,requests.get=yt_post,yt_put,yt_get
with tempfile.NamedTemporaryFile(suffix=".mp4",delete=False) as f: f.write(b"y"*1024); yt_path=f.name
try:
    r=YouTubePublisher().publish(yt_path,"title","description",["drama"],"pub_yt_e2e")
    test("YouTube mocked videoId -> PUBLISHED",r["state"]==PublicationState.PUBLISHED and r["receipt"]=="yt123")
    test("YouTube evidence verified",r["evidence_record"]["evidence_status"]=="VERIFIED")
finally: os.unlink(yt_path)
requests.post,requests.put,requests.get=real_post,real_put,real_get
real_post=requests.post; requests.post=lambda url,**kwargs: FakeResponse(200,body={})
with tempfile.NamedTemporaryFile(suffix=".mp4",delete=False) as f: f.write(b"z"*1024); bad_path=f.name
try:
    r=YouTubePublisher().publish(bad_path,"title","description",[],"pub_yt_fake")
    test("YouTube HTTP 200 without Location -> FAILED",r["state"]==PublicationState.FAILED)
    test("YouTube no receipt -> not PUBLISHED",r["receipt"] is None and r["state"]!=PublicationState.PUBLISHED)
finally: os.unlink(bad_path)
requests.post=real_post
print("=== Summary: all assertions passed if no failure above ===")