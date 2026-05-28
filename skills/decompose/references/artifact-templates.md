# Artifact Body Templates (Jira Wiki Markup)

Templates for Initiative and Outcome issue descriptions. For the Feature template, see `feature-definition.md`. For wiki markup syntax, see `wiki-markup.md`.

All text in `[brackets]` is guidance — replace with real content. Be concise; less detail is preferred over placeholder-heavy descriptions.

**CRITICAL:** Always use `acli jira workitem create --from-json` for issue creation. Descriptions must be in ADF (Atlassian Document Format), not wiki markup. See `feature-definition.md` for the JSON schema and command pattern.

**Required on all AI-created issues:**
- `"customfield_12310031": [{"value": "Red Hat Employee"}]` — security field
- `"labels": ["ai-generated-jira"]` — marks AI-generated issues for review

---

## Initiative Template

Use for: architectural, infrastructure, or improvement-focused work that delivers capability to Red Hat associates (not directly to customers). Project: `ROSA`, `ARO`, `GCP`, `HCMPE`, or `CRCPLAN`.

Use `h2.` for major sections, `h3.` for sub-sections. Do not use Markdown.

```
<Brief one-paragraph overview of what this Initiative will achieve and why.>

h2. Goal

[What is our purpose in implementing this? What are we enabling? Time-box goals to 4-6 months.]

h2. Benefit Hypothesis

[What are the benefits — to Red Hat, to customers, to the community? Why is this work a priority?

We believe that the result of doing this work will be ...]

h2. Success Criteria

[Specific, measurable, achievable criteria that fit within the time-box. Include quantified targets where possible — e.g. "reduce deploy time from 30min to 5min", "eliminate class of support escalations X".]

h2. Planned Epics

* Epic 1: [name and brief description]
* Epic 2: [name and brief description]

h2. Timeline

* Total duration: [timeframe — ~6 months]
* Target completion: [quarter/release]

h3. Milestones
* Q1 [Year]: [deliverable]
* Q2 [Year]: [deliverable]

h2. Resources

[Add any resources (docs, slides, RFEs, Outcomes) pertinent to the definition of the work.]

h2. Responsibilities

[Indicate which roles and/or teams will be responsible and what they will contribute.]

h2. Results

[Add results here once the Initiative is started. Recommend quarterly updates in bullets.]
```

### `acli` JSON payload for Initiative creation

```json
{
  "projectKey": "<PROJECT>",
  "summary": "<SUMMARY>",
  "type": "Initiative",
  "description": {
    "type": "doc",
    "version": 1,
    "content": [
      {"type": "paragraph", "content": [{"type": "text", "text": "<overview paragraph>"}]}
    ]
  },
  "labels": ["ai-generated-jira"],
  "additionalAttributes": {
    "customfield_12310031": [{"value": "Red Hat Employee"}]
  }
}
```

---

## Outcome Template

Use for: specific, measurable business results that connect Features/Initiatives to corporate strategy. Project: `HCMSTRAT` only. Create sparingly — confirm with PM leadership before creating a new Outcome.

```
h1. Outcome Overview

[Once all Features and/or Initiatives in this Outcome are complete, what tangible, incremental, and (ideally) measurable movement will be made toward the company's Strategic Goal(s)?]

h1. Success Criteria

[What must be true for this outcome to be considered delivered? Avoid listing Features or Initiatives — describe observable business results instead.]

h1. Expected Results (what, how, when)

[What incremental impact do you expect to create toward Strategic Goals? For each expected result, list what you will measure and when (e.g., 60 days after work is complete). Include links to metrics.]

h1. Post Completion Review – Actual Results

[After completing the work, list the actual results observed/measured during Post Completion review(s).]
```

### `acli` JSON payload for Outcome creation

```json
{
  "projectKey": "HCMSTRAT",
  "summary": "<SUMMARY>",
  "type": "Outcome",
  "description": {
    "type": "doc",
    "version": 1,
    "content": [
      {"type": "paragraph", "content": [{"type": "text", "text": "<overview paragraph>"}]}
    ]
  },
  "additionalAttributes": {
    "customfield_12310031": [{"value": "Red Hat Employee"}]
  }
}
```
