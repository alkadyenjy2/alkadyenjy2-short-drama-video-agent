# TikTok + YouTube P0.4 Implementation Audit

## Scope
Real API transport flows for TikTok Direct Post and YouTube Data API resumable uploads. Existing publication state machine and Evidence Gate are preserved. Meta code was not modified by this patch.

## TikTok
Creator-info query → Direct Post init → optional FILE_UPLOAD chunk transfer → status polling. Direct Post requires video.publish. PULL_FROM_URL requires verified URL ownership. File chunks are sequential; normal chunks are 5–64 MB. PUBLISH_COMPLETE without a post_id remains PENDING_VERIFICATION because the project rule requires a real receipt before PUBLISHED.

## YouTube
OAuth access token → resumable videos.insert session → Location header → PUT media chunks → videoId → verification read via videos.list. Default privacy is private. HTTP 200 alone is never treated as publication evidence.

## Evidence Gate
Missing credentials = FAILED. Missing TikTok publish_id = FAILED. TikTok PUBLISH_COMPLETE without post_id = PENDING_VERIFICATION. Missing YouTube Location = FAILED. Missing videoId = FAILED. Verification failure = PENDING_VERIFICATION. Only verified provider receipts produce PUBLISHED.

## Human blockers
TikTok developer app/OAuth video.publish/app audit; verified domain for PULL_FROM_URL; YouTube Cloud OAuth client/user consent/refresh token; Railway plan activation; live Muse API credentials.

## Sources
TikTok Direct Post: https://developers.tiktok.com/docs/en/content-posting-api-reference-direct-post
TikTok Creator Info: https://developers.tiktok.com/docs/en/content-posting-api-reference-query-creator-info
TikTok Status: https://developers.tiktok.com/docs/en/content-posting-api-reference-get-video-status
TikTok Media Transfer: https://developers.tiktok.com/docs/en/content-posting-api-media-transfer-guide
YouTube Upload: https://developers.google.com/youtube/v3/guides/uploading_a_video
YouTube Resumable: https://developers.google.com/youtube/v3/guides/using_resumable_upload_protocol
YouTube Quota: https://developers.google.com/youtube/v3/determine_quota_cost