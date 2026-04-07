#!/usr/bin/env python3
"""Generate a prioritization report from RFE search results.

Usage:
    uv run --with requests python3 rfe-report.py --jql "..." [--all] [--limit N] [--output FILE]

Reads RFEs from JIRA (via the same API as rfe-search.py), categorizes them,
and writes a markdown prioritization report to stdout or a file.

Environment:
    JIRA_API_TOKEN  Personal Access Token for redhat.atlassian.net/jira
"""

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import date


def fetch_issues(jql, token, fetch_all=False, limit=25):
    """Fetch issues from JIRA v3 search API."""
    import requests

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    fields = "summary,status,priority,components,labels,votes,created,updated,issuelinks,description"

    if fetch_all:
        issues = []
        next_page_token = None

        while True:
            params = {"jql": jql, "maxResults": 100, "fields": fields}
            if next_page_token:
                params["nextPageToken"] = next_page_token

            resp = requests.get(
                "https://redhat.atlassian.net/jira/rest/api/3/search/jql",
                headers=headers,
                params=params,
            )
            if not resp.ok:
                print(f"Error {resp.status_code}: {resp.text}", file=sys.stderr)
                sys.exit(1)

            data = resp.json()
            issues.extend(data.get("issues", []))

            if data.get("isLast", True) or not data.get("nextPageToken"):
                break
            next_page_token = data["nextPageToken"]

        return issues
    else:
        resp = requests.get(
            "https://redhat.atlassian.net/jira/rest/api/3/search/jql",
            headers=headers,
            params={"jql": jql, "maxResults": limit, "fields": fields},
        )
        if not resp.ok:
            print(f"Error {resp.status_code}: {resp.text}", file=sys.stderr)
            sys.exit(1)
        return resp.json().get("issues", [])


def extract_text(node):
    """Extract plain text from an ADF (Atlassian Document Format) node."""
    if isinstance(node, str):
        return node
    if isinstance(node, dict):
        if node.get("type") == "text":
            return node.get("text", "")
        return "".join(extract_text(c) for c in node.get("content", []))
    if isinstance(node, list):
        return "".join(extract_text(c) for c in node)
    return ""


def normalize_issue(issue):
    """Convert raw JIRA issue to a flat dict."""
    f = issue["fields"]

    feature_links = []
    for link in f.get("issuelinks", []):
        for direction in ("inwardIssue", "outwardIssue"):
            li = link.get(direction)
            if li:
                ltype = li.get("fields", {}).get("issuetype", {}).get("name", "")
                if ltype == "Feature":
                    feature_links.append(li["key"])

    status = f["status"]["name"]
    coverage = "none"
    if feature_links:
        coverage = (
            "partial"
            if status not in ("Closed", "Done", "Resolved")
            else "decomposed"
        )

    raw_desc = f.get("description") or ""
    if isinstance(raw_desc, dict):
        raw_desc = extract_text(raw_desc)

    return {
        "key": issue["key"],
        "summary": f.get("summary", ""),
        "status": status,
        "priority": (f.get("priority") or {}).get("name", "Unknown"),
        "votes": (f.get("votes") or {}).get("votes", 0),
        "components": ", ".join(c["name"] for c in f.get("components", [])),
        "labels": f.get("labels", []),
        "created": (f.get("created") or "")[:10],
        "updated": (f.get("updated") or "")[:10],
        "description": raw_desc[:500],
        "feature_links": feature_links,
        "coverage": coverage,
    }


PRIORITY_WEIGHT = {
    "Blocker": 5,
    "Critical": 4,
    "Major": 3,
    "Normal": 2,
    "Minor": 1,
    "Undefined": 0,
}


def composite_score(rfe, today):
    ps = PRIORITY_WEIGHT.get(rfe["priority"], 0) * 10
    vs = rfe["votes"]
    try:
        age = (today - date.fromisoformat(rfe["created"])).days
        recency = max(0, (365 - age) / 365) * 5
    except ValueError:
        recency = 0
    return ps + vs + recency


def generate_report(rfes, today):
    """Build the markdown report from normalized RFEs."""
    for r in rfes:
        r["_score"] = composite_score(r, today)

    by_component = defaultdict(list)
    for r in rfes:
        comp = r["components"].split(", ")[0] if r["components"] else "Uncategorized"
        by_component[comp].append(r)

    # Component-level aggregates
    comp_scores = {}
    for comp, items in by_component.items():
        comp_scores[comp] = {
            "count": len(items),
            "total_votes": sum(r["votes"] for r in items),
            "total_score": sum(r["_score"] for r in items),
            "no_coverage": sum(1 for r in items if r["coverage"] == "none"),
            "critical_blocker": sum(
                1 for r in items if r["priority"] in ("Critical", "Blocker")
            ),
        }
    sorted_comps = sorted(
        comp_scores.items(), key=lambda x: x[1]["total_score"], reverse=True
    )

    # Derived lists
    bc_uncovered = sorted(
        [
            r
            for r in rfes
            if r["priority"] in ("Blocker", "Critical") and r["coverage"] == "none"
        ],
        key=lambda r: r["_score"],
        reverse=True,
    )
    hv_uncovered = sorted(
        [r for r in rfes if r["votes"] >= 10 and r["coverage"] == "none"],
        key=lambda r: r["votes"],
        reverse=True,
    )
    undef = sorted(
        [r for r in rfes if r["priority"] == "Undefined"],
        key=lambda r: r["votes"],
        reverse=True,
    )
    undef_voted = [r for r in undef if r["votes"] > 0]

    stale_old = []
    for r in rfes:
        if r["votes"] == 0 and r["coverage"] == "none":
            try:
                age = (today - date.fromisoformat(r["created"])).days
                if age >= 730:
                    stale_old.append(r)
            except ValueError:
                pass

    # Age stats
    ages = []
    for r in rfes:
        try:
            ages.append((today - date.fromisoformat(r["created"])).days)
        except ValueError:
            pass
    median_age = sorted(ages)[len(ages) // 2] if ages else 0

    # --- Build report ---
    L = []

    L.append("# RFE Prioritization Report")
    L.append(f"**Generated:** {today.isoformat()}  ")
    L.append(f"**Total open RFEs:** {len(rfes)}  ")

    L.append("")
    L.append("## Executive Summary")
    L.append("")
    L.append(
        f"- **{len(rfes)}** open RFEs across **{len(by_component)}** component areas"
    )
    none_count = sum(1 for r in rfes if r["coverage"] == "none")
    L.append(
        f"- **{none_count}** ({none_count * 100 // len(rfes)}%) have **no Feature coverage**"
    )
    bc_count = sum(
        1 for r in rfes if r["priority"] in ("Blocker", "Critical")
    )
    L.append(f"- **{bc_count}** are **Blocker/Critical** priority")
    voted_10 = sum(1 for r in rfes if r["votes"] >= 10)
    L.append(f"- **{voted_10}** have **10+ votes** from the field")
    L.append(f"- Median age: **{median_age}** days")
    L.append(
        f"- **{len(undef)}** ({len(undef) * 100 // len(rfes)}%) have **Undefined** priority"
    )

    # Status table
    L.append("")
    L.append("## Status Breakdown")
    L.append("")
    L.append("| Status | Count | % |")
    L.append("|--------|------:|--:|")
    for s, c in Counter(r["status"] for r in rfes).most_common():
        L.append(f"| {s} | {c} | {c * 100 // len(rfes)}% |")

    # Priority table
    L.append("")
    L.append("## Priority Breakdown")
    L.append("")
    L.append("| Priority | Count | % | With Votes | No Coverage |")
    L.append("|----------|------:|--:|-----------:|------------:|")
    for p in ["Blocker", "Critical", "Major", "Normal", "Minor", "Undefined"]:
        c = sum(1 for r in rfes if r["priority"] == p)
        if c == 0:
            continue
        wv = sum(1 for r in rfes if r["priority"] == p and r["votes"] > 0)
        nc = sum(1 for r in rfes if r["priority"] == p and r["coverage"] == "none")
        L.append(f"| {p} | {c} | {c * 100 // len(rfes)}% | {wv} | {nc} |")

    # Coverage table
    L.append("")
    L.append("## Feature Coverage")
    L.append("")
    L.append("| Coverage | Count | % |")
    L.append("|----------|------:|--:|")
    for cv in ["none", "partial"]:
        c = sum(1 for r in rfes if r["coverage"] == cv)
        L.append(f"| {cv} | {c} | {c * 100 // len(rfes)}% |")

    # Top 30 components
    L.append("")
    L.append("## Top 30 Component Areas (by composite score)")
    L.append("")
    L.append(
        "Composite score = priority weight x 10 + votes + recency bonus."
    )
    L.append("")
    L.append("| # | Component | RFEs | Votes | Blk/Crit | No Coverage | Score |")
    L.append("|--:|-----------|-----:|------:|---------:|------------:|------:|")
    for i, (comp, s) in enumerate(sorted_comps[:30], 1):
        L.append(
            f"| {i} | {comp} | {s['count']} | {s['total_votes']} "
            f"| {s['critical_blocker']} | {s['no_coverage']} | {s['total_score']:.0f} |"
        )

    # Top 50 individual RFEs
    L.append("")
    L.append("## Top 50 RFEs by Composite Score")
    L.append("")
    L.append("| # | Key | Score | Votes | Priority | Coverage | Component | Summary |")
    L.append("|--:|-----|------:|------:|----------|----------|-----------|---------|")
    for i, r in enumerate(
        sorted(rfes, key=lambda r: r["_score"], reverse=True)[:50], 1
    ):
        comp = r["components"] or "-"
        L.append(
            f"| {i} | {r['key']} | {r['_score']:.0f} | {r['votes']} "
            f"| {r['priority']} | {r['coverage']} | {comp} | {r['summary'][:70]} |"
        )

    # Blocker/Critical uncovered
    L.append("")
    L.append("## Immediate Action: Blocker/Critical with No Feature Coverage")
    L.append("")
    L.append(
        f"**{len(bc_uncovered)} RFEs** are Blocker/Critical with no linked Feature work."
    )
    L.append("")
    if bc_uncovered:
        L.append("| Key | Votes | Priority | Status | Component | Summary |")
        L.append("|-----|------:|----------|--------|-----------|---------|")
        for r in bc_uncovered[:40]:
            comp = r["components"] or "-"
            L.append(
                f"| {r['key']} | {r['votes']} | {r['priority']} "
                f"| {r['status']} | {comp} | {r['summary'][:70]} |"
            )

    # High-voted uncovered
    L.append("")
    L.append("## High-Voted RFEs with No Coverage (10+ votes)")
    L.append("")
    L.append(
        f"**{len(hv_uncovered)} RFEs** have significant community support but no Feature work."
    )
    L.append("")
    if hv_uncovered:
        L.append("| Key | Votes | Priority | Status | Component | Summary |")
        L.append("|-----|------:|----------|--------|-----------|---------|")
        for r in hv_uncovered:
            comp = r["components"] or "-"
            L.append(
                f"| {r['key']} | {r['votes']} | {r['priority']} "
                f"| {r['status']} | {comp} | {r['summary'][:70]} |"
            )

    # Undefined priority
    L.append("")
    L.append("## Triage Needed: Undefined Priority")
    L.append("")
    L.append(
        f"**{len(undef)}** RFEs have no priority set. Of those, **{len(undef_voted)}** have votes."
    )
    L.append("")
    L.append("Top 20 undefined-priority RFEs by votes:")
    L.append("")
    L.append("| Key | Votes | Status | Component | Summary |")
    L.append("|-----|------:|--------|-----------|---------|")
    for r in undef[:20]:
        comp = r["components"] or "-"
        L.append(
            f"| {r['key']} | {r['votes']} | {r['status']} "
            f"| {comp} | {r['summary'][:70]} |"
        )

    # Stale candidates
    L.append("")
    L.append("## Candidates for Closure: Stale RFEs")
    L.append("")
    L.append(
        f"**{len(stale_old)}** RFEs are 2+ years old, have zero votes, and no Feature coverage."
    )
    L.append("")
    L.append("Breakdown by status:")
    for s, c in Counter(r["status"] for r in stale_old).most_common():
        L.append(f"- {s}: {c}")
    L.append("")
    L.append("Breakdown by component (top 15):")
    stale_comps = Counter()
    for r in stale_old:
        comp = r["components"].split(", ")[0] if r["components"] else "Uncategorized"
        stale_comps[comp] += 1
    for comp, c in stale_comps.most_common(15):
        L.append(f"- {comp}: {c}")

    # Recommendations
    L.append("")
    L.append("## Recommended Prioritization Actions")
    L.append("")
    L.append("### 1. Immediate: Triage Blocker/Critical uncovered RFEs")
    L.append(f"- **{len(bc_uncovered)}** Blocker/Critical RFEs lack Feature coverage")
    L.append(
        "- These represent the highest-risk gaps — customers care and nothing is planned"
    )
    L.append("- Action: Review each, create Features or re-prioritize")
    L.append("")
    L.append("### 2. Short-term: Address high-voted uncovered RFEs")
    L.append(f"- **{len(hv_uncovered)}** RFEs with 10+ votes and no coverage")
    L.append("- Strong field signal; potential customer satisfaction wins")
    L.append("- Action: Evaluate for Feature creation or roadmap inclusion")
    L.append("")
    L.append("### 3. Triage: Set priority on Undefined RFEs")
    L.append(
        f"- **{len(undef)}** RFEs ({len(undef) * 100 // len(rfes)}% of total) have no priority"
    )
    L.append("- Action: Bulk-triage by component, starting with voted items")
    L.append("")
    L.append("### 4. Cleanup: Close stale RFEs")
    L.append(
        f"- **{len(stale_old)}** RFEs are 2+ years old with no votes and no coverage"
    )
    L.append("- Action: Notify submitters, close with 30-day re-open window")
    L.append("")
    L.append("### 5. Focus areas by component")
    L.append("Top 5 component areas by composite urgency score:")
    for i, (comp, s) in enumerate(sorted_comps[:5], 1):
        L.append(
            f"  {i}. **{comp}** — {s['count']} RFEs, "
            f"{s['total_votes']} votes, {s['critical_blocker']} Blk/Crit"
        )

    return "\n".join(L) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Generate RFE prioritization report")
    parser.add_argument("--jql", required=True, help="JQL query string")
    parser.add_argument(
        "--limit", type=int, default=25, help="Max results (default 25)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Fetch all results via pagination (ignores --limit)",
    )
    parser.add_argument(
        "--output", "-o", help="Output file path (default: stdout)"
    )
    args = parser.parse_args()

    token = os.environ.get("JIRA_API_TOKEN")
    if not token:
        print("ERROR: JIRA_API_TOKEN not set", file=sys.stderr)
        sys.exit(1)

    print("Fetching RFEs from JIRA...", file=sys.stderr)
    raw_issues = fetch_issues(args.jql, token, fetch_all=args.all, limit=args.limit)
    print(f"Fetched {len(raw_issues)} issues, generating report...", file=sys.stderr)

    rfes = [normalize_issue(i) for i in raw_issues]
    if not rfes:
        print("No RFEs matched the query.", file=sys.stderr)
        sys.exit(1)

    report = generate_report(rfes, date.today())

    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()
