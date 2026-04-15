#!/usr/bin/env python3
"""Thin wrapper around the Jira REST API v3.

Required environment variables (all must be set):
    JIRA_URL        Base URL of the Jira instance (e.g. https://redhat.atlassian.net)
    JIRA_API_TOKEN  API token
    JIRA_USER       Email address for Basic auth

Usage in inline scripts (run from repo root):
    import sys; sys.path.insert(0, 'scripts')
    import jira

    issue  = jira.get_issue('RFE-1234')
    issues = jira.search('project = RFE AND status != Closed')
    issues = jira.search_all('project = RFE')
    key    = jira.create_issue({...})
    jira.link_issues('Implements', 'NEW-KEY', 'SOURCE-KEY')
    jira.add_comment('RFE-1234', 'text')
    jira.transition_issue('RFE-1234', transition_id)
    transitions = jira.get_transitions('RFE-1234')
    print(jira.browse_url('RFE-1234'))

Usage in scripts outside scripts/:
    import os, sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'scripts'))
    import jira
"""

import os
import sys

import requests as _req


def _init():
    url = os.environ.get("JIRA_URL")
    token = os.environ.get("JIRA_API_TOKEN")
    email = os.environ.get("JIRA_USER")
    missing = [
        k
        for k, v in (("JIRA_URL", url), ("JIRA_API_TOKEN", token), ("JIRA_USER", email))
        if not v
    ]
    if missing:
        print(f"ERROR: {', '.join(missing)} not set", file=sys.stderr)
        sys.exit(1)
    return url, (email, token)


_URL, _AUTH = _init()

_RFE_FIELDS = "summary,status,priority,components,labels,votes,created,updated,issuelinks,description"


def get_issue(key, fields=None):
    """Fetch a single issue by key. Returns the full issue dict."""
    params = {}
    if fields:
        params["fields"] = fields
    r = _req.get(f"{_URL}/rest/api/3/issue/{key}", auth=_AUTH, params=params)
    r.raise_for_status()
    return r.json()


def search(jql, fields=_RFE_FIELDS, max_results=50):
    """Run a JQL search. Returns list of issue dicts."""
    r = _req.get(
        f"{_URL}/rest/api/3/search/jql",
        auth=_AUTH,
        params={"jql": jql, "maxResults": max_results, "fields": fields},
    )
    r.raise_for_status()
    return r.json().get("issues", [])


def search_all(jql, fields=_RFE_FIELDS):
    """Paginate through all results. Returns list of issue dicts."""
    issues = []
    next_page_token = None
    while True:
        params = {"jql": jql, "maxResults": 100, "fields": fields}
        if next_page_token:
            params["nextPageToken"] = next_page_token
        r = _req.get(f"{_URL}/rest/api/3/search/jql", auth=_AUTH, params=params)
        r.raise_for_status()
        data = r.json()
        page = data.get("issues", [])
        issues.extend(page)
        if data.get("isLast", True) or not page or not data.get("nextPageToken"):
            break
        next_page_token = data["nextPageToken"]
    return issues


def create_issue(fields):
    """Create an issue. fields is the 'fields' dict. Returns the new issue key."""
    r = _req.post(
        f"{_URL}/rest/api/3/issue",
        auth=_AUTH,
        headers={"Content-Type": "application/json"},
        json={"fields": fields},
    )
    r.raise_for_status()
    return r.json()["key"]


def link_issues(link_type, inward_key, outward_key):
    """Create an issue link. link_type is the link type name (e.g. 'Implements', 'Duplicate')."""
    r = _req.post(
        f"{_URL}/rest/api/3/issueLink",
        auth=_AUTH,
        headers={"Content-Type": "application/json"},
        json={
            "type": {"name": link_type},
            "inwardIssue": {"key": inward_key},
            "outwardIssue": {"key": outward_key},
        },
    )
    r.raise_for_status()


def get_transitions(key):
    """Get available transitions. Returns list of {'id': ..., 'name': ...}."""
    r = _req.get(f"{_URL}/rest/api/3/issue/{key}/transitions", auth=_AUTH)
    r.raise_for_status()
    return r.json().get("transitions", [])


def transition_issue(key, transition_id, resolution=None):
    """Apply a transition. Pass resolution='Done' if the workflow requires it."""
    body = {"transition": {"id": transition_id}}
    if resolution:
        body["fields"] = {"resolution": {"name": resolution}}
    r = _req.post(
        f"{_URL}/rest/api/3/issue/{key}/transitions",
        auth=_AUTH,
        headers={"Content-Type": "application/json"},
        json=body,
    )
    r.raise_for_status()


def add_comment(key, body):
    """Add a comment to an issue."""
    r = _req.post(
        f"{_URL}/rest/api/3/issue/{key}/comment",
        auth=_AUTH,
        headers={"Content-Type": "application/json"},
        json={"body": body},
    )
    r.raise_for_status()


def browse_url(key):
    """Return the browser URL for an issue key."""
    return f"{_URL}/jira/browse/{key}"
