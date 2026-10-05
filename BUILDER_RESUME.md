# Builder Resume Handoff

Purpose: resume Short Drama World / 7mody work without rebuilding.

Canonical branch: main
Last GitHub HEAD audited: b875199959ec1751cbde9d5b58d260619df5bd65

Rules:
- Preserve the existing GeneratedWorlds / Nojy short-drama architecture.
- No fake episode completion, video renders, publication, views, or platform responses.
- Keep episode/version identity and evidence artifacts consistent.
- Run the repository's existing tests/build scripts discovered from the current tree.
- Use builder credits only after code health is known.
- Commit verified changes to GitHub before builder generation.

Next builder action: inspect repository tree and current CI, identify the first real failing check, fix only that, and verify.
