#!/usr/bin/env python3
"""Render the static work map from data/snapshot.json."""

from __future__ import annotations

import html
import json
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import quote

from areas import AREA_LABELS, AREA_ORDER

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "data" / "snapshot.json"
SITE = ROOT / "site"

WINDOWS = {
    "30d": timedelta(days=30),
    "90d": timedelta(days=90),
    "all": None,
}


def load_snapshot():
    if not SNAPSHOT.exists():
        raise SystemExit(f"missing {SNAPSHOT}; run scripts/collect.py first")
    return json.loads(SNAPSHOT.read_text())


def parse_time(stamp):
    return datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )


def in_window(merged_at, now, delta):
    if delta is None:
        return True
    return parse_time(merged_at) >= now - delta


def summarize(snapshot):
    now = datetime.now(timezone.utc)
    prs = snapshot["prs"]
    area_counts = {
        area: {key: 0 for key in WINDOWS} for area in AREA_ORDER
    }
    area_prs = defaultdict(list)
    people = {}
    for pr in prs:
        for area in pr["areas"]:
            area_prs[area].append(pr)
            for key, delta in WINDOWS.items():
                if in_window(pr["merged_at"], now, delta):
                    area_counts.setdefault(area, {k: 0 for k in WINDOWS})
                    area_counts[area][key] += 1
        login = pr["author"]
        person = people.setdefault(
            login,
            {
                "login": login,
                "prs": [],
                "areas": set(),
                "first_merged_at": pr["merged_at"],
                "last_merged_at": pr["merged_at"],
            },
        )
        person["prs"].append(pr)
        person["areas"].update(pr["areas"])
        if pr["merged_at"] < person["first_merged_at"]:
            person["first_merged_at"] = pr["merged_at"]
        if pr["merged_at"] > person["last_merged_at"]:
            person["last_merged_at"] = pr["merged_at"]
    for person in people.values():
        person["areas"] = sorted(
            person["areas"], key=lambda area: AREA_ORDER.index(area)
            if area in AREA_ORDER
            else 99
        )
        person["prs"].sort(key=lambda item: item["merged_at"], reverse=True)
    return area_counts, area_prs, people


def escape(text):
    return html.escape(str(text), quote=True)


def person_href(login):
    return f"../person/{quote(login, safe='')}.html"


def page(title, body, root="."):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <link rel="stylesheet" href="{root}/style.css">
</head>
<body>
  <header>
    <p class="mark"><a href="{root}/index.html">Omarchy work map</a></p>
    <p class="sub">Merged labor on <a href="https://github.com/basecamp/omarchy">basecamp/omarchy</a>. Unofficial.</p>
  </header>
  <main>
{body}
  </main>
  <footer>
    <p>Unofficial. Not Omacom, not Basecamp. We count merged pull requests only.
    <a href="{root}/methodology.html">Methodology</a>.</p>
  </footer>
</body>
</html>
"""


def pr_list(prs, person_links=True):
    rows = []
    for pr in prs:
        who = escape(pr["author"])
        if person_links:
            who = f'<a href="{person_href(pr["author"])}">{who}</a>'
        areas = ", ".join(
            f'<a href="../area/{escape(area)}.html">{escape(AREA_LABELS.get(area, area))}</a>'
            for area in pr["areas"]
        )
        day = pr["merged_at"][:10]
        rows.append(
            f"<li><time datetime=\"{escape(pr['merged_at'])}\">{escape(day)}</time> "
            f'<a href="{escape(pr["url"])}">#{pr["number"]}</a> '
            f"{escape(pr['title'])} — {who} "
            f'<span class="areas">{areas}</span></li>'
        )
    if not rows:
        return "<p>No merged PRs in this view.</p>"
    return "<ol class=\"prs\">\n" + "\n".join(rows) + "\n</ol>"


def write_home(snapshot, area_counts, people):
    rows = []
    for area in AREA_ORDER:
        counts = area_counts.get(area, {key: 0 for key in WINDOWS})
        label = AREA_LABELS[area]
        rows.append(
            "<tr>"
            f'<th scope="row"><a href="area/{escape(area)}.html">{escape(label)}</a></th>'
            f'<td>{counts["30d"]}</td>'
            f'<td>{counts["90d"]}</td>'
            f'<td>{counts["all"]}</td>'
            "</tr>"
        )
    people_links = " ".join(
        f'<a href="person/{quote(login, safe="")}.html">{escape(login)}</a>'
        for login in sorted(people, key=str.lower)
    )
    body = f"""    <p class="lede">Where merged work landed. Not a scoreboard. Not a grant formula.
    Counts are merged pull requests on <code>basecamp/omarchy</code>.</p>
    <p class="meta">Snapshot {escape(snapshot["generated_at"])} · {snapshot["pr_count"]} merged PRs</p>
    <table>
      <thead>
        <tr><th>Area</th><th>30 days</th><th>90 days</th><th>All</th></tr>
      </thead>
      <tbody>
{chr(10).join("        " + row for row in rows)}
      </tbody>
    </table>
    <h2>People who landed work</h2>
    <p class="dir">{people_links}</p>
"""
    (SITE / "index.html").write_text(page("Omarchy work map", body, root="."))


def write_area(area, prs):
    label = AREA_LABELS.get(area, area)
    people = sorted({pr["author"] for pr in prs}, key=str.lower)
    who = (
        " ".join(
            f'<a href="{person_href(login)}">{escape(login)}</a>' for login in people
        )
        or "Nobody yet."
    )
    body = f"""    <h1>{escape(label)}</h1>
    <p>{len(prs)} merged PRs. People: {who}</p>
    {pr_list(prs)}
"""
    directory = SITE / "area"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{area}.html").write_text(
        page(f"{label} — Omarchy work map", body, root="..")
    )


def write_person(person):
    login = person["login"]
    facts = ", ".join(AREA_LABELS.get(area, area) for area in person["areas"])
    first = person["first_merged_at"][:10]
    body = f"""    <h1>{escape(login)}</h1>
    <p>{len(person["prs"])} merged PRs. First landed {escape(first)}. Areas: {escape(facts)}.</p>
    {pr_list(person["prs"], person_links=False)}
"""
    directory = SITE / "person"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{login}.html").write_text(
        page(f"{login} — Omarchy work map", body, root="..")
    )


def write_methodology(snapshot):
    body = f"""    <h1>Methodology</h1>
    <p>This is an unofficial map of merged pull requests on
    <a href="https://github.com/basecamp/omarchy">basecamp/omarchy</a>.
    It is not affiliated with the Omacom Foundation or Basecamp.
    We do not speak for them and we do not allocate their funds.</p>
    <p>Omacom’s public mandate is to hold trademarks, fund infrastructure,
    and support the open-source projects Omarchy depends on. This page only
    shows work that already merged <em>inside</em> the distro repo. That can
    be useful as a picture of where labor is landing. It is not a grant
    formula.</p>
    <h2>What we count</h2>
    <ul>
      <li>Pull requests with state merged, including the GitHub login on the PR.
      Whether an agent helped is irrelevant. The login did the work.</li>
      <li>Each merged PR is counted once per area it touched (from changed file
      paths, first 100 files on the PR). A PR that changes <code>shell/</code>
      and <code>bin/</code> appears in both.</li>
    </ul>
    <h2>What we do not count</h2>
    <ul>
      <li>Opened but unmerged PRs, issues, comments, reactions, stars, or lines of code.</li>
      <li>Ranks, points, streaks, or participation trophies.</li>
      <li>Work on Hyprland, Quickshell, or other upstreams. That is out of v1.</li>
    </ul>
    <p>Generated {escape(snapshot["generated_at"])} from {escape(snapshot["source"])}.</p>
"""
    (SITE / "methodology.html").write_text(
        page("Methodology — Omarchy work map", body, root=".")
    )


def write_css():
    (SITE / "style.css").write_text(
        """
:root {
  --ink: #1c1917;
  --paper: #f5f0e8;
  --muted: #57534e;
  --line: #d6d3d1;
  --link: #1d4e4f;
}
* { box-sizing: border-box; }
html { font-size: 18px; }
body {
  margin: 0 auto;
  max-width: 48rem;
  padding: 2rem 1.25rem 4rem;
  background: var(--paper);
  color: var(--ink);
  font-family: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
  line-height: 1.45;
}
header { margin-bottom: 2rem; }
.mark { font-size: 1.15rem; margin: 0; }
.sub, .meta, footer, .areas { color: var(--muted); font-size: 0.92rem; }
a { color: var(--link); }
table { width: 100%; border-collapse: collapse; margin: 1.5rem 0; }
th, td { text-align: left; padding: 0.4rem 0.5rem; border-bottom: 1px solid var(--line); }
td { font-variant-numeric: tabular-nums; }
.lede { font-size: 1.15rem; }
.dir { line-height: 1.9; }
.dir a { margin-right: 0.75rem; }
ol.prs { padding-left: 1.25rem; }
ol.prs li { margin: 0.45rem 0; }
time { font-variant-numeric: tabular-nums; }
footer { margin-top: 3rem; border-top: 1px solid var(--line); padding-top: 1rem; }
"""
    )


def main():
    snapshot = load_snapshot()
    area_counts, area_prs, people = summarize(snapshot)
    SITE.mkdir(parents=True, exist_ok=True)
    write_css()
    write_home(snapshot, area_counts, people)
    for area in AREA_ORDER:
        write_area(area, area_prs.get(area, []))
    for person in people.values():
        write_person(person)
    write_methodology(snapshot)
    (SITE / "snapshot.json").write_text(json.dumps(snapshot))
    print(f"wrote site/ ({len(people)} people, {snapshot['pr_count']} PRs)")


if __name__ == "__main__":
    main()
