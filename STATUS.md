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

## NEXT
1. Verify fresh CI execution when the GitHub Actions push run is exposed by the connector.
2. Add a concrete transcription provider behind the existing boundary.
3. Add Meta analytics ingestion.
4. Add ad-spend/revenue adapters where official APIs expose them.
5. Add actual video-generation provider adapter after its API contract is available.
6. Run live discovery/analytics only after credentials/permissions are supplied; then capture evidence IDs and timestamps.
