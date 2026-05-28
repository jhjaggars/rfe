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
| `status` | Workflow state | Name values: `New`, `In Progress`, `Under Consideration`, `Triaged`, `Closed`, `Won't Fix` |
| `priority` | Priority level | Values: `Critical`, `Major`, `Minor`, `Undefined` |
| `components` | Product components | Array of `{name}` objects |
| `labels` | Free-form tags | Array of strings |
| `votes` | Vote object | `votes.votes` = count; `votes.hasVoted` = current user |
| `created` | ISO-8601 creation timestamp | Slice `[:10]` for YYYY-MM-DD |
| `updated` | ISO-8601 last-updated timestamp | |
| `issuelinks` | Linked issue array | Each entry has `type.inward`, `type.outward`, `inwardIssue`, `outwardIssue` |
| `description` | Full body text (wiki markup) | May be `null`; truncate for display |

---

## REST API Search Endpoint

```
GET $JIRA_URL/rest/api/3/search
```

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `jql` | string | URL-encoded JQL query |
| `maxResults` | int | Max issues to return (default 50, cap 100) |
| `startAt` | int | Pagination offset (default 0) |
| `fields` | comma-list | Fields to return; controls response size |

**Recommended `fields` value for `/rfe:triage`:**

```
summary,status,priority,components,labels,votes,created,updated,issuelinks,description
```

**Authentication:** Basic auth using `$JIRA_USER` (email) and `$JIRA_API_TOKEN`.

```bash
Run `acli jira workitem view <KEY> --json` (or appropriate acli command) and parse the JSON output directly.
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
