# TikTok + YouTube Gap Matrix — Hardened 2026-09-22

| Component | Current | Gap found | Fix | Status |
|---|---|---|---|---|
| TikTok Direct Post init | Official `/v2/post/publish/video/init/` | Legacy implementation lacked complete evidence metadata/idempotency | Hardened init, bounded retry, evidence record | PATCHED |
| TikTok creator info | Official `/v2/post/publish/creator_info/query/` | Needed explicit credential/evidence handling | Preserved required preflight and fail-closed path | PATCHED |
| TikTok status | Official `/v2/post/publish/status/fetch/` | Old code treated public post ID as generic receipt without full evidence fields | Receipt now requires `PUBLISH_COMPLETE` + TikTok `publicaly_available_post_id` | PATCHED |
| TikTok receipt naming | Official response calls it `post_id`, not `video_id` | User contract used `video_id` wording | Code uses provider `post_id` as `provider_object_id`/receipt; no invented `video_id` | VERIFIED |
| TikTok scopes | `video.publish` for Direct Post; `video.upload` for Upload; `user.info.basic` is a Login Kit/basic identity scope | No scope declaration in publisher | Added explicit required-scope constants; runtime still depends on OAuth grant | PATCHED / HUMAN AUTH |
| TikTok OAuth | Current Login Kit uses authorization code; PKCE is required for desktop/mobile, not web; refresh tokens may rotate | Publisher had no refresh helper | Added refresh helper with rotation detection; persistence remains external | PATCHED / HUMAN AUTH |
| TikTok privacy | `PUBLIC_TO_EVERYONE` is constrained by creator options and unaudited clients are private-only | Public visibility could be overclaimed | Default remains `SELF_ONLY`; creator options are authoritative | PATCHED |
| TikTok PULL_FROM_URL | HTTPS + verified domain/URL prefix; redirects are not followed | Existing code only checked HTTPS | Contract documented; runtime cannot independently prove ownership | PARTIAL / HUMAN |
| TikTok FILE_UPLOAD | Sequential `Content-Range`; 5–64 MB chunks, final chunk exception; <5 MB whole upload; max 1000 chunks | Chunk count/evidence needed hardening | Enforced size/chunk-count bounds and sequential transfer | PATCHED |
| TikTok rate/retry | Init 6 req/min/user; status 30 req/min/user; retryable 429/5xx/spam-cap cases | Error taxonomy/retry accounting incomplete | Explicit classifier + max 3 retries + evidence retry count | PATCHED |
| TikTok secrets | Tokens must not enter logs | Error strings could leak tokenized URLs | Added sensitive-token sanitization | PATCHED |
| TikTok idempotency | No provider-native idempotency key is documented in current Direct Post request schema | Internal key was not consistently attached | Deterministic SHA-256 key from publication video/story/platform context | PATCHED |
| YouTube resumable init | Official resumable `videos.insert` upload session + `Location` | Old code accepted Location but lacked full evidence | Preserved flow and fail-closed Location check | PATCHED |
| YouTube OAuth | `https://www.googleapis.com/auth/youtube.upload` | No explicit scope constant | Added required scope constant; live OAuth remains external | PATCHED / HUMAN AUTH |
| YouTube chunks | Chunk size must be multiple of 256 KB except final chunk | Existing 8 MiB chunk is valid, but evidence/retry path needed review | Retained 8 MiB and added chunk-level retry | PATCHED |
| YouTube processing | `videos.list` supports `status` + `processingDetails`; processing can remain `processing` | Old code verified only video ID, then marked PUBLISHED | Polls until processed/succeeded before PUBLISHED | PATCHED |
| YouTube privacy | `status.privacyStatus` is source of truth; unverified projects are restricted to private | Old code could mark PUBLISHED after ID verification | Privacy mismatch yields `RECEIPT_VERIFIED`, not `PUBLISHED` | PATCHED |
| YouTube quota | Current docs changed in 2026: `videos.insert` has a separate 100-calls/day bucket and 1 unit/call; old 1600-unit assumption is stale | Prior documentation claimed ~6/day from 1600 units | Matrix corrected to current official quota model | VERIFIED |
| YouTube errors | `quotaExceeded` and `uploadLimitExceeded` are distinct; `forbidden`/invalid media are non-retryable | Old classifier treated quota as non-retryable | Current classifier separates retryable quota/upload-limit from auth/invalid errors | PATCHED |
| YouTube secrets | Refresh token/client secret must stay out of logs | Error sanitization was incomplete | Added sensitive-token sanitization | PATCHED |
| Shared PublicationState | Existing enum | Risk of duplicate state machine | Reused existing `PublicationState`; no new enum | VERIFIED |
| Shared publications dict | Existing dict | Risk of second persistence/router | Reused existing `publications` dict for deterministic key context | VERIFIED |
| Meta boundary | Out of scope | None intentionally addressed | No MetaPublisher changes in this patch | PRESERVED |

## Official evidence

- TikTok Direct Post / scopes / privacy / init: official TikTok docs.
- TikTok status: official status response exposes `publicaly_available_post_id`; TikTok does not call this a `video_id`.
- TikTok media transfer: official chunk and URL-ownership rules.
- TikTok OAuth: official Login Kit/token-management docs.
- YouTube upload/resumable/processing/privacy/quota: official Google Developers docs.

## Fresh execution boundary

The repository contains a printed audit suite with mocked provider responses. The GitHub connector currently exposes no workflow status for the new push commits, and no live credentials are present. Therefore this report does not claim a fresh CI PASS for the hardened revision.