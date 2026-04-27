# Spec Review Stage Map

This reference maps the general review protocol onto spec-workflow phases.

## Routing Model

Within spec-workflow, treat review in two layers:

1. source artifact
2. approval exchange layer

Default mapping:

- source artifact: `.spec-workflow/steering/*.md` or `.spec-workflow/specs/<name>/*.md`
- exchange layer: current approval record under `.spec-workflow/approvals/...`

Supplementary persistence, when needed:

- `ai-peer-review/<review-session-id>/<review-target-id>/review-state.md`
- `ai-peer-review/<review-session-id>/<review-target-id>/review-log.md`

Use supplementary files only for long-running review memory, not as a replacement for approval comments.

## Phase Map

### Steering

- source: `.spec-workflow/steering/product.md`, `tech.md`, `structure.md`
- exchange: approval `comments`
- focus:
  - product vs tech boundary
  - clean steering language
  - no review history in source files

### Requirements

- source: `.spec-workflow/specs/<name>/requirements.md`
- exchange: approval `comments`
- focus:
  - user stories
  - acceptance criteria
  - coverage of intended outcomes

### Design

- source: `.spec-workflow/specs/<name>/design.md`
- exchange: approval `comments`
- focus:
  - architecture clarity
  - codebase reuse
  - implementation feasibility
  - boundaries between design and tasks

### Tasks

- source: `.spec-workflow/specs/<name>/tasks.md`
- exchange: approval `comments`
- focus:
  - task atomicity
  - requirement references
  - file ownership
  - prompt completeness

### Implementation

- source:
  - code files
  - `.spec-workflow/specs/<name>/tasks.md`
  - `.spec-workflow/specs/<name>/Implementation Logs/`
- exchange:
  - approval comments if an approval phase exists
  - otherwise code review comments or a dedicated review file
- focus:
  - regressions
  - missing tests
  - behavior mismatch vs task/design
  - implementation log completeness

## Approval-State Guidance

Prefer live state from the host's approval-status interface.

Interpretation:

- `pending`: no approval outcome yet
- `needs-revision`: reviewer found blocking issues
- `approved`: passed this phase
- `mustWait: true`: do not move forward
- `blockNext: true`: workflow gate is still closed
- `canProceed: true`: safe to move to the next step

## How This Embeds Into Spec Workflow

Use the adapter as a thin overlay on top of the normal Spec workflow:

1. Spec workflow defines the phase gate and the official source artifact.
2. Approval comments carry the primary reviewer-drafter exchange.
3. The general review protocol defines how findings, rebuttals, and role boundaries work.
4. Supplementary review state files are optional support for long-running rounds or session recovery.

This means:

- Spec workflow remains the official process.
- Review protocol governs the quality of the exchange.
- Supplementary files preserve continuity when approval metadata alone is not enough.

## Snapshot Guidance

Snapshots are supporting context, not the authority for workflow state.

Use snapshots to:

- compare current content vs the submitted round
- recover prior wording
- inspect comments tied to older rounds

Do not create or manage snapshots manually unless the host tooling explicitly requires it.
