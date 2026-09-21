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

## NEXT
1. Verify the fresh GitHub Actions run for P1/P1.1.
2. Add URL fetch/transcription for Idea Inbox.
3. Add platform-specific rights-policy evidence.
4. Add analytics persistence and live ingestion.
5. Add ads/revenue and learning loop.
6. Run controlled SELF_ONLY/private E2E and capture real receipts.