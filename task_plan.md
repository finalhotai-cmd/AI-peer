# Task Plan: Harden AI Review Protocol

## Goal

Convert `Skills/ai-review-protocol` from a principle-heavy review protocol into a file-enforced peer-review skill with deterministic persistence, recovery, and role boundaries.

Scope is limited to the generic skill:

- `Skills/ai-review-protocol/SKILL.md`
- `Skills/ai-review-protocol/references/core.md`
- optional helper files under `Skills/ai-review-protocol/`

Out of scope for this round:

- `Skills/spec-review-adapter`
- framework-specific approval-state behavior
- changing project source artifacts outside the skill

## First Principles

- Chat memory is volatile and cannot be the exchange layer.
- Cross-agent peer review needs a fixed disk entrypoint.
- Weak models drift unless state, file paths, and role boundaries are re-injected at tool and stop boundaries.
- The generic review skill should not become a planning skill clone. It should borrow only the enforcement pattern: fixed files, fixed timing, hooks, and completion checks.
- Fewer moving parts are better: one state entrypoint, one log, sequential round files.

## Current Finding Summary

- Existing protocol says to persist state, but does not define one canonical state authority.
- Existing fallback wording lets agents treat chat or host context as sufficient exchange memory.
- Existing round naming permits drift such as `round-2-reviewer-response.md`.
- Existing role rules are advisory; reviewers can drift into drafting, and drafters can drift into approving.
- Existing protocol has no hook or stop verification equivalent to `planning-with-files`.

## Proposed Target Contract

Use these generic project-local files:

- `ai-peer-review/review-state.md`: canonical resume entrypoint.
- `ai-peer-review/review-log.md`: chronological action log.
- `ai-peer-review/rounds/round-N.md`: detailed round exchange.

`review-state.md` owns dynamic identity and routing:

- `session_id`
- `target_id`
- `source_artifact`
- `current_round`
- `current_round_file`
- `current_role`
- `next_actor`
- `state`
- `open_major_findings`
- `open_minor_findings`
- `role_switch_allowed`
- `updated_at`

## Phases

### Phase 1: Capture Discussion Context

Status: complete

Tasks:

- Record current diagnosis and constraints in `findings.md`.
- Record this implementation plan in `task_plan.md`.
- Record session activity in `progress.md`.

### Phase 2: Inspect Current Skill Shape

Status: complete

Tasks:

- Re-read `Skills/ai-review-protocol/SKILL.md`.
- Re-read `Skills/ai-review-protocol/references/core.md`.
- Identify sections to replace or compress instead of adding more prose.

### Phase 3: Design Minimal Enforcement Changes

Status: in_progress

Tasks:

- Define fixed file contract.
- Define restore order.
- Define reviewer write contract.
- Define drafter write contract.
- Define role lock.
- Define drift handling.
- Define stop verification behavior.

## Detailed Modification Plan

### 1. Frontmatter Hardening

Update `Skills/ai-review-protocol/SKILL.md` frontmatter to add:

- `user-invocable: true`
- `allowed-tools: "Read Write Edit Bash Glob Grep"`
- hooks modeled on `planning-with-files`, limited to review-state enforcement

Hook intent:

- `UserPromptSubmit`: if `ai-peer-review/review-state.md` exists, print the active review state, recent log, and current round file pointer.
- `PreToolUse`: before read/write/search tools, print only role-lock fields from `review-state.md`.
- `PostToolUse`: after writes, remind that round file, `review-state.md`, and `review-log.md` must be synchronized.
- `Stop`: run `scripts/check-review-complete.sh` if available.

Do not add planning semantics, phase planning, research capture, or task management hooks.

### 2. Replace Conditional Fallback With Fixed Local File Contract

Replace the current fallback wording with a mandatory generic contract:

- Chat history is never an exchange layer.
- For generic peer review, use project-local files under `ai-peer-review/`.
- `ai-peer-review/review-state.md` is the single canonical entrypoint.
- `ai-peer-review/review-log.md` is the chronological log.
- `ai-peer-review/rounds/round-N.md` is the detailed per-round exchange.

Remove or demote old nested examples:

- `ai-peer-review/<review-session-id>/<review-target-id>/...`
- `review.md`
- `review-notes/<round>.md`
- timestamp or role-labeled round names

Dynamic identifiers move into `review-state.md`.

### 3. Define Restore Order

Add a short required restore sequence:

1. Read `ai-peer-review/review-state.md` if it exists.
2. Read the `current_round_file` named inside it.
3. Read the tail of `ai-peer-review/review-log.md`.
4. Continue only if the role and target are clear.

Do not scan directories to guess the latest round except for drift diagnosis.

### 4. Define Write Contracts

Reviewer completion requires:

- write next `ai-peer-review/rounds/round-N.md`
- update `ai-peer-review/review-state.md`
- append `ai-peer-review/review-log.md`
- set `next_actor` to `Drafter` or `User`
- stop after final handoff

Drafter completion requires:

- apply accepted changes to the source artifact
- write next `ai-peer-review/rounds/round-N.md`
- update `ai-peer-review/review-state.md`
- append `ai-peer-review/review-log.md`
- set `state: resubmitted`
- set `next_actor: Reviewer`
- stop after final handoff

Writing only chat output or only a round file is incomplete.

### 5. Define Role Lock

Add one compact role-lock section:

- Current turn has exactly one role.
- `next_actor` is a future handoff target, not permission to continue.
- Reviewer must not edit `source_artifact`.
- Drafter must not approve its own work.
- Role switch requires explicit current-turn user instruction.
- `role_switch_allowed` defaults to `false`.

### 6. Define Drift Handling

Add one rule:

- If a newer or differently named round file exists but is not referenced by `review-state.md`, mark the exchange inconsistent and repair state/log before continuing.

No broad directory archaeology as normal workflow.

### 7. Add Minimal Check Script

Add `Skills/ai-review-protocol/scripts/check-review-complete.sh`.

Checks:

- if no `ai-peer-review/review-state.md` exists, exit quietly
- extract `current_round_file`
- verify the current round file exists
- verify current round file path matches `ai-peer-review/rounds/round-[0-9]+.md`
- verify `ai-peer-review/review-log.md` exists
- verify log mentions the current round file
- warn if role-lock fields are missing

This script should print actionable warnings only. It should not modify files.

### 8. Verification Plan

After patching:

- Search for conditional fallback phrases and old filename recommendations.
- Search for nested default path examples.
- Run the check script in a no-review-state project root; it should exit quietly.
- Create a temporary minimal `ai-peer-review/` fixture under `/tmp` and run the script against valid and invalid states.
- Confirm `Skills/spec-review-adapter` is untouched.

### Phase 4: Patch Generic Skill Only

Status: pending

Tasks:

- Update `Skills/ai-review-protocol/SKILL.md`.
- Update `Skills/ai-review-protocol/references/core.md`.
- Add a minimal check script only if the skill format supports it cleanly.
- Do not modify `Skills/spec-review-adapter`.

### Phase 5: Verify

Status: pending

Tasks:

- Check the resulting skill for contradictory fallback wording.
- Check that only one canonical entrypoint exists.
- Check that round naming cannot drift.
- Check that role switching requires explicit current-turn user instruction.
- Check that reviewer and drafter completion each require state/log synchronization.

## Acceptance Criteria

- A future agent can find the latest review round from `ai-peer-review/review-state.md` without scanning.
- A reviewer cannot correctly finish by writing only chat output or only a round file.
- A drafter cannot correctly finish without updating state and log.
- Role switching is treated as a hard boundary, not a suggestion.
- The protocol remains a peer-review skill, not a general planning workflow.
