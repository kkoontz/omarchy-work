#!/usr/bin/env python3
"""Render the static work map from data/snapshot.json."""

from __future__ import annotations

import html
import json
from pathlib import Path
from urllib.parse import quote

from achievements import CATALOG, CATALOG_LABELS
from areas import AREA_LABELS, AREA_ORDER
from classes import load as load_classes
from ranks import load as load_ranks
from seasons import current as current_season
from summarize import WINDOWS, summarize

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "data" / "snapshot.json"
SITE = ROOT / "site"


def load_snapshot():
    if not SNAPSHOT.exists():
        raise SystemExit(f"missing {SNAPSHOT}; run scripts/collect.py first")
    return json.loads(SNAPSHOT.read_text())


def escape(text):
    return html.escape(str(text), quote=True)


def person_href(login, root=".."):
    return f"{root}/person/{quote(login, safe='')}.html"


def area_href(area, root=".."):
    return f"{root}/area/{escape(area)}.html"


def class_href(class_id, root=".."):
    return f"{root}/class/{escape(class_id)}.html"


def page(title, body, root="."):
    season = current_season()
    season_line = (
        f'{escape(season["name"])} season '
        f'{escape(season["start"])} – {escape(season["end"])}'
    )
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
    <p class="mark"><a href="{root}/index.html">Omarchy Quattro Arena</a></p>
    <p class="sub">Merged work on <a href="https://github.com/basecamp/omarchy">basecamp/omarchy</a>
    · {season_line}</p>
    <nav>
      <a href="{root}/index.html">Areas</a>
      <a href="{root}/people.html">People</a>
      <a href="{root}/classes.html">Categories</a>
      <a href="{root}/methodology.html">How we count</a>
    </nav>
  </header>
  <main>
{body}
  </main>
  <footer>
    <p><a href="{root}/methodology.html">How the numbers work</a></p>
  </footer>
</body>
</html>
"""


def pr_list(prs, person_links=True, root=".."):
    rows = []
    for pr in prs:
        who = escape(pr["author"])
        if person_links:
            who = f'<a href="{person_href(pr["author"], root)}">{who}</a>'
        areas = ", ".join(
            f'<a href="{area_href(area, root)}">{escape(AREA_LABELS.get(area, area))}</a>'
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


def week_table(weekly):
    rows = "".join(
        f"<tr><td>{escape(row['week'])}</td><td>{row['merges']}</td></tr>"
        for row in weekly
    )
    return (
        "<table class=\"weeks\"><thead><tr><th>Week of</th><th>Merges</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
    )


def write_home(snapshot, summary):
    facts = summary["facts"]
    rows = []
    for area in AREA_ORDER:
        counts = summary["area_counts"].get(area, {key: 0 for key in WINDOWS})
        extra = summary["area_extra"].get(area, {})
        people_90 = extra.get("unique_people", {}).get("90d", 0)
        lead = extra.get("median_days_open")
        lead_cell = "—" if lead is None else f"{lead:.1f}"
        label = AREA_LABELS[area]
        rows.append(
            "<tr>"
            f'<th scope="row"><a href="area/{escape(area)}.html">{escape(label)}</a></th>'
            f'<td>{counts["30d"]}</td>'
            f'<td>{counts["90d"]}</td>'
            f'<td>{counts["all"]}</td>'
            f"<td>{people_90}</td>"
            f"<td>{lead_cell}</td>"
            "</tr>"
        )
    conc = facts["concentration"]["90d"]
    ret = facts["retention_90d"]
    ret_s = "—" if ret["percent"] is None else f"{ret['percent']}%"
    lead = facts["median_days_open_90d"]
    lead_s = "—" if lead is None else f"{lead} days"
    funnel = facts["funnel_90d"]
    funnel_bits = []
    if funnel:
        if "merged_90d" in funnel:
            funnel_bits.append(f"{funnel['merged_90d']} merged")
        if "open" in funnel:
            funnel_bits.append(f"{funnel['open']} still open")
        if "closed_unmerged_90d" in funnel:
            funnel_bits.append(f"{funnel['closed_unmerged_90d']} closed unmerged")
    funnel_line = ", ".join(funnel_bits)
    frag_items = "".join(
        "<li>"
        f'<span class="frag">{escape(hit["frag"])}</span> '
        f'<a href="{person_href(hit["login"], ".")}">{escape(hit["login"])}</a> '
        f'<a href="{escape(hit["url"])}">#{hit["number"]}</a> '
        f"{escape(hit['title'])}"
        "</li>"
        for hit in facts.get("recent_frags") or []
    )
    frag_block = (
        f"<h2>Kill feed</h2><p class=\"meta\">Frags from the last 7 days.</p><ul class=\"frags\">{frag_items}</ul>"
        if frag_items
        else ""
    )
    body = f"""    <p class="lede">Where work landed. Merged pull requests, by area and by the people who shipped them.</p>
    <p class="meta">Snapshot {escape(snapshot["generated_at"])} · {snapshot["pr_count"]} merged PRs</p>
    <ul class="facts">
      <li>People who merged in 30 / 90 days: <strong>{facts["unique_people"]["30d"]}</strong> / <strong>{facts["unique_people"]["90d"]}</strong></li>
      <li>Last 90 days, share of merges from the busiest 5 logins: <strong>{conc["top5"]}%</strong></li>
      <li>Of people who merged in the prior 90 days, still merging: <strong>{ret_s}</strong> ({ret["stayed"]} of {ret["prior"]})</li>
      <li>Median days a merged PR sat open (90 days): <strong>{escape(lead_s)}</strong></li>
      <li>Pipe, last 90 days: {escape(funnel_line) if funnel_line else "—"}</li>
    </ul>
    <table>
      <thead>
        <tr>
          <th>Area</th><th>30 days</th><th>90 days</th><th>All</th>
          <th>People (90d)</th><th>Median days open</th>
        </tr>
      </thead>
      <tbody>
{chr(10).join("        " + row for row in rows)}
      </tbody>
    </table>
    <h2>Merges by week</h2>
    {week_table(facts["weekly"])}
    {frag_block}
    <p><a href="people.html">Beta ladder</a></p>
"""
    (SITE / "index.html").write_text(page("Omarchy Quattro Arena", body, root="."))


def write_people(summary):
    rows = []
    for person in summary["standings"]:
        placing = person.get("season", {}).get("placing")
        mark = ' <span class="placing">placing</span>' if placing else ""
        rows.append(
            "<tr>"
            f'<td>{person["rank"]}</td>'
            f'<th scope="row"><a href="{person_href(person["login"], ".")}">{escape(person["login"])}</a>{mark}</th>'
            f'<td>{escape(person.get("tier_label", ""))}</td>'
            f'<td>{person.get("season", {}).get("points", 0)}</td>'
            f'<td>{person.get("season", {}).get("event_count", 0)}</td>'
            f'<td>{person.get("lifetime_points", 0)}</td>'
            "</tr>"
        )
    body = f"""    <h1>Beta ladder</h1>
    <p>Order is seasonal score. Placing until 10 season merges and 14 days in.
    Class lives on the person page. <a href="classes.html">Category ladders</a>.</p>
    <table>
      <thead>
        <tr><th>#</th><th>Login</th><th>Tier</th><th>Beta</th><th>Merges</th><th>Lifetime</th></tr>
      </thead>
      <tbody>
{chr(10).join("        " + row for row in rows)}
      </tbody>
    </table>
"""
    (SITE / "people.html").write_text(
        page("Beta ladder — Omarchy Quattro Arena", body, root=".")
    )


def write_area(area, summary):
    label = AREA_LABELS.get(area, area)
    prs = summary["area_prs"].get(area, [])
    extra = summary["area_extra"].get(area, {})
    counts = {}
    for person in summary["people"].values():
        n = person["area_counts"].get(area, 0)
        if n:
            counts[person["login"]] = n
    people_rows = "".join(
        "<tr>"
        f'<th scope="row"><a href="{person_href(login)}">{escape(login)}</a></th>'
        f"<td>{n}</td>"
        "</tr>"
        for login, n in sorted(counts.items(), key=lambda item: (-item[1], item[0].lower()))
    )
    lead = extra.get("median_days_open")
    lead_s = "—" if lead is None else f"{lead} days"
    unique = extra.get("unique_people", {})
    season_board = summary.get("area_season", {}).get(area, [])
    season_rows = []
    last_pts = None
    place = 0
    shown = 0
    for row in season_board:
        shown += 1
        pts = row["points"]
        if pts != last_pts:
            place = shown
            last_pts = pts
        person = row["person"]
        placing = person.get("season", {}).get("placing")
        mark = ' <span class="placing">placing</span>' if placing else ""
        season_rows.append(
            "<tr>"
            f"<td>{place}</td>"
            f'<th scope="row"><a href="{person_href(person["login"])}">{escape(person["login"])}</a>{mark}</th>'
            f'<td>{escape(person.get("tier_label") or "—")}</td>'
            f"<td>{pts}</td>"
            "</tr>"
        )
    season_table = (
        "<table>"
        "<thead><tr><th>#</th><th>Login</th><th>Tier</th><th>Here</th></tr></thead>"
        f"<tbody>{''.join(season_rows)}</tbody></table>"
        if season_rows
        else "<p>No Beta points in this area yet.</p>"
    )
    body = f"""    <h1>{escape(label)}</h1>
    <p>{len(prs)} merged PRs. People in 30 / 90 / all: {unique.get("30d", 0)} / {unique.get("90d", 0)} / {unique.get("all", 0)}. Median days open: {escape(lead_s)}.</p>
    <h2>Beta ladder here</h2>
    <p>Seasonal points from merges that touched this folder, split when a merge hits several areas.</p>
    {season_table}
    <h2>People in this area</h2>
    <table>
      <thead><tr><th>Login</th><th>Merges here</th></tr></thead>
      <tbody>{people_rows}</tbody>
    </table>
    <h2>Merges by week</h2>
    {week_table(extra.get("weekly") or [])}
    <h2>Pull requests</h2>
    {pr_list(prs)}
"""
    directory = SITE / "area"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{area}.html").write_text(
        page(f"{label} — Omarchy Quattro Arena", body, root="..")
    )


def sheet_row(term, value):
    return f"<dt>{escape(term)}</dt><dd>{value}</dd>"


def standing_line(person):
    info = person.get("class") or {}
    bits = []
    if person.get("rank"):
        bits.append(f'#{person["rank"]}')
        if person.get("tier_label"):
            bits.append(person["tier_label"])
    if info.get("label"):
        bits.append(info["label"])
    text = " ".join(bits) if bits else "—"
    html = escape(text)
    if info.get("source") == "lifetime" and info.get("label"):
        html += ' <span class="meta">lifetime mix</span>'
    if person.get("season", {}).get("placing"):
        html += ' <span class="placing">placing</span>'
    return html


def person_sheet(person):
    ach = person["achievements"]
    season = person.get("season") or {}
    info = person.get("class") or {}
    beta = str(season.get("points", 0))
    decay = season.get("decay")
    if decay is not None and decay < 1:
        beta += f' <span class="meta">×{decay}</span>'
    rows = []
    if info.get("secondary_label"):
        rows.append(sheet_row("Also", escape(info["secondary_label"])))
    rows += [
        sheet_row("Beta", beta),
        sheet_row("Lifetime", str(person.get("lifetime_points", 0))),
        sheet_row(
            "Catalog",
            f'{ach["percent"]}% ({ach["earned"]} of {ach["total"]})',
        ),
        sheet_row(
            "Merges",
            f'{season.get("event_count", 0)} this season / {len(person["prs"])} all',
        ),
        sheet_row(
            "Span",
            f'{escape(person["first_merged_at"][:10])} – {escape(person["last_merged_at"][:10])}',
        ),
        sheet_row(
            "Active",
            "last 90 days" if person["still_active"] else "not in the last 90 days",
        ),
    ]
    return (
        f'<p class="standing">{standing_line(person)}</p>\n    '
        '<dl class="sheet">\n      ' + "\n      ".join(rows) + "\n    </dl>"
    )


def write_person(person):
    login = person["login"]
    ach = person["achievements"]
    area_rows = "".join(
        "<tr>"
        f'<th scope="row"><a href="{area_href(area)}">{escape(AREA_LABELS.get(area, area))}</a></th>'
        f"<td>{person['area_counts'].get(area, 0)}</td>"
        "</tr>"
        for area in person["areas"]
    )
    earned = set(ach["ids"])
    catalog = "".join(
        "<li class=\"{cls}\">{mark} {label}</li>".format(
            cls="got" if aid in earned else "missing",
            mark="✓" if aid in earned else "·",
            label=escape(CATALOG_LABELS[aid]),
        )
        for aid, _ in CATALOG
    )
    log_rows = []
    for event in person.get("combat_log") or []:
        frag = (
            f'<span class="frag">{escape(event["frag"])}</span> '
            if event.get("frag")
            else ""
        )
        log_rows.append(
            "<li>"
            f'<time datetime="{escape(event["merged_at"])}">{escape(event["merged_at"][:10])}</time> '
            f"{frag}"
            f'<a href="{escape(event["url"])}">#{event["number"]}</a> '
            f"{escape(event['title'])} "
            f'<span class="pts">+{event["points"]}</span>'
            "</li>"
        )
    log_html = (
        "<ol class=\"prs combat\">" + "".join(log_rows) + "</ol>"
        if log_rows
        else "<p>No scored merges yet.</p>"
    )
    body = f"""    <h1>{escape(login)}</h1>
    {person_sheet(person)}
    <h2>Catalog</h2>
    <ul class="achievements">{catalog}</ul>
    <h2>Areas</h2>
    <table>
      <thead><tr><th>Area</th><th>Merges</th></tr></thead>
      <tbody>{area_rows}</tbody>
    </table>
    <h2>Combat log</h2>
    {log_html}
"""
    directory = SITE / "person"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{login}.html").write_text(
        page(f"{login} — Omarchy Quattro Arena", body, root="..")
    )


def write_class_board(class_id, people):
    jobs = load_classes()
    label = jobs["labels"].get(class_id, class_id)
    rows = []
    last_pts = None
    place = 0
    shown = 0
    for person in people:
        shown += 1
        pts = person.get("season", {}).get("points", 0)
        if pts != last_pts:
            place = shown
            last_pts = pts
        placing = person.get("season", {}).get("placing")
        mark = ' <span class="placing">placing</span>' if placing else ""
        rows.append(
            "<tr>"
            f"<td>{place}</td>"
            f'<th scope="row"><a href="{person_href(person["login"])}">{escape(person["login"])}</a>{mark}</th>'
            f'<td>{escape(person.get("tier_label") or "—")}</td>'
            f"<td>{pts}</td>"
            f'<td>{person.get("season", {}).get("event_count", 0)}</td>'
            "</tr>"
        )
    table = (
        "<table>"
        "<thead><tr><th>#</th><th>Login</th><th>Tier</th><th>Beta</th><th>Merges</th></tr></thead>"
        f"<tbody>{chr(10).join('        ' + row for row in rows)}</tbody></table>"
        if rows
        else "<p>No Beta merges in this class yet.</p>"
    )
    body = f"""    <h1>{escape(label)}</h1>
    <p>Beta ladder for this class. Primary mix only. Ordered by seasonal score.</p>
    {table}
    <p><a href="../classes.html">All category ladders</a></p>
"""
    directory = SITE / "class"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{class_id}.html").write_text(
        page(f"{label} — Omarchy Quattro Arena", body, root="..")
    )


def write_classes_index(summary):
    jobs = load_classes()
    boards = summary.get("class_boards") or {}
    class_items = "".join(
        "<li>"
        f'<a href="{class_href(class_id, ".")}">{escape(jobs["labels"][class_id])}</a>'
        f' — {len(boards.get(class_id) or [])}'
        "</li>"
        for class_id in jobs["order"]
    )
    area_items = "".join(
        "<li>"
        f'<a href="{area_href(area, ".")}">{escape(AREA_LABELS[area])}</a>'
        f' — {len(summary.get("area_season", {}).get(area) or [])}'
        "</li>"
        for area in AREA_ORDER
    )
    body = f"""    <h1>Category ladders</h1>
    <p>Season boards by labor and by folder. The overall ladder stays on
    <a href="people.html">People</a>.</p>
    <h2>Class</h2>
    <ul>{class_items}</ul>
    <h2>Area</h2>
    <ul>{area_items}</ul>
"""
    (SITE / "classes.html").write_text(
        page("Category ladders — Omarchy Quattro Arena", body, root=".")
    )


def write_methodology(snapshot):
    season = current_season()
    ranks = load_ranks()
    floors = ranks["absolute"]
    cuts = ranks["percentile"]
    jobs = load_classes()
    class_bits = ", ".join(
        escape(jobs["labels"][key]) for key in jobs["order"]
    )
    catalog = "".join(
        f"<li><strong>{escape(label)}</strong> (<code>{escape(aid)}</code>)</li>"
        for aid, label in CATALOG
    )
    body = f"""    <h1>How we count</h1>
    <p>Source: merged pull requests on
    <a href="https://github.com/basecamp/omarchy">{escape(snapshot["source"])}</a>.
    The login on the PR is the person who did the work.</p>
    <ul>
      <li><strong>Area counts</strong> — a merge that touches several folders is counted in each of those areas.</li>
      <li><strong>People (30 / 90)</strong> — distinct logins who merged in that window.</li>
      <li><strong>Busiest 5</strong> — share of merges in the window from the five logins with the most merges. A thin bench, not a prize.</li>
      <li><strong>Still merging</strong> — of logins who merged in the previous 90 days, how many also merged in the last 90.</li>
      <li><strong>Median days open</strong> — middle time from opening a PR to merge. How the pipe is moving.</li>
      <li><strong>Pipe</strong> — currently open PRs, merges in 90 days, and PRs closed without merge in 90 days. Opening is not credit.</li>
      <li><strong>Achievements</strong> — facts about landed work. Spreading across the tree fills the catalog on the person page. It is not the ladder sort.</li>
      <li><strong>Points</strong> — each merged PR scores <code>(area base + 2 × extra areas) × size × week</code>.
        Area base is 10 for shell/commands/hyprland/install/migrations, 8 for agent-skill/applications/systemd, 6 for themes/tests/docs/manual/config, 3 for other.
        Size is 0.6 for one file, 1.0 for 2–8 files, 1.15 for 9+.
        In a given week the 1st merge is full value, then 0.85, 0.70, … never below 0.25. Extra work still counts.</li>
      <li><strong>Frags</strong> — 2+ merges by the same login in 24 hours: Double Kill, Triple Kill, Multi Kill, Mega Kill, Monster Kill, Ultra Kill, Godlike. The home kill feed is those callouts from the last 7 days.</li>
      <li><strong>{escape(season["name"])} season</strong> — {escape(season["start"])} through {escape(season["end"])}. Seasonal points are merges in that window. After 21 days with no merge, seasonal score eases toward 40% of its raw value; it does not fall to zero. Placing while you have fewer than 10 season merges and have been in the season under 14 days.</li>
      <li><strong>Ladder</strong> — people with at least one season merge, ordered by seasonal score. Newcomer / Contributor / Active are point floors ({floors["contributor"]} / {floors["active"]}). Core / Elite / Legend / Omakase are the top {cuts["core"]} / {cuts["elite"]} / {cuts["legend"]} / {cuts["omakase"]} percent of that pool, and only if already Active. Peak this rebuild is the current tier; we do not yet keep a history across nights.</li>
      <li><strong>Person page</strong> — a sheet: class, place, tier, scores, catalog, areas, combat log.</li>
      <li><strong>Class</strong> — on the person page, not the overall ladder. Placeholder names: {class_bits}. Taken from this season’s scored areas (lifetime mix if they have no season merge). A merge that touches several areas splits its points among them. Migrations if that folder is the top area; otherwise those points count as Desktop. Secondary if a second bucket is at least {int(jobs["secondary_share"] * 100)}% of classified points. Names are temporary.</li>
      <li><strong>Category ladders</strong> — a season board per class (primary mix) and per area (points from merges that touched that folder, split across areas on the same merge).</li>
    </ul>
    <h2>Achievement catalog</h2>
    <ul class="catalog">{catalog}</ul>
    <p>Generated {escape(snapshot["generated_at"])}.</p>
"""
    (SITE / "methodology.html").write_text(
        page("How we count — Omarchy Quattro Arena", body, root=".")
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
  --got: #3f6212;
}
* { box-sizing: border-box; }
html { font-size: 18px; }
body {
  margin: 0 auto;
  max-width: 52rem;
  padding: 2rem 1.25rem 4rem;
  background: var(--paper);
  color: var(--ink);
  font-family: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
  line-height: 1.45;
}
header { margin-bottom: 2rem; }
nav { margin-top: 0.5rem; }
nav a { margin-right: 1rem; }
.mark { font-size: 1.15rem; margin: 0; }
.sub, .meta, footer, .areas { color: var(--muted); font-size: 0.92rem; }
a { color: var(--link); }
table { width: 100%; border-collapse: collapse; margin: 1.5rem 0; }
th, td { text-align: left; padding: 0.4rem 0.5rem; border-bottom: 1px solid var(--line); }
td { font-variant-numeric: tabular-nums; }
.lede { font-size: 1.15rem; }
.facts { padding-left: 1.2rem; }
ol.prs { padding-left: 1.25rem; }
ol.prs li { margin: 0.45rem 0; }
time { font-variant-numeric: tabular-nums; }
footer { margin-top: 3rem; border-top: 1px solid var(--line); padding-top: 1rem; }
ul.achievements { list-style: none; padding: 0; }
ul.achievements li.got { color: var(--got); }
ul.achievements li.missing { color: var(--muted); }
.weeks { max-width: 20rem; }
.frag { font-weight: 700; color: #9a3412; margin-right: 0.35rem; }
.pts { color: var(--muted); font-variant-numeric: tabular-nums; }
ul.frags { list-style: none; padding: 0; }
.placing { color: var(--muted); font-style: italic; font-weight: normal; }
.standing { font-size: 1.15rem; margin: 0.35rem 0 1rem; }
dl.sheet {
  display: grid;
  grid-template-columns: 7rem 1fr;
  gap: 0.2rem 1rem;
  margin: 1rem 0 1.75rem;
}
dl.sheet dt { color: var(--muted); margin: 0; }
dl.sheet dd { margin: 0; font-variant-numeric: tabular-nums; }
"""
    )


def main():
    snapshot = load_snapshot()
    summary = summarize(snapshot)
    SITE.mkdir(parents=True, exist_ok=True)
    write_css()
    write_home(snapshot, summary)
    write_people(summary)
    write_classes_index(summary)
    for class_id, group in (summary.get("class_boards") or {}).items():
        write_class_board(class_id, group)
    for area in AREA_ORDER:
        write_area(area, summary)
    for person in summary["people"].values():
        write_person(person)
    write_methodology(snapshot)
    (SITE / "snapshot.json").write_text(json.dumps(snapshot))
    print(
        f"wrote site/ ({len(summary['people'])} people, {snapshot['pr_count']} PRs)"
    )


if __name__ == "__main__":
    main()
