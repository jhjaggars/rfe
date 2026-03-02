---
name: feature-create-from
description: Create well-defined JIRA Feature issues from a strategy-level source issue (RFE, Outcome, OCPSTRAT, or any issue with linked RFEs). Triggers on: /feature-create-from, "create features from RFE", "decompose outcome into features", "create features from OCPSTRAT"
argument-hint: <JIRA-KEY>
---

# rfe-to-features

You take a strategy-level JIRA issue — an RFE, Outcome, OCPSTRAT issue, or similar — gather deep context from it and all its linked issues, ask targeted interview questions to fill gaps, then create well-defined Feature issues in the appropriate JIRA project.

Read `references/feature-definition.md` now. It defines what a Feature must contain, the official body template, project routing rules, and the critical requirement to use the REST API (not jira-cli) for issue creation.

---

## Phase 1: Gather Context

**Step 1: Fetch the source issue.**

```bash
jira issue view <KEY> --raw | python3 -c "
import sys, json
d = json.load(sys.stdin)
f = d['fields']
print('Summary:', f.get('summary'))
print('Type:', f['issuetype']['name'])
print('Status:', f['status']['name'])
print('Description:', (f.get('description') or '')[:2000])
print()
print('Issue Links:')
for link in f.get('issuelinks', []):
    inward = link.get('inwardIssue')
    outward = link.get('outwardIssue')
    if inward:
        print(f'  [{link[\"type\"][\"inward\"]}] {inward[\"key\"]}: {inward[\"fields\"][\"summary\"]}')
    if outward:
        print(f'  [{link[\"type\"][\"outward\"]}] {outward[\"key\"]}: {outward[\"fields\"][\"summary\"]}')
"
```

**Step 2: Fetch linked issues.**

Parse all linked issue keys from the output above. Fetch each one, prioritizing:
1. Parent issues (blocks, is blocked by, parent link)
2. RFE-type issues (Feature Request, RFE, Requirement)
3. Related issues

Cap at 10 linked issues. For each:

```bash
jira issue view <LINKED-KEY> --raw | python3 -c "
import sys, json
d = json.load(sys.stdin)
f = d['fields']
print('Key:', d['key'])
print('Summary:', f.get('summary'))
print('Type:', f['issuetype']['name'])
print('Status:', f['status']['name'])
print('Description:', (f.get('description') or '')[:1500])
"
```

**Step 3: Synthesize context.**

Organize what you've learned against the 9 required Feature elements from `references/feature-definition.md`:

- Feature Overview / Goal Summary: [known / partial / unknown]
- Goals / expected user outcomes: [known / partial / unknown]
- Requirements / Acceptance Criteria: [known / partial / unknown]
- Out of Scope: [known / partial / unknown]
- Target Release: [known / partial / unknown]
- Background / Strategic Fit: [known / partial / unknown]
- Customer Considerations: [known / partial / unknown]
- Documentation Considerations: [known / partial / unknown]
- Interoperability Considerations: [known / partial / unknown]

Also note:
- How many distinct Features should be created? (separate RFEs → separate Features)
- Which JIRA project(s) should own each Feature? (see project routing in reference doc)

---

## Phase 2: Generate & Ask Interview Questions

Compare your synthesis against the required Feature elements. Identify the most important gaps — things that would make the Feature incomplete or unactionable without answers.

Generate questions that target those gaps. Pre-fill partial answers from context where possible. Do not ask about things that are already clearly answered by the gathered context.

Ask up to 4 questions using AskUserQuestion, then ask a 5th separately if needed (the tool accepts max 4 at once).

Good question framing:
- "The source issue mentions X but doesn't clarify Y — what should the acceptance criteria be for Z?"
- "Should this be one Feature or two? The RFE covers both A and B, which seem separable."
- "Which project should own this — ROSA or XCMSTRAT? (The issue involves cross-cutting concerns.)"
- "What is the target release for this work? The source issue doesn't specify."

Poor question framing (avoid):
- Asking about things already stated clearly in the gathered context
- Generic questions that don't reflect the specific issue content
- More than one question about the same topic

---

## Phase 3: Draft Features

Using all gathered context plus the interview answers, draft each Feature.

Apply the official template from `references/feature-definition.md`. Fill every section with real content — no placeholders. If a section is explicitly not applicable, say so briefly.

Present the draft(s) to the user:

```
## Draft: [Feature Title]
**Project:** [ROSA / XCMSTRAT / etc.]
**Summary:** [one-line title]

[Full body in Jira wiki markup]
```

Ask the user to confirm or request revisions before proceeding to creation. Do not create until approved.

---

## Phase 4: Create in JIRA

**CRITICAL:** Use the Python REST API for creation — jira-cli corrupts wiki markup formatting (converts numbered lists to headers, escapes hyphens). See `references/feature-definition.md` for the exact pattern.

For each approved Feature:

**Step 1: Create via REST API**

```python
import os, requests

token = os.environ['JIRA_API_TOKEN']

payload = {
    "fields": {
        "project": {"key": "<PROJECT>"},
        "summary": "<SUMMARY>",
        "description": """<WIKI MARKUP BODY>""",
        "issuetype": {"name": "Feature"},
        "customfield_12310031": [{"value": "Red Hat Employee"}],
    }
}

resp = requests.post(
    'https://issues.redhat.com/rest/api/2/issue',
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
    json=payload
)

if resp.ok:
    key = resp.json()['key']
    print(f"Created: {key}")
else:
    print(f"Error {resp.status_code}: {resp.text}")
```

**Step 2: Link to source issue**

```bash
jira issue link <NEW-KEY> <SOURCE-KEY> "Implements"
```

**Step 3: Link to parent Outcome (if known)**

```bash
jira issue link <NEW-KEY> <OUTCOME-KEY> "is implemented by"
```

**Step 4: Report results**

```
## Created Features

| Key | Summary | Project | Link |
|-----|---------|---------|------|
| ROSA-456 | ... | ROSA | https://issues.redhat.com/browse/ROSA-456 |

Links created:
- ROSA-456 Implements OCPSTRAT-2666
```

---

## Error Handling

- **JIRA_API_TOKEN not set:** Tell the user: "Set `export JIRA_API_TOKEN=<your-PAT>` before running. Generate a PAT at https://issues.redhat.com/secure/ViewProfile.jspa under Personal Access Tokens."
- **Project routing unclear:** Ask the user which project to use rather than guessing.
- **REST API 400 / field errors:** Show the error and ask the user whether to retry with modified fields or proceed manually.
- **Issue not found:** Report the key that failed and continue with the others.
