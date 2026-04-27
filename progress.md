# Progress: AI Review Protocol Hardening

## 2026-04-27

- Created `task_plan.md`, `findings.md`, and `progress.md` in the project root per `planning-with-files`.
- Captured current discussion findings about `ai-review-protocol` persistence drift, role drift, and hook-based enforcement.
- Scoped the plan to the generic `Skills/ai-review-protocol` only.
- Explicitly excluded `Skills/spec-review-adapter` from this round.
- Re-read current `Skills/ai-review-protocol/SKILL.md` and `references/core.md`.
- Expanded `task_plan.md` with a concrete modification plan: frontmatter hooks, fixed file contract, restore order, write contracts, role lock, drift handling, and stop verification script.
- Verification note: `git diff --name-only` is unavailable because `/Volumes/OSX ExtNVME/code_projects/AI-peer` is not a Git repository.
- Alternative verification: listed project files and `Skills/spec-review-adapter` files; this turn only created/updated planning files in the project root.
- Read `planning-with-files` scripts: `init-session.sh`, `init-session.ps1`, `check-complete.sh`, `check-complete.ps1`, and `session-catchup.py`.
- Recorded which script ideas transfer to `ai-review-protocol`: minimal initializer optional, stop checker important, session catchup not appropriate for the generic peer-review contract.
- Refined script analysis after user correction: borrow the deterministic file-locator idea from `session-catchup.py`, but not its full chat-history recovery behavior.
- Updated plan to include a `review-context.py` locator script that prints exact review files and compact role/state fields for hooks.
- Re-read `planning-with-files` hooks and templates to separate read-path and write-path logic.
- Optimized the proposed review script from separate locator/checker scripts into one `review-flow.py` with bounded modes: `context`, `compact`, `next-round`, `init`, and `check`.
- Clarified role handling: `review-flow.py` should validate and lock roles from explicit input or existing state, not infer role from natural-language prompts.
- Created `ai-review-protocol-hardening-review-plan.md` as a standalone plan for another AI to review before implementation.
- Reviewed `gemin-peer.md` in anti-sycophancy mode and wrote `gpt-peer.md` with accepted points, partial rebuttals, rejected points, and revised plan deltas.
- Revised the path-position after user challenged the single active project-level entrypoint: peer review needs thread/session-scoped state, not one global project state file. Updated `gpt-peer.md` and `findings.md` with an active-pointer plus sessions directory approach.
- Settled four implementation decisions: no assumed universal skill-root variable, use `.ai-peer-review/`, use CLI args for `commit-round`, and promote `next_actor` through a script-managed begin-turn handoff.
- Refined the skill-root decision after comparing `planning-with-files`: avoid skill-root lookup in hot-path hooks by installing/copying `review-flow.py` into `.ai-peer-review/bin/` during init, then call that project-local helper.
- Audited the write path and identified needed hardening: reserve round paths before writing, make `commit-round` the only normal state/log writer, include open-finding/source-status metadata, and verify reviewer source-artifact immutability without relying on Git.
- Rechecked the design against `planning-with-files` and simplified the v1 baseline: keep project-local files, simple hook reminders, `init/context/compact/commit-round/check`, and defer reservation locks, source hashing, and complex promotion logic.
- Reframed `ai-review-protocol` files as temporary peer-review coordination files rather than durable project memory. Durable conclusions remain the responsibility of `planning-with-files`. Updated `task_plan.md` and `findings.md` to supersede thread/session routing with one disposable `.ai-peer-review/` workspace.
- Simplified stale-file handling: existing `.ai-peer-review/` is not treated as a collision for scripts to adjudicate. Agents read the file state and proceed; no closed marker is used in v1.
- Removed the closed-marker/finish concept after comparing with the Autoresearch open-loop pattern. The peer-review loop should continue until the user stops it or asks for a durable planning summary.
- Re-reviewed the global plan under first principles and Occam's razor. Removed remaining stale concepts from `task_plan.md`: durable persistence wording, `session_id`, `handoff_ready`, `disposable`, `--session-id`, and "final handoff" stop wording.
- Decoupled the target `ai-review-protocol` design from `planning-with-files`: planning remains a reference pattern and this working discussion's tracking mechanism, but the target skill must not mention or require other skill files in its protocol.
- Removed remaining `planning-with-files` named references from the executable portions of `task_plan.md`; remaining mentions of `task_plan.md`, `findings.md`, and `progress.md` describe this planning session only, not the target skill protocol.
- Implemented AI Review Protocol V1 in `Skills/ai-review-protocol`: updated `SKILL.md`, updated `references/core.md`, and added `scripts/init-review.sh`, `scripts/check-review.sh`, and `scripts/review-flow.py`.
- Verified `review-flow.py` with `python3 -m py_compile`.
- Verified fixture behavior: no-state check exits 0, init creates `.ai-peer-review/`, valid `round-1.md` commit updates state/log, invalid `round-1-reviewer.md` is rejected, role mismatch is rejected, missing log produces a warning and exits 0.
- Verified static cleanup: no old nested fallback path, no `review-session-id`, no `review-target-id`, no `review-notes`, no `closed`, no `finish`, no `approved`, and no `planning-with-files` references remain under `Skills/ai-review-protocol`.
- Removed automatic hooks from `Skills/ai-review-protocol/SKILL.md` after identifying token/context bleed risk when the skill is not actively used. The skill now exposes only on-demand scripts.
- Updated `task_plan.md` to reflect the implemented hook-free design: `init-review.sh`, `check-review.sh`, and `review-flow.py commit-round`.
- Compressed `Skills/ai-review-protocol/SKILL.md` from 1031 words to 337 words and `references/core.md` from 1030 words to 346 words by removing duplicated explanations and moving the skill body to an operation-only shape.
- Added a short `Mandatory Lifecycle` section to `SKILL.md` so the skill has planning-style structured execution while still avoiding automatic frontmatter hooks.
- Ran a skill-creator style review/test pass. Found a handoff bug and replaced immediate role promotion with `handoff_pending: true` plus explicit `begin-turn` for the next user-invoked turn.
- Verified multi-round loop with the final handoff model: Reviewer round 1 commits and sets pending; immediate Drafter commit is rejected; `begin-turn` promotes Drafter; duplicate `round-1.md` is rejected; correct `round-2.md` succeeds.
- Added `user-override-role` so natural-language user role reassignment has a scripted path instead of requiring hand edits to `review-state.md`. Verified override enables a user-requested role switch, rejects invalid roles, and rejects empty reasons.
- Fixed non-blocking review findings: all command examples now resolve helpers from `<skill-root>/scripts/...`, and `check-review.sh` now uses the same positive round regex as `review-flow.py`.
- Verified static path hygiene under `Skills/ai-review-protocol`: no repo-root `Skills/ai-review-protocol` command paths, user directory paths, absolute local paths, parent-directory drift, or other-skill dependencies remain.
- Re-ran code review. Result: no blocking or non-blocking actionable findings in the target skill changes.
- Updated `metadata.version` in `Skills/ai-review-protocol/SKILL.md` to `"2.0.0"` because this is a major rewrite from descriptive protocol to script-enforced file workflow.

## Errors Encountered

| Error | Attempt | Resolution |
|-------|---------|------------|
| `git diff --name-only` failed because the current directory is not a Git repository. | Tried to verify changed files through Git. | Used filesystem listing instead and recorded the limitation. |
