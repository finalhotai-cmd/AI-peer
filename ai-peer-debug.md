# AI Peer Review Debug Report

## Topic

Why the latest reviewer feedback was not discoverable through the expected exchange layer, and how to harden `ai-review-protocol` so the next reviewer/drafter pair cannot drift the state again.

## Event Summary

During the `session-handoff-v2-refactor / session-handoff-v1` peer-review loop, the reviewer created a new feedback artifact:

- `ai-peer-review/session-handoff-v2-refactor/session-handoff-v1/round-2-reviewer-response.md`

But the canonical exchange-state files were not updated:

- `ai-peer-review/session-handoff-v2-refactor/session-handoff-v1/review-state.md`
- `ai-peer-review/session-handoff-v2-refactor/session-handoff-v1/review-log.md`

As a result, the latest review round could not be reliably discovered by reading the state file alone. The latest feedback had to be found either by scanning the directory or by the user explicitly naming the file.

## Root Cause

The problem has two layers.

### 1. Immediate process failure

The reviewer did not fully persist the new review state after a material review action.

What happened:

- a new reviewer response file was written
- `review-state.md` was left stale
- `review-log.md` was left stale

This violated the intended meaning of the protocol rule:

- after each material review action, persist the new state in the exchange layer before moving on

### 2. Protocol design weakness

`ai-review-protocol` expresses persistence as a principle, but not as an unambiguous operational contract.

The skill currently says:

- treat the exchange layer as persistent working memory
- after each material review action, persist the new state

But it does **not** make these items explicit enough:

- which file is the canonical state authority
- which files must be updated on every round
- what the required recovery order is
- whether a new round file alone is sufficient persistence
- whether alternate filenames such as `round-2-reviewer-response.md` are allowed

Because of that ambiguity, a reviewer can believe:

- “I wrote a new file, so I persisted state”

even though the system as a whole can no longer recover the latest state reliably.

## Sequence Of Events

1. Reviewer wrote `round-1.md` with four major findings.
2. Drafter wrote `round-2.md`, `review-state.md`, and `review-log.md`.
3. Reviewer later wrote `round-2-reviewer-response.md` and kept one major finding open.
4. Reviewer did **not** update `review-state.md`.
5. Reviewer did **not** update `review-log.md`.
6. The canonical state still pointed to the older drafter round.
7. On resume, the latest reviewer position was not discoverable from the state file alone.
8. The user had to explicitly point to the latest reviewer file.

## Why This Matters

This is not just a naming nuisance. It breaks the core promise of the protocol:

- resumability
- clean role handoff
- no dependence on chat memory

Without a single discoverable state authority:

- the drafter may respond to an outdated round
- the reviewer may think a blocking issue remains while the state file says otherwise
- user intervention becomes necessary just to identify the latest round
- session recovery degrades into directory archaeology

## Conclusion

### Responsibility

The immediate protocol miss was on the reviewer side.

The reviewer created a material review artifact without updating the canonical exchange-state files.

### Structural cause

The skill design also contributed. `ai-review-protocol` is currently stronger as a principles document than as an execution protocol.

It does not yet have enough hard constraints to force:

- one canonical discovery path
- one canonical round progression
- one required set of files to update per round

So the answer is:

- **yes**, the reviewer missed the protocol in practice
- **yes**, the skill is under-specified in the places that matter for enforcement

## Recommended Fixes To `ai-review-protocol`

The protocol should be revised from “guidance” toward an explicit file-state contract.

### A. Define one canonical authority

Add a hard rule:

- `review-state.md` is the single canonical entrypoint for resuming a review

Everything else is subordinate:

- `round-*.md` stores detailed exchange content
- `review-log.md` stores chronological audit history
- `review-state.md` tells the next agent what the latest valid round is

### B. Make state updates mandatory, not implied

Add a hard rule:

- every material reviewer or drafter action MUST update:
  - the new round file
  - `review-state.md`
  - `review-log.md`

Writing only a new round file must be explicitly defined as insufficient.

### C. Make discovery fields mandatory in `review-state.md`

Require these fields at minimum:

- `session_id`
- `target_id`
- `current_role`
- `current_round`
- `current_round_file`
- `state`
- `open_major_findings`
- `open_minor_findings`
- `next_actor`
- `source_artifact_status`

This removes any need to guess which file is current.

### D. Freeze round naming

Add a hard rule:

- use exactly `round-1.md`, `round-2.md`, `round-3.md`, ...
- role labels belong inside the file body, not in the filename

Disallow parallel naming such as:

- `round-2-reviewer-response.md`
- `round-2-final.md`
- `round-2b.md`

unless a framework-specific adapter explicitly overrides this.

### E. Define recovery order explicitly

Add a required resume sequence:

1. Read `review-state.md`
2. Read the file named by `current_round_file`
3. Read `review-log.md`
4. Only then continue reviewing or responding

This prevents agents from scanning the directory and guessing the latest round.

### F. Bind the state machine to file writes

Today the state machine is conceptual. It should become operational.

Example:

- Reviewer ending a round MUST:
  - write `round-N.md`
  - set `state: reviewing` or `approved`
  - update `current_round_file`
  - record current open major/minor findings
  - append `review-log.md`

- Drafter ending a round MUST:
  - write `round-N.md`
  - set `state: resubmitted`
  - update `current_round_file`
  - record accepted / rejected / partial responses
  - append `review-log.md`

### G. Add a protocol violation rule

Add a new explicit rule:

- if an agent finds a newer round artifact than the one named in `review-state.md`, it must treat the exchange as inconsistent and record a protocol violation before continuing

That makes drift visible instead of silently tolerated.

## Proposed Edit Direction

The construction team should modify:

- `/Users/arkbo/.kiro/skills/ai-review-protocol/SKILL.md`
- `/Users/arkbo/.kiro/skills/ai-review-protocol/references/core.md`

Priority order:

1. make `review-state.md` the canonical resume entrypoint
2. require state/log updates after every material action
3. require `current_round_file` in the state record
4. freeze round naming
5. add explicit recovery order
6. add inconsistency-handling rule

## Suggested Acceptance Criteria For The Protocol Fix

The revised protocol is only complete if all of these are true:

1. A third-party agent can find the latest round without scanning the directory.
2. A reviewer cannot complete a round correctly without updating `review-state.md`.
3. A drafter cannot complete a round correctly without updating `review-state.md`.
4. Mixed naming like `round-2-reviewer-response.md` is either forbidden or explicitly normalized by the protocol.
5. Resume behavior is deterministic and identical across sessions.

## Handoff Note For Implementer

Do not solve this by adding more prose alone.

The fix must convert the protocol from:

- “persist state somewhere in the exchange layer”

to:

- “update these exact state artifacts in this exact order”

That is the minimum change needed to restore recoverability and prevent the same drift in future peer-review rounds.
