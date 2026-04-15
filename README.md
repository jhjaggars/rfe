# rfe

A Claude Code plugin with skills for triaging RFEs and decomposing them into well-defined JIRA Feature issues.

## Skills

- **`/rfe:init`** — Check and install prerequisites, configure JIRA credentials (API token + email), verify REST API access, and print a status summary. Run this first.
- **`/rfe:triage`** — Query the RFE project, classify results by Feature coverage, and identify which RFEs are ready to decompose.
- **`/rfe:decompose`** — Fetch a strategy issue and all its linked RFEs, conduct a targeted interview to fill gaps, draft Feature issues for review, then create them via the JIRA REST API.
- **`/rfe:analyze`** — Fetch all RFEs from a configurable time window, group them by component, identify themes (clusters of RFEs addressing the same capability), and surface cross-component opportunities for combined Features.

## Prerequisites

- **python3** — standard on macOS; install via `brew install python3` if missing
- **uv** — install via `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **JIRA_URL** — base URL of your Jira instance (e.g. `https://redhat.atlassian.net`)
- **JIRA_API_TOKEN** — generated at [https://id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
- **JIRA_USER** — your email address (used for Basic auth)

Run `/rfe:init` to have Claude check and install prerequisites and walk you through token setup automatically.

## Installation

### From GitHub

```
/plugin marketplace add jhjaggars/rfe
/plugin install rfe@rfe
```

### From a local clone

```
git clone git@github.com:jhjaggars/rfe.git
/plugin marketplace add ./rfe
/plugin install rfe@rfe
```

## Usage

### 1. Getting started

Run `/rfe:init` once to verify your environment and configure JIRA access:

```
/rfe:init
```

This works through four phases:

1. **Prerequisites** — checks for `python3` and `uv`, installs them via Homebrew/curl if missing
2. **JIRA credentials** — checks for `JIRA_API_TOKEN` and `JIRA_USER` in your environment; if absent, guides you to create an API token and configure your email
3. **API verification** — runs a live search to confirm the token works and the REST API is reachable
4. **Summary** — prints a status table showing pass/fail for each check

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

### 2. Discovering RFEs

Use `/rfe:triage` to browse open RFEs and identify candidates to decompose:

```
/rfe:triage
```

When run with no filters, it asks what you're looking for and offers four quick-starts:

- **High priority** — Critical and Major RFEs not yet Closed
- **Most voted** — RFEs with the most votes (proxy for customer demand)
- **Recent** — RFEs created or updated in the last 90 days
- **By keyword or component** — search by text or product area

You can also pass filters directly:

```
/rfe:triage priority:Critical component:ROSA
/rfe:triage text:"managed cluster" limit:10
/rfe:triage label:cloud-experience status:Approved
```

**Supported filters:**

| Filter | Example | Effect |
|--------|---------|--------|
| `status:<value>` | `status:New` | Restrict by workflow status |
| `component:<name>` | `component:ROSA` | Restrict by component |
| `priority:<level>` | `priority:Critical` | Restrict by priority |
| `label:<tag>` | `label:cloud-experience` | Restrict by label |
| `text:<keywords>` | `text:"managed cluster"` | Full-text search |
| `limit:<n>` | `limit:20` | Max results (default 25) |

Results are displayed in a table and classified by Feature coverage:

```
Found 18 RFEs  (showing 10, 18 total matches)

  KEY           PRIORITY   VOTES  STATUS        FEATURES  COMPONENTS        SUMMARY
  ──────────────────────────────────────────────────────────────────────────────────────
★ RFE-1234      Critical      12  Approved      none      ROSA              Managed cluster auto-scaling
  RFE-5678      Major          7  Refinement    partial   XCMSTRAT          Cross-cluster networking
★ RFE-9012      Minor          2  Backlog       none      HyperShift        Node pool tainting support

★ = no linked Features (actionable)
```

Coverage values:

- `none` — No Features linked; prime candidate for `/rfe:decompose`
- `partial` — Has some Feature links but RFE is still open; may need more
- `decomposed` — Fully addressed; RFE is closed with Feature links

Select any RFE for a drill-down showing full description, linked issues, and a readiness assessment (description quality, scope clarity, existing coverage). When ready:

```
To create Features from this RFE, run:

  /rfe:decompose <KEY>
```

### 3. Creating Features

Pass a JIRA key to decompose a strategy issue into Features:

```
/rfe:decompose OCPSTRAT-2666
```

The skill works through four phases:

1. **Context gathering** — fetches the source issue and up to 10 linked RFEs, then maps each piece of information against the 9 required Feature elements (overview, goals, acceptance criteria, out-of-scope, target release, background, customer considerations, documentation, interoperability)

2. **Interview** — asks up to 5 targeted questions to fill the most important gaps. Questions are specific to the issue content — e.g., "Should this be one Feature or two? The RFE covers both A and B, which seem separable."

3. **Draft review** — presents complete Feature drafts using the official template, with all sections filled using real content (no placeholders). No issues are created until you approve.

4. **JIRA creation** — creates each approved Feature via the REST API, then links it back to the source issue. Reports the new keys and direct browse URLs.

Example output after creation:

```
## Created Features

| Key | Summary | Project | Link |
|-----|---------|---------|------|
| ROSA-456 | Auto-scaling for managed clusters | ROSA | $JIRA_URL/jira/browse/ROSA-456 |

Links created:
- ROSA-456 Implements OCPSTRAT-2666
```

### 4. Analyzing RFE themes

Use `/rfe:analyze` to identify patterns and combined-effort opportunities across many RFEs:

```
/rfe:analyze
```

When run with no filters, it fetches all open RFEs from the last 18 months and analyzes them. You can narrow the scope:

```
/rfe:analyze period:6
/rfe:analyze component:ROSA period:12
/rfe:analyze status:Approved component:HyperShift
```

**Supported arguments:**

| Argument | Example | Effect |
|----------|---------|--------|
| `period:<months>` | `period:12` | Time window in months (default 18) |
| `component:<name>` | `component:ROSA` | Restrict to one component |
| `status:<value>` | `status:Approved` | Restrict by workflow status |

The skill works through five phases:

1. **Query building** — constructs JQL from your arguments and the base RFE query
2. **Data fetch** — paginates through all matching RFEs (warns if > 500)
3. **Theme analysis** — groups by component, clusters RFEs by shared capability, finds cross-component patterns, flags high-value standalones
4. **Report** — structured markdown with component breakdown table, themes by component, cross-component themes, high-value standalones, and top recommendations
5. **Follow-up** — offers to drill into a theme, hand off to `/rfe:decompose`, or re-run with different filters

Example report excerpt:

```
## ROSA

### Theme: Auto-scaling for managed clusters
RFEs: RFE-1234, RFE-5678, RFE-9012
Combined votes: 34  |  Priority floor: Critical  |  Coverage: none
Rationale: Three RFEs request dynamic node scaling; a single Feature covering
the scaling framework would address all three.
```

## Technical notes

All JIRA operations use the REST API via Python (`uv run --with requests`). The `requests` dependency is fetched automatically by `uv` on each invocation — no manual install required. `jira-cli` is not used because it corrupts wiki markup formatting (converts numbered lists to headers, escapes hyphens). `JIRA_API_TOKEN` must be set in your environment — run `/rfe:init` if you haven't configured it yet.
