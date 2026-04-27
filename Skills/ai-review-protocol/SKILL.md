---
name: ai-review-protocol
description: Temporary AI peer-review exchange protocol.
user-invocable: true
allowed-tools: "Read Write Edit Bash Glob Grep"
metadata:
  version: "2.1.0"
---

## Invocation Contract

When this skill is invoked, do not output full review content in chat.

Complete this sequence:

```text
RESTORE -> ACT -> COMMIT -> CHECK -> STOP
```

A review answer is incomplete until it exists in `.ai-peer-review/rounds/round-N.md` and `commit-round` succeeds.

After commit and check, chat output must be limited to a brief handoff summary: committed round file, current role, next actor, finding IDs or counts, and any user-blocking question. Full findings, rebuttals, evidence, and detailed reasoning must remain in the round file.

# AI Review Protocol

Use this skill only for an active AI-to-AI review exchange. It has no automatic hooks.

For detailed finding and rebuttal rules, read [core rules](./references/core.md).

Resolve `<skill-root>` as the directory containing this `SKILL.md`. All helper scripts are under `<skill-root>/scripts/`; do not resolve them from the project root or any parent directory.

## Files

Use only these project-local files:

- `.ai-peer-review/review-state.md`
- `.ai-peer-review/review-log.md`
- `.ai-peer-review/rounds/round-N.md`

Do not use chat history as the exchange layer. Do not create session/target subdirectories, date-based round files, or role-labeled round files.

## First Action

Before inspecting or answering the review target:

IF `.ai-peer-review/review-state.md` exists:

- Read it.
- If `handoff_pending: true`, run `begin-turn`, then read state again.
- Read `current_round_file`.
- Read `.ai-peer-review/review-log.md`.

IF `.ai-peer-review/review-state.md` is missing:

- Run `init-review.sh`.
- Read the created state.

## Initialize

Initialize only when `.ai-peer-review/review-state.md` is missing:

```bash
sh <skill-root>/scripts/init-review.sh <target-id> <source-artifact> <Reviewer|Drafter>
```

## Required Sequence

RESTORE:

- Complete `First Action`.

ACT:

- Use exactly one role: `Reviewer` or `Drafter`.
- Write the next `.ai-peer-review/rounds/round-N.md`.

COMMIT:

- Run `commit-round`.
- A successful commit records a pending handoff but does not authorize same-response role switching.

CHECK:

- Run `check-review.sh .`.

STOP:

- Report only a brief handoff summary.
- Do not act as `next_actor` in the same response.

## Role Lock

- Follow `current_role`.
- `next_actor` is a future handoff target, not permission to continue as that role.
- Run `begin-turn` only at the start of a new user-invoked turn, never after your own commit in the same response.
- If the user explicitly changes your role in natural language, do not edit `review-state.md` by hand. Run `user-override-role` first.
- If role or target is unclear, stop and ask the user.

Begin-turn command:

```bash
python3 <skill-root>/scripts/review-flow.py begin-turn .
```

Role override command:

```bash
python3 <skill-root>/scripts/review-flow.py user-override-role . \
  --role Reviewer \
  --reason "user explicitly reassigned this turn to Reviewer"
```

## Round Commit

Reviewer:

Inspect only as `Reviewer`; do not edit the source artifact. Commit with:

```bash
python3 <skill-root>/scripts/review-flow.py commit-round . \
  --round-file .ai-peer-review/rounds/round-N.md \
  --acting-role Reviewer \
  --next-actor Drafter \
  --state responding
```

Then run `check-review.sh .` and stop.

Drafter:

Edit the source artifact only as needed. Write responses and remaining issues to the round file. Commit with:

```bash
python3 <skill-root>/scripts/review-flow.py commit-round . \
  --round-file .ai-peer-review/rounds/round-N.md \
  --acting-role Drafter \
  --next-actor Reviewer \
  --state resubmitted
```

Then run `check-review.sh .` and stop.

## Check

Run this when state may be stale or before handing off:

```bash
sh <skill-root>/scripts/check-review.sh .
```

The check reports missing or inconsistent files but does not block or clean up.

## State Values

Use only these `commit-round --state` values:

- `intake`
- `reviewing`
- `responding`
- `resubmitted`
- `blocked`
