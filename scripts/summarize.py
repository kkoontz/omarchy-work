"""Facts derived from a snapshot of merged PRs."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta

from achievements import score as achievement_score
from areas import AREA_ORDER
from classes import area_points
from classes import for_person as classify_person
from classes import load as load_classes
from ranks import assign as assign_ladder
from ranks import load_peaks
from ranks import merge_peaks
from scoring import score_events
from seasons import current as current_season
from seasons import in_season
from seasons import season_status

WINDOWS = {
    "30d": timedelta(days=30),
    "90d": timedelta(days=90),
    "all": None,
}


def parse_time(stamp):
    return datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )


def in_window(stamp, now, delta):
    if delta is None:
        return True
    return parse_time(stamp) >= now - delta


def median(values):
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def days_open(pr):
    created = pr.get("created_at")
    merged = pr.get("merged_at")
    if not created or not merged:
        return None
    return (parse_time(merged) - parse_time(created)).total_seconds() / 86400


def week_monday(stamp):
    day = parse_time(stamp).date()
    monday = day - timedelta(days=day.weekday())
    return monday.isoformat()


def prs_in_window(prs, now, delta):
    return [pr for pr in prs if in_window(pr["merged_at"], now, delta)]


def unique_people(prs):
    return {pr["author"] for pr in prs}


def concentration(prs):
    if not prs:
        return {"top1": None, "top5": None, "n": 0}
    counts = Counter(pr["author"] for pr in prs)
    ranked = [n for _, n in counts.most_common()]
    total = len(prs)
    top1 = ranked[0] / total
    top5 = sum(ranked[:5]) / total
    return {
        "top1": round(100 * top1, 1),
        "top5": round(100 * top5, 1),
        "n": total,
    }


def retention(prs, now):
    recent = unique_people(prs_in_window(prs, now, timedelta(days=90)))
    prior = unique_people(
        [
            pr
            for pr in prs
            if in_window(pr["merged_at"], now, timedelta(days=180))
            and not in_window(pr["merged_at"], now, timedelta(days=90))
        ]
    )
    if not prior:
        return {"prior": 0, "stayed": 0, "percent": None}
    stayed = len(prior & recent)
    return {
        "prior": len(prior),
        "stayed": stayed,
        "percent": round(100.0 * stayed / len(prior), 1),
    }


def weekly_counts(prs, weeks=26, now=None):
    now = now or datetime.now(timezone.utc)
    start = (now.date() - timedelta(days=now.date().weekday())) - timedelta(
        weeks=weeks - 1
    )
    buckets = {}
    cursor = start
    today = now.date()
    while cursor <= today:
        buckets[cursor.isoformat()] = 0
        cursor += timedelta(days=7)
    for pr in prs:
        key = week_monday(pr["merged_at"])
        if key in buckets:
            buckets[key] += 1
    return [{"week": week, "merges": n} for week, n in buckets.items()]


def lead_times(prs):
    values = [days_open(pr) for pr in prs]
    values = [v for v in values if v is not None]
    med = median(values)
    return None if med is None else round(med, 1)


def build_people(prs, now):
    season = current_season()
    people = {}
    for pr in prs:
        login = pr["author"]
        person = people.setdefault(
            login,
            {
                "login": login,
                "prs": [],
                "areas": set(),
                "area_counts": Counter(),
                "first_merged_at": pr["merged_at"],
                "last_merged_at": pr["merged_at"],
            },
        )
        person["prs"].append(pr)
        person["areas"].update(pr["areas"])
        for area in pr["areas"]:
            person["area_counts"][area] += 1
        if pr["merged_at"] < person["first_merged_at"]:
            person["first_merged_at"] = pr["merged_at"]
        if pr["merged_at"] > person["last_merged_at"]:
            person["last_merged_at"] = pr["merged_at"]
    for person in people.values():
        person["areas"] = sorted(
            person["areas"],
            key=lambda area: AREA_ORDER.index(area) if area in AREA_ORDER else 99,
        )
        person["prs"].sort(key=lambda item: item["merged_at"], reverse=True)
        person["area_counts"] = dict(person["area_counts"])
        person["achievements"] = achievement_score(person, now=now)
        person["still_active"] = in_window(
            person["last_merged_at"], now, timedelta(days=90)
        )
        events, total = score_events(person["prs"])
        person["combat_log"] = events
        person["lifetime_points"] = total
        person["season"] = season_status(events, season, now=now)
        person["class"] = classify_person(
            person, lambda stamp, window=season: in_season(stamp, window)
        )
    return people


def recent_frags(people, now, days=7):
    cutoff = now - timedelta(days=days)
    hits = []
    for person in people.values():
        for event in person.get("combat_log") or []:
            if not event.get("frag"):
                continue
            if parse_time(event["merged_at"]) < cutoff:
                continue
            hits.append(
                {
                    "login": person["login"],
                    "frag": event["frag"],
                    "merged_at": event["merged_at"],
                    "number": event["number"],
                    "title": event["title"],
                    "url": event["url"],
                }
            )
    hits.sort(key=lambda item: item["merged_at"], reverse=True)
    return hits[:20]


def rank_people(people, season=None):
    season = season or current_season()
    archive, prior = load_peaks(season["id"])
    ladder = assign_ladder(people.values(), peaks=prior)
    return ladder, merge_peaks(archive, season["id"], ladder)


def rank_lifetime(people):
    ordered = sorted(
        [person for person in people.values() if person.get("lifetime_points", 0) > 0],
        key=lambda person: (-person["lifetime_points"], person["login"].lower()),
    )
    last_points = None
    place = 0
    shown = 0
    for person in ordered:
        shown += 1
        pts = person["lifetime_points"]
        if pts != last_points:
            place = shown
            last_points = pts
        person["lifetime_rank"] = place
    return ordered


def class_boards(people, config=None):
    config = config or load_classes()
    boards = {key: [] for key in config["order"]}
    for person in people.values():
        info = person.get("class") or {}
        if info.get("source") != "season" or not info.get("primary"):
            continue
        boards.setdefault(info["primary"], []).append(person)
    for group in boards.values():
        group.sort(
            key=lambda person: (
                -person["season"]["points"],
                person["login"].lower(),
            )
        )
    return boards


def area_season_boards(people, season):
    boards = {area: [] for area in AREA_ORDER}
    for person in people.values():
        events = [
            event
            for event in person.get("combat_log") or []
            if in_season(event["merged_at"], season)
        ]
        for area, points in area_points(events).items():
            if points <= 0:
                continue
            boards.setdefault(area, []).append(
                {"person": person, "points": round(points, 2)}
            )
    for group in boards.values():
        group.sort(
            key=lambda row: (-row["points"], row["person"]["login"].lower())
        )
    return boards


def summarize(snapshot, now=None):
    now = now or datetime.now(timezone.utc)
    prs = snapshot["prs"]
    area_counts = {area: {key: 0 for key in WINDOWS} for area in AREA_ORDER}
    area_prs = defaultdict(list)
    for pr in prs:
        if "areas" not in pr:
            continue
        for area in pr["areas"]:
            area_prs[area].append(pr)
            for key, delta in WINDOWS.items():
                if in_window(pr["merged_at"], now, delta):
                    area_counts.setdefault(area, {k: 0 for k in WINDOWS})
                    area_counts[area][key] += 1
    people = build_people(prs, now)
    season = current_season()
    standings, peaks = rank_people(people, season)
    lifetime = rank_lifetime(people)
    window_prs = {
        key: prs_in_window(prs, now, delta) for key, delta in WINDOWS.items()
    }
    facts = {
        "unique_people": {
            key: len(unique_people(window_prs[key])) for key in WINDOWS
        },
        "concentration": {
            key: concentration(window_prs[key]) for key in WINDOWS
        },
        "retention_90d": retention(prs, now),
        "median_days_open": lead_times(prs),
        "median_days_open_90d": lead_times(window_prs["90d"]),
        "weekly": weekly_counts(prs, weeks=26, now=now),
        "funnel_90d": snapshot.get("funnel_90d") or {},
        "recent_frags": recent_frags(people, now),
    }
    area_extra = {}
    for area in AREA_ORDER:
        group = area_prs.get(area, [])
        area_extra[area] = {
            "unique_people": {
                key: len(unique_people(prs_in_window(group, now, delta)))
                for key, delta in WINDOWS.items()
            },
            "median_days_open": lead_times(group),
            "weekly": weekly_counts(group, weeks=26, now=now),
        }
    return {
        "area_counts": area_counts,
        "area_prs": area_prs,
        "area_extra": area_extra,
        "people": people,
        "standings": standings,
        "lifetime": lifetime,
        "peaks": peaks,
        "class_boards": class_boards(people),
        "area_season": area_season_boards(people, season),
        "facts": facts,
        "now": now,
    }
