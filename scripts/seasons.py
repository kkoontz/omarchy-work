"""Season calendar, placement, and idle decay."""

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEASONS_PATH = ROOT / "data" / "seasons.json"

PLACEMENT_DAYS = 14
PLACEMENT_EVENTS = 10
DECAY_AFTER_DAYS = 21
DECAY_PER_DAY = 0.02
DECAY_FLOOR = 0.4


def load():
    return json.loads(SEASONS_PATH.read_text())


def current():
    data = load()
    wanted = data["current"]
    for season in data["seasons"]:
        if season["id"] == wanted:
            return season
    raise KeyError(f"no season named {wanted}")


def in_season(stamp, season):
    day = stamp[:10]
    return season["start"] <= day <= season["end"]


def decay_multiplier(idle_days):
    if idle_days is None or idle_days <= DECAY_AFTER_DAYS:
        return 1.0
    return max(DECAY_FLOOR, 1.0 - DECAY_PER_DAY * (idle_days - DECAY_AFTER_DAYS))


def season_status(events, season, now=None):
    now = now or datetime.now(timezone.utc)
    seasonal = [event for event in events if in_season(event["merged_at"], season)]
    raw = round(sum(event["points"] for event in seasonal), 2)
    if not seasonal:
        return {
            "raw": 0.0,
            "points": 0.0,
            "decay": 1.0,
            "idle_days": None,
            "placing": False,
            "event_count": 0,
        }
    last = max(event["merged_at"] for event in seasonal)
    first = min(event["merged_at"] for event in seasonal)
    last_dt = datetime.strptime(last, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    first_dt = datetime.strptime(first, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    idle_days = (now - last_dt).days
    decay = decay_multiplier(idle_days)
    days_in = (now - first_dt).days
    placing = len(seasonal) < PLACEMENT_EVENTS and days_in < PLACEMENT_DAYS
    return {
        "raw": raw,
        "points": round(raw * decay, 2),
        "decay": decay,
        "idle_days": idle_days,
        "placing": placing,
        "event_count": len(seasonal),
    }
