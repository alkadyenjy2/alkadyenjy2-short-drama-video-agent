# Builder Handoff — Short Drama World
Canonical repo: alkadyenjy2/alkadyenjy2-short-drama-video-agent, main.
Product: AI short-drama/video generation workflow. Preserve existing GeneratedWorlds/Nojy direction and current pipeline.
Known proof: HEAD 6fbe3112... and CI previously successful.
Rules: no fake rendered episodes, fake media URLs, fake upload/publication success, or fabricated episode evidence.
Before credits: inspect current pipeline, episode artifacts, tests and CI; reuse all existing implementation.
Closure: generation pipeline/tests/build pass; every claimed episode/render has real artifact evidence; missing external media credentials/providers are BLOCKED rather than simulated.
When credits return: pull main, run verification before generation, fix only confirmed defects, commit/push and verify CI/artifacts. Do not spend builder credits on speculative redesign.