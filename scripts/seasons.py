"""Season calendar. Scoring comes later; identity uses the current season name."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEASONS_PATH = ROOT / "data" / "seasons.json"


def load():
    return json.loads(SEASONS_PATH.read_text())


def current():
    data = load()
    wanted = data["current"]
    for season in data["seasons"]:
        if season["id"] == wanted:
            return season
    raise KeyError(f"no season named {wanted}")
