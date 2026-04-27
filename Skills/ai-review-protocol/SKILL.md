---
name: ai-review-protocol
description: Temporary AI peer-review exchange protocol.
user-invocable: true
allowed-tools: "Read Write Edit Bash Glob Grep"
metadata:
  version: "2.0.0"
---

# AI Review Protocol

Use this skill only for an active AI-to-AI review exchange. It has no automatic hooks.

The exchange is temporary. It coordinates rounds in `.ai-peer-review/`; it does not decide when to stop, summarize, archive, or delete that directory.

For detailed finding and rebuttal rules, read [core rules](./references/core.md).

Resolve `<skill-root>` as the directory containing this `SKILL.md`. All helper scripts are under `<skill-root>/scripts/`; do not resolve them from the project root or any parent directory.

## Files

Use only these project-local files:

- `.ai-peer-review/review-state.md`
- `.ai-peer-review/review-log.md`
- `.ai-peer-review/rounds/round-N.md`

Do not use chat history as the exchange layer. Do not create session/target subdirectories, date-based round files, or role-labeled round files.

## Mandatory Lifecycle

Every active review turn MUST follow this order:

1. Restore
   - If `.ai-peer-review/review-state.md` exists, read it.
   - If `handoff_pending: true` at the start of a user-invoked turn, run `review-flow.py begin-turn .`, then read state again.
   - Then read its `current_round_file` and `.ai-peer-review/review-log.md`.
   - If it does not exist, run `init-review.sh`.

2. Act
   - Use exactly one role: `Reviewer` or `Drafter`.
   - Write the next `.ai-peer-review/rounds/round-N.md`.

3. Commit
   - After writing `round-N.md`, run `review-flow.py commit-round`.
   - A round is incomplete until `commit-round` succeeds.
   - A successful commit records a pending handoff but does not authorize same-response role switching.

4. Check And Handoff
   - Run `check-review.sh .`.
   - Stop after reporting the round file and next actor.
   - Your task for this role is complete.
   - Do not act as `next_actor` in the same response.

## Initialize

If `.ai-peer-review/review-state.md` does not exist, initialize:

```bash
sh <skill-root>/scripts/init-review.sh <target-id> <source-artifact> <Reviewer|Drafter>
```

If it exists, read it first, then read its `current_round_file` and `.ai-peer-review/review-log.md`.

## Role Lock

- Current turn has exactly one role: `Reviewer` or `Drafter`.
- If `current_role` exists in `review-state.md`, follow it.
- `next_actor` is a future handoff target, not permission to continue as that role.
- `handoff_pending: true` after your own commit means your task is complete. Stop.
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

## Reviewer Round

Inspect only as `Reviewer`; do not edit the source artifact. Commit with:

```bash
python3 <skill-root>/scripts/review-flow.py commit-round . \
  --round-file .ai-peer-review/rounds/round-N.md \
  --acting-role Reviewer \
  --next-actor Drafter \
  --state responding
```

Then run `check-review.sh .` and stop.

## Drafter Round

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
