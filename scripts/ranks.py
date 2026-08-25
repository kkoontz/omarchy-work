"""Season tiers from points and standing among people who merged this season."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RANKS_PATH = ROOT / "data" / "ranks.json"


def load():
    return json.loads(RANKS_PATH.read_text())


def _index(tier, config):
    return config["order"].index(tier)


def higher_tier(left, right, config):
    if left is None:
        return right
    if right is None:
        return left
    if _index(left, config) >= _index(right, config):
        return left
    return right


def absolute_tier(points, config):
    if points >= config["absolute"]["active"]:
        return "active"
    if points >= config["absolute"]["contributor"]:
        return "contributor"
    return "newcomer"


def top_percent(place, pool_size):
    if pool_size <= 0 or place is None:
        return None
    return 100.0 * place / pool_size


def percentile_tier(place, pool_size, config):
    share = top_percent(place, pool_size)
    if share is None:
        return None
    for tier in reversed(config["order"]):
        cutoff = config["percentile"].get(tier)
        if cutoff is not None and share <= cutoff:
            return tier
    return None


def is_bot(login, config):
    return bool(login) and login in (config.get("bots") or [])


def season_tier(points, place, pool_size, config, login=None):
    floor = absolute_tier(points, config)
    if is_bot(login, config):
        if _index(floor, config) > _index("active", config):
            return "active"
        return floor
    if _index(floor, config) < _index("active", config):
        return floor
    earned = percentile_tier(place, pool_size, config)
    return higher_tier(floor, earned, config)


def assign(people, config=None, peaks=None):
    """Ladder order is seasonal score. Mutates rank fields on season-active people."""
    config = config or load()
    peaks = peaks or {}
    active = [person for person in people if person.get("season", {}).get("points", 0) > 0]
    active.sort(
        key=lambda person: (
            -person["season"]["points"],
            person["login"].lower(),
        )
    )
    pool_size = len(active)
    last_points = None
    place = 0
    shown = 0
    for person in active:
        shown += 1
        points = person["season"]["points"]
        if points != last_points:
            place = shown
            last_points = points
        tier = season_tier(points, place, pool_size, config, login=person["login"])
        peak = higher_tier(tier, peaks.get(person["login"]), config)
        person["rank"] = place
        person["tier"] = tier
        person["tier_label"] = config["labels"][tier]
        person["peak_tier"] = peak
        person["peak_label"] = config["labels"][peak]
    return active
