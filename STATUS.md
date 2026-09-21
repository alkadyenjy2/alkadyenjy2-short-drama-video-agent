# STATUS.md - Single Source of Truth - Short Drama Video Agent

## CURRENT STATE (2026-09-21)
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
- Python tests have not been executed in this GitHub-only environment; no PASS claim is made.
- Docker build, Railway deployment, and live platform publishing are not claimed.

## NEXT
1. Run tests/test_meta_audit.py and tests/test_tiktok_youtube_audit.py in a Python environment with requests.
2. Fix any runtime failures from fresh execution.
3. Add secrets only to deployment environment.
4. Run controlled SELF_ONLY/private E2E and capture real receipts.