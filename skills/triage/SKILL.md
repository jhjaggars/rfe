---
name: triage
description: "Browse and discover RFEs (Feature Requests) in JIRA, classify them by Feature coverage, and select one to hand off to /rfe:decompose. Triggers on: /rfe:triage, \"triage RFEs\", \"browse RFEs\", \"find RFEs\", \"discover feature requests\", \"show open RFEs\", \"which RFEs need features\""
argument-hint: "[status:<value>] [component:<name>] [priority:<level>] [label:<tag>] [text:<keywords>] [limit:<n>]"
---

# triage

You help the user discover RFEs (Feature Requests) in the RFE project, understand which ones already have Features linked, and identify the best candidates to decompose into well-defined Features.

Read `references/rfe-jql-patterns.md` now. It contains the base JQL, field names, and pre-built query patterns.

---

## Phase 1: Parse Filters & Build Query

**Parse the arguments** provided by the user. Recognized filters:

| Filter | Example | JQL clause added |
|--------|---------|-----------------|
| `status:<value>` | `status:New` | `AND status = "New"` |
| `component:<name>` | `component:ROSA` | `AND component = "ROSA"` |
| `priority:<level>` | `priority:Critical` | `AND priority = Critical` |
| `label:<tag>` | `label:cloud-experience` | `AND labels = "cloud-experience"` |
| `text:<keywords>` | `text:"managed cluster"` | `AND text ~ "managed cluster"` |
| `limit:<n>` | `limit:20` | `maxResults=<n>` (default 25) |

**If no filters are provided**, ask the user what they're looking for using AskUserQuestion. Offer exactly **4** quick-starts (the tool enforces a maximum of 4 options):

- **High priority** — Critical and Major RFEs not yet Closed
- **Most voted** — RFEs with the most votes (proxy for customer demand)
- **Recent** — RFEs created or updated in the last 90 days
- **By keyword or component** — search by text keywords or a specific product area

Build the final JQL. Start from the base query in `references/rfe-jql-patterns.md` and append filter clauses. Use the sort order appropriate to the selected quick-start or default to `ORDER BY priority ASC, votes DESC, created DESC`.

---

## Phase 2: Search & Classify

**Search JIRA** using the reusable script at `scripts/rfe-search.py` within this skill's base directory:

```bash
Run the appropriate `acli jira workitem` command (e.g. `acli jira workitem search --jql \"<BUILT JQL>\" --json`) directly to fetch data.

> **WARNING:** Do NOT use restricted fields (like `components`, `created`, `updated`, `parent`, etc.) in the `--fields` argument. The `acli` tool has a strict allowlist and will fail with a "field not allowed" error. Rely on the default JSON output instead.

The script prints a summary header line followed by one JSON object per issue. Classify each RFE by its `coverage` field:

| Coverage | Meaning |
|----------|---------|
| `none` | No Features linked — actionable candidate |
| `partial` | Has Feature links but RFE still open — may need more Features |
| `decomposed` | Has Feature links and RFE is closed — likely fully addressed |

---

## Phase 3: Present & Select

**Display results** as a table. Highlight actionable candidates (coverage = `none`).

```
Found <N> RFEs  (showing <shown>, <total> total matches)

  KEY           PRIORITY   VOTES  STATUS        FEATURES  COMPONENTS        SUMMARY
  ──────────────────────────────────────────────────────────────────────────────────────
★ RFE-1234      Critical      12  Approved      none      ROSA              Managed cluster auto-scaling
  RFE-5678      Major          7  Refinement    partial   XCMSTRAT          Cross-cluster networking
★ RFE-9012      Minor          2  Backlog       none      HyperShift        Node pool tainting support
  ...

★ = no linked Features (actionable)
```

**Then prompt the user** (using AskUserQuestion or text + follow-up):

- Enter an RFE key to see full details and readiness assessment
- Enter new filters to refine and search again
- Or type `done` to exit

**When user selects an RFE for drill-down**, fetch its full details:

```bash
Run `acli jira workitem view <KEY> --json` (or appropriate acli command) and parse the JSON output directly.
```

**Assess readiness** for Feature creation. Report on:

- **Description quality**: Is there enough context to draft acceptance criteria? (Good / Partial / Sparse)
- **Scope clarity**: Is the scope well-bounded, or does it cover multiple independent concerns?
- **Existing coverage**: Are any linked Features already addressing part of this?
- **Recommendation**: Ready to decompose / Needs clarification / Already covered

**Handoff**: When the user is ready to create Features from an RFE, tell them:

```
To create Features from this RFE, run:

  /rfe:decompose <KEY>
```

---

## Error Handling

- **JIRA_API_TOKEN or JIRA_USER not set:** Tell the user: "Set `export JIRA_API_TOKEN=<your-token>` and `export JIRA_USER=<your-email>` before running, or run `/rfe:init`."
- **No results returned:** Report the JQL used and suggest relaxing filters (e.g., drop `priority`, broaden `status`, remove `text` filter).
- **REST API 400 with "value does not exist for field 'status'":** The JQL contains a status name that doesn't exist in this project. Use `AND status not in ("Closed")` instead of listing open statuses explicitly. See `references/rfe-jql-patterns.md` for the verified status values.
- **REST API error (other):** Show the status code and response body, then ask whether to retry with modified parameters.
