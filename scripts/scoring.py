"""Points for merged PRs. Extra work still counts; later merges in a week pay less."""

from collections import defaultdict
from datetime import datetime, timezone, timedelta

# Highest matching area sets the base. Extra areas add a small breadth bonus.
AREA_BASE = {
    "shell": 10,
    "commands": 10,
    "hyprland": 10,
    "install": 10,
    "migrations": 10,
    "agent-skill": 8,
    "applications": 8,
    "systemd": 8,
    "themes": 6,
    "tests": 6,
    "docs": 6,
    "manual": 6,
    "config": 6,
    "other": 3,
}

BREADTH_BONUS = 2
WEEK_STEP = 0.15
WEEK_FLOOR = 0.25


def parse_time(stamp):
    return datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )


def week_monday(stamp):
    day = parse_time(stamp).date()
    return day - timedelta(days=day.weekday())


def size_multiplier(path_count):
    if path_count <= 1:
        return 0.6
    if path_count <= 8:
        return 1.0
    return 1.15


def week_multiplier(index):
    """index is 0-based order within that login's ISO week."""
    return max(WEEK_FLOOR, 1.0 - WEEK_STEP * index)


def area_base(areas):
    if not areas:
        return AREA_BASE["other"]
    return max(AREA_BASE.get(area, AREA_BASE["other"]) for area in areas)


def raw_points(pr):
    areas = pr.get("areas") or ["other"]
    paths = pr.get("paths") or []
    base = area_base(areas)
    extra = max(0, len(set(areas) - {"other"}) - 1)
    size = size_multiplier(len(paths) if paths else 2)
    raw = (base + BREADTH_BONUS * extra) * size
    return round(raw, 2), {
        "base": base,
        "breadth": extra,
        "files": len(paths),
        "size": size,
    }


FRAGS = (
    (8, "Godlike"),
    (7, "Ultra Kill"),
    (6, "Monster Kill"),
    (5, "Mega Kill"),
    (4, "Multi Kill"),
    (3, "Triple Kill"),
    (2, "Double Kill"),
)


def frag_for_count(n):
    for threshold, name in FRAGS:
        if n >= threshold:
            return name
    return None


def score_events(prs):
    """Return scored events newest-first, plus lifetime total."""
    ordered = sorted(prs, key=lambda pr: pr["merged_at"])
    week_counts = defaultdict(int)
    events = []
    times = []
    for pr in ordered:
        raw, detail = raw_points(pr)
        week = week_monday(pr["merged_at"])
        idx = week_counts[week]
        week_counts[week] += 1
        week_mult = week_multiplier(idx)
        points = round(raw * week_mult, 2)
        stamp = parse_time(pr["merged_at"])
        window = stamp - timedelta(hours=24)
        streak = 1 + sum(1 for t in times if t > window)
        times.append(stamp)
        events.append(
            {
                "number": pr["number"],
                "title": pr["title"],
                "url": pr["url"],
                "merged_at": pr["merged_at"],
                "author": pr["author"],
                "areas": pr.get("areas") or [],
                "points": points,
                "raw": raw,
                "week_index": idx + 1,
                "week_mult": week_mult,
                "frag": frag_for_count(streak),
                "detail": detail,
            }
        )
    events.reverse()
    total = round(sum(event["points"] for event in events), 2)
    return events, total
