#!/bin/bash
# Initialize temporary AI peer review files.
# Usage: sh scripts/init-review.sh <target-id> <source-artifact> <Reviewer|Drafter>

set -e

TARGET_ID="${1:-}"
SOURCE_ARTIFACT="${2:-}"
ROLE="${3:-}"
DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

if [ -z "$TARGET_ID" ] || [ -z "$SOURCE_ARTIFACT" ] || [ -z "$ROLE" ]; then
    echo "Usage: sh scripts/init-review.sh <target-id> <source-artifact> <Reviewer|Drafter>"
    exit 1
fi

if [ "$ROLE" != "Reviewer" ] && [ "$ROLE" != "Drafter" ]; then
    echo "[ai-review-protocol] role must be Reviewer or Drafter"
    exit 1
fi

mkdir -p .ai-peer-review/rounds

if [ ! -f .ai-peer-review/review-state.md ]; then
    cat > .ai-peer-review/review-state.md << EOF
# AI Peer Review State

target_id: $TARGET_ID
source_artifact: $SOURCE_ARTIFACT
current_round: 0
current_round_file:
current_role: $ROLE
next_actor:
handoff_pending: false
state: intake
open_major_findings: 0
open_minor_findings: 0
role_switch_allowed: false
updated_at: $DATE
EOF
    echo "[ai-review-protocol] Created .ai-peer-review/review-state.md"
else
    echo "[ai-review-protocol] .ai-peer-review/review-state.md already exists, skipping"
fi

if [ ! -f .ai-peer-review/review-log.md ]; then
    cat > .ai-peer-review/review-log.md << EOF
# AI Peer Review Log

- $DATE init target=$TARGET_ID source=$SOURCE_ARTIFACT role=$ROLE
EOF
    echo "[ai-review-protocol] Created .ai-peer-review/review-log.md"
else
    echo "[ai-review-protocol] .ai-peer-review/review-log.md already exists, skipping"
fi

echo "[ai-review-protocol] Temporary review files ready."
