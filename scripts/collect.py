#!/usr/bin/env python3
"""Pull merged PRs from basecamp/omarchy into data/snapshot.json."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

from areas import areas_for_paths

OWNER = "basecamp"
REPO = "omarchy"
GRAPHQL = "https://api.github.com/graphql"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "snapshot.json"

PRS_QUERY = """
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    pullRequests(
      states: MERGED
      first: 50
      after: $cursor
      orderBy: { field: UPDATED_AT, direction: DESC }
    ) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number
        title
        url
        createdAt
        mergedAt
        author { login }
        files(first: 100) {
          nodes { path }
        }
      }
    }
  }
}
"""


def github_token():
    for key in ("GITHUB_TOKEN", "GH_TOKEN"):
        value = os.environ.get(key)
        if value:
            return value
    try:
        return subprocess.check_output(
            ["gh", "auth", "token"], text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError) as err:
        raise SystemExit(
            "No GITHUB_TOKEN / GH_TOKEN and `gh auth token` failed."
        ) from err


def graphql(token, query, variables):
    body = json.dumps({"query": query, "variables": variables}).encode()
    request = urllib.request.Request(
        GRAPHQL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "omarchy-work-map",
        },
    )
    try:
        with urllib.request.urlopen(request) as response:
            payload = json.loads(response.read().decode())
    except urllib.error.HTTPError as err:
        detail = err.read().decode()[:500]
        raise SystemExit(f"GitHub GraphQL HTTP {err.code}: {detail}") from err
    if payload.get("errors"):
        raise SystemExit(f"GitHub GraphQL errors: {payload['errors']}")
    return payload["data"]


def record_from_node(node):
    if not node.get("mergedAt"):
        return None
    paths = [file["path"] for file in (node.get("files") or {}).get("nodes") or []]
    author = (node.get("author") or {}).get("login") or "ghost"
    return {
        "number": node["number"],
        "title": node["title"],
        "url": node["url"],
        "created_at": node.get("createdAt"),
        "merged_at": node["mergedAt"],
        "author": author,
        "paths": paths,
        "areas": areas_for_paths(paths),
    }


def collect_merged_prs(token):
    records = []
    cursor = None
    while True:
        data = graphql(
            token,
            PRS_QUERY,
            {"owner": OWNER, "name": REPO, "cursor": cursor},
        )
        connection = data["repository"]["pullRequests"]
        for node in connection["nodes"]:
            record = record_from_node(node)
            if record:
                records.append(record)
        page = connection["pageInfo"]
        if not page["hasNextPage"]:
            break
        cursor = page["endCursor"]
        print(f"fetched {len(records)} merged PRs…", file=sys.stderr)
    records.sort(key=lambda item: item["merged_at"], reverse=True)
    return records


FUNNEL_QUERY = """
query($openQ: String!, $closedQ: String!) {
  open: search(query: $openQ, type: ISSUE, first: 1) { issueCount }
  closed: search(query: $closedQ, type: ISSUE, first: 1) { issueCount }
}
"""


def collect_funnel(token, now):
    start = (now - timedelta(days=90)).strftime("%Y-%m-%d")
    data = graphql(
        token,
        FUNNEL_QUERY,
        {
            "openQ": f"repo:{OWNER}/{REPO} is:pr is:open",
            "closedQ": (
                f"repo:{OWNER}/{REPO} is:pr is:unmerged is:closed "
                f"updated:>={start}"
            ),
        },
    )
    return {
        "open": data["open"]["issueCount"],
        "closed_unmerged_90d": data["closed"]["issueCount"],
    }


def main():
    token = github_token()
    now = datetime.now(timezone.utc)
    records = collect_merged_prs(token)
    merged_90d = sum(
        1
        for pr in records
        if datetime.strptime(pr["merged_at"], "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
        >= now - timedelta(days=90)
    )
    funnel = collect_funnel(token, now)
    funnel["merged_90d"] = merged_90d
    snapshot = {
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": f"{OWNER}/{REPO}",
        "pr_count": len(records),
        "funnel_90d": funnel,
        "prs": records,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(snapshot, indent=2) + "\n")
    print(f"wrote {len(records)} merged PRs to {OUT}")


if __name__ == "__main__":
    main()
