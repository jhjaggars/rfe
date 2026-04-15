# Red Hat Feature Definition Reference

A Feature is a **Level 4** issue in the Red Hat Jira hierarchy. It sits below Outcomes (L5) and above Epics (L3).

## What a Feature Is

**Official definition:** A capability or well-defined set of functionality that delivers business value. Describes *tangible pieces of value*, often delivered incrementally within a Release *to customers*. Focused on the "What" and the "Why" to Engineering — not the "How".

**Completion criteria:** A Feature is done when all dependent Epics have been delivered in a Release. Delivery creates the *ability for customers* to do something in the product more/better/differently.

**Scope:** Fits within a Release. Scoped to a single product/engineering area. Can span multiple teams. Contains 3–8 Epics.

**Not:** a bucket for unrelated Epics. Not a single-Epic effort. Not intended to cross multiple Releases.

## Required Elements for a Well-Defined Feature

Before creating a Feature, gather or ask for all of these:

1. **Market Problem** — who is affected, what pain they experience, why solving this matters now, what happens if we don't
2. **Proposed Solution** — the capability being delivered (high level)
3. **Strategic Value** — quantified customer value, business impact, competitive advantage, strategic alignment
4. **Success Criteria** — measurable adoption, usage, outcome, and business metrics (not just "feature is done")
5. **Requirements / Acceptance Criteria** — specific, testable conditions including non-functional requirements. For each interface, note whether it is supported: ROSA CLI, OCM CLI, OCM UI, Terraform, CAPI, FedRAMP, OCP version
6. **Planned Epics** — 3–8 major work streams that will deliver this feature
7. **Out of Scope** — explicit list of what this does NOT cover
8. **Target Release / Timeline** — which release; milestones per quarter
9. **Background** — context explaining *why* this matters; link to source RFE or Outcome
10. **Customer Considerations** — anything specific to customer environments or migration
11. **Documentation Considerations** — what docs will be needed
12. **Interoperability Considerations** — which other products or versions are affected

Optional but useful:
- **Dependencies** — linked issues that must be delivered first
- **Risks and Mitigation** — known risks and planned mitigations
- **Use Cases** — main success scenarios and alternative flows

## Project Routing

Features go in **product-specific strategy projects**. See `artifact-hierarchy.md` for full routing logic.

| Product area | Feature project |
|---|---|
| OCP platform tools (oc-mirror, OLM, installer, oc) | `OCPSTRAT` |
| ROSA (OpenShift on AWS) | `ROSA` |
| ARO (Azure Red Hat OpenShift) | `ARO` |
| GCP HCP | `GCP` |
| Hybrid Cloud Console | `CRCPLAN` |
| Cross-cluster management strategy | `XCMSTRAT` |
| Control Plane (HyperShift) | `CNTRLPLANE` |

Features are **never** created in execution projects (OCM, SREP, OHSS, OCMUI, CLID, etc.).

## Required Custom Fields

```python
# In the REST API additional_fields dict:
"customfield_12310031": [{"value": "Red Hat Employee"}]  # Security — REQUIRED for ALL issues
"labels": ["ai-generated-jira"]                           # REQUIRED for all AI-created issues
```

### Parent Linking (use these to establish hierarchy)

| Link | Field | Type | Usage |
|------|-------|------|-------|
| Feature → Outcome (parent) | `customfield_12313140` | String (issue key) | Set when Outcome is known |
| Epic → Feature (parent) | `customfield_12313140` | String (issue key) | Set when creating child Epics |
| Story/Task → Epic | `customfield_12311140` | String (issue key) | Epic Link |
| Epic Name | `customfield_12311141` | String | Required when creating Epics; must match summary |
| Target Version | `customfield_12319940` | Array of `{"id": "<version_id>"}` | Set target release |

## Feature Lifecycle

`New` → `Refinement` → `Backlog` → `In Progress` → `Closed`

Features start in `New` when the need is identified, move to `Refinement` when actively scoped with engineering, then `Backlog` when committed for a release.

## CRITICAL: Issue Creation Must Use REST API (not jira-cli)

**jira-cli corrupts wiki markup** when creating/updating issue descriptions. It converts `#` numbered list items to `h1.` headers, escapes hyphens and parentheses, and removes blank lines. **Always use the Python REST API for creating Features with formatted descriptions.** See `wiki-markup.md` for formatting syntax.

```python
uv run --with requests python3 - << 'EOF'
import sys; sys.path.insert(0, 'scripts')
import jira

key = jira.create_issue({
    "project": {"key": "OCPSTRAT"},
    "summary": "Feature summary here",
    "description": "h2. Market Problem\n\n...",  # Jira wiki markup — use h2. for sections
    "issuetype": {"name": "Feature"},
    "customfield_12310031": [{"value": "Red Hat Employee"}],  # security
    "labels": ["ai-generated-jira"],
})
print(f"Created: {key}")
print(f"URL: {jira.browse_url(key)}")
EOF
```

### Linking a Feature to its parent Outcome

```python
uv run --with requests python3 - << 'EOF'
import sys; sys.path.insert(0, 'scripts')
import jira

jira.link_issues('Implements', '<FEATURE-KEY>', '<OUTCOME-KEY>')
print("Link created")
EOF
```

## Official Feature Body Template (Jira Wiki Markup)

Use `h2.` for major sections, `h3.` for sub-sections. Do not use Markdown formatting.

```
<Brief one-paragraph overview of the feature and what it delivers.>

h2. Market Problem

<Who is affected by this problem, what pain they experience today, why solving it matters now, and what happens if we don't solve it.>

h2. Proposed Solution

<The capability being delivered — high level description of what oc-mirror / the product will do differently.>

h2. Strategic Value

h3. Customer Value
* <Quantified benefit — e.g. "60% reduction in X", "eliminates manual Y">
* <Quantified benefit>

h3. Business Impact
* <Revenue, cost reduction, competitive impact>
* <Customer retention or deal impact>

h3. Strategic Alignment
<How this supports product/company strategy and roadmap.>

h2. Success Criteria

h3. Adoption
* <Adoption metric with specific target — e.g. "50% of affected customers adopt within 6 months">

h3. Outcomes
* <Customer outcome metric — e.g. "40% reduction in support tickets for X">

h3. Business
* <Business metric — e.g. "Closes N blocked deals">

h2. Requirements (aka. Acceptance Criteria)

<Specific, testable conditions the feature must deliver. Include non-functional requirements: security, reliability, performance, maintainability, scalability, usability.>

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

h2. Scope

h3. Planned Epics
* Epic 1: <name and brief description>
* Epic 2: <name and brief description>
* Epic 3: <name and brief description>

h3. Out of Scope
* <Related work explicitly excluded from this Feature>

h2. Timeline

* Total duration: <timeframe>
* Target GA: <release / quarter>

h3. Milestones
* Q1 <Year> (<release>): <major deliverable>
* Q2 <Year> (<release>): <major deliverable>

h2. Background

<Additional context to frame the feature. Link to source RFE, Outcome, or strategy issue. Explain the history and why this is being worked now.>

h2. Customer Considerations

<Customer-specific considerations for design and delivery — migration paths, existing tooling impact, regulated environment concerns.>

h2. Documentation Considerations

<What documentation will be needed to meet customer needs.>

h2. Interoperability Considerations

<Which other projects and versions does this impact? What interoperability test scenarios should be factored in?>

h2. Dependencies (if any)

* [PROJ-XXX] - <what this depends on and why>

h2. Risks (if any)

* <Risk description> — Mitigation: <planned mitigation>
```

## Single Feature vs. Multiple Features

Create **multiple** Features when:
- The source issue links to distinct RFEs solving different problems for different customer segments
- Different owning teams/projects would deliver different parts
- The scope contains more than 8 Epics across distinct capability areas
- Two pieces could reasonably ship in different releases

Create a **single** Feature when:
- The work is cohesive and one team/project owns it end-to-end
- The Epic breakdown is 3–5 clear items
- Splitting would create artificial dependencies
