---
name: report
description: "Generate a prioritization report across all open RFEs, categorized by component, priority, coverage, and votes. Triggers on: /rfe:report, \"RFE report\", \"prioritization report\", \"RFE summary\", \"RFE prioritization\""
argument-hint: "[component:<name>] [status:<value>] [output:<path>]"
---

# report

You generate a comprehensive RFE prioritization report that categorizes all open Feature Requests by component, priority, coverage status, and community votes — then recommends where to focus effort.

Read `../triage/references/rfe-jql-patterns.md` now. It contains the base JQL, verified status values, and field reference.

---

## Phase 1: Parse Arguments & Build Query

**Parse the arguments** provided by the user. Recognized arguments:

| Argument | Example | Effect |
|----------|---------|--------|
| `component:<name>` | `component:ROSA` | Restrict to a single component |
| `status:<value>` | `status:Approved` | Restrict by workflow status |
| `output:<path>` | `output:reports/q2-report.md` | Output file path |

**Defaults:**
- No component filter (all components)
- All open statuses: `AND status not in ("Closed")`
- Output: `reports/rfe-prioritization-<YYYY-MM-DD>.md`

**Build the JQL:**

Start from the base query:

```
project = RFE AND issuetype = "Feature Request"
```

Append clauses:
1. Status: `AND status not in ("Closed")` (always, unless `status:` overrides)
2. Component: `AND component = "<name>"` (if provided)

Order by: `ORDER BY priority ASC, votes DESC, created DESC`

---

## Phase 2: Fetch & Generate

Fetch all matching RFEs using `acli`:

```bash
acli jira workitem search --jql "<BUILT JQL>" --json --paginate
```

> **WARNING:** Do NOT use restricted fields (like `components`, `created`, `updated`, `parent`, etc.) in the `--fields` argument. The `acli` tool has a strict allowlist and will fail with a "field not allowed" error. Rely on the default JSON output instead.

Parse the JSON output, then:
1. Classify each RFE by Feature coverage (examine `issuelinks` for Feature-type links: `none` / `partial`)
2. Compute composite scores (priority weight × 10 + votes + recency bonus)
3. Generate a full markdown report with these sections:
   - Executive Summary
   - Status / Priority / Coverage breakdowns
   - Top 30 components by composite score
   - Top 50 individual RFEs by composite score
   - Blocker/Critical RFEs with no Feature coverage
   - High-voted RFEs (10+) with no coverage
   - Undefined-priority RFEs needing triage
   - Stale RFE closure candidates (2+ years, no votes, no coverage)
   - Recommended prioritization actions

---

## Phase 3: Present Results

After the report generates, read it and present a concise summary to the user:

1. **Key numbers** — total RFEs, % uncovered, Blocker/Critical count, stale count
2. **Top 5 component areas** by urgency
3. **Top 5 individual RFEs** by composite score
4. **Recommended actions** (from the report's recommendations section)
5. **File location** — where the full report was saved

Then offer next steps:

```
What would you like to do next?
- Drill into a specific component area
- Run /rfe:triage to browse individual RFEs
- Run /rfe:decompose <KEY> to create Features for a high-priority RFE
- Run /rfe:analyze to identify themes across RFEs
- Re-run with filters (e.g., component:ROSA)
```

---

## Error Handling

- **JIRA_API_TOKEN or JIRA_USER not set:** Tell the user: "Set `export JIRA_API_TOKEN=<your-token>` and `export JIRA_USER=<your-email>` before running, or run `/rfe:init`."
- **No results returned:** Report the JQL used and suggest relaxing filters.
- **acli error:** Show the error message and response body, then ask whether to retry with modified parameters.
