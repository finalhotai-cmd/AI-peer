---
name: spec-review-adapter
description: Spec review mapping.
---

# Spec Review Adapter

Spec workflow mapping layer on top of `ai-review-protocol`.

Read [stage map](./references/stage-map.md) when you need phase detection, approval-state handling, or source/exchange file mapping.

## Live State Rule

- Use the host's live approval-status interface as the authority for current approval state when available.
- Read approval JSON files as the durable exchange layer.
- If live status output and file contents disagree, trust the live status interface for state and the file for stored comments.

## Context Load

1. Detect that the task is inside `.spec-workflow/`.
2. Call the host's approval-status interface for the current approval when possible.
3. Load the current approval JSON under `.spec-workflow/approvals/.../approval_*.json`.
4. Load the source document referenced by `filePath`.
5. If needed, load the latest snapshot under `.spec-workflow/approvals/.../.snapshots/...`.

## Exchange Mapping

- `approval title`: short round summary only
- `approval comments`: primary exchange layer for findings and rebuttals
- `approval annotations`: optional longer structured responses if supported
- source document under `.spec-workflow/steering/` or `.spec-workflow/specs/...`: final approved content only

If the review becomes long-running, cross-session, or extends beyond what approval metadata can hold cleanly, add companion persistence files under:

- `ai-peer-review/<review-session-id>/<review-target-id>/review-state.md`
- `ai-peer-review/<review-session-id>/<review-target-id>/review-log.md`

Do not use these files to replace approval comments. Use them only as supplementary review memory.

## Status Interpretation

- `pending`: review is waiting for a host workflow decision; do not treat it as approved
- `needs-revision`: blocking issues remain; update the source document and resubmit
- `approved`: content passed this phase, but do not proceed if cleanup/delete is still required by workflow
- `blockNext: true` or `mustWait: true`: do not advance the workflow
- `canProceed: true`: phase gate is open

Map review state to Spec workflow like this:

- `pending` => `reviewing`
- `needs-revision` => `responding`
- fresh resubmission awaiting review => `resubmitted`
- `approved` plus successful cleanup => `approved`
- unclear role / unclear phase / conflicting artifacts => `blocked`

## Spec-Specific Rules

- Do not place `Revision Notes`, acceptance tables, rebuttal essays, or round summaries inside `product.md`, `tech.md`, `structure.md`, `requirements.md`, `design.md`, or `tasks.md`.
- Keep stage-specific findings anchored to the source file and section being reviewed.
- Keep implementation review findings anchored to code, `tasks.md`, and implementation logs.

## Phase Detection

- `.spec-workflow/steering/*.md` => steering review
- `requirements.md` => requirements review
- `design.md` => design review
- `tasks.md` => task-planning review
- code + `tasks.md` + `Implementation Logs/` => implementation review

## When To Escalate To Stage Map

Load `references/stage-map.md` when:

- the current phase is unclear
- you need phase-specific review priorities
- a rebuttal depends on whether content belongs in product, design, tasks, or implementation
- the approval state fields need interpretation
