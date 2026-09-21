# تعليمات ChatGPT - TikTok + YouTube فقط - لا تلمس Meta / bot / main

## ما خلصته أنا (Meta AI):
- MetaPublisher كامل P0.3 hardened: evidence_record, error classification 190/200/4/17/2207001, retry bounded exponential backoff, sanitization EAA_REDACTED, idempotency_key
- Tests P0.9 كلها PASS (14/14)
- Gap Matrix + Evidence Report + ZIP
- publisher.py الحالي لا يحتوي fake success - ENFORCED - HTTP 200 is NOT proof

## ما عليك انت (ChatGPT):

### 1. TikTokPublisher - حافظ على نفس النمط:
```
- _check_credentials: TIKTOK_CLIENT_KEY, CLIENT_SECRET, ACCESS_TOKEN
- ENDPOINTS: INIT_URL_DIRECT https://open.tiktokapis.com/v2/post/publish/video/init/
  STATUS_URL https://open.tiktokapis.com/v2/post/publish/status/fetch/
  CREATOR_INFO_URL https://open.tiktokapis.com/v2/post/publish/creator_info/query/
- Flow: INIT (PULL_FROM_URL أو FILE_UPLOAD chunked 5-64MB sequential) -> publish_id -> poll STATUS_URL -> video_id
- Privacy: SELF_ONLY default until audit, PUBLIC_TO_EVERYONE requires app review
- Receipt: video_id from status response
- Error taxonomy: 401 auth (190), 403 permission (200), 429 rate_limit retryable, 500 temporary retryable
- Evidence record same structure as Meta: operation_id, video_id, platform, request_timestamp, provider_object_id=video_id, terminal_status, evidence_status
- No fake success - receipt None -> FAILED
- Sanitization same
```

### 2. YouTubePublisher:
```
- ENDPOINT: POST https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable
  -> Location header -> PUT chunks -> videoId
- OAuth: YOUTUBE_CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN, scope https://www.googleapis.com/auth/youtube.upload
- Quota: 10k units/day default, 1600 per upload
- Critical: Unverified projects forced PRIVATE after July 28 2020
- Privacy_status: private default until verification
- Receipt: videoId
- Same evidence gate
```

### 3. لا تلمس:
- MetaPublisher (instagram/facebook) - خلاص hardened
- bot.py - Approval Gate + versioning + Arabic parser
- main.py - deployment foundation
- PublicationState enum - حافظ عليه

### 4. Deliverables منك:
- test_tiktok_youtube_audit.py - نفس P0.9 pattern but for TikTok/YouTube
- TIKTOK_YOUTUBE_GAP_MATRIX.md
- TIKTOK_YOUTUBE_EVIDENCE_REPORT.json
- ZIP نهائي v1.2_P0_FULL_PATCHED.zip يجمع Meta + TikTok + YouTube

### 5. Rules:
- لا success: True بدون receipt حقيقي
- لا PUBLISHED بدون video_id
- HTTP 200 alone NOT proof
- لا credentials حقيقية في tests
- لا second architecture

ابدأ من publisher.py الحالي اللي في ZIP المرفق - هو بالفعل فيه TikTokPublisher و YouTubePublisher كـ stubs BLOCKED - طورهم فقط.
