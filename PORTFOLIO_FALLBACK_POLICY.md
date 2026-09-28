# PORTFOLIO FALLBACK & QUOTA POLICY

Status: CANONICAL PORTFOLIO OPERATING RULE — 2026-09-28

## Purpose
Prevent any project from stopping because a preferred builder, model, browser, media generator, deployment service, or automation provider runs out of credits/quota.

## Source of truth
- GitHub canonical repository = implementation truth.
- Notion Portfolio Master Control Room = product/business/verification truth.
- Tool/provider accounts are execution layers, never the canonical project state.

## Fallback rule
For every capability, maintain:
1. Primary provider/tool
2. Verified fallback provider/tool
3. Direct/local/free implementation path where technically possible
4. Human action blocker only when authorization/credential ownership is genuinely required

A provider failure, quota exhaustion, expired session, or unavailable connector must trigger fallback evaluation before asking the user to purchase credits or rebuild anything.

## Cost guard
- Months 0–6: free-first / zero-cost wherever technically possible.
- Do not spend credits merely to make a demo appear complete.
- Before paid generation, deployment, API calls, or subscriptions, verify necessity and available free/local alternatives.
- Never create duplicate applications just because a builder has no credits.

## Continuity rule
- Never replace the canonical GitHub project with a parallel builder project.
- Preserve existing backend, auth, data, security, evidence gates, and architecture unless a documented project decision explicitly changes them.
- A Builder is an execution surface; GitHub remains canonical.

## Evidence rule
NO EVIDENCE = NO SUCCESS.
A fallback is not considered active until its relevant output is verified.
Do not claim integration, publication, deployment, payment, outreach, media generation, or E2E success without fresh evidence.

## Failure routing
- Builder quota exhausted → continue through GitHub/direct implementation or another verified builder.
- AI/model quota exhausted → use verified free/local model or deterministic path.
- Browser quota/session failure → use another authorized browser path or direct API where contractually supported.
- Media generation quota exhausted → use verified free/local rendering path; never relabel static/fallback artifacts as canonical generated media.
- Deployment quota/provider unavailable → use an already-authorized compatible deployment path without changing architecture.
- Connector unavailable → continue read-only/direct/local where possible; stop only at a true credential/authorization gate.

## Seven canonical projects
IdeaCollector; RIZKAHA/FLOURISH; JARVIS/ENJY AI COO; ZA Media AI Growth Engine; ZE Outsourcing AI Ops; AI Short Drama/7mody; Scholarship AI Agent Team.

NileCare remains separate.

## Required reporting
Every execution report must state:
- primary tool/provider used
- fallback(s) available
- whether quota/cost was consumed
- verification evidence
- remaining blocker, if any
