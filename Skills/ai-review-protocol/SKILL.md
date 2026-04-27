---
name: ai-review-protocol
description: Review exchange protocol.
---

# AI Review Protocol

Framework-agnostic review protocol. It does not know about Spec MCP or any other host workflow.

Read [core rules](./references/core.md) when you need the full field schema, rebuttal format, or decision heuristics.

## What This Skill Decides

- how to separate source documents from review dialogue
- what a reviewer writes
- what a drafter writes back
- how blocking and non-blocking findings are expressed
- how rebuttals and partial acceptance are recorded
- how review state is persisted across rounds and session gaps

## What This Skill Does Not Decide

- where a project stores its source files
- what tool or workflow owns review state
- which file or record is the exchange layer for a specific framework

Use a framework-specific adapter for those mappings when needed.

## Roles

- `Reviewer`: inspects the current artifact, writes findings, and decides whether blocking issues remain.
- `Drafter`: edits the source artifact and answers findings without polluting the source artifact with review history.

If your role is clear, infer it from the task:

- if asked to critique, inspect, or approve, act as `Reviewer`
- if asked to revise, rewrite, or resubmit, act as `Drafter`

If your role is not clear and the user did not explicitly assign one, stop and ask the user before taking action. Do not guess.

## Core Rules

- Keep the source artifact publication-ready at every round.
- Keep review dialogue out of the source artifact.
- Treat the exchange layer as persistent working memory on disk, not as optional chat residue.
- Put each finding in a separate structured comment object.
- Make every finding actionable: problem, why it matters, what must change.
- Allow disagreement, but keep rebuttals in the exchange layer, not in the source artifact.
- Keep round summaries short and separate from detailed findings.
- Do not flatter, appease, or defer to the other side just to keep the exchange smooth.
- Do not invent objections just to appear rigorous or adversarial.
- Every finding and every rebuttal must be technically or logically grounded and able to survive scrutiny.
- If you are about to accept all opposing points, perform one independent self-check first. If no reasonable disagreement remains, full acceptance is allowed. Do not manufacture disagreement just to avoid a 100% acceptance rate.
- If the review target, the feedback, and the requested action do not point to the same artifact or phase, stop and ask the user to clarify before continuing.
- Review systematically by artifact type instead of relying on intuition alone.
- After each material review action, persist the new state in the exchange layer before moving on.
- When resuming after a gap, reconstruct state from the exchange layer before making new findings or edits.

## Required Finding Shape

Use one object per finding with these fields:

- `id`
- `section`
- `severity`
- `comment`

Recommended values:

- `severity: major` for blocking issues
- `severity: minor` for tightening, polish, or non-blocking clarity

Example:

```json
{
  "id": "comment_metric_baseline",
  "section": "Success Metrics",
  "severity": "major",
  "comment": "The metric cannot be validated because the baseline workflow and measurement rule are undefined. Specify the baseline process, sampling window, and whether the statistic uses average or median."
}
```

## Reviewer Workflow

1. Read the latest source artifact and current exchange record.
2. Check whether prior blocking findings were resolved.
3. Write only delta findings for the current round.
4. Mark clearly whether remaining issues are blocking or non-blocking.
5. Do not rewrite the source artifact unless explicitly asked to switch roles.
6. Persist round outcome before ending the turn.

## Drafter Workflow

1. Read all current findings before editing.
2. Apply accepted changes directly in the source artifact.
3. Record disagreement, partial acceptance, or alternative proposals in the exchange layer.
4. Resubmit a clean source artifact with no review history embedded in it.
5. Persist what changed, what remains open, and what was intentionally rejected.

## Review State Machine

Use this minimal state machine:

- `intake`: identify target artifact, role, and exchange layer
- `reviewing`: reviewer inspects and records findings
- `responding`: drafter applies changes and records responses
- `resubmitted`: clean source artifact plus updated exchange layer are ready for the next review
- `approved`: no blocking findings remain
- `blocked`: role, topic, or workflow state is unclear; ask the user

Allowed transitions:

- `intake -> reviewing`
- `intake -> responding`
- `reviewing -> blocked`
- `reviewing -> responding`
- `reviewing -> approved`
- `responding -> blocked`
- `responding -> resubmitted`
- `resubmitted -> reviewing`

Do not skip from ambiguous intake directly to editing or approval.

## Rebuttal Rules

- Rebuttals are allowed.
- Rebuttals must answer a specific finding.
- Rebuttals must state whether the finding is accepted, partial, or rejected.
- Rebuttals must propose the replacement wording or boundary when rejecting a finding.
- Rebuttals do not belong in the source artifact.
- Rebuttals must address substance, not tone or authority.

## Round Summary Rules

- Keep summaries short.
- Use summaries for what changed this round, not for extended argument.
- Put detailed argument in the exchange layer.

## Fallback Rule

If the host workflow does not define where review dialogue goes, create a dedicated review artifact and keep the source artifact clean.

Default fallback artifact:

- path: `ai-peer-review/<review-session-id>/<review-target-id>/round-<round-id>.md`
- format: Markdown
- purpose: round summary, structured findings, drafter rebuttals, and outcome state

Default companion state files when the review is long-running or spans multiple sessions:

- `ai-peer-review/<review-session-id>/<review-target-id>/review-state.md`
- `ai-peer-review/<review-session-id>/<review-target-id>/review-log.md`

Use them only when the host workflow does not already provide equivalent persistence.
