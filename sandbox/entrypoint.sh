#!/bin/bash
set -euo pipefail

if [ -n "${JIRA_API_TOKEN:-}" ] && [ -n "${JIRA_URL:-}" ] && [ -n "${JIRA_USER:-}" ]; then
    JIRA_SITE="${JIRA_URL#https://}"
    JIRA_SITE="${JIRA_SITE#http://}"
    JIRA_SITE="${JIRA_SITE%%/*}"

    echo "$JIRA_API_TOKEN" | acli jira auth login \
        --site "$JIRA_SITE" --email "$JIRA_USER" --token 2>/dev/null \
        || echo "WARN: acli auth setup failed — run /rfe:init inside the sandbox"
fi

exec "$@"
