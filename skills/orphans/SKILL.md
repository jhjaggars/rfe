---
name: orphans
description: "Find open RFEs where the requested functionality already exists in the product (shipped but unlinked), and suggest closing them. Triggers on: /rfe:orphans, \"find orphan RFEs\", \"find shipped RFEs\", \"RFEs already done\", \"unlinked done RFEs\", \"orphaned feature requests\""
argument-hint: "[component:<name>] [period:<months>] [status:<value>]"
---

# orphans

You identify "orphan" RFEs — open feature requests that describe functionality already delivered in the product but never linked or closed. These are RFEs that should be closed as "Done" or "Won't Fix / Already Exists" rather than decomposed into new Features.

Read `../triage/references/rfe-jql-patterns.md` now. It contains the base JQL and verified status values.

---

## Phase 1: Parse Arguments & Build Query

**Parse the arguments** provided by the user. Recognized arguments:

| Argument | Example | Effect |
|----------|---------|--------|
| `component:<name>` | `component:ROSA` | Restrict to a single component |
| `period:<months>` | `period:24` | RFEs created/updated within this window (default 36 months) |
| `status:<value>` | `status:Backlog` | Restrict by workflow status |

**If no filters are given**, ask the user using AskUserQuestion with up to 4 options:

- **By component** — focus orphan search on one product area (recommended)
- **Oldest uncovered RFEs** — RFEs with no Feature links, sorted by age (oldest most likely to be orphaned)
- **Low-vote uncovered RFEs** — zero-vote RFEs with no Feature links (least customer traction, easiest to close)
- **All uncovered open RFEs** — full scan (may be large)

Build the JQL. Start from the base query and always restrict to uncovered RFEs. Coverage is derived in post-processing (by checking `issuelinks` for Feature-type links) rather than in JQL, since JQL cannot filter on derived fields:

```
project = RFE AND issuetype = "Feature Request"
AND status not in ("Closed")
AND (created >= -<days>d OR updated >= -<days>d)
```

Sort by `ORDER BY created ASC` (oldest first — these are most likely shipped).

---

## Phase 2: Fetch RFEs

Fetch RFEs using `acli`:

```bash
acli jira workitem search --jql "<BUILT JQL>" --json --paginate
```

> **WARNING:** Do NOT use restricted fields (like `components`, `created`, `updated`, `parent`, etc.) in the `--fields` argument. The `acli` tool has a strict allowlist and will fail with a "field not allowed" error. Rely on the default JSON output instead.

**Post-filter**: Keep only RFEs where `issuelinks` contains no Feature-type linked issues (coverage = `none`). RFEs with Feature links are tracked and not orphans.

If more than 400 RFEs remain, warn and suggest narrowing before proceeding.

---

## Phase 3: Search for Shipped Functionality

For each RFE (or in batches), extract 2–4 keyword phrases from the `summary` and first 300 characters of `description`. Then search the strategy and delivery projects for **closed or Done** Features that match.

**Search each component's strategy project** (infer from component name — e.g., ROSA → ROSA or XCMSTRAT; HyperShift → OCPSTRAT; MCE → CNTRLPLANE):

```bash
acli jira workitem search --jql 'project = <PROJ> AND issuetype = Feature AND status in (Done, Closed) AND text ~ "<keywords>"' --json
```

Run this for each uncovered RFE. Batch where possible (process all RFEs in a component together before moving to the next component, reusing the same project search).

**Rate limiting:** Pause 50ms between requests. Batch JIRA text searches in groups of 10–20 RFEs before re-querying.

---

## Phase 4: Score & Classify Each RFE

For each RFE, evaluate the search results and classify:

| Classification | Criteria | Recommended Action |
|---------------|----------|--------------------|
| **Shipped** | Found a Done/Closed Feature with high confidence match (same capability, plausible version) | Close as Done; link to the Feature |
| **Likely Shipped** | Found a partial or probable match; capability may exist but less certain | Flag for human review; suggest closing |
| **Possibly Orphaned** | RFE is old (>2 years), zero votes, no description detail — may have shipped incidentally | Flag for human review; suggest closing |
| **Active** | No evidence of shipping; skip | Do not recommend closing |

Use your judgment on "high confidence match." High confidence = the Feature summary describes essentially the same end-user capability as the RFE, and the Feature is in Done/Closed/Released status.

---

## Phase 5: Present Report

Display results grouped by component:

```
## Orphan RFE Analysis  —  <N> uncovered open RFEs scanned

Found <S> shipped, <L> likely shipped, <P> possibly orphaned.

---

### [ROSA]

#### Shipped — close recommended

  RFE-1234  12v  2023-03-15  "Cluster-level audit log export to S3"
    → ROSA-789 (Done, 4.14): "Audit log forwarding to S3-compatible storage"
    → Confidence: High (same capability, same storage target)

  RFE-5678   0v  2022-11-02  "Custom OIDC provider support for ROSA clusters"
    → ROSA-456 (Released, 4.13): "BYOIDC support for ROSA"
    → Confidence: High

#### Likely Shipped — review recommended

  RFE-9012   3v  2023-08-20  "Granular RBAC for cluster admin delegation"
    → OCPSTRAT-1122 (Done): "Delegated admin access controls"
    → Confidence: Partial (admin delegation matches; granularity unclear)

#### Possibly Orphaned — review recommended

  RFE-3456   0v  2021-06-10  "Support for <feature with no description>"
    → No matches found but RFE is 3+ years old with 0 votes and no description
    → May have shipped incidentally or may never have been actionable

---

### [HyperShift]
...

---

## Summary

| Classification   | Count | Combined Votes |
|------------------|-------|----------------|
| Shipped          |     8 |             47 |
| Likely Shipped   |     5 |             12 |
| Possibly Orphaned|     9 |              0 |
| Active (no match)|   130 |            --- |
```

---

## Phase 6: Confirm & Close

Ask the user how to proceed using AskUserQuestion with up to 4 options:

- **Close all Shipped** — immediately close confirmed matches
- **Review one by one** — step through each candidate interactively
- **Export report** — save to `reports/orphans-<date>.md`
- **Done** — take no action

**When closing an RFE as shipped**, for each:

**Step 1: Add a link to the shipping Feature**

```bash
acli jira workitem link create --out <RFE-KEY> --in <FEATURE-KEY> --type "Implements" --yes
```

**Step 2: Add a comment**

```bash
acli jira workitem comment create --key <RFE-KEY> --body "Closing — functionality delivered in <FEATURE-KEY>. See that issue for details."
```

**Step 3: Close the RFE**

```bash
acli jira workitem transition --key <RFE-KEY> --status "Closed" --yes
```

Print a final closure summary when done.

---

## Error Handling

- **JIRA_API_TOKEN or JIRA_USER not set:** Tell the user: "Set `export JIRA_API_TOKEN=<your-token>` and `export JIRA_USER=<your-email>` before running, or run `/rfe:init`."
- **Transition requires resolution field:** Try adding `"fields": {"resolution": {"name": "Done"}}` to the transition payload.
- **No orphans found:** Report the scan scope. If no shipped matches were found, the component's RFEs may genuinely be undelivered — this is useful signal too.
- **Too many RFEs to search individually:** Prioritize the oldest and lowest-vote RFEs for orphan checking; skip RFEs with >5 votes (high-vote RFEs are unlikely to have shipped without notice).
