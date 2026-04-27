# AI Review Protocol Core

## Purpose

This protocol defines the stable review language shared across frameworks.

It answers:

- how review dialogue is separated from source artifacts
- how reviewer findings are shaped
- how drafters respond
- how to distinguish blocking vs non-blocking issues
- how role ambiguity is handled
- how adversarial review stays rigorous instead of flattering or performative
- how review state persists across rounds

It does not answer framework-specific routing questions. Those belong in adapter skills.

## Exchange Layer Concept

Every review workflow has two layers:

1. `source artifact`
   The document, code, task list, or deliverable that should remain clean.

2. `exchange layer`
   The record where findings, rebuttals, round summaries, and status discussion live.

Examples of exchange layers:

- structured review comments in a host workflow
- code review comments
- a dedicated review markdown file
- a structured JSON review record

Treat the exchange layer as persistent working memory. If the conversation context drops, the exchange layer is the authority for what happened, what remains disputed, and what state the review is in.

## Persistence Rules

- Important review state must live on disk or in the host exchange system.
- Do not rely on chat memory alone for open findings, rebuttals, or round outcome.
- After material review actions, update the exchange layer before moving on.
- When resuming after a break, read the latest exchange state before acting.

## Review State Record

At minimum, the exchange layer should preserve:

- target artifact
- current role
- current round id
- open major findings
- open minor findings
- drafter responses
- current outcome state

## Role Ambiguity Rule

If the acting AI cannot determine whether it is the `Reviewer` or the `Drafter`, and the user has not explicitly assigned the role, it must stop and ask the user before acting.

Do not resolve role ambiguity by guessing from weak context.

## Anti-Flattery Rule

The other AI is a peer in an adversarial review loop, not the user.

- Do not agree just to be agreeable.
- Do not soften valid criticism to preserve harmony.
- Do not reject points just to appear independent.
- Do not search for trivial issues merely to produce findings.

Every finding must be grounded in text, structure, logic, behavior, or workflow rules.

Every rebuttal must be grounded in the same way.

The standard is: a reasonable third party should be able to inspect the artifact and follow the argument without needing social context.

## Evidence Standard

Use comments that can answer:

1. What is the issue?
2. What evidence supports the claim?
3. Why does it matter?
4. What change would resolve it?

Avoid:

- vague approval language
- performative disagreement
- authority-based claims without reasoning
- “feels wrong” comments with no concrete basis

## Full-Acceptance Check

If an agent is about to accept all opposing points with no objections, it must first perform one independent re-check.

The purpose of this re-check is to catch avoidable sycophancy, not to force disagreement.

If the re-check finds no defensible objection, full acceptance is valid.

Do not create artificial pushback merely to avoid a complete acceptance outcome.

## Topic-Mismatch Rule

Stop and ask the user to clarify when any of these diverge:

- the target artifact under review
- the artifact being edited
- the subject of the current findings
- the current workflow phase

Examples:

- reviewing `product.md` but arguing about `tech.md` implementation details
- acting as reviewer while editing the source artifact
- replying to findings from an older round while a different round is active

## Artifact-Type Review Discipline

Do not review only by instinct. Review according to artifact type.

### Document artifacts

Check:

- scope and boundary clarity
- internal consistency
- verifiability of goals, claims, and metrics
- layer correctness, such as product vs tech vs structure

### Task artifacts

Check:

- task atomicity
- dependency clarity
- traceability to requirements or design
- execution completeness

### Code artifacts

Check:

- logic defects
- boundary conditions
- security controls where relevant
- concurrency or async risk where relevant
- coupling and maintainability

## Dedicated Review Artifact Default

When no host exchange layer exists, create a dedicated Markdown artifact at:

`ai-peer-review/<review-session-id>/<review-target-id>/round-<round-id>.md`

Where:

- `review-session-id` is the current review conversation container, regardless of host product terminology
- `review-target-id` is a stable identifier such as `product-md` or `design-auth-flow`
- `round-id` is a sortable round marker such as `rev1`, `20260330T013500Z`, or `rev3-reviewer`

Recommended sections:

1. `# Review Exchange`
2. `## Target`
3. `## Round Summary`
4. `## Findings`
5. `## Drafter Responses`
6. `## Outcome`

For multi-round or session-spanning reviews, also maintain:

- `ai-peer-review/<review-session-id>/<review-target-id>/review-state.md`
- `ai-peer-review/<review-session-id>/<review-target-id>/review-log.md`

Recommended purpose:

- `review-state.md`: current role, current round, open issues, current state-machine status
- `review-log.md`: chronological log of review actions and decisions

## Finding Schema

Minimum shape:

```json
{
  "id": "comment_example",
  "section": "Section Name",
  "severity": "major",
  "comment": "Explain the problem, why it matters, and the required change."
}
```

Field guidance:

- `id`: stable identifier for later rebuttal or traceability
- `section`: target section or process area
- `severity`: `major` or `minor`
- `comment`: one concise paragraph, not a fragment

## Rebuttal Schema

Recommended shape:

```json
{
  "commentId": "comment_example",
  "status": "partial",
  "reason": "The original finding correctly rejects vendor-specific wording, but the source document still needs a product-level transparency requirement.",
  "resolution": "Keep generic transparency language in the source artifact and move named vendors to the framework-specific technical artifact."
}
```

Allowed `status` values:

- `accepted`
- `partial`
- `rejected`

## Approval Heuristic

Use a blocking outcome when:

- any `major` finding remains unresolved
- the source artifact still contains review history
- the artifact is not yet publication-ready

Approval is reasonable when:

- all `major` findings are resolved
- only `minor` tightening remains
- the source artifact is clean

## Dedicated Review File Fallback

If no native exchange layer exists, create a dedicated review file.

Recommended filenames:

- `review.md`
- `review-notes/<round>.md`
- `ai-peer-review/<review-session-id>/<review-target-id>/round-<timestamp>.md`

The dedicated review file may contain:

- round summary
- structured findings
- drafter rebuttals
- acceptance status

The dedicated review file must not replace the source artifact.

## Review Session Identifier

`review-session-id` is a host-agnostic name for the current review conversation container.

It may map to:

- a conversation id
- a chat id
- a review run id
- a convention/session name
- a generated local session id when the host provides nothing stable

Do not assume any specific IDE term. Use the host's nearest stable conversation identifier, or generate one locally.

## Review State Machine

Use this minimal lifecycle:

1. `intake`
2. `reviewing`
3. `responding`
4. `resubmitted`
5. `approved`
6. `blocked`

Interpretation:

- `intake`: role or target is being established
- `reviewing`: reviewer is generating or updating findings
- `responding`: drafter is applying changes and writing responses
- `resubmitted`: updated source artifact is ready for the next pass
- `approved`: no blocking issues remain
- `blocked`: user clarification is required

The goal is not ceremony. The goal is to prevent lost context, silent role drift, and accidental phase confusion.
