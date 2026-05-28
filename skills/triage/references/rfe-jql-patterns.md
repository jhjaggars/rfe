# RFE JQL Patterns & Field Reference

## Base Query

Every `/rfe:triage` search starts from:

```
project = RFE AND issuetype = "Feature Request"
```

Append filter clauses and sort order before executing.

---

## RFE Project Status Values

These are the **actual** workflow statuses in the `RFE` project (verified 2026-03-02):

| Status | Category |
|--------|----------|
| `Approved` | Open |
| `Refinement` | Open |
| `Waiting` | Open |
| `Backlog` | Open |
| `Closed` | Terminal |

**Do not** use `New`, `In Progress`, `Under Consideration`, or `Triaged` — they do not exist in this project and will cause a 400 error.

To exclude terminal statuses, use `AND status not in ("Closed")` (simpler and future-proof against new open statuses being added).

---

## Pre-built JQL Patterns

### Open RFEs (default)

```
project = RFE AND issuetype = "Feature Request"
AND status not in ("Closed")
ORDER BY priority ASC, votes DESC, created DESC
```

### High-priority open RFEs

```
project = RFE AND issuetype = "Feature Request"
AND status not in ("Closed")
AND priority in (Critical, Major)
ORDER BY priority ASC, votes DESC
```

### Most-voted open RFEs

```
project = RFE AND issuetype = "Feature Request"
AND status not in ("Closed")
AND votes > 0
ORDER BY votes DESC, priority ASC
```

### Recent RFEs (created or updated in last 90 days)

```
project = RFE AND issuetype = "Feature Request"
AND (created >= -90d OR updated >= -90d)
ORDER BY updated DESC
```

### By component

```
project = RFE AND issuetype = "Feature Request"
AND component = "<COMPONENT-NAME>"
AND status not in ("Closed")
ORDER BY priority ASC, votes DESC
```

Replace `<COMPONENT-NAME>` with values like `ROSA`, `HyperShift`, `XCMSTRAT`, `MCE`, etc.

### By label

```
project = RFE AND issuetype = "Feature Request"
AND labels = "<LABEL>"
ORDER BY priority ASC, votes DESC
```

### Text search (summary and description)

```
project = RFE AND issuetype = "Feature Request"
AND text ~ "<KEYWORDS>"
ORDER BY priority ASC, votes DESC, created DESC
```

Use double quotes for multi-word phrases: `text ~ "managed cluster"`.

### Combined: high-priority + component + open

```
project = RFE AND issuetype = "Feature Request"
AND component = "<COMPONENT>"
AND priority in (Critical, Major)
AND status not in ("Closed")
ORDER BY votes DESC, created DESC
```

---

## Field Reference

| API field name | Description | Notes |
|----------------|-------------|-------|
| `summary` | Issue title / one-liner | Always present |
| `status` | Workflow state | Name values: `Approved`, `Refinement`, `Waiting`, `Backlog`, `Closed` |
| `priority` | Priority level | Values: `Critical`, `Major`, `Minor`, `Undefined` |
| `components` | Product components | Array of `{name}` objects |
| `labels` | Free-form tags | Array of strings |
| `votes` | Vote object | `votes.votes` = count; `votes.hasVoted` = current user |
| `created` | ISO-8601 creation timestamp | Slice `[:10]` for YYYY-MM-DD |
| `updated` | ISO-8601 last-updated timestamp | |
| `issuelinks` | Linked issue array | Each entry has `type.inward`, `type.outward`, `inwardIssue`, `outwardIssue` |
| `description` | Full body text (wiki markup) | May be `null`; truncate for display |

---

## acli Search Commands

```bash
# Paginate through all results
acli jira workitem search --jql "<JQL>" --json --paginate

# Cap at N results
acli jira workitem search --jql "<JQL>" --json --limit <N>

# Count only
acli jira workitem search --jql "<JQL>" --count
```

> **WARNING:** Do NOT use restricted fields in `--fields`. The `acli` tool has a strict allowlist and will fail with a "field not allowed" error. Rely on the default JSON output instead.

**View a single issue:**

```bash
acli jira workitem view <KEY> --json
acli jira workitem view <KEY> --fields '*all' --json   # include all available fields
```

**Response structure per issue:**

```json
{
  "key": "RFE-1234",
  "fields": {
    "summary": "...",
    "status": {"name": "New"},
    "priority": {"name": "Critical"},
    "components": [{"name": "ROSA"}],
    "labels": ["cloud-experience"],
    "votes": {"votes": 12, "hasVoted": false},
    "created": "2024-11-01T10:00:00.000+0000",
    "updated": "2025-01-15T14:30:00.000+0000",
    "issuelinks": [
      {
        "type": {"inward": "is implemented by", "outward": "implements"},
        "outwardIssue": {
          "key": "ROSA-456",
          "fields": {
            "summary": "...",
            "status": {"name": "In Progress"},
            "issuetype": {"name": "Feature"}
          }
        }
      }
    ],
    "description": "..."
  }
}
```
