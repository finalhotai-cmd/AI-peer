# AI Review Protocol Core

## Purpose

This protocol keeps review dialogue out of the source artifact while preserving enough temporary state for the next AI to continue the exchange.

It does not own project routing, durable records, cleanup, or final stopping decisions.

## Temporary Exchange Layer

Generic reviews use only:

```text
.ai-peer-review/
  review-state.md
  review-log.md
  rounds/
    round-1.md
    round-2.md
```

`review-state.md` should preserve:

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

Round files must be `.ai-peer-review/rounds/round-N.md`. Do not use nested session directories, date-based filenames, or role-labeled filenames.

## Role Rules

- `Reviewer` inspects and writes findings; it does not edit the source artifact.
- `Drafter` edits the source artifact and answers findings; it does not approve its own work.
- If role or target is unclear, stop and ask the user.
- `next_actor` is only the next handoff target. It never authorizes same-response role switching.
- After a successful round commit, `handoff_pending` blocks another commit until `begin-turn` promotes `next_actor`.
- `begin-turn` is only for the start of a new user-invoked turn, not for the same response that created the handoff.
- If the user explicitly reassigns the role, record it with `user-override-role`; do not hand-edit role fields in `review-state.md`.

## Finding Shape

Use one object per finding:

```json
{
  "id": "comment_example",
  "section": "Section Name",
  "severity": "major",
  "comment": "Explain the problem, why it matters, and the required change."
}
```

Use `major` for blocking issues and `minor` for non-blocking tightening.

## Rebuttal Shape

Answer findings directly:

```json
{
  "commentId": "comment_example",
  "status": "partial",
  "reason": "What is accepted, disputed, or constrained.",
  "resolution": "What changed or what alternative is proposed."
}
```

Allowed `status` values: `accepted`, `partial`, `rejected`.

## Review Discipline

- Keep the source artifact publication-ready and free of review history.
- Make findings actionable: issue, evidence, impact, required change.
- Keep round summaries short; put detailed argument in findings or rebuttals.
- Do not agree just to be agreeable.
- Do not invent objections just to appear rigorous.
- If accepting all opposing points, perform one independent self-check first.
- If target artifact, edited artifact, findings, or role diverge, stop and ask the user.

## States

Use only:

- `intake`
- `reviewing`
- `responding`
- `resubmitted`
- `blocked`

No terminal state is defined by this protocol. The loop continues until the user stops it or asks for external handling.
