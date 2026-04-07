#!/usr/bin/env python3
"""Search JIRA for RFEs and classify each by Feature coverage.

Usage:
    uv run --with requests python3 rfe-search.py --jql "..." [--limit N] [--all]

Environment:
    JIRA_API_TOKEN  Personal Access Token for redhat.atlassian.net/jira

Output:
    Line 1: summary header  "Total matches: N (showing M)"
    Lines 2+: one JSON object per issue, fields:
        key, summary, status, priority, votes, components,
        labels, created, updated, description, feature_links, coverage
    coverage values: "none" | "partial" | "decomposed"
"""

import argparse
import json
import os
import sys


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

    token = os.environ.get("JIRA_API_TOKEN")
    if not token:
        print("ERROR: JIRA_API_TOKEN not set", file=sys.stderr)
        print("Set:      export JIRA_API_TOKEN=<your-PAT>", file=sys.stderr)
        print(
            "Generate: https://redhat.atlassian.net/jira/secure/ViewProfile.jspa",
            file=sys.stderr,
        )
        sys.exit(1)

    import requests

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    fields = "summary,status,priority,components,labels,votes,created,updated,issuelinks,description"

    if args.all:
        # Paginate through all results using nextPageToken
        issues = []
        next_page_token = None

        while True:
            params = {
                "jql": args.jql,
                "maxResults": 100,
                "fields": fields,
            }
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
            page_issues = data.get("issues", [])
            issues.extend(page_issues)

            if data.get("isLast", True) or not page_issues:
                break
            next_page_token = data.get("nextPageToken")
            if not next_page_token:
                break
    else:
        resp = requests.get(
            "https://redhat.atlassian.net/jira/rest/api/3/search/jql",
            headers=headers,
            params={
                "jql": args.jql,
                "maxResults": args.limit,
                "fields": fields,
            },
        )

        if not resp.ok:
            print(f"Error {resp.status_code}: {resp.text}", file=sys.stderr)
            sys.exit(1)

        data = resp.json()
        issues = data.get("issues", [])

    print(f"Total: {len(issues)}")
    print()

    for issue in issues:
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
            # ADF format — extract plain text from content nodes
            def extract_text(node):
                if isinstance(node, str):
                    return node
                if isinstance(node, dict):
                    if node.get("type") == "text":
                        return node.get("text", "")
                    return "".join(extract_text(c) for c in node.get("content", []))
                if isinstance(node, list):
                    return "".join(extract_text(c) for c in node)
                return ""
            raw_desc = extract_text(raw_desc)
        description = raw_desc[:500]

        print(
            json.dumps(
                {
                    "key": key,
                    "summary": f.get("summary", ""),
                    "status": status,
                    "priority": (f.get("priority") or {}).get("name", "Unknown"),
                    "votes": (f.get("votes") or {}).get("votes", 0),
                    "components": ", ".join(c["name"] for c in f.get("components", [])),
                    "labels": f.get("labels", []),
                    "created": (f.get("created") or "")[:10],
                    "updated": (f.get("updated") or "")[:10],
                    "description": description,
                    "feature_links": feature_links,
                    "coverage": coverage,
                }
            )
        )


if __name__ == "__main__":
    main()
