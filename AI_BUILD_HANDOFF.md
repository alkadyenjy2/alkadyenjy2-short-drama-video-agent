# AI Build Handoff

## Canonical repository
- Repository: alkadyenjy2/alkadyenjy2-short-drama-video-agent
- Branch: main
- Product: Short Drama World / Nojy Short Drama

## Low-credit execution rule
1. Pull/inspect main and preserve the existing episode/world pipeline.
2. Do not regenerate completed episodes/assets just because a builder is available.
3. Run existing CI/tests and inspect the latest generated artifacts before spending generation credits.
4. Repair deterministic code/render issues first; use generation only for genuinely missing assets.
5. Never claim a video/episode is complete without the actual artifact and verification evidence.
6. Commit every real code/config fix to GitHub so future builder sessions resume from the exact state.

## Definition of done
CI green, latest episode artifacts verified, deterministic render pipeline healthy, and any external/generation blockers clearly marked.
