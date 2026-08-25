"""Primary/secondary class from an area mix of scored events."""

from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLASSES_PATH = ROOT / "data" / "classes.json"


def load():
    return json.loads(CLASSES_PATH.read_text())


def _empty(source=None):
    return {
        "primary": None,
        "label": None,
        "secondary": None,
        "secondary_label": None,
        "source": source,
    }


def area_points(events):
    totals = Counter()
    for event in events:
        areas = [area for area in (event.get("areas") or []) if area != "other"]
        if not areas:
            continue
        share = event["points"] / len(areas)
        for area in areas:
            totals[area] += share
    return totals


def _bucket_points(area_totals, config):
    scores = Counter()
    for bucket, areas in config["buckets"].items():
        scores[bucket] = sum(area_totals.get(area, 0) for area in areas)
    return scores


def classify(events, config=None, source=None):
    config = config or load()
    totals = area_points(events)
    if not totals:
        return _empty(source)
    scores = _bucket_points(totals, config)
    order = config.get("order") or list(config["labels"])
    ranked = [
        (bucket, points)
        for bucket, points in scores.items()
        if points > 0
    ]
    ranked.sort(
        key=lambda item: (
            -item[1],
            order.index(item[0]) if item[0] in order else 99,
        )
    )
    if not ranked:
        return _empty(source)
    classified = sum(points for _, points in ranked)
    primary = ranked[0][0]
    secondary = None
    if (
        len(ranked) > 1
        and ranked[1][1] / classified >= config["secondary_share"]
    ):
        secondary = ranked[1][0]
    labels = config["labels"]
    return {
        "primary": primary,
        "label": labels[primary],
        "secondary": secondary,
        "secondary_label": labels[secondary] if secondary else None,
        "source": source,
    }


def display(info):
    if not info or not info.get("label"):
        return "—"
    if info.get("secondary_label"):
        return f"{info['label']} / {info['secondary_label']}"
    return info["label"]


def for_person(person, in_season):
    events = person.get("combat_log") or []
    seasonal = [event for event in events if in_season(event["merged_at"])]
    if seasonal:
        return classify(seasonal, source="season")
    if events:
        return classify(events, source="lifetime")
    return _empty()
