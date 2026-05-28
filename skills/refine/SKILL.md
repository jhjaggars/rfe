---
name: refine
description: "Systematically work through a priority-ordered queue of open RFEs, assessing each for readiness and advancing them toward Feature creation. Triggers on: /rfe:refine, \"refine RFEs\", \"work through RFE queue\", \"process refinement queue\", \"RFE refinement session\", \"advance RFEs to features\""
argument-hint: "[component:<name>] [status:<value>] [priority:<level>] [limit:<n>]"
---

# refine

You run a structured refinement session — a queue of open RFEs worked through in priority order. For each RFE you assess readiness, fill description gaps by asking targeted questions, and either advance it to Feature creation (via `/rfe:decompose`) or flag it as blocked/deferred with a clear reason.

The goal: leave every reviewed RFE in a better state than you found it.

Read `../triage/references/rfe-jql-patterns.md` now. It contains the base JQL and verified status values.

---

## Phase 1: Build the Refinement Queue

**Parse the arguments** provided by the user. Recognized arguments:

| Argument | Example | Effect |
|----------|---------|--------|
| `component:<name>` | `component:ROSA` | Restrict to one product area |
| `status:<value>` | `status:Approved` | Default: `Approved` then `Refinement` (highest-priority statuses) |
| `priority:<level>` | `priority:Critical` | Filter by priority |
| `limit:<n>` | `limit:10` | Max RFEs to queue (default 15) |

**If no arguments are given**, ask the user using AskUserQuestion with up to 4 options:

- **Approved only** — RFEs in the `Approved` status (highest PM signal)
- **Refinement queue** — RFEs in `Refinement` status (actively being worked)
- **High-priority uncovered** — Critical + Major with no Feature links, any status
- **By component** — pick a component to focus the session

**Build the JQL.** Default queue:

```
project = RFE AND issuetype = "Feature Request"
AND status in ("Approved", "Refinement")
AND status not in ("Closed")
ORDER BY priority ASC, votes DESC, updated ASC
```

Apply argument overrides. The sort order prioritizes: critical before major, high vote count, least recently touched (stalest work first).

---

## Phase 2: Fetch the Queue

Run the search script:

```bash
Run the appropriate `acli jira workitem` command (e.g. `acli jira workitem search --jql \"<BUILT JQL>\" --json`) directly to fetch data.

> **WARNING:** Do NOT use restricted fields (like `components`, `created`, `updated`, `parent`, etc.) in the `--fields` argument. The `acli` tool has a strict allowlist and will fail with a "field not allowed" error. Rely on the default JSON output instead.

Where `<SKILL_BASE_DIR>` is the directory containing this SKILL.md file.

Display a queue overview before starting:

```
Refinement Session  —  <N> RFEs queued

  #   KEY           PRI      VOTES  STATUS       FEATURES  SUMMARY
  ──────────────────────────────────────────────────────────────────────────
  1   RFE-1234      Critical    12  Approved      none      Managed cluster auto-scaling
  2   RFE-5678      Critical     9  Approved      none      Custom OIDC provider
  3   RFE-9012      Major        7  Refinement    partial   Multi-tenant control plane
  4   RFE-3456      Major        5  Approved      none      Audit log export
  ...

Starting with RFE-1234. Type 'skip' to move to the next, 'done' to end the session.
```

---

## Phase 3: Work Each RFE

For each RFE in the queue, run through the following steps. Keep session state: track how many reviewed, how many advanced, how many deferred.

### Step 3a: Fetch Full Detail

```bash
Run `acli jira workitem view <KEY> --json` (or appropriate acli command) and parse the JSON output directly.
```

### Step 3b: Assess Readiness

Evaluate the RFE against the 5 readiness dimensions:

| Dimension | Assessment | Guidance |
|-----------|-----------|----------|
| **Description quality** | Good / Partial / Sparse | "Good" = clear problem statement + use case. "Sparse" = one-liner with no context. |
| **Scope** | Bounded / Broad / Unclear | "Bounded" = one addressable capability. "Broad" = multiple independent concerns. |
| **Customer signal** | Strong / Weak | Votes ≥5 or linked customers = Strong. Zero votes, no comments = Weak. |
| **Existing coverage** | None / Partial / Covered | Based on `feature_links` from search output. |
| **Actionability** | Ready / Needs input / Blocked | Can a Feature be drafted now, or is critical information missing? |

Render the assessment compactly:

```
━━━ RFE-1234  [1 of 10]  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Priority: Critical  |  Votes: 12  |  Status: Approved
Component: ROSA  |  Coverage: none  |  Created: 2024-01-15

Summary: Managed cluster auto-scaling

Description quality : Good     — clear pain, includes SLA example
Scope               : Bounded  — CPU-based scaling only
Customer signal     : Strong   — 12 votes, 2 linked customers
Existing coverage   : None     — no Features linked
Actionability       : Ready    — all elements present to draft a Feature
```

### Step 3c: Decide Next Action

Based on the assessment, recommend one of these actions and ask the user to confirm using AskUserQuestion with up to 4 options matching the situation:

**If Actionability = Ready:**
- **Decompose now** — hand off to `/rfe:decompose <KEY>`
- **Add to decompose list** — queue for batch decompose at end of session
- **Skip** — move to next RFE without action
- **Close** — close this RFE (enter reason)

**If Actionability = Needs input:**
- **Ask clarifying questions** — gather missing info now (see Step 3d)
- **Add comment requesting info** — leave a comment on the JIRA issue and defer
- **Skip** — move to next RFE
- **Close** — close this RFE

**If Actionability = Blocked:**
- **Add comment with blocker** — document why it can't proceed
- **Skip** — move to next RFE
- **Close** — close if the blocker is permanent (e.g., capability out of scope)
- **Link to blocker** — link to the issue that must complete first

### Step 3d: Fill Gaps (if Needs Input)

If the user chooses to ask clarifying questions, generate up to 4 targeted questions using AskUserQuestion. Pre-fill partial answers from context.

Good questions for RFE refinement:
- "The RFE mentions X but doesn't specify Y — what's the expected behavior when Z?"
- "This covers both A and B — should these be one Feature or two?"
- "Is there a target release or GA date driving this?"
- "Who is the primary customer persona for this? (operator, developer, cluster admin?)"

After getting answers, re-assess readiness.

### Step 3e: Act

**If decomposing now:**
Tell the user:
```
Ready to decompose. Run:

  /rfe:decompose <KEY>
```

Then pause — wait for the user to run that command and return before continuing to the next RFE. Ask "Continue to the next RFE?" before proceeding.

**If adding a comment:**

```bash
Run `acli jira workitem view <KEY> --json` (or appropriate acli command) and parse the JSON output directly.
```

**If changing status (transitioning):**

First get transitions, then apply the chosen one — same pattern as in the duplicates skill.

---

## Phase 4: Session Summary

After all RFEs are processed (or the user types "done"), display a session summary:

```
━━━ Session Complete ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Reviewed:    10 RFEs

  Ready to decompose : 4
    RFE-1234, RFE-3456, RFE-7890, RFE-2345

  Comments added     : 3
    RFE-5678  — requested use case details from reporter
    RFE-6789  — noted dependency on OCPSTRAT-1234
    RFE-8901  — flagged for close (out of scope)

  Skipped            : 2
  Closed             : 1  (RFE-4567)

Next steps:
  Run /rfe:decompose <KEY> for each Ready RFE to create Features.
  Re-run /rfe:refine after clarifications are received to advance deferred RFEs.
```

---

## Error Handling

- **JIRA_API_TOKEN or JIRA_USER not set:** Tell the user: "Set `export JIRA_API_TOKEN=<your-token>` and `export JIRA_USER=<your-email>` before running, or run `/rfe:init`."
- **Empty queue:** If no RFEs match the filter, report the JQL used and suggest broadening (e.g., include `Backlog` status, drop priority filter).
- **REST API error on comment/transition:** Show the error and ask whether to retry or skip. Do not abort the session.
- **User wants to restart queue:** Accept "restart" at any prompt to re-display the queue from the beginning.
