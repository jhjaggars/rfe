# Red Hat Feature Definition Reference

A Feature is a **Level 4** issue in the Red Hat Jira hierarchy. It sits below Outcomes (L5) and above Epics (L3).

## What a Feature Is

**Official definition:** A capability or well-defined set of functionality that delivers business value. Describes *tangible pieces of value*, often delivered incrementally within a Release *to customers*. Focused on the "What" and the "Why" to Engineering — not the "How".

**Completion criteria:** A Feature is done when all dependent Epics have been delivered in a Release. Delivery creates the *ability for customers* to do something in the product more/better/differently.

**Scope:** Fits within a Release. Scoped to a single product/engineering area. Can span multiple teams and potentially multiple releases.

**Not:** a bucket for unrelated Epics. Not intended to cross multiple Releases.

## Required Elements for a Well-Defined Feature

Before creating a Feature, gather or ask for all of these:

1. **Feature Overview / Goal Summary** — an elevator pitch: what will this deliver to customers?
2. **Goals (expected user outcomes)** — the observable functionality the user gains; what they can now do that they couldn't before
3. **Requirements / Acceptance Criteria** — specific, testable conditions including non-functional requirements (security, reliability, performance, scalability). For each interface, note whether it is supported:
   - ROSA CLI, OCM CLI, OCM UI, Terraform, CAPI
   - FedRAMP supported?
   - Already supported in OCP? (if yes, what version?)
4. **Out of Scope** — explicit list of what this does NOT cover; prevents scope creep
5. **Target Release** — which release or milestone; Features must fit within a Release
6. **Background / Strategic Fit** — context explaining *why* this matters; link to source RFE or Outcome
7. **Customer Considerations** — anything specific to customer environments or migration
8. **Documentation Considerations** — what docs will be needed
9. **Interoperability Considerations** — which other products or versions are affected

Optional but useful:
- **Use Cases** — main success scenarios and alternative flows
- **Questions to Answer** — open refinement or architectural questions

## Project Routing

Features go in **product-specific strategy projects**. For HCM:

| Product area | Feature project |
|---|---|
| ROSA (OpenShift on AWS) | `ROSA` |
| ARO (Azure Red Hat OpenShift) | `ARO` |
| GCP HCP | `GCP` |
| Hybrid Cloud Console | `CRCPLAN` |
| OCP / OpenShift platform | `OCPSTRAT` or `XCMSTRAT` |
| Cross-functional / strategic | `XCMSTRAT` |
| Control Plane | `CNTRLPLANE` |

Features are **never** created in execution projects (OCM, SREP, OHSS, OCMUI, etc.).

## Required Custom Fields

```bash
--custom security="Red Hat Employee"   # Required for ALL issues
# Note: activity-type is NOT required for Features
```

To link a Feature to its parent Outcome:
```bash
--parent HCMSTRAT-123   # or OCPSTRAT-XXX, XCMSTRAT-XXX, etc.
```

## Feature Lifecycle

`New` → `Refinement` → `Backlog` → `In Progress` → `Closed`

Features start in `New` when the need is identified, move to `Refinement` when actively scoped with engineering, then `Backlog` when committed for a release.

## CRITICAL: Issue Creation Must Use REST API

**jira-cli corrupts wiki markup** when creating/updating issue descriptions. It converts `#` numbered list items to `h1.` headers, escapes hyphens and parentheses, and removes blank lines. **Always use the Python REST API for creating Features with formatted descriptions.**

```python
import os, requests

token = os.environ['JIRA_API_TOKEN']

payload = {
    "fields": {
        "project": {"key": "ROSA"},
        "summary": "Feature summary here",
        "description": "h1. Feature Overview\n\n...",  # Jira wiki markup
        "issuetype": {"name": "Feature"},
        "customfield_12310031": [{"value": "Red Hat Employee"}],  # security
    }
}

resp = requests.post(
    'https://issues.redhat.com/rest/api/2/issue',
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
    json=payload
)
print(resp.json()['key'])  # e.g., ROSA-456
```

**Linking** (jira-cli works fine for link operations):
```bash
jira issue link ROSA-456 OCPSTRAT-2666 "Implements"
```

## Official Feature Body Template (Jira Wiki Markup)

```
h1. Feature Overview (aka. Goal Summary)

[Elevator pitch: what significant capability will this provide to customers?]

h1. Goals (aka. expected user outcomes)

[The observable functionality the user now has as a result of this feature.]

h1. Requirements (aka. Acceptance Criteria)

[Specific, testable conditions the feature must deliver. Include non-functional requirements: security, reliability, performance, maintainability, scalability, usability.]

|| Supported Clients || Option ||
| Supported in ROSA CLI | ( ) Yes ( ) No ( ) N/A |
| Supported in OCM CLI | ( ) Yes ( ) No ( ) N/A |
| Supported in OCM UI | ( ) Yes ( ) No ( ) N/A |
| Supported in Terraform | ( ) Yes ( ) No ( ) N/A |
| Supported in CAPI | ( ) Yes ( ) No ( ) N/A |
|| Supported Offerings || Option ||
| FedRAMP supported? | ( ) Yes ( ) No ( ) N/A |
|| OCP Support || Option ||
| Already supported in OCP? | ( ) Yes ( ) No ( ) N/A |

h1. Use Cases (Optional)

[Main success scenarios and alternative flows.]

h1. Questions to Answer (Optional)

[Open refinement or architectural questions before coding can begin.]

h1. Out of Scope

[High-level list of items explicitly out of scope.]

h1. Background

[Additional context to frame the feature. Link to source RFE, Outcome, or strategy issue.]

h1. Customer Considerations

[Customer-specific considerations for design and delivery.]

h1. Documentation Considerations

[What documentation will be needed to meet customer needs.]

h1. Interoperability Considerations

[Which other projects and versions does this impact?]
```

## Single Feature vs. Multiple Features

Create **multiple** Features when:
- The source issue links to distinct RFEs solving different problems for different customer segments
- Different owning teams/projects would deliver different parts
- The scope is large enough that acceptance criteria would exceed 6–7 items
- Two pieces could reasonably ship in different releases or go to different projects

Create a **single** Feature when:
- The work is cohesive and one team/project owns it end-to-end
- Acceptance criteria are 2–4 clear items
- Splitting would create artificial dependencies
