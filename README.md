# feature-create-from

A Claude Code plugin with skills for creating well-defined JIRA Feature issues from higher-level strategy issues — RFEs, Outcomes, OCPSTRAT issues, or any issue with linked Feature Requests.

## Skills

- **`/feature-create-from`** — Fetch a strategy issue and all its linked RFEs, ask targeted questions to fill gaps, then draft and create Feature issues in the appropriate JIRA project.

## Prerequisites

### 1. Install jira-cli

**macOS (recommended):**
```bash
brew install jira-cli
```

**Go (any platform):**
```bash
go install github.com/ankitpokhrel/jira-cli/cmd/jira@latest
```

### 2. Get a Personal Access Token from JIRA

1. Log in to [https://issues.redhat.com](https://issues.redhat.com)
2. Click your profile avatar (top right) → **Profile**
3. In the left sidebar, click **Personal Access Tokens**
4. Click **Create token**, give it a name (e.g. `claude-code`), set an expiry
5. Copy the token — you won't see it again

### 3. Configure your environment

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
export JIRA_API_TOKEN="your-token-here"
export JIRA_AUTH_TYPE=bearer
```

Then reload your shell:
```bash
source ~/.zshrc
```

### 4. Initialize jira-cli

```bash
jira init
```

When prompted:
- **Installation type**: Cloud or Server → choose **Server** (Red Hat uses Server)
- **Server URL**: `https://issues.redhat.com`
- **Login**: your Red Hat email address
- **API token**: paste the token from step 2

Verify it works:
```bash
jira issue list -q "assignee = currentUser()" --plain
```

## Installation

### From local directory

Add the plugin to your Claude Code settings (`.claude/settings.local.json`):

```json
{
  "localMarketplaces": [
    {
      "type": "local",
      "path": "/path/to/feature-create-from"
    }
  ]
}
```

Restart Claude Code. The `/feature-create-from` skill will be available.

## Usage

```
/feature-create-from OCPSTRAT-2666
```

The skill will:
1. Fetch the source issue and all linked RFEs from JIRA
2. Identify what's missing for a well-defined Feature
3. Ask targeted questions to fill the gaps
4. Draft Feature issue(s) for your review
5. Create the approved Features via the JIRA REST API and link them back to the source

## Notes on JIRA issue creation

This plugin uses the JIRA REST API (via Python) rather than jira-cli for creating Feature issues. jira-cli escapes parentheses in issue bodies — `(text)` becomes `\(text\)` — which corrupts the `( ) Yes ( ) No ( ) N/A` checkboxes in the official Feature requirements table. It also converts `#` numbered list items into `h1.` headers.

For this to work, `JIRA_API_TOKEN` must be set in your environment (see setup above). Python 3 and the `requests` library must be available:

```bash
pip3 install requests
```
