#!/bin/bash
# Ensures the assess-rfe plugin is available locally.
# Safe to run multiple times — clones on first run, pulls updates after.
#
# Set RFE_SKIP_BOOTSTRAP=1 to skip (e.g. in offline environments).

set -euo pipefail

if [ -n "${RFE_SKIP_BOOTSTRAP:-}" ]; then
  echo "RFE_SKIP_BOOTSTRAP set — skipping"
  exit 0
fi

CONTEXT_DIR=".context/assess-rfe"
RUBRIC_FILE="$CONTEXT_DIR/scripts/agent_prompt.md"
REPO_URL="https://github.com/n1hility/assess-rfe"

if [ ! -d "$CONTEXT_DIR" ]; then
  echo "Cloning assess-rfe into $CONTEXT_DIR..."
  git clone --depth 1 "$REPO_URL" "$CONTEXT_DIR" 2>&1
else
  echo "Updating assess-rfe..."
  git -C "$CONTEXT_DIR" pull --ff-only 2>&1 || echo "WARN: pull failed, using cached version" >&2
fi

if [ ! -f "$RUBRIC_FILE" ]; then
  echo "ERROR: Rubric not found at $RUBRIC_FILE after bootstrap" >&2
  exit 1
fi

echo "assess-rfe ready at $CONTEXT_DIR"
