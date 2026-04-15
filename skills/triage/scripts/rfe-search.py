#!/usr/bin/env python3
"""Search JIRA for RFEs and classify each by Feature coverage.

Usage:
    uv run --with requests python3 rfe-search.py --jql "..." [--limit N] [--all]

Environment:
    JIRA_URL        Jira base URL (e.g. https://redhat.atlassian.net)
    JIRA_API_TOKEN  API token
    JIRA_USER       Email address for Basic auth (e.g. you@redhat.com)

Output:
    Line 1: "Total: N"
    Lines 2+: one JSON object per issue, fields:
        key, summary, status, priority, votes, components,
        labels, created, updated, description, feature_links, coverage
    coverage values: "none" | "partial" | "decomposed"
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "scripts"))
import jira


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


def normalize(issue):
    key = issue["key"]
    f = issue["fields"]
    status = f["status"]["name"]

    feature_links = []
    for link in f.get("issuelinks", []):
        for direction in ("inwardIssue", "outwardIssue"):
            li = link.get(direction)
            if li:
                ltype = li.get("fields", {}).get("issuetype", {}).get("name", "")
                if ltype == "Feature":
                    feature_links.append(li["key"])

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
        "key": key,
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


def main():
    parser = argparse.ArgumentParser(description="Search JIRA RFEs")
    parser.add_argument("--jql", required=True, help="JQL query string")
    parser.add_argument(
        "--limit", type=int, default=25, help="Max results (default 25)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Fetch all results via pagination (ignores --limit)",
    )
    args = parser.parse_args()

    issues = jira.search_all(args.jql) if args.all else jira.search(args.jql, max_results=args.limit)

    print(f"Total: {len(issues)}")
    print()

    for issue in issues:
        print(json.dumps(normalize(issue)))


if __name__ == "__main__":
    main()
