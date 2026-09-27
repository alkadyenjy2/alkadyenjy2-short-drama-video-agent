# Short Drama World — 10-Episode Release Pipeline

## Canonical stage contract
Every episode must move through these independent gates:

1. SCRIPT → READY only when the script artifact exists and is identified.
2. ASSETS → READY only when required source assets exist and provenance is recorded.
3. RENDER → GENERATED only when a real renderer returns a real media artifact.
4. MP4_EVIDENCE → GENERATED only after file existence, non-zero size, ffprobe/decode validation, and SHA-256.
5. METADATA → READY only when title/description/tags/privacy metadata is present.
6. APPROVAL → READY only from an explicit approval record containing approver + timestamp.
7. PUBLISH_EVIDENCE → PUBLISHED only after a real YouTube videoId receipt and post-processing/privacy verification.

No stage may infer success from source code, a workflow run, HTTP 200, or a planned URL.

## Release cap
- Maximum episodes in this release: 10.
- The orchestrator rejects episode numbers outside EP01–EP10.
- No batch publish is enabled; each episode remains independently gated.

## Current evidence matrix

| Episode | Script | Assets | Render | MP4 Evidence | Metadata | Approval | Publish Evidence | Overall |
|---|---|---|---|---|---|---|---|---|
| EP01 | READY | READY | GENERATED | GENERATED | READY | BLOCKED | BLOCKED | GENERATED |
| EP02 | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | BLOCKED | BLOCKED | NOT VERIFIED |
| EP03 | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | BLOCKED | BLOCKED | NOT VERIFIED |
| EP04 | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | BLOCKED | BLOCKED | NOT VERIFIED |
| EP05 | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | BLOCKED | BLOCKED | NOT VERIFIED |
| EP06 | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | BLOCKED | BLOCKED | NOT VERIFIED |
| EP07 | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | BLOCKED | BLOCKED | NOT VERIFIED |
| EP08 | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | BLOCKED | BLOCKED | NOT VERIFIED |
| EP09 | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | BLOCKED | BLOCKED | NOT VERIFIED |
| EP10 | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | BLOCKED | BLOCKED | NOT VERIFIED |

## YouTube execution gate
The existing `publisher.py` contains real resumable-upload transport and verification logic. The new `youtube_agent.py` is the approval-gated orchestrator. It will not call the transport unless an explicit approval record exists and real OAuth client/token material is available at runtime.

Current connector audit: no connected YouTube execution account was found. Therefore no publication was attempted.

## Creative adapters
- Primary/core generation: DramaClaw if a real authorized executor becomes available.
- Secondary creative adapter: OpenArt posters. Current OpenArt Free balance was 10 credits; the catalog's only affordable image model was Kling 3 Omni at 10 credits. One EP01 poster request was submitted; completion remains pending and is not claimed here.
- Qwen Image 2.1 and MovieFlow: deferred until after the DramaClaw pilot and only if an authorized, non-duplicate executor is actually available.
- Cantina AI fruit-pregnancy meme: explicitly excluded.

## Evidence rule
`READY`, `GENERATED`, `PUBLISHED`, `BLOCKED`, and `NOT VERIFIED` are evidence states, not optimistic labels.
