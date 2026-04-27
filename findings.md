# Findings: AI Review Protocol Hardening

## Inputs Considered

- `Skills/ai-review-protocol/SKILL.md`
- `Skills/ai-review-protocol/references/core.md`
- `ai-peer-debug.md`
- `/Users/arkbo/.gemini/antigravity/brain/ff47acb9-ea9e-495c-9f03-ca044a2bb9f2/artifacts/analysis_results.md.resolved`
- `planning-with-files` skill pattern supplied by user

## Problem Diagnosis

The current `ai-review-protocol` fails in two ways:

1. Some agents do not write review files at all.
2. Some agents write a review file but do not update the state files needed for the next agent to locate it.

The root cause is not lack of prose. The root cause is lack of a hard execution contract.

## Specific Weaknesses

- "Exchange layer" is abstract and can be misread as chat context.
- Dedicated review files are framed as fallback or conditional.
- `review-state.md` is not defined as the single resume entrypoint.
- `round-id` is too flexible and permits names such as `round-2-reviewer-response.md`.
- Companion state files are optional in wording.
- Role separation is advisory rather than enforced by state and completion checks.
- There are no hooks that re-inject the current role, current round file, or required write contract.
- There is no stop-time consistency check.

## Useful Pattern From Planning With Files

Only these ideas should be borrowed:

- Fixed project-local files.
- Fixed file responsibilities.
- Restore context before acting.
- Re-inject state before tool use.
- Remind after writes to update companion files.
- Stop-time completion check.

Ideas not to copy:

- General planning phases.
- Research capture behavior.
- Broad task management semantics.
- Additional index files unless strictly necessary.

## Minimal Review-Specific File Model

- `ai-peer-review/review-state.md`: canonical state and routing entrypoint.
- `ai-peer-review/review-log.md`: chronological audit trail.
- `ai-peer-review/rounds/round-N.md`: detailed findings, rebuttals, and outcome for one round.

The dynamic review identity should live inside `review-state.md`, not in variable directory names.

## Role Boundary Finding

Weak agents often continue from reviewer into drafter because coding agents are biased toward fixing. This should be blocked through:

- `current_role`
- `next_actor`
- `role_switch_allowed: false`
- stop checks that reject reviewer edits to `source_artifact`

`next_actor` must be defined as a handoff target, not permission for the current agent to continue.

## Proposed Enforcement Hooks

The generic skill should add hooks similar in shape to `planning-with-files`:

- On user prompt: print current review state and recent review log if present.
- Before tools: print role lock and current round file.
- After writes: remind that round, state, and log must be synchronized.
- On stop: run a small consistency checker.

## Open Design Choice

Whether to preserve the old nested path:

`ai-peer-review/<review-session-id>/<review-target-id>/...`

or replace it with fixed root paths:

`ai-peer-review/review-state.md`

Recommendation: use fixed root paths for the generic skill. Store `session_id` and `target_id` as fields. This removes path drift with the fewest moving parts.

