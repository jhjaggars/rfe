---
name: init
description: Check and install prerequisites for the rfe plugin, configure JIRA access, and verify connectivity. Triggers on: /rfe:init, "set up rfe", "configure rfe", "initialize rfe", "rfe setup"
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

Check whether `JIRA_API_TOKEN` is set:

```bash
echo "${JIRA_API_TOKEN:+set}"
```

- If the output is `set` → the token is already configured. Skip to Phase 3.
- If the output is empty → guide the user through creating one.

### Collecting the token

Tell the user:

> To use the rfe plugin you need a Personal Access Token from https://issues.redhat.com.
>
> Steps:
> 1. Log in to https://issues.redhat.com
> 2. Click your profile avatar (top right) → **Profile**
> 3. In the left sidebar, click **Personal Access Tokens**
> 4. Click **Create token**, give it a name (e.g. `claude-code`), and set an expiry
> 5. Copy the token — you won't see it again

Then use `AskUserQuestion` to collect the token value.

Once collected:

1. Determine the user's shell profile file. Check in order:
   - `~/.zshrc` (if `$SHELL` contains `zsh` or if the file exists)
   - `~/.bashrc` (fallback)

2. Append the export to the profile file:

```bash
echo 'export JIRA_API_TOKEN="<TOKEN>"' >> ~/.zshrc
```

3. Export it in the current session:

```bash
export JIRA_API_TOKEN="<TOKEN>"
```

4. Tell the user:
> Token saved to `~/.zshrc`. It will be available automatically in new shell sessions. For the current session it has already been exported.

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
  > "Could not reach https://issues.redhat.com. Check your network connection and try again."

---

## Phase 4: Report Summary

Print a summary table:

```
rfe setup check
───────────────────────────────────
  python3          ✓  3.x.y
  uv               ✓  x.y.z
  JIRA_API_TOKEN   ✓  configured
  JIRA access      ✓  REST API reachable
───────────────────────────────────
All checks passed. You're ready to use the rfe plugin.

Next step: /rfe:triage
```

If any check failed, replace the corresponding line with `✗` and the failure reason, and omit the "Next step" line.
