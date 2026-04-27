# AI Review Protocol Core

## Purpose

This file defines review-content semantics only.

Operational state, file paths, helper commands, and handoff mechanics are defined by `SKILL.md` and scripts.

## Round File Shape

Use this recommended structure for each round file:

```markdown
# Round N

## Role
Reviewer|Drafter

## Summary
Short delta for this round.

## Findings
Reviewer findings, if acting as Reviewer.

## Responses
Drafter responses, if acting as Drafter.

## Open Questions
Only blockers that require user clarification.

## Handoff
Next actor and reason.
```

This is a content convention, not a script-validated schema.

## Reviewer Findings

`Reviewer` inspects the source artifact and writes findings. It does not edit the source artifact.

Use one object per finding:

```json
{
  "id": "comment_example",
  "section": "Section Name",
  "severity": "major",
  "comment": "Explain the problem, why it matters, and the required change."
}
```

Finding rules:

- Review the current source artifact and unresolved findings.
- Write only new, still-open, or newly-resolved findings for this round.
- Make each finding locatable, actionable, and evidence-backed.
- Use `major` for issues that block acceptance or safe continuation.
- Use `minor` for useful tightening that does not block continuation.
- Do not create findings only to appear adversarial.

## Drafter Responses

`Drafter` edits the source artifact when needed and answers findings. It does not approve its own work.

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

Response rules:

- Answer every open `major` finding.
- Bind each response to a finding id.
- For `accepted`, state what changed.
- For `partial`, state the accepted part, rejected part, and replacement boundary.
- For `rejected`, provide technical or logical evidence and an alternative.
- If a finding remains open, say why.

## Review Discipline

- Keep the source artifact publication-ready and free of review history.
- Keep round summaries short; put detailed argument in findings or responses.
- Accept a point only because the artifact, logic, or workflow improves.
- Reject a point only because evidence, scope, or constraints justify rejection.
- Do not defer to the other AI's confidence.
- Do not agree just to be agreeable.
- Do not invent weak objections to avoid full agreement.
- If accepting all opposing points, perform one independent pass and state that no defensible objection remains.
- If target artifact, edited artifact, findings, or role diverge, stop and ask the user.
