
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
for k in ["META_APP_ID","META_APP_SECRET","META_PAGE_ACCESS_TOKEN","META_IG_USER_ID","META_PAGE_ID"]:
    os.environ.pop(k, None)
from publisher import MetaPublisher, PublicationState, _classify_meta_error, _sanitize_log

def test(name, cond, details=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {name} {details}")
    return cond

print("=== P0.9 Meta Audit Tests ===")
ig = MetaPublisher("instagram")
res = ig.publish_instagram_reel("https://example.com/video.mp4", "test caption", "pub_test_1")
test("1 Instagram blocked without creds", res["state"] == PublicationState.FAILED and res["receipt"] is None)
test("1b No fake PUBLISHED", res["state"] != PublicationState.PUBLISHED)
test("1c Evidence BLOCKED_CREDENTIALS", "evidence_record" in res and res["evidence_record"]["evidence_status"] == "BLOCKED_CREDENTIALS")

fb = MetaPublisher("facebook")
res_fb = fb.publish_facebook_video("https://example.com/video.mp4", "title", "desc", "pub_test_1")
test("1d Facebook blocked", res_fb["state"] == PublicationState.FAILED and res_fb["receipt"] is None)

os.environ["META_APP_ID"]="test"; os.environ["META_APP_SECRET"]="test_secret_12345"
os.environ["META_PAGE_ACCESS_TOKEN"]="EAAQtesttoken1234567890longtoken_should_be_redacted_in_logs"
os.environ["META_IG_USER_ID"]="17841480019199018"; os.environ["META_PAGE_ID"]="1000127223180923"
ig2 = MetaPublisher("instagram")
res2 = ig2.publish_instagram_reel("https://example.com/video.mp4", "test", "pub_test_2")
log_str = str(res2)
test("2 No EAA token in logs", "EAAQtesttoken" not in log_str)
test("2b No secret in logs", "test_secret_12345" not in log_str)
for k in ["META_APP_ID","META_APP_SECRET","META_PAGE_ACCESS_TOKEN","META_IG_USER_ID","META_PAGE_ID"]:
    os.environ.pop(k, None)

cat, retry = _classify_meta_error(190, None, 401, "Invalid OAuth access token")
test("4a Auth 190 not retryable", cat == "authentication_failure" and not retry)
cat2, retry2 = _classify_meta_error(200, None, 403, "Application does not have permission (#10)")
test("4b Perm 200 not retryable", cat2 == "authorization_failure" and not retry2)
cat3, retry3 = _classify_meta_error(4, None, 429, "Too many calls")
test("4c Rate limit retryable", cat3 == "rate_limit" and retry3)
cat4, retry4 = _classify_meta_error(2207001, None, 400, "Media creation failed")
test("4d Invalid media not retryable", cat4 == "invalid_media" and not retry4)

res_no = MetaPublisher("instagram").publish_instagram_reel("https://example.com/video.mp4", "caption", "pub_test_5")
test("5 No receipt => not PUBLISHED", res_no["state"] != PublicationState.PUBLISHED and res_no["receipt"] is None)

os.environ["META_APP_ID"]="app"; os.environ["META_APP_SECRET"]="secret"; os.environ["META_PAGE_ACCESS_TOKEN"]="token"
os.environ["META_IG_USER_ID"]="17841480019199018"; os.environ["META_PAGE_ID"]="123"
ig_fake = MetaPublisher("instagram")
res_fake = ig_fake.publish_instagram_reel("https://example.com/video.mp4", "test", "pub_test_6")
test("6 Even with creds but no real API, not PUBLISHED", res_fake["state"] == PublicationState.FAILED and "ENFORCED" in res_fake["evidence_gate"])
test("6b HTTP 200 is NOT proof", "HTTP 200 is NOT proof" in res_fake["evidence_gate"])
for k in ["META_APP_ID","META_APP_SECRET","META_PAGE_ACCESS_TOKEN","META_IG_USER_ID","META_PAGE_ID"]:
    os.environ.pop(k, None)

res_ev = MetaPublisher("instagram").publish_instagram_reel("https://example.com/video.mp4", "test", "pub_evidence")
ev = res_ev.get("evidence_record", {})
required = ["operation_id","video_id","platform","request_timestamp","terminal_status","evidence_status","retry_count","idempotency_key"]
missing = [f for f in required if f not in ev]
test("10 Evidence record fields", len(missing)==0, f"missing={missing}" if missing else "all present")

print("=== Summary ===")
