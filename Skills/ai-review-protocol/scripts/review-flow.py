#!/usr/bin/env python3
"""
Mechanical state/log update for ai-review-protocol.

Initialization and checking stay in small shell scripts. This helper only
performs mechanical state/log transitions.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple


ROUND_RE = re.compile(r"^\.ai-peer-review/rounds/round-([1-9][0-9]*)\.md$")
VALID_ROLES = {"Reviewer", "Drafter"}
VALID_NEXT_ACTORS = {"Reviewer", "Drafter", "User"}
VALID_STATES = {"intake", "reviewing", "responding", "resubmitted", "blocked"}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fail(message: str) -> int:
    print(f"[ai-review-protocol] ERROR: {message}", file=sys.stderr)
    return 1


def state_bool(state: Dict[str, str], key: str) -> bool:
    return state.get(key, "false").lower() == "true"


def state_int(state: Dict[str, str], key: str, default: int = 0) -> int:
    raw = state.get(key, str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{key} must be an integer") from exc
    if value < 0:
        raise ValueError(f"{key} must be non-negative")
    return value


def read_state(path: Path) -> Tuple[List[str], Dict[str, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    state: Dict[str, str] = {}
    for line in lines:
        if ":" not in line or line.lstrip().startswith("#"):
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if key:
            state[key] = value.strip()
    return lines, state


def replace_or_append(lines: List[str], updates: Dict[str, str]) -> List[str]:
    remaining = dict(updates)
    new_lines: List[str] = []

    for line in lines:
        if ":" not in line or line.lstrip().startswith("#"):
            new_lines.append(line)
            continue
        key, _ = line.split(":", 1)
        key = key.strip()
        if key in remaining:
            new_lines.append(f"{key}: {remaining.pop(key)}")
        else:
            new_lines.append(line)

    if remaining:
        if new_lines and new_lines[-1] != "":
            new_lines.append("")
        for key, value in remaining.items():
            new_lines.append(f"{key}: {value}")

    return new_lines


def normalize_round_file(project_root: Path, round_file: str) -> Tuple[str, Path]:
    raw = Path(round_file)
    if raw.is_absolute():
        try:
            relative = raw.resolve().relative_to(project_root.resolve()).as_posix()
        except ValueError:
            raise ValueError("round file must be inside the project root")
    else:
        relative = raw.as_posix()

    if relative.startswith("./"):
        relative = relative[2:]
    match = ROUND_RE.match(relative)
    if not match:
        raise ValueError("round file must match .ai-peer-review/rounds/round-N.md")

    return relative, project_root / relative


def commit_round(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    state_file = project_root / ".ai-peer-review" / "review-state.md"
    log_file = project_root / ".ai-peer-review" / "review-log.md"

    if args.acting_role not in VALID_ROLES:
        return fail("--acting-role must be Reviewer or Drafter")
    if args.next_actor not in VALID_NEXT_ACTORS:
        return fail("--next-actor must be Reviewer, Drafter, or User")
    if args.state not in VALID_STATES:
        return fail(f"--state must be one of: {', '.join(sorted(VALID_STATES))}")
    if not state_file.exists():
        return fail(".ai-peer-review/review-state.md is missing; run init-review.sh first")

    try:
        relative_round, round_path = normalize_round_file(project_root, args.round_file)
    except ValueError as exc:
        return fail(str(exc))

    if not round_path.exists():
        return fail(f"round file does not exist: {relative_round}")

    lines, state = read_state(state_file)
    current_role = state.get("current_role", "")
    role_switch_allowed = state_bool(state, "role_switch_allowed")
    handoff_pending = state_bool(state, "handoff_pending")

    if handoff_pending:
        return fail("handoff is pending; run begin-turn before committing another round")

    if current_role and current_role != args.acting_role and not role_switch_allowed:
        return fail(
            f"acting role {args.acting_role} does not match current_role {current_role}"
        )

    match = ROUND_RE.match(relative_round)
    assert match is not None
    round_number = int(match.group(1))
    try:
        expected_round = state_int(state, "current_round") + 1
    except ValueError as exc:
        return fail(str(exc))
    if round_number != expected_round:
        return fail(f"round file must be round-{expected_round}.md")
    now = utc_now()

    updates = {
        "current_round": str(round_number),
        "current_round_file": relative_round,
        "current_role": args.acting_role,
        "next_actor": args.next_actor,
        "handoff_pending": "true",
        "state": args.state,
        "updated_at": now,
    }

    state_file.write_text("\n".join(replace_or_append(lines, updates)) + "\n", encoding="utf-8")

    if not log_file.exists():
        log_file.write_text("# AI Peer Review Log\n\n", encoding="utf-8")

    with log_file.open("a", encoding="utf-8") as log:
        log.write(
            f"- {now} commit-round role={args.acting_role} "
            f"round={relative_round} next_actor={args.next_actor} state={args.state}\n"
        )

    print(f"[ai-review-protocol] committed {relative_round}")
    print(f"[ai-review-protocol] handoff_role={args.next_actor}")
    print("[ai-review-protocol] This role's task is complete. Stop now.")
    print("[ai-review-protocol] Do not run begin-turn or act as handoff_role in this response.")
    return 0


def begin_turn(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    state_file = project_root / ".ai-peer-review" / "review-state.md"
    log_file = project_root / ".ai-peer-review" / "review-log.md"

    if not state_file.exists():
        return fail(".ai-peer-review/review-state.md is missing; run init-review.sh first")

    lines, state = read_state(state_file)
    if not state_bool(state, "handoff_pending"):
        print("[ai-review-protocol] no pending handoff")
        return 0

    next_actor = state.get("next_actor", "")
    if next_actor not in VALID_ROLES:
        return fail("pending handoff is not to an AI role; ask the user or run user-override-role")

    now = utc_now()
    updates = {
        "current_role": next_actor,
        "handoff_pending": "false",
        "role_switch_allowed": "false",
        "updated_at": now,
    }
    state_file.write_text("\n".join(replace_or_append(lines, updates)) + "\n", encoding="utf-8")

    if not log_file.exists():
        log_file.write_text("# AI Peer Review Log\n\n", encoding="utf-8")

    with log_file.open("a", encoding="utf-8") as log:
        log.write(f"- {now} begin-turn current_role={next_actor}\n")

    print(f"[ai-review-protocol] begin-turn set current_role={next_actor}")
    return 0


def user_override_role(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    state_file = project_root / ".ai-peer-review" / "review-state.md"
    log_file = project_root / ".ai-peer-review" / "review-log.md"

    if args.role not in VALID_ROLES:
        return fail("--role must be Reviewer or Drafter")
    if not args.reason.strip():
        return fail("--reason is required")
    if not state_file.exists():
        return fail(".ai-peer-review/review-state.md is missing; run init-review.sh first")

    lines, _ = read_state(state_file)
    now = utc_now()
    updates = {
        "current_role": args.role,
        "next_actor": args.role,
        "handoff_pending": "false",
        "role_switch_allowed": "false",
        "updated_at": now,
    }
    state_file.write_text("\n".join(replace_or_append(lines, updates)) + "\n", encoding="utf-8")

    if not log_file.exists():
        log_file.write_text("# AI Peer Review Log\n\n", encoding="utf-8")

    clean_reason = " ".join(args.reason.split())
    with log_file.open("a", encoding="utf-8") as log:
        log.write(f"- {now} user-override-role role={args.role} reason={clean_reason}\n")

    print(f"[ai-review-protocol] user override set current_role={args.role}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI review protocol helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    commit = subparsers.add_parser("commit-round", help="commit a completed review round")
    commit.add_argument("project_root", nargs="?", default=".")
    commit.add_argument("--round-file", required=True)
    commit.add_argument("--acting-role", required=True)
    commit.add_argument("--next-actor", required=True)
    commit.add_argument("--state", required=True)
    commit.set_defaults(func=commit_round)

    begin = subparsers.add_parser("begin-turn", help="promote a pending handoff")
    begin.add_argument("project_root", nargs="?", default=".")
    begin.set_defaults(func=begin_turn)

    override = subparsers.add_parser(
        "user-override-role", help="record an explicit user role override"
    )
    override.add_argument("project_root", nargs="?", default=".")
    override.add_argument("--role", required=True)
    override.add_argument("--reason", required=True)
    override.set_defaults(func=user_override_role)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
