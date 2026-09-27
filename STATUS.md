# STATUS.md - Single Source of Truth - Short Drama Video Agent

## CURRENT STATE (2026-09-21)
- P1 foundation added: Trend Intelligence, Rights/Provenance Gate, Idea/URL Inbox, and platform-neutral Analytics schema.
- P1 modules are deterministic and evidence-first; they do not fabricate live platform data or claim legal clearance.
- P1 live connectors/production telemetry are not yet connected.
- GitHub repo source verified.
- MetaPublisher: P0.3 hardened; Meta scope preserved.
- TikTokPublisher: P0.4 real Direct Post transport implemented; blocked without live OAuth credentials.
- YouTubePublisher: P0.4 real resumable upload transport implemented; blocked without live OAuth credentials.
- Visual Factory and web dashboard present.
- SQLite persistence foundation present.

## VERIFIED BY SOURCE INSPECTION
- TikTok endpoints/state flow implemented in publisher.py.
- YouTube resumable upload implemented in publisher.py.
- Evidence Gate is fail-closed: no receipt => no PUBLISHED.
- No real credentials stored in repository.
- Meta code was outside the TikTok/YouTube replacement scope.

## HUMAN ACTION REQUIRED
- TikTok developer app + OAuth grant for video.publish + app audit for public visibility.
- TikTok PULL_FROM_URL domain/URL-prefix verification.
- YouTube Google Cloud OAuth client + user consent + refresh token.
- Railway plan activation before deployment.
- Muse Video API key/endpoint for real generation.

## FRESH EXECUTION STATUS
- GitHub Actions run 35653974857 = SUCCESS on 2026-09-21.
- Meta audit = 14 visible PASS assertions.
- TikTok/YouTube audit = 17 visible PASS assertions.
- Tests use mocked provider responses and no live credentials.
- Docker build, Railway deployment, and live platform publishing are not claimed.

## P1 AUDIT
- `tests/test_p1_intelligence_audit.py` added with 8 deterministic assertions.
- Trend score is explicitly a heuristic and requires observed source metrics.
- Rights engine is an operational screening gate, not legal advice.
- Analytics keeps unavailable metrics as `UNKNOWN`/`None`; no fabricated revenue/views.

## P1.1 DISCOVERY PIPELINE
- Added SourceAdapter -> Fetch -> Normalize -> Trend Rank -> Rights Gate -> Platform Fit orchestration.
- YouTube adapter uses the official Data API search.list + videos.list flow and fails closed without `YOUTUBE_DATA_API_KEY`.
- TikTok adapter targets the official Research API video query and fails closed without `TIKTOK_RESEARCH_ACCESS_TOKEN`.
- No live platform data is fabricated; access failures are surfaced as `ACCESS_REQUIRED`.
- Platform fit is descriptive and constraint-based, not a performance guarantee.

## FRESH EXECUTION STATUS
- P1.1 commits added to `main`: `dc90297240549777eb870008fea0d6ab92291d8d`, `1eb8bc64775696c8d1768b83703d0e9d97075f26`, `b632ee48710ada1391cf4db8a1ea526bab437d91`, `445ddb833174258390cb873de8f63b9b846ca26f`.
- These commit SHAs prove repository writes only; they do not prove CI success.

## P1.2 SOURCE INGESTION + POLICY EVIDENCE
- Added public URL metadata/text fetcher for Idea Inbox; it does not download or republish third-party media.
- Transcript state remains `NOT_AVAILABLE` until a real transcript provider or user-supplied transcript is present.
- Added platform-specific policy evidence for YouTube, TikTok, Instagram, and Facebook with official source URLs.
- YouTube permission does not automatically clear monetization review; reused-content policy is tracked separately.

## P1.3 ANALYTICS + LEARNING
- Added SQLite persistence for analytics events with deterministic event IDs.
- Added authorized YouTube Analytics ingestion for views/engagement/watch time and optional revenue metrics.
- Added authorized TikTok Display API ingestion for recent owned/public video snapshots.
- Added a deterministic learning loop that converts observed performance into reusable selection features without inventing missing metrics.
- YouTube Analytics monetary metrics require the appropriate OAuth scope; TikTok access requires the applicable Login Kit/API permissions.

## VERIFIED IMPLEMENTATION BOUNDARY
- Discovery is now real-API capable for YouTube Data API and TikTok Research API, but credentials/approvals are not present in the repository and live calls were not executed.
- URL ingestion is implemented for public HTML metadata/text; transcription remains an explicit provider boundary.
- Rights screening is fail-closed and backed by official policy evidence; it is not legal clearance.
- Platform recommendation is rule-based fit, not a guaranteed performance prediction.
- Analytics persistence and learning logic are implemented; no live analytics execution is claimed.

## CURRENT BLOCKERS
- YouTube Data API key for public discovery.
- TikTok Research API approval/token for public discovery; TikTok states developer account alone is insufficient and Research access requires eligibility/application/approval.
- YouTube Analytics OAuth with `yt-analytics.readonly`; monetary metrics additionally require `yt-analytics-monetary.readonly`.
- TikTok authorized user token with `video.list` for owned-video analytics.
- Actual video-generation provider endpoint/key.
- Railway plan activation before production deployment.

## P1.4 META ADS + GENERATION BOUNDARY
- Added Meta Graph/Marketing API adapters with explicit credential gates.
- Meta Graph default moved to v26.0 and remains configurable.
- Added Meta Ads Insights normalization for observed spend and attribution values; conversion/action values are not silently relabeled as business revenue.
- Added a generic authenticated HTTP video-generation adapter. It accepts only an explicit provider contract and real artifact evidence.
- Existing visual factory is now explicitly PROMPT_ONLY_UNTIL_PROVIDER_CONFIGURED; it no longer presents the placeholder Muse model as a real generator.
- Dashboard fake ROI/profit claims were removed. /generate now returns PLAN_ONLY until a real generation artifact exists.
- Railway was checked again: only natural-success and innovative-clarity are accessible; no Short Drama service/project exists, so no deployment was attempted.

## FRESH EXTERNAL RESEARCH
- TikTok Direct Post currently requires video.publish; unaudited clients are restricted to private viewing until audit.
- TikTok Display API currently requires video.list plus Login Kit/API product approval for authorized user video access.
- TikTok Research API requires an approved research project/client credentials.
- YouTube Analytics monetary metrics require the monetary readonly scope and applicable monetization access; Analytics processing can lag real-time Data API statistics.
- Meta Graph API v26.0 is current in the researched September 2026 version list; Marketing API versioning is separately versioned.

## FINAL IMPLEMENTATION BOUNDARY
Discovery -> Trend scoring -> Idea Inbox -> URL evidence fetch -> Rights screening -> Platform fit -> Story/beat planning -> Generation contract -> Approval -> Publisher Evidence Gate -> Analytics -> Ad spend/revenue normalization -> Learning signals.

Still not executable without external credentials/approvals/provider access:
- YouTube Data API key
- TikTok Research approval/token
- TikTok Login/API approval + user authorization
- YouTube Analytics OAuth
- Meta access/permissions
- actual video-generation provider endpoint/key
- Railway billing/plan activation

## NEXT
1. Verify fresh CI execution when the GitHub Actions push run is exposed by the connector.
2. Add a concrete transcription provider behind the existing boundary.
3. Add Meta analytics ingestion.
4. Add ad-spend/revenue adapters where official APIs expose them.
5. Add actual video-generation provider adapter after its API contract is available.
6. Run live discovery/analytics only after credentials/permissions are supplied; then capture evidence IDs and timestamps.

## FINAL LOCAL AUDIT — 2026-09-21
- Desktop Commander cloned and audited the exact GitHub main revision.
- Python compile: PASS.
- Dependency imports (python-telegram-bot, FastAPI, Uvicorn): PASS after adding missing runtime dependencies.
- Bot safe-catalog smoke: PASS; production trend fixture is now empty until live discovery evidence exists.
- Web app import smoke: PASS.
- Full deterministic audit suite: PASS — P1 8, discovery 4, idea/rights 3, analytics persistence 1, analytics adapters 2, analytics ingestion 1, learning 2, media/finance 4, Meta Ads/generation 2, repository lifecycle 1, Meta legacy audit 14, TikTok/YouTube legacy audit 17.
- Repository lifecycle bug fixed: SQLite connections now close explicitly; analytics table is included in health checks; analytics tests close repositories.
- Fake-success paths fixed in Telegram bot: no stale trend ranking, no fake Muse generation, no fake Preview/Approve/Publish, and edit responses are PLAN_ONLY until a real artifact exists.
- Stale fixed-ROI dashboard/document claims removed.
- Stale trend fixture catalog removed from production (trending_stories.json is now empty).
- Final local working tree was clean after removing generated cache directories.
- Latest audited main revision before this status-only commit: 5d5bcaf3fe19c018136066a7fa40fa55be4343bc.

## FRESH REAL VIDEO EVIDENCE - 2026-09-27
- Shot 1 of THE LAST VOICEMAIL was generated as a real MP4 through the connected Higgsfield executor.
- Artifact: C:\Users\LTC\ShortDrama_Shot1_20260927.mp4
- Verified: 1430570 bytes; H.264 480x854 24fps; 7.041667s; AAC audio; ffmpeg full decode PASS.
- SHA-256: 0F12F280B776B73B1760F00DEE2D55EC6BD5C7DDC8BC39570C34899A8F6D8423
- Publication was not attempted.
- This is generation evidence, not a claim that Episode 1 or the full pilot is complete.

## RELEASE CANDIDATE BOUNDARY
The codebase passes the local deterministic audit, but production runtime still requires external credentials/approvals/provider access listed above. No production deployment was performed.

## TIKTOK + YOUTUBE HARDENING — 2026-09-22
- Fresh official-doc audit completed against current TikTok and YouTube documentation.
- TikTok hardened: credential gate returns `BLOCKED_CREDENTIALS`; explicit error taxonomy; bounded max-3 retry; token sanitization; deterministic platform idempotency key; evidence fields completed; Direct Post receipt requires `PUBLISH_COMPLETE` plus `publicaly_available_post_id`.
- TikTok OAuth refresh helper added; current TikTok documentation says refresh tokens can rotate, so the returned replacement must be persisted by the external credential layer.
- TikTok FILE_UPLOAD now enforces the current 4GB/1000-chunk boundary and sequential Content-Range transfer rules. PULL_FROM_URL remains dependent on TikTok URL/domain verification.
- YouTube hardened: credential gate; explicit `youtube.upload` scope constant; resumable Location gate; chunk-level retry; bounded retry count; token sanitization; deterministic platform idempotency key.
- YouTube verification now polls `videos.list` with `status,processingDetails` and only reaches `PUBLISHED` after a real `videoId`, processed state, and matching requested privacy status.
- Important current-doc correction: the old 1600-unit `videos.insert` quota assumption is stale. Current Google documentation uses a separate 100-calls/day `videos.insert` bucket at 1 unit/call; other methods use the general quota bucket.
- Fresh local execution on Desktop Commander device Fattouh at commit `f5b5ec8e96e4baf58b9d8957e58c7abdc5f4821f`: Python 3.14.6; `py_compile` PASS; `tests/test_tiktok_youtube_audit.py` printed `=== Summary: 30 PASS / 0 FAIL ===`. No live credentials or live publishing were used.
- MetaPublisher, Meta state, Meta persistence, and Meta architecture were not modified by this hardening patch.

## FRESH FREE PRODUCTION FALLBACK — 2026-09-27
- Added `rendering/episode1_animatic.py` as an isolated deterministic fallback renderer.
- It does not pretend to be AI video generation: it uses the verified real Shot 1 MP4 plus existing fictional-character/reference stills, FFmpeg Ken-Burns motion, captions, and local `espeak-ng` speech.
- GitHub Actions public-runner execution completed successfully: run `36333723374`, job `108660451880`.
- Evidence Gate: `EVIDENCE_GATE_PASS`.
- Final Episode 1 fallback artifact: 95.000 seconds, H.264 720x1280 24fps, AAC 48kHz stereo, 4,205,506 bytes in the latest GitHub Actions render.
- Final artifact SHA-256 from the latest verified GitHub Actions render: `A638A844C6D95CDDF8B6CAC8B82DE94AEB23F101A55BB94009FFD7993CF47581`.
- Full FFmpeg decode: `FFMPEG_DECODE_PASS`.
- Source Shot 1 SHA-256 matches the previously verified real Shot 1: `0F12F280B776B73B1760F00DEE2D55EC6BD5C7DDC8BC39570C34899A8F6D8423`.
- Publication: `NOT_PERFORMED`.
- The fallback removes the immediate production dead-end when an AI video provider is unavailable. It is explicitly labeled `DETERMINISTIC_MOTION_FALLBACK`; it does not replace or weaken the external AI video-generation Evidence Gate.
- GitHub Actions standard runners are free for public repositories, so this fallback does not require Railway, a paid video model, or a local GPU.


## RIGHTS / PROVENANCE EVIDENCE — 2026-09-27
- CreativeClaw Terms of Service (updated 2026-09-13) state that CreativeClaw does not claim ownership of generated Output and permits commercial use, while placing responsibility for third-party rights on the user.
- Higgsfield Terms of Use (updated 2026-07-26) state that Higgsfield does not claim ownership of Outputs and does not restrict commercial use; users remain responsible for third-party rights and applicable AI disclosure.
- The Episode 1 fictional character prompts explicitly excluded celebrity/real-person resemblance.
- Publication remains disabled until the separate publication approval/evidence gate is satisfied.


## PRODUCTION PIPELINE AUDIT — 2026-09-27
- Canonical repo verified: `alkadyenjy2/alkadyenjy2-short-drama-video-agent`, public, default branch `main`.
- Latest repo revision after this audit work: `d17f3d506b881793731190d412a5315d71bf2c03`.
- Existing deterministic audit evidence remains valid: latest full Python audit run `36335553519` completed SUCCESS; prior TikTok/YouTube audit run `35662151553` completed SUCCESS with the documented 30 PASS / 0 FAIL suite. No claim is made that these tests prove live provider execution.
- Real video evidence remains limited to Shot 1 and the Episode 1 deterministic fallback artifact documented above. Code/workflow presence is not treated as media evidence.
- YouTube transport is implemented and hardened, but the current ChatGPT YouTube execution connector has no connected YouTube account: xpost account discovery returned an empty account list. Repository OAuth variables are not exposed/verified in this environment. Therefore YouTube publication is BLOCKED and was not attempted.
- Added `youtube_agent.py`: one release orchestrator, maximum 10 episodes, explicit stage states SCRIPT -> ASSETS -> RENDER -> MP4_EVIDENCE -> METADATA -> APPROVAL -> PUBLISH_EVIDENCE, and a hard approval record requirement before calling the existing YouTube transport.
- Added isolated `tests/test_youtube_agent.py` and `.github/workflows/youtube-agent-audit.yml`. The pre-existing Python audit also ran successfully because its test path includes `tests/**`; this does not constitute live publishing evidence.
- OpenArt account is authenticated on Free plan with 10 credits. Current catalog has no Qwen Image 2.1 or MovieFlow entries and no DramaClaw executor. The only currently affordable OpenArt image route is Kling 3 Omni at 10 credits/image. One Episode 1 poster was submitted as the requested secondary creative adapter; it is pending and no poster completion is claimed yet.
- Qwen Image 2.1 / MovieFlow were NOT executed because the required DramaClaw-first pilot condition is not satisfied by an available authorized executor, and the OpenArt catalog does not expose those models.
- Cantina AI fruit-pregnancy meme was not executed.
- No YouTube/TikTok/Meta publication or test post was sent.
- Release status taxonomy: READY = stage prerequisites verified; GENERATED = real artifact exists; PUBLISHED = real platform receipt + verification exists; BLOCKED = required external gate unavailable; NOT VERIFIED = evidence insufficient.


## EVIDENCE CORRECTION — 2026-09-27
- The latest GitHub Actions Episode 1 render run `36333867611` is the canonical reproducible artifact evidence for the repository.
- Its manifest reports 95.000s, H.264 720x1280 24fps, AAC 48kHz stereo, `FFMPEG_DECODE_PASS`, 4,205,506 MP4 bytes, SHA-256 `A638A844C6D95CDDF8B6CAC8B82DE94AEB23F101A55BB94009FFD7993CF47581`.
- The uploaded artifact exists as GitHub Actions artifact `10936862104` (ZIP containing MP4 + manifest; 4,210,961 bytes). The artifact ZIP digest is `43d4d583c2d0de90d7f46ddc474f6790bab2250f74a565b86bf7e26415d74bdc`.
- An earlier local artifact hash recorded elsewhere (`8556...`) is not used as current canonical evidence because the latest reproducible CI render has different bytes. No publication claim is attached to either artifact.


## FINAL EXECUTION AUDIT — 2026-09-27 20:45 +03:00
- Latest repository HEAD after execution fixes: `103f84bcd11d57922256e405f2c0dc5ba34c3e3a` (documentation-only final-audit update).
- YouTube Agent CI regression was diagnosed from GitHub Actions run `36337790527`: the test failed because the repository root was not on `sys.path`. Fixed in commit `56279d223593a946935816096168c9df01019578` by invoking the test with `PYTHONPATH=.`; added a missing-file MP4 gate assertion in `2b0270a282ea5aa097cea6fda2575e28dc8bdbbb`.
- Fresh Actions evidence for the repaired HEAD was not exposed by the connected GitHub connector at audit time; therefore the repaired YouTube Agent CI is NOT VERIFIED, not marked PASS.
- Railway audit found two pre-existing services named `short-drama-video-agen`, both sourced from the non-canonical repository name `alkadyenjy2/short-drama-video-agen`. The active Docker service deployment `b8c071cd-0aa0-45ba-9903-d92c92f23de3` is CRASHED because Telegram rejected the configured BOT_TOKEN. This is stale/non-canonical infrastructure and was not repointed or overwritten.
- Canonical production publication remains unverified: no connected YouTube execution account was available, and no live publication was attempted.
- Canonical real-media evidence remains EP01 deterministic fallback: 95.000s H.264 720x1280/AAC artifact, SHA-256 `A638A844C6D95CDDF8B6CAC8B82DE94AEB23F101A55BB94009FFD7993CF47581`, FFmpeg decode PASS, publication NOT_PERFORMED.
- EP02–EP10 remain NOT VERIFIED; the release orchestrator hard-caps publication at 10 episodes and independently gates each episode.
