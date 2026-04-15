---
name: duplicates
description: "Scan open RFEs for duplicates, cluster similar requests, and recommend which to close. Triggers on: /rfe:duplicates, \"find duplicate RFEs\", \"deduplicate RFEs\", \"identify duplicate feature requests\", \"which RFEs are duplicates\""
argument-hint: "[component:<name>] [status:<value>] [period:<months>] [limit:<n>]"
---

# duplicates

You scan open RFEs for duplicate or near-duplicate requests — multiple RFEs asking for the same capability — and recommend which to keep as the canonical issue and which to close as duplicates.

Read `../triage/references/rfe-jql-patterns.md` now. It contains the base JQL and verified status values.

---

## Phase 1: Parse Arguments & Build Query

**Parse the arguments** provided by the user. Recognized arguments:

| Argument | Example | Effect |
|----------|---------|--------|
| `component:<name>` | `component:ROSA` | Restrict to a single component |
| `status:<value>` | `status:Approved` | Restrict by workflow status |
| `period:<months>` | `period:24` | Only RFEs created/updated within this window (default: all time) |
| `limit:<n>` | `limit:200` | Cap the number of RFEs fetched (default: all) |

**If no filters are given**, ask the user using AskUserQuestion with up to 4 options:

- **By component** — focus duplicate search on one product area (recommended for large datasets)
- **High-priority only** — Critical and Major RFEs, any component
- **Most-voted only** — RFEs with >0 votes (noise-reduced set)
- **All open RFEs** — full scan (may be slow; warn if >300 results)

Build the JQL. Start from the base query:

```
project = RFE AND issuetype = "Feature Request" AND status not in ("Closed")
```

Append clauses based on arguments. Always sort `ORDER BY component ASC, summary ASC` so similar items are adjacent.

---

## Phase 2: Fetch Data

Run the search script with `--all` to paginate all results:

```bash
uv run --with requests python3 <SKILL_BASE_DIR>/../triage/scripts/rfe-search.py \
  --jql "<BUILT JQL>" \
  --all
```

Where `<SKILL_BASE_DIR>` is the directory containing this SKILL.md file.

If the total exceeds 500 RFEs, warn the user and suggest narrowing:

```
Warning: <N> RFEs matched. Duplicate analysis across a large set is slower
and may miss nuance. Recommend narrowing with:
  component:<name>   to focus on one product area
  period:18          to limit to the last 18 months
  status:Approved    to focus on highest-priority open RFEs

Proceed with full scan? (y/n)
```

---

## Phase 3: Cluster by Similarity

Group the fetched RFEs by component first. Within each component, read every issue's `summary` and the first 400 characters of `description`, then identify **duplicate clusters** — groups of 2 or more RFEs requesting the same underlying capability.

A duplicate cluster exists when:
- The summaries describe the same end-user capability (not just the same technology)
- The descriptions reveal the same pain point even if worded differently
- The requests would be satisfied by the same Feature

**Do not** cluster RFEs that are merely related (e.g., two different aspects of "storage" are not duplicates unless they request the exact same behavior).

For each cluster, determine the **canonical RFE** to keep:
1. Highest vote count (most customer signal)
2. If tied: oldest (first to file = most established)
3. If still tied: best description quality (most detail)

All other members of the cluster are **duplicate candidates** to close.

Also flag **near-duplicates** — pairs where you're not certain but similarity is high enough to warrant human review. Label these separately as "Possible Duplicate."

---

## Phase 4: Present Report

Display a structured report, component by component:

```
## Duplicate Analysis  —  <N> RFEs scanned, <C> components

Found <X> confirmed duplicate clusters and <Y> possible duplicate pairs.

---

### [ROSA]  <total RFEs in component>

#### Cluster 1: Auto-scaling triggers  (3 RFEs, 28 combined votes)
  KEEP   RFE-1234  18v  Critical  "Auto-scale managed clusters on CPU threshold"
  CLOSE  RFE-5678   7v  Major     "Scale nodes automatically based on workload"
  CLOSE  RFE-9012   3v  Minor     "Dynamic node scaling for OpenShift managed clusters"
  Rationale: All three request the same CPU-based auto-scaling behavior for managed cluster nodes.

#### Possible Duplicate: Memory vs CPU scaling  (2 RFEs)
  ?      RFE-2345  11v  Major     "Scale clusters on memory pressure"
  ?      RFE-3456   9v  Major     "Auto-scale on resource exhaustion"
  Rationale: Both involve resource-based scaling but may differ (memory vs any resource).
             Review before closing.

---

### [HyperShift]  ...

---

## Summary

| Action          | Count | Combined Votes |
|-----------------|-------|----------------|
| Confirmed CLOSE |    12 |             47 |
| Possible dup    |     6 |             34 |
| No action       |   180 |            --- |
```

---

## Phase 5: Confirm & Close

After presenting the report, ask the user:

```
What would you like to do?
- Review a specific cluster in more detail (enter cluster number or RFE key)
- Confirm all suggested closures
- Confirm closures one cluster at a time
- Export this report to a file
- Done (no changes)
```

Use AskUserQuestion to present these options.

**When the user confirms closures**, for each RFE to close:

**Step 1: Get available transitions**

```bash
uv run --with requests python3 - << 'EOF'
import sys; sys.path.insert(0, 'scripts')
import jira

for t in jira.get_transitions('<KEY>'):
    print(f"  {t['id']}  {t['name']}")
EOF
```

Find the transition ID for "Close" (or equivalent terminal transition).

**Step 2: Add a duplicate link**

```bash
uv run --with requests python3 - << 'EOF'
import sys; sys.path.insert(0, 'scripts')
import jira

jira.link_issues('Duplicate', '<DUPLICATE-KEY>', '<CANONICAL-KEY>')
print("Linked: <DUPLICATE-KEY> duplicates <CANONICAL-KEY>")
EOF
```

**Step 3: Add a comment before closing**

```bash
uv run --with requests python3 - << 'EOF'
import sys; sys.path.insert(0, 'scripts')
import jira

canonical = '<CANONICAL-KEY>'
jira.add_comment('<DUPLICATE-KEY>', f"Closing as duplicate of {canonical}, which has higher vote count and represents the same capability request. Customer signal is consolidated there.")
print("Comment added")
EOF
```

**Step 4: Transition to Closed**

```bash
uv run --with requests python3 - << 'EOF'
import sys; sys.path.insert(0, 'scripts')
import jira

jira.transition_issue('<DUPLICATE-KEY>', '<TRANSITION-ID>')
print("Closed: <DUPLICATE-KEY>")
EOF
```

After all closures, print a final summary:

```
Closed <N> duplicate RFEs. Canonical issues retained:
  RFE-1234  (was head of 3-RFE cluster)
  ...
```

---

## Error Handling

- **JIRA_API_TOKEN or JIRA_USER not set:** Tell the user: "Set `export JIRA_API_TOKEN=<your-token>` and `export JIRA_USER=<your-email>` before running, or run `/rfe:init`."
- **Transition not found:** List all available transitions and ask the user which to use.
- **No duplicates found:** Report the scan scope and note that the dataset appears deduplicated.
- **Link type "Duplicate" rejected:** Try `"Duplicates"` or `"is duplicate of"` — link type names vary by instance. Fetch available types from `GET /rest/api/3/issueLinkType` if needed.
