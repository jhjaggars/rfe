# rfe

A Claude Code plugin with skills for triaging RFEs and decomposing them into well-defined JIRA Feature issues.

## Skills

- **`/rfe:init`** — Check and install prerequisites (python3, uv), configure your JIRA Personal Access Token, and verify REST API access. Run this first.
- **`/rfe:triage`** — Query the RFE project, classify results by Feature coverage, and identify which RFEs are ready to decompose. Use this to discover candidates before running `/rfe:decompose`.
- **`/rfe:decompose`** — Fetch a strategy issue and all its linked RFEs, ask targeted questions to fill gaps, then draft and create Feature issues in the appropriate JIRA project.

## Prerequisites

- **python3** — standard on macOS; install via `brew install python3` if missing
- **uv** — install via `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **JIRA Personal Access Token** — generated at [https://issues.redhat.com](https://issues.redhat.com) under Profile → Personal Access Tokens

Run `/rfe:init` to have Claude check and install prerequisites and walk you through token setup automatically.

## Installation

### From local directory

Add the plugin to your Claude Code settings (`.claude/settings.local.json`):

```json
{
  "localMarketplaces": [
    {
      "type": "local",
      "path": "/path/to/rfe"
    }
  ]
}
```

Restart Claude Code. The `/rfe:init`, `/rfe:triage`, and `/rfe:decompose` skills will be available.

## Usage

### Discover RFEs to work on

```
/rfe:triage
```

Browse with filters:

```
/rfe:triage priority:Critical component:ROSA
/rfe:triage unlinked
/rfe:triage text:"managed cluster" limit:10
```

The skill will:
1. Build a JQL query from your filters (or ask what you're looking for)
2. Fetch results including linked-issue data
3. Classify each RFE: no Features linked / partially covered / already decomposed
4. Display a table; let you drill into individual RFEs for a readiness assessment
5. Tell you to run `/rfe:decompose <KEY>` when you're ready to act

### Create Features from a specific issue

```
/rfe:decompose OCPSTRAT-2666
```

The skill will:
1. Fetch the source issue and all linked RFEs from JIRA
2. Identify what's missing for a well-defined Feature
3. Ask targeted questions to fill the gaps
4. Draft Feature issue(s) for your review
5. Create the approved Features via the JIRA REST API and link them back to the source

## Notes on JIRA issue creation

This plugin uses the JIRA REST API (via Python) for all JIRA operations — fetching issues, creating Features, and creating links. jira-cli is not required.

`uv` handles the `requests` dependency automatically on each invocation with no manual install required. `JIRA_API_TOKEN` must be set in your environment — run `/rfe:init` if you haven't configured it yet.
