---
name: init
description: "Check and install prerequisites for the rfe plugin, configure JIRA access, and verify connectivity. Triggers on: /rfe:init, \"set up rfe\", \"configure rfe\", \"initialize rfe\", \"rfe setup\""
argument-hint: ""
---

# init

You help the user get set up to use the rfe plugin. Work through the three phases below in order, stopping if any required step fails.

---

## Phase 1: Check & Install Prerequisites

### python3

Run:

```bash
python3 --version
```

- If it succeeds → note the version and continue.
- If it fails (command not found) → install it:

```bash
brew install python3
```

Re-verify with `python3 --version`. If it still fails, stop and tell the user:
> "python3 could not be installed automatically. Please install it manually from https://www.python.org/downloads/ and re-run `/rfe:init`."

### uv

Run:

```bash
uv --version
```

- If it succeeds → note the version and continue.
- If it fails (command not found) → install it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Re-verify with `uv --version`. If it still fails, stop and tell the user:
> "uv could not be installed automatically. Please install it manually by following the instructions at https://docs.astral.sh/uv/getting-started/installation/ and re-run `/rfe:init`."

---

## Phase 2: Configure JIRA Access

Check whether `JIRA_URL`, `JIRA_API_TOKEN`, and `JIRA_USER` are set:

```bash
echo "JIRA_URL=${JIRA_URL:+set}"
echo "JIRA_API_TOKEN=${JIRA_API_TOKEN:+set}"
echo "JIRA_USER=${JIRA_USER:+set}"
```

- If all three are `set` → skip to Phase 3.
- If any are missing → guide the user through setup.

### Collecting credentials

Tell the user:

> To use the rfe plugin you need the Jira base URL, an API token, and your email address.
>
> Steps:
> 1. Your JIRA_URL is the base URL of your Jira instance (e.g. `https://redhat.atlassian.net`)
> 2. Go to https://id.atlassian.com/manage-profile/security/api-tokens
> 3. Click **Create API token**, give it a name (e.g. `claude-code`)
> 4. Copy the token — you won't see it again
> 5. Your JIRA_USER is the email address you use to log in to Jira

Then use `AskUserQuestion` to collect the Jira URL (if missing), token value (if missing), and email (if missing).

Once collected:

1. Determine the user's shell profile file. Check in order:
   - `~/.zshrc` (if `$SHELL` contains `zsh` or if the file exists)
   - `~/.bashrc` (fallback)

2. Append the exports to the profile file:

```bash
echo 'export JIRA_URL="<URL>"' >> ~/.zshrc
echo 'export JIRA_API_TOKEN="<TOKEN>"' >> ~/.zshrc
echo 'export JIRA_USER="<EMAIL>"' >> ~/.zshrc
```

3. Export them in the current session:

```bash
export JIRA_URL="<URL>"
export JIRA_API_TOKEN="<TOKEN>"
export JIRA_USER="<EMAIL>"
```

4. Tell the user:
> Credentials saved to `~/.zshrc`. They will be available automatically in new shell sessions. For the current session they have already been exported.

---

## Phase 3: Verify Access

Run a minimal search using the rfe-search script to confirm the token works and the REST API is reachable:

```bash
uv run --with requests python3 <SKILL_BASE_DIR>/../../skills/triage/scripts/rfe-search.py \
  --jql "project = RFE ORDER BY updated DESC" \
  --limit 1
```

> Note: `<SKILL_BASE_DIR>` is the directory containing this SKILL.md file. Use the actual path.

- If it returns one issue → access is confirmed.
- If it returns an authentication error (401/403) → tell the user:
  > "The JIRA API token was rejected. Check that it hasn't expired and that it was copied correctly. Re-run `/rfe:init` to enter a new token."
- If it returns a network error → tell the user:
  > "Could not reach $JIRA_URL. Check your network connection and try again."

---

## Phase 4: Report Summary

Print a summary table:

```
rfe setup check
───────────────────────────────────
  python3          ✓  3.x.y
  uv               ✓  x.y.z
  JIRA_URL         ✓  configured
  JIRA_API_TOKEN   ✓  configured
  JIRA_USER        ✓  configured
  JIRA access      ✓  REST API reachable
───────────────────────────────────
All checks passed. You're ready to use the rfe plugin.

Next step: /rfe:triage
```

If any check failed, replace the corresponding line with `✗` and the failure reason, and omit the "Next step" line.
