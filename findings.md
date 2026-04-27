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

## Planning Script Analysis

`planning-with-files` has three script categories:

- `init-session.sh` / `init-session.ps1`: create default project-local memory files if absent.
- `check-complete.sh` / `check-complete.ps1`: stop-time consistency/status reporter. Always exits 0 and uses stdout to guide the agent.
- `session-catchup.py`: scans Claude/Codex session history to find conversation/tool activity after the last planning file update, then prints unsynced context.

Reusable for `ai-review-protocol`:

- A minimal initializer can create `ai-peer-review/review-state.md`, `ai-peer-review/review-log.md`, and `ai-peer-review/rounds/`.
- A stop-time checker is strongly reusable and should verify file consistency without modifying files.
- Cross-platform shell/PowerShell parity is useful only if this skill must run on Windows; otherwise a small POSIX shell checker is enough for the current project.

Important correction:

- `session-catchup.py` should not be copied for chat-history recovery, but its deterministic locator pattern is worth borrowing.
- The script prevents the agent from manually guessing which files matter. It locates the relevant project/session files and prints only the context the agent should read.
- For `ai-review-protocol`, the equivalent should be a small locator script that reads `ai-peer-review/review-state.md`, extracts `current_round_file` and role-lock fields, verifies existence, and prints the exact files to read next.

Reusable locator idea:

- `scripts/review-context.sh` or `scripts/review-context.py`
- Input: project root, default current working directory.
- Output: canonical file list and compact state:
  - `ai-peer-review/review-state.md`
  - value of `current_round_file`
  - `ai-peer-review/review-log.md`
  - `current_role`
  - `next_actor`
  - `state`
  - any missing-file warning
- No directory guessing except reporting drift.

Still not worth copying:

- Planning-specific phase counting does not map to review rounds.
- Full Claude/Codex session-log archaeology should not become the review recovery path.

## Planning Read/Write Flow Extraction

Planning read flow:

- `UserPromptSubmit` reads a small, fixed slice of `task_plan.md` plus recent `progress.md`.
- `PreToolUse` re-reads the top of `task_plan.md` before every relevant tool call.
- `session-catchup.py` deterministically finds unsynced context and prints a bounded report.
- The agent is not asked to discover the memory files; the system either reads fixed paths or runs a script that prints exact next reads.

Planning write flow:

- `init-session.*` creates the fixed memory files from templates and never overwrites existing files.
- `PostToolUse` reminds the agent immediately after file writes to update `progress.md` and phase status.
- `check-complete.*` runs at stop time and reports whether the persistent state is complete enough.
- The fixed file layout does most of the discipline; prose rules only explain the intent.

Transferable essence for peer review:

- Move file discovery, round allocation, and consistency checks into a script.
- Keep AI responsible for judgment and review content, not path selection or state recovery.
- Hooks should call the script in bounded modes so token load stays low.
- The script should print exact files and exact missing updates, not broad instructions.

Optimized script shape:

- Prefer one Python utility over multiple shell fragments: `scripts/review-flow.py`.
- Modes:
  - `context`: print exact review files to read and compact state.
  - `compact`: print only role lock, state, and current round pointer.
  - `next-round --role Reviewer|Drafter`: print the next valid `round-N.md` path without creating content.
  - `init`: create `ai-peer-review/`, `review-log.md`, and a minimal `review-state.md` only when enough required values are supplied.
  - `check`: validate state/log/round consistency for Stop hook.
- Optional shell wrappers are only for host compatibility; the Python script should own the real logic.

## Role Detection Boundary

Role selection should not be guessed by the script from natural-language prompts.

Reliable role sources, in priority order:

1. Explicit current-turn user instruction, passed by the agent when initializing or switching role.
2. Existing `ai-peer-review/review-state.md` fields:
   - `current_role`
   - `next_actor`
   - `role_switch_allowed`
3. Host adapter metadata, if a future adapter provides structured role context.

The generic Python utility can enforce and validate role state, but it should not infer role from words like "review", "fix", or "resubmit" by itself. Keyword inference would recreate the same weak-model ambiguity in code.

Recommended contract:

- `review-flow.py init --target-id ... --source-artifact ... --role Reviewer|Drafter` requires explicit role and target.
- `review-flow.py context` reads and prints the locked role from `review-state.md`.
- `review-flow.py compact` prints role-lock fields before tool use.
- `review-flow.py commit-round --acting-role Reviewer|Drafter ...` verifies the acting role matches `current_role`, unless `role_switch_allowed: true`.
- `review-flow.py check` warns if role fields are missing or inconsistent.

This means the script decides whether a role is allowed, not what the user's natural-language intent means.

## Open Design Choice

Whether to preserve the old nested path:

`ai-peer-review/<review-session-id>/<review-target-id>/...`

or replace it with fixed root paths:

`ai-peer-review/review-state.md`

Recommendation: use fixed root paths for the generic skill. Store `session_id` and `target_id` as fields. This removes path drift with the fewest moving parts.

## Thread-Scoped State Correction

Superseded by `Temporary Workspace Correction`.

The fixed root-path recommendation is insufficient for the real peer-review use case.

`planning-with-files` can use project-root files because it is project-wide working memory. `ai-review-protocol` is conversation/review-session scoped: different threads in the same project may review different artifacts.

Revised recommendation:

- Keep deterministic recovery, but make it thread/session scoped.
- Do not use target auto-detection.
- Use an active pointer resolved by script:

```text
ai-peer-review/active/<thread-or-session-key>.json
```

pointing to:

```text
ai-peer-review/sessions/<review-session-id>/review-state.md
```

Session directory:

```text
ai-peer-review/sessions/<review-session-id>/
  review-state.md
  review-log.md
  rounds/round-N.md
```

`review-flow.py` should resolve the active pointer from a host thread/session id when available, or from explicit `--session-id` during init. If multiple active sessions exist and no key is available, it should halt instead of guessing.

## Implementation Decisions Before Coding

Superseded where it mentions thread keys, active pointers, installed project-local helpers, or automatic role promotion. The current v1 keeps only one temporary `.ai-peer-review/` workspace and does not promote roles automatically.

### 1. Skill Root Resolution

Local environment observation:

- `CODEX_THREAD_ID` is available and can be used as a thread key.
- No generic skill-root environment variable such as `CLAUDE_PLUGIN_ROOT` is visible in the current environment.

Planning comparison:

- `planning-with-files` avoids skill-root lookup in its hot-path hooks by using project-root files directly:
  - `head task_plan.md`
  - `tail progress.md`
  - `cat task_plan.md`
- It uses `${CLAUDE_PLUGIN_ROOT}` only for explicit script calls documented in the body.
- Its Stop hook uses a broad cache search fallback for `check-complete.*`.

Revised decision:

- Do not make normal hook behavior depend on locating the skill install directory.
- Put the runtime helper in the project metadata directory during `init`:

```text
.ai-peer-review/bin/review-flow.py
```

Then hooks can call the project-local helper:

```text
python3 .ai-peer-review/bin/review-flow.py ...
```

This mirrors `planning-with-files`: hot-path hooks operate on project-local state using stable project-relative paths.

The skill-installed `Skills/ai-review-protocol/scripts/review-flow.py` remains the source template. `init` copies it into `.ai-peer-review/bin/` if absent or outdated. If the helper is missing, hooks should fail quietly and the skill text should instruct the agent to run `init`.

### 2. Review State Directory Name

Decision:

- Use a hidden project-local metadata directory:

```text
.ai-peer-review/
```

Reason:

- Review exchange state is process metadata, not project source.
- Hidden directory keeps the project root cleaner.
- It still remains deterministic and inspectable.

### 3. `commit-round` Metadata Source

Decision:

- Use CLI arguments as the authoritative metadata source for v1.
- Do not require Markdown frontmatter parsing for state transitions.

Reason:

- CLI arguments are explicit, deterministic, and easy for hooks/scripts to validate.
- Markdown frontmatter parsing adds another schema and another failure mode.

Allowed v1 command shape:

```text
review-flow.py commit-round <project-root> --round-file <path> --acting-role Reviewer --next-actor Drafter --state reviewing
```

### 4. Promoting `next_actor` To `current_role`

Superseded for v1.

Decision:

- Do not rely on AI self-declaration for normal handoff promotion.
- Let `review-flow.py` manage promotion at the next turn boundary.

Mechanism:

- `commit-round` sets:

```yaml
current_role: Reviewer
next_actor: Drafter
handoff_ready: true
role_switch_allowed: false
```

- `compact` and `check` never promote roles.
- A prompt-start hook should call a mode such as `begin-turn` or `context --begin-turn`.
- That mode may promote:

```yaml
current_role: Drafter
next_actor: null
handoff_ready: false
```

only when `handoff_ready: true`.

Explicit user overrides should use a separate explicit command path, not natural-language inference by the script.

## Write-Path Audit

Partially superseded by `Temporary Workspace Correction`.

The write path is now the critical risk area. Reading can be stable if hooks only read project-local fixed paths, but writing must ensure those paths are created and updated mechanically.

Required write pipeline:

1. `init`: create `.ai-peer-review/`, install `.ai-peer-review/bin/review-flow.py`, create active pointer, create session directory, create initial `review-state.md` and `review-log.md`.
2. `begin-turn`: resolve active pointer and promote handoff state if needed.
3. `start-round` or `next-round --reserve`: allocate and reserve the next `round-N.md` path.
4. AI writes only the round content to the reserved file.
5. `commit-round`: validate the round file and mechanically update `review-state.md` and `review-log.md`.
6. `check`: verify state/log/round consistency before stop.

Potential flaws in the current plan:

- `next-round` only prints a path. If it does not reserve the file, two agents or two attempts can pick the same next round.
- `commit-round` needs enough metadata to update state correctly. `--acting-role`, `--next-actor`, and `--state` are not enough for open findings and source artifact status.
- Reviewer source-artifact protection cannot rely on Git. The script should store a source artifact hash or mtime at `begin-turn` and verify it at `commit-round` for Reviewer.
- Drafter completion should verify the source artifact changed only when accepted changes exist; otherwise the round must explain rejection/no-op.
- `begin-turn` promotion is a write. It must be idempotent and should append a short log entry when it promotes `next_actor` to `current_role`.
- `init` must create the active pointer atomically and refuse conflicting session ids for the same thread key unless explicitly overridden.
- `commit-round` must be the only normal writer of `review-state.md` and `review-log.md`; AI should not hand-edit these files except for emergency repair.

Revised script modes:

- `init`
- `begin-turn`
- `context`
- `compact`
- `start-round` or `next-round --reserve`
- `commit-round`
- `check`
- `repair` only for explicit drift recovery

Minimum `commit-round` arguments:

```text
--round-file
--acting-role Reviewer|Drafter
--next-actor Reviewer|Drafter|User
--state reviewing|resubmitted|approved|blocked
--open-major-count
--open-minor-count
--source-artifact-status clean|modified|unchanged|not-checked
```

The script should derive `current_round` from the round filename, not from an AI-supplied round number.

## Simplification After Rechecking Planning Pattern

The previous write-path audit drifted too far toward a transaction system.

`planning-with-files` works because it is simple:

- fixed project-local files
- AI writes the content
- hooks keep the important state visible
- scripts initialize, locate, catch up, or check
- Stop hook reports incomplete persistent state

It does not reserve files, lock transactions, hash source files, or automate every state transition.

For `ai-review-protocol`, v1 should mirror that level of complexity:

- `init`: create `.ai-peer-review/<session>/review-state.md`, `review-log.md`, and the first expected round path.
- `context`: print exact files to read and the next expected round path.
- `compact`: print role lock and current/next round.
- `commit-round`: after AI writes `round-N.md`, update `review-state.md` and append `review-log.md`.
- `check`: verify state/log/round consistency.

Defer:

- source artifact hash enforcement
- round reservation/locking
- frontmatter parsing as required metadata
- automatic target discovery
- complex active-pointer promotion logic

Reason:

- The observed failures are missing files, stale state/log, and role drift.
- They do not yet require a full transaction system.
- Simpler mechanics are more likely to work across weak agents and different hosts.

## Temporary Workspace Correction

The thread/session complexity came from a wrong durability assumption.

Irreducible facts:

- `ai-review-protocol` only coordinates a temporary review exchange.
- Review conclusions and accepted solution decisions are outside this skill's protocol.
- The raw peer-review exchange does not need to be kept forever unless the user explicitly asks.

Therefore the simpler file model is:

```text
.ai-peer-review/
  review-state.md
  review-log.md
  rounds/
    round-1.md
    round-2.md
```

This removes the need for:

- `.ai-peer-review/active/<thread-or-session-key>.json`
- `.ai-peer-review/sessions/<review-session-id>/...`
- host thread id dependency
- session pointer resolution
- multi-session routing
- project-level review archive semantics

New lifecycle:

1. `init` creates one temporary active review workspace.
2. reviewer/drafter exchange through fixed files.
3. `commit-round` performs mechanical state/log updates.
4. `check` prevents incomplete handoff.
5. The exchange can continue indefinitely until the user stops it or asks for a durable summary.

Stale-file handling becomes deliberately weak:

- The script does not decide whether an existing `.ai-peer-review/` is stale.
- A newly joined AI reads the files and follows the state it sees.
- Cleanup is not automatic because stale-vs-current is a human/project judgment.
- There is no v1 closed marker. A closed marker gives weak agents a new place to hallucinate premature completion.

This matches Occam's razor better than thread-scoped routing because it uses the minimum state needed for the real job: one active temporary exchange.

## Autoresearch Principle Applied

Autoresearch's useful design lesson is the open loop:

- run a bounded iteration
- record the result
- continue without asking whether to stop
- externalize stopping to the human or the harness

For `ai-review-protocol`, the analogous loop is:

1. read current review state
2. produce the next reviewer/drafter round
3. commit the round state/log mechanically
4. hand off to the next actor
5. repeat until the user stops or requests an external summary

Therefore v1 should not include:

- `finish`
- `state: closed`
- closed marker files
- automatic cleanup prompts as normal flow
- AI-owned conclusion authority

The only end condition is external: the user asks to stop, summarize, clean up, or persist the conclusion through whatever workflow is active.

## Final Implementation Findings 2026-04-27

The final accepted implementation under `Skills/ai-review-protocol` is the authority over earlier exploratory notes in this file.

Current facts:

- The target skill is hook-free and user-invoked only.
- Helper scripts are resolved from `<skill-root>/scripts/...`, where `<skill-root>` is the directory containing `SKILL.md`.
- Runtime exchange files are fixed project-local files under `.ai-peer-review/`.
- `review-flow.py commit-round` mechanically updates `review-state.md` and `review-log.md` after the AI writes a valid round file.
- Round files must be sequential `.ai-peer-review/rounds/round-N.md`, with `N >= 1`.
- `commit-round` rejects pending handoffs, role mismatches, skipped rounds, duplicate rounds, stale rounds, missing round files, and nonstandard round names.
- `commit-round` keeps `current_role` on the acting role, sets `next_actor`, sets `handoff_pending: true`, and prints an explicit stop instruction.
- `begin-turn` promotes `next_actor` only at the start of a new user-invoked turn.
- `user-override-role` is the scripted path for explicit natural-language user role reassignment.
- `check-review.sh` is warning-only and always exits 0.

Superseded notes above:

- automatic hooks
- `review-context.py`, `context`, `compact`, or `next-round` modes
- active pointers, session routing, thread keys, or copied `.ai-peer-review/bin/` helpers
- `handoff_ready` terminology
- immediate `current_role` promotion during `commit-round`
- `approved`, `closed`, or `finish` states
- source artifact hashing or transaction locks
- any dependency on `planning-with-files` in the target skill protocol

Verification performed:

- `python3 -m py_compile Skills/ai-review-protocol/scripts/review-flow.py`
- end-to-end temp workspace test for init, round 1 commit, pending rejection, begin-turn, duplicate rejection, round 2 commit, and check-review
- static path hygiene search under `Skills/ai-review-protocol`
- code review pass with no remaining actionable findings
