# Jira Wiki Markup Reference

Use this syntax when writing Feature, Initiative, and Outcome descriptions for redhat.atlassian.net/jira. **Never use Markdown** (no `#`, `**`, `-`, `` ``` ``) — Jira does not render it.

Source: openshift-eng/ai-helpers jira plugin.

---

## Headings

```
h1. Top-level heading  (use sparingly; typically only for document title)
h2. Major section
h3. Sub-section
h4. Sub-sub-section
```

**Convention for Feature/Initiative descriptions:** Use `h2.` for major sections (Market Problem, Strategic Value, etc.) and `h3.` for sub-sections. Reserve `h1.` for the document title only.

---

## Lists

```
* Bullet item
* Bullet item
** Nested bullet
** Nested bullet

# Numbered item
# Numbered item
## Nested numbered

*# Bullet with numbered sub-items
```

---

## Text Effects

```
*bold*
_italic_
{{monospace}}
-deleted-
+inserted+
```

---

## Links

```
[PROJ-123]                          ← auto-links to Jira issue
[Link text|http://example.com]      ← external link
[~username]                         ← user link
```

---

## Tables

```
||Header 1||Header 2||Header 3||
|Data 1|Data 2|Data 3|
|Data 4|Data 5|Data 6|
```

---

## Code Blocks

```
{code}
plain code block
{code}

{code:bash}
language-specific block
{code}

{{inline monospace}}
```

---

## Panels / Callouts

```
{info}
Informational note.
{info}

{warning}
Warning note.
{warning}

{panel:title=My Title|borderStyle=solid|bgColor=#FFFFCE}
Custom panel content.
{panel}
```

---

## Horizontal Rule

```
----
```

Four dashes produces a horizontal rule. Three dashes (`---`) produces an em-dash (—).

---

## Common Issue Description Templates

### Feature / Initiative description structure

```
<Brief one-paragraph overview of what this delivers.>

h2. Market Problem

<Who is affected, what pain they experience, impact of not solving, why now.>

h2. Proposed Solution

<The capability being delivered.>

h2. Strategic Value

h3. Customer Value
* <Quantified benefit 1>
* <Quantified benefit 2>

h3. Business Impact
* <Revenue, cost, competitive impact>

h3. Strategic Alignment
<How this supports product/company strategy.>

h2. Success Criteria

h3. Adoption
* <Adoption metric with target>

h3. Outcomes
* <Customer outcome metric with target>

h3. Business
* <Business metric with target>

h2. Scope

h3. Planned Epics
* Epic 1: <name>
* Epic 2: <name>

h3. Out of Scope
* <Related work explicitly excluded>

h2. Timeline

* Total duration: <timeframe>
* Target: <release>

h3. Milestones
* Q1 <Year>: <deliverable>
* Q2 <Year>: <deliverable>

h2. Dependencies (if any)

* [PROJ-XXX] - <what this depends on>

h2. Risks (if any)

* <Risk> — Mitigation: <strategy>
```

### Epic description structure

```
h2. Use Case / Context

<Why this Epic exists and what problem it solves.>

h2. Desired State

* <Outcome 1>
* <Outcome 2>

h2. Scope

*In scope:*
* <Item 1>

*Out of scope:*
* <Item 1>

h2. Acceptance Criteria

* Test that <condition 1>
* Test that <condition 2>
```

### Story / Task description structure

```
As a {{<user type>}}, I want to {{<action>}}, so that {{<benefit>}}.

h2. Acceptance Criteria

* Test that <condition 1>
* Test that <condition 2>

h2. Dependencies (if any)

* [PROJ-XXX] - <dependency>
```
