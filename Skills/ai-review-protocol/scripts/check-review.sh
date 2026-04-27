#!/bin/bash
# Check temporary AI peer review consistency.
# Always exits 0; stdout is guidance, not a blocker.

ROOT="${1:-.}"
STATE_FILE="$ROOT/.ai-peer-review/review-state.md"
LOG_FILE="$ROOT/.ai-peer-review/review-log.md"

if [ ! -f "$STATE_FILE" ]; then
    echo "[ai-review-protocol] No .ai-peer-review/review-state.md found -- no active temporary review."
    exit 0
fi

echo "[ai-review-protocol] Active temporary review found."

if [ ! -f "$LOG_FILE" ]; then
    echo "[ai-review-protocol] WARNING: .ai-peer-review/review-log.md is missing."
fi

CURRENT_ROUND_FILE=$(grep -E '^current_round_file:' "$STATE_FILE" 2>/dev/null | head -1 | sed 's/^current_round_file:[[:space:]]*//')
HANDOFF_PENDING=$(grep -E '^handoff_pending:' "$STATE_FILE" 2>/dev/null | head -1 | sed 's/^handoff_pending:[[:space:]]*//')
NEXT_ACTOR=$(grep -E '^next_actor:' "$STATE_FILE" 2>/dev/null | head -1 | sed 's/^next_actor:[[:space:]]*//')

if [ "$HANDOFF_PENDING" = "true" ]; then
    echo "[ai-review-protocol] Handoff pending to: $NEXT_ACTOR"
fi

if [ -z "$CURRENT_ROUND_FILE" ]; then
    echo "[ai-review-protocol] No current_round_file set yet."
    exit 0
fi

if ! printf '%s\n' "$CURRENT_ROUND_FILE" | grep -Eq '^\.ai-peer-review/rounds/round-[1-9][0-9]*\.md$'; then
    echo "[ai-review-protocol] WARNING: current_round_file must be .ai-peer-review/rounds/round-N.md"
fi

if [ ! -f "$ROOT/$CURRENT_ROUND_FILE" ]; then
    echo "[ai-review-protocol] WARNING: current round file is missing: $CURRENT_ROUND_FILE"
else
    echo "[ai-review-protocol] Current round file exists: $CURRENT_ROUND_FILE"
fi

if [ -f "$LOG_FILE" ]; then
    if grep -F "$CURRENT_ROUND_FILE" "$LOG_FILE" >/dev/null 2>&1; then
        echo "[ai-review-protocol] Review log references current round."
    else
        echo "[ai-review-protocol] WARNING: review-log.md does not reference current_round_file."
    fi
fi

exit 0
