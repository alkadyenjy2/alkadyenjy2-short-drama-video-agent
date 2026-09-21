# META GAP MATRIX - Instagram + Facebook - v1.2 P0 Real Audit

## Current State (from publisher.py inspected)
- File: publisher.py (fake version) contains:
  - `class PlatformAdapter: publish() return {"success": True, "platform_id": f"ig_{video_path}"}` -> FAKE SUCCESS VIOLATION
  - No container polling, no media_id/video_id verification, no error classification, no evidence record

## Expected State (P0 Real Contract - Graph API v21.0/v24.0)

### Instagram Reels
- Prerequisites: Business/Creator Professional account linked to Facebook Page, App with instagram_basic + instagram_content_publish + pages_show_list + pages_read_engagement
- Endpoint: POST https://graph.facebook.com/{version}/{ig-user-id}/media
  - Params: media_type=REELS, video_url=public HTTPS (Meta cURLs it), caption max 2200 chars 30 hashtags, share_to_feed=true, access_token=Page token
  - Response: { id: container_id } e.g. 179123456789
- Poll: GET https://graph.facebook.com/{version}/{container_id}?fields=status_code,status
  - Status: IN_PROGRESS -> backoff 5s/8s/12s/15s max 12 attempts (~60-90s), FINISHED -> proceed, ERROR -> FAILED, EXPIRED -> FAILED (24h expiry)
- Publish: POST https://graph.facebook.com/{version}/{ig-user-id}/media_publish creation_id=container_id -> { id: media_id } e.g. 180123456789
- Verify: GET https://graph.facebook.com/{version}/{media_id}?fields=id,permalink -> permalink for audit
- Receipt: media_id + permalink
- Limits: 25 Reels per 24h (some docs 100 per 24h), 100 posts per 24h via /content_publishing_limit, 200 calls/hour per user+app, X-App-Usage header
- Media: MP4/MOV, H.264 Progressive High Profile 4:2:0, AAC 48kHz stereo, 1080x1920 9:16, 3-90 seconds strict, max 1GB, container expires 24h

### Facebook Page Videos (Reels as of June 2025)
- Endpoint: POST https://graph-video.facebook.com/{version}/{page-id}/videos multipart/form-data
- Resumable: POST ?upload_phase=start -> session_id -> transfer -> finish -> video_id (standard 1GB 20min, resumable 1.5GB 45min)
- Receipt: video_id + permalink_url
- Rate: 429 handling exponential backoff

### Gap List
| # | Gap | Severity | Fix Required |
|---|-----|----------|--------------|
| 1 | Fake success without receipt | P0 | Enforce FAILED when receipt None, never PUBLISHED without media_id/video_id |
| 2 | No container status polling | P0 | Implement poll loop with backoff, handle ERROR/EXPIRED |
| 3 | No error classification | P0 | Classify 190 auth, 200 permission, 10, 100, 2207001 invalid_media, 4/17 rate_limit, 5xx temporary |
| 4 | No retry bounded | P1 | Only retry rate_limit, temporary, timeout - bounded 3 retries base 1.5s cap 60s jitter |
| 5 | No evidence record | P0 | operation_id, video_id, platform, request_timestamp, provider_object_id, media_id, permalink, terminal_status, error_code, retry_count, idempotency_key |
| 6 | No token redaction | P0 | _sanitize_log + _redact_token EAA |
| 7 | No idempotency | P1 | Application-level key hashlib video_id+story_id+platforms, check existing publications |
| 8 | No media hosting docs | P1 | Public HTTPS requirement documented |

### Evidence Gate Rules (Absolute)
- Never return success=True as substitute for platform response
- Never mark PUBLISHED without real receipt (media_id/video_id)
- Receipt must contain provider object ID from provider
- HTTP 200 is NOT proof of publication
- If receipt missing -> FAILED or PENDING_VERIFICATION never PUBLISHED
- No hardcoded secrets, env only, no tokens in logs
