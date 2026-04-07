---
name: analyze
description: "Analyze RFEs to identify themes by component and recommend combined efforts. Triggers on: /rfe:analyze, \"analyze RFEs\", \"RFE themes\", \"theme analysis\""
argument-hint: "[period:<months>] [component:<name>] [status:<value>]"
---

# analyze

You help the user identify patterns and themes across RFEs — clusters of Feature Requests that address the same underlying capability and could be satisfied by a coordinated Feature set. This surfaces opportunities for combined engineering effort.

Read `../triage/references/rfe-jql-patterns.md` now. It contains the base JQL, verified status values, and field reference.

---

## Phase 1: Parse Arguments & Build Query

**Parse the arguments** provided by the user. Recognized arguments:

| Argument | Example | Effect |
|----------|---------|--------|
| `period:<months>` | `period:12` | Time window in months (default 18); converted to days |
| `component:<name>` | `component:ROSA` | Restrict to a single component |
| `status:<value>` | `status:Approved` | Restrict by workflow status |

**Defaults:**
- `period` = 18 months → 548 days
- No component filter (fetch all)
- No status filter (fetch all open RFEs; use `AND status not in ("Closed")`)

**Build the JQL:**

Start from the base query in `../triage/references/rfe-jql-patterns.md`:

```
project = RFE AND issuetype = "Feature Request"
```

Append clauses in this order:
1. Status: `AND status not in ("Closed")` (always, unless `status:` overrides it)
2. Time window: `AND (created >= -<days>d OR updated >= -<days>d)`
3. Component: `AND component = "<name>"` (if provided)

Order by: `ORDER BY component ASC, votes DESC`

Example for default run:
```
project = RFE AND issuetype = "Feature Request"
AND status not in ("Closed")
AND (created >= -548d OR updated >= -548d)
ORDER BY component ASC, votes DESC
```

---

## Phase 2: Fetch All Data

Run the search script with `--all` to paginate through every matching RFE:

```bash
uv run --with requests python3 <SKILL_BASE_DIR>/../triage/scripts/rfe-search.py \
  --jql "<BUILT JQL>" \
  --all
```

Where `<SKILL_BASE_DIR>` is the directory containing this SKILL.md file.

The script prints a summary header followed by one JSON object per line. Each object includes:
`key`, `summary`, `status`, `priority`, `votes`, `components`, `labels`, `created`, `updated`, `description`, `feature_links`, `coverage`

**If the total exceeds 500 results**, warn the user before proceeding:

```
Warning: This query matched <N> RFEs — analysis will take longer and results
may be harder to navigate. Consider narrowing with:
  component:<name>   to focus on one product area
  period:6           to shorten the time window
  status:Approved    to focus on highest-priority open RFEs

Proceed with full analysis? (y/n)
```

If the user declines, re-enter Phase 1 with updated filters.

---

## Phase 3: Analyze & Identify Themes

Read all JSONL output. Perform the following analysis:

### 3a. Group by component

For each distinct component value in the data, compute:
- **Count**: total RFEs in this component
- **Priority breakdown**: count of Critical / Major / Minor / Undefined
- **Vote total**: sum of all `votes` values
- **Coverage breakdown**: count of `none` (no Feature links) vs `partial` (has Feature links, treating `decomposed` the same as `partial` since the query excludes closed RFEs)

RFEs with multiple components should appear in each component's group. RFEs with no component go into an "Unassigned" group.

### 3b. Identify themes within each component

Within each component, cluster RFEs by shared capability. Use `summary` and `description` (truncated at 500 chars) to identify clusters.

**A theme** = 2 or more RFEs that address the same capability and could plausibly be satisfied by a single coordinated Feature (or small Feature set). Look for:
- Identical or near-identical capability requests (e.g., "auto-scaling" appears in 4 different RFEs)
- Complementary capabilities that form a coherent feature area (e.g., "node pool labels" + "node pool taints" → "node pool metadata management")
- Common customer pain points referenced across multiple RFEs

For each theme, record:
- **Theme name**: short capability label (3–6 words)
- **Constituent RFEs**: list of keys
- **Combined votes**: sum
- **Priority floor**: highest priority among members (Critical > Major > Minor > Undefined)
- **Coverage**: are any already partially addressed?
- **Rationale**: 1–2 sentence explanation of what these RFEs have in common

### 3c. Cross-component themes

After per-component analysis, look for themes that span multiple components — RFEs in different components that address the same capability from different product angles (e.g., "networking improvements" requested separately in ROSA, HyperShift, and MCE).

### 3d. High-value standalone RFEs

Identify RFEs that are **not** part of any theme but are individually significant:
- Vote count in the top 10% for their component
- Priority = Critical
- Already partially covered (has Feature links but still open)

---

## Phase 4: Present Report

Output a structured markdown report with the following sections:

---

### Component Breakdown

A summary table across all components:

```
| Component   | RFEs | Critical | Major | Minor | Total Votes | No Features | Has Features |
|-------------|------|----------|-------|-------|-------------|-------------|--------------|
| ROSA        |   42 |        5 |    18 |    19 |         287 |          28 |           14 |
| HyperShift  |   31 |        3 |    12 |    16 |         198 |          19 |           12 |
| ...         |      |          |       |       |             |             |              |
| **Total**   |  xxx |       xx |    xx |    xx |         xxx |         xxx |          xxx |
```

"No Features" = `coverage == "none"`. "Has Features" = `coverage == "partial"` or `"decomposed"` (both indicate Feature links exist; decomposed is not separately shown since the query excludes closed RFEs).

---

### Themes by Component

For each component with at least one theme, list themes in descending combined-vote order:

```
## ROSA

### Theme: Auto-scaling for managed clusters
**RFEs:** RFE-1234, RFE-5678, RFE-9012
**Combined votes:** 34  |  **Priority floor:** Critical  |  **Coverage:** none
**Rationale:** Three separate RFEs request dynamic node scaling based on workload metrics,
differing only in trigger mechanism (CPU, memory, custom metrics). A single Feature
covering the scaling framework would address all three.

### Theme: ...
```

---

### Cross-Component Themes

```
## Cross-Component: Observability & Metrics

**Components involved:** ROSA, HyperShift, MCE
**RFEs:** RFE-2345 (ROSA), RFE-6789 (HyperShift), RFE-3456 (MCE)
**Combined votes:** 52
**Rationale:** Each component independently requests custom metrics endpoints for cluster
health. A shared observability framework feature could address all three simultaneously.
```

---

### High-Value Standalone RFEs

```
| Key       | Component  | Priority | Votes | Coverage | Summary                          |
|-----------|------------|----------|-------|----------|----------------------------------|
| RFE-4567  | ROSA       | Critical |    18 | none     | FIPS-compliant key management    |
| RFE-8901  | HyperShift | Major    |    14 | partial  | Multi-tenant control plane auth  |
```

---

### Top Recommendations

Rank the top 5–10 opportunities by combined impact (votes × priority weight × cross-team factor):

```
1. **[ROSA] Auto-scaling for managed clusters** — 34 combined votes, Critical floor,
   3 RFEs ready to decompose. High-value, no existing coverage.

2. **[Cross-component] Observability & Metrics** — 52 combined votes across ROSA/HyperShift/MCE.
   Coordination opportunity for platform-wide Feature.

3. ...
```

---

## Phase 5: Follow-Up

After presenting the report, offer next steps:

```
What would you like to do next?
- Drill into a specific theme for more detail
- Run /rfe:decompose <KEY> to create Features for a specific RFE
- Re-run with different filters (e.g., period:6, component:ROSA)
- Export this report as a file
```

Use AskUserQuestion to present these options if the conversation is interactive.

---

## Error Handling

- **JIRA_API_TOKEN not set:** Tell the user: "Set `export JIRA_API_TOKEN=<your-PAT>` before running. Generate a PAT at https://redhat.atlassian.net/jira/secure/ViewProfile.jspa under Personal Access Tokens."
- **No results returned:** Report the JQL used and suggest relaxing filters (e.g., extend `period`, broaden `status`, remove `component` filter).
- **REST API 400 with status error:** The JQL uses a status name that doesn't exist in this project. Use `AND status not in ("Closed")` instead. See `../triage/references/rfe-jql-patterns.md` for verified status values.
- **REST API error (other):** Show the status code and response body, then ask whether to retry with modified parameters.
- **Script not found:** The search script lives at `../triage/scripts/rfe-search.py` relative to this skill directory. Confirm the path before running.
