# Task Plan: Harden AI Review Protocol

## Goal

Convert `Skills/ai-review-protocol` from a principle-heavy review protocol into a file-enforced peer-review skill with deterministic temporary coordination, recovery, and role boundaries.

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
- Cross-agent peer review needs a fixed disk entrypoint while the review is active.
- AI peer review files are temporary coordination files, not the durable project memory.
- Durable conclusions, decisions, and follow-up work are outside this skill's responsibility.
- Weak models drift unless state, file paths, and role boundaries are made explicit in the review files and commit/check scripts.
- The generic review skill should not depend on any other skill. It should borrow only the engineering pattern: fixed files, fixed timing, small scripts, and completion checks.
- Fewer moving parts are better: one temporary workspace, one state entrypoint, one log, sequential round files.
- Use project-local files and simple scripts. Avoid automatic hooks and avoid turning v1 into a transaction system.

## Current Finding Summary

- Existing protocol says to persist state, but does not define one canonical state authority.
- Existing fallback wording lets agents treat chat or host context as sufficient exchange memory.
- Existing round naming permits drift such as `round-2-reviewer-response.md`.
- Existing role rules are advisory; reviewers can drift into drafting, and drafters can drift into approving.
- Existing protocol has no script-level verification for review-state consistency.

## Proposed Target Contract

Supersedes the earlier thread/session registry idea.

Use one temporary project-local workspace:

- `.ai-peer-review/review-state.md`: canonical active review state.
- `.ai-peer-review/review-log.md`: chronological temporary exchange log.
- `.ai-peer-review/rounds/round-N.md`: detailed temporary round exchange.

`review-state.md` owns dynamic identity and routing:

- `target_id`
- `source_artifact`
- `current_round`
- `current_round_file`
- `current_role`
- `next_actor`
- `handoff_pending`
- `state`
- `open_major_findings`
- `open_minor_findings`
- `role_switch_allowed`
- `updated_at`

## Final Implemented Contract

Status: implemented and reviewed

The final v1 implementation is intentionally smaller than several intermediate plans.

Implemented:

- `Skills/ai-review-protocol/SKILL.md` is hook-free and user-invoked only.
- `Skills/ai-review-protocol/SKILL.md` declares `metadata.version: "2.0.0"` for the major protocol rewrite.
- `Skills/ai-review-protocol/references/core.md` contains the compact protocol rules.
- `Skills/ai-review-protocol/scripts/init-review.sh` initializes `.ai-peer-review/`.
- `Skills/ai-review-protocol/scripts/check-review.sh` reports consistency warnings and always exits 0.
- `Skills/ai-review-protocol/scripts/review-flow.py` implements `commit-round`, `begin-turn`, and `user-override-role`.
- Helper scripts are referenced as `<skill-root>/scripts/...`, where `<skill-root>` is the directory containing `SKILL.md`.
- Runtime review files stay in the project-local `.ai-peer-review/` directory.
- Round files must be sequential `.ai-peer-review/rounds/round-N.md`, with `N >= 1`.
- `commit-round` rejects skipped, duplicate, stale, or wrongly named rounds.
- `commit-round` sets `handoff_pending: true` and prints a direct stop instruction.
- `begin-turn` is only for the start of a new user-invoked turn.
- `user-override-role` handles explicit natural-language user role reassignment without hand-editing state.

Not implemented by design:

- automatic hooks
- chat/session history recovery
- active pointer registry
- thread/session routing
- copying helpers into `.ai-peer-review/bin/`
- source artifact hashing
- closed/finish/approved terminal states
- automatic cleanup
- dependency on any other skill

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

Status: complete

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

Do not add automatic hooks. This skill should only enter context when invoked.

### 2. Replace Conditional Fallback With Fixed Local File Contract

Replace the current fallback wording with a mandatory generic contract:

- Chat history is never an exchange layer.
- For generic peer review, use project-local files under `.ai-peer-review/`.
- `.ai-peer-review/review-state.md` is the canonical temporary state.
- `.ai-peer-review/review-log.md` is the chronological temporary log.
- `.ai-peer-review/rounds/round-N.md` is the detailed per-round exchange.

Remove or demote old nested examples:

- `ai-peer-review/<review-session-id>/<review-target-id>/...`
- `review.md`
- `review-notes/<round>.md`
- timestamp or role-labeled round names

Dynamic identifiers move into `review-state.md`.

### 3. Define Restore Order

Add a short required restore sequence:

1. Read `.ai-peer-review/review-state.md` if it exists.
2. Read the `current_round_file` named inside it.
3. Read the tail of `.ai-peer-review/review-log.md`.
4. Continue only if the role and target are clear.

Do not scan directories to guess the latest round or target except for drift diagnosis.

### 4. Define Write Contracts

Reviewer completion requires:

- write next `.ai-peer-review/rounds/round-N.md`
- run `review-flow.py commit-round` to update `review-state.md` and append `review-log.md`
- set `next_actor` to `Drafter` or `User`
- do not continue as the next role in the same response

Drafter completion requires:

- apply accepted changes to the source artifact
- write next `.ai-peer-review/rounds/round-N.md`
- run `review-flow.py commit-round` to update `review-state.md` and append `review-log.md`
- set `state: resubmitted`
- set `next_actor: Reviewer`
- do not continue as Reviewer in the same response

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

### 7. Add Minimal Scripts

Add:

- `Skills/ai-review-protocol/scripts/init-review.sh`
- `Skills/ai-review-protocol/scripts/check-review.sh`
- `Skills/ai-review-protocol/scripts/review-flow.py`

Purpose:

- initialize the fixed directory and state/log files when required values are supplied
- commit a completed round by mechanically updating state and log
- validate state/log/round consistency on demand
- avoid AI directory guessing and reduce token load

Commands:

- `sh scripts/init-review.sh <target-id> <source-artifact> <Reviewer|Drafter>`: create fixed files if absent.
- `python3 scripts/review-flow.py commit-round --round-file ... --acting-role ... --next-actor ... --state ...`: update state/log after round content exists.
- `sh scripts/check-review.sh [project-root]`: consistency check and warnings.

Checks:

- if no active `review-state.md` exists, exit 0 with a short message
- extract `current_round_file`
- verify the current round file exists
- verify current round file path matches `.ai-peer-review/rounds/round-[1-9][0-9]*.md`
- verify `review-log.md` exists
- verify log mentions the current round file
- warn if role-lock fields are missing

`check-review.sh` should not modify files and should always exit 0. `init-review.sh` may create missing files only. `commit-round` may update state/log only after the round file exists and passes validation.

Write-path constraints:

- `commit-round` is the normal writer of `review-state.md` and `review-log.md`.
- AI writes round content, not state/log mechanics.
- The next round path is the next sequential `.ai-peer-review/rounds/round-N.md`, but v1 does not need a separate reservation protocol.
- `commit-round` derives round number from the filename.
- Reviewer commits should warn if the round metadata implies a role switch. Source-artifact hash enforcement is deferred until there is an observed need.

## Simplified V1 Baseline

V1 should stay intentionally small.

Keep:

- project-local review files under `.ai-peer-review/`
- `init-review.sh`
- `review-flow.py commit-round`
- `check-review.sh`
- on-demand consistency checks

Do not include in v1:

- active pointer registry
- per-thread session routing
- transaction locks
- round reservation protocol
- source artifact hash enforcement
- automatic target discovery
- Markdown frontmatter as required metadata
- automatic same-turn role switching
- complex multi-session routing

The v1 write flow:

1. `init` creates the session files.
2. the agent reads `.ai-peer-review/review-state.md` and `.ai-peer-review/review-log.md`.
3. AI writes `round-N.md`.
4. `commit-round` updates `review-state.md` and `review-log.md`.
5. The loop may continue indefinitely until the user stops it or asks for a durable summary.

## Temporary Workspace Correction

The previous plan over-modeled review files as durable records. That was wrong for this skill.

First-principles split:

- `ai-review-protocol` is a temporary peer-review workbench.
- The review workbench exists only while agents are exchanging findings and responses.
- When the user decides the review is useful enough to keep, durable recording is handled outside this skill.
- The temporary `.ai-peer-review/` directory can then be deleted.

Resulting simplification:

- No thread registry.
- No active pointer.
- No multi-session routing in v1.
- No permanent review archive requirement.
- If `.ai-peer-review/` already exists, the agent reads it and continues from the explicit file state instead of guessing whether it is stale.

Stale-file handling:

- The script must not infer whether an existing `.ai-peer-review/` belongs to an old or new discussion.
- The script must not block normal continuation only because files already exist.
- Cleanup is a user decision, not an automatic protocol responsibility.
- There is no `closed` marker in v1. Stopping, summarizing, reusing, or deleting is user-owned.

### 8. Verification Plan

After patching:

- Search for conditional fallback phrases and old filename recommendations.
- Search for nested default path examples.
- Run the check script in a no-review-state project root; it should exit quietly.
- Create a temporary minimal `.ai-peer-review/` fixture under `/tmp` and run the script against valid and invalid states.
- Confirm `Skills/spec-review-adapter` is untouched.

### Phase 4: Patch Generic Skill Only

Status: complete

Tasks:

- Update `Skills/ai-review-protocol/SKILL.md`.
- Update `Skills/ai-review-protocol/references/core.md`.
- Add `init-review.sh`, `check-review.sh`, and `review-flow.py`.
- Do not modify `Skills/spec-review-adapter`.

### Phase 5: Verify

Status: complete

Tasks:

- Check the resulting skill for contradictory fallback wording.
- Check that only one canonical entrypoint exists.
- Check that round naming cannot drift.
- Check that role switching requires explicit current-turn user instruction.
- Check that reviewer and drafter completion each require state/log synchronization.
- Re-run code review after P0/P1 fixes and non-blocking fixes.
- Verify no repo-root script path assumptions remain under `Skills/ai-review-protocol`.
- Verify `round-0.md` is rejected by `check-review.sh` warning logic.

## Acceptance Criteria

- A future agent can find the latest temporary review round from `.ai-peer-review/review-state.md` without scanning.
- A reviewer cannot correctly complete a round by writing only chat output or only a round file.
- A drafter cannot correctly complete a round without updating state and log.
- Role switching is treated as a handoff boundary: `commit-round` sets `handoff_pending`, tells the current AI to stop, and the next user-invoked turn runs `begin-turn`.
- The protocol remains a peer-review skill, not a general planning workflow.
- Durable outcomes are outside this skill's protocol; `.ai-peer-review/` is not a permanent archive.
