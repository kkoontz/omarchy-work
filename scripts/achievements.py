"""Achievements for landed work. Rank is share earned, not PR volume."""

from datetime import datetime, timezone, timedelta

from areas import AREA_ORDER

NAMED_AREAS = tuple(area for area in AREA_ORDER if area != "other")

# Breadth and depth facts. Volume is a minority of the catalog so a
# pile of one-area PRs cannot max the board.
CATALOG = (
    ("landed", "Landed a merge"),
    ("still-active", "Landed in the last 90 days"),
    ("span-pr", "One merge touched two areas"),
    ("three-areas", "Worked in 3 areas"),
    ("five-areas", "Worked in 5 areas"),
    ("eight-areas", "Worked in 8 areas"),
    ("five-in-one-area", "Five merges in a single area"),
    ("ten-merges", "Ten merges"),
    ("area-shell", "Landed in Shell"),
    ("area-commands", "Landed in Commands"),
    ("area-agent-skill", "Landed in Agent skill"),
    ("area-hyprland", "Landed in Hyprland"),
    ("area-install", "Landed in Install"),
    ("area-migrations", "Landed in Migrations"),
    ("area-manual", "Landed in Manual"),
    ("area-themes", "Landed in Themes"),
    ("area-systemd", "Landed in Systemd"),
    ("area-config", "Landed in Config"),
    ("area-tests", "Landed in Tests"),
    ("area-docs", "Landed in Docs"),
    ("area-applications", "Landed in Applications"),
)

CATALOG_IDS = tuple(item[0] for item in CATALOG)
CATALOG_LABELS = dict(CATALOG)
TOTAL = len(CATALOG)

AREA_ACHIEVEMENT = {
    "shell": "area-shell",
    "commands": "area-commands",
    "agent-skill": "area-agent-skill",
    "hyprland": "area-hyprland",
    "install": "area-install",
    "migrations": "area-migrations",
    "manual": "area-manual",
    "themes": "area-themes",
    "systemd": "area-systemd",
    "config": "area-config",
    "tests": "area-tests",
    "docs": "area-docs",
    "applications": "area-applications",
}


def _area_counts(prs):
    counts = {area: 0 for area in AREA_ORDER}
    for pr in prs:
        for area in pr["areas"]:
            counts[area] = counts.get(area, 0) + 1
    return counts


def earned_ids(person, now=None):
    now = now or datetime.now(timezone.utc)
    prs = person["prs"]
    areas = set(person["areas"])
    named = {area for area in areas if area != "other"}
    counts = _area_counts(prs)
    last = datetime.strptime(person["last_merged_at"], "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )
    got = set()
    if prs:
        got.add("landed")
    if last >= now - timedelta(days=90):
        got.add("still-active")
    if any(len(pr["areas"]) >= 2 for pr in prs):
        got.add("span-pr")
    if len(named) >= 3:
        got.add("three-areas")
    if len(named) >= 5:
        got.add("five-areas")
    if len(named) >= 8:
        got.add("eight-areas")
    if any(n >= 5 for area, n in counts.items() if area != "other"):
        got.add("five-in-one-area")
    if len(prs) >= 10:
        got.add("ten-merges")
    for area, aid in AREA_ACHIEVEMENT.items():
        if counts.get(area, 0):
            got.add(aid)
    return [aid for aid in CATALOG_IDS if aid in got]


def score(person, now=None):
    got = earned_ids(person, now=now)
    return {
        "ids": got,
        "earned": len(got),
        "total": TOTAL,
        "percent": round(100.0 * len(got) / TOTAL, 1) if TOTAL else 0.0,
    }
