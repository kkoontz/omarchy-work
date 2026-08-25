#!/usr/bin/env python3
import unittest

from classes import classify, display, for_person

CONFIG = {
    "secondary_share": 0.3,
    "order": [
        "session",
        "bin",
        "image",
        "migrations",
        "themes",
        "plugins",
        "docs",
    ],
    "labels": {
        "session": "Session",
        "bin": "Bin",
        "image": "Image",
        "migrations": "Migrations",
        "themes": "Themes",
        "plugins": "Plugins",
        "docs": "Docs",
    },
    "buckets": {
        "session": ["shell", "hyprland"],
        "bin": ["commands", "systemd", "config", "tests"],
        "image": ["install"],
        "migrations": ["migrations"],
        "themes": ["themes"],
        "plugins": ["applications", "agent-skill"],
        "docs": ["manual", "docs"],
    },
}


def event(points, areas):
    return {"points": points, "areas": areas, "merged_at": "2026-08-12T00:00:00Z"}


class Mix(unittest.TestCase):
    def test_empty(self):
        info = classify([], config=CONFIG)
        self.assertIsNone(info["primary"])
        self.assertEqual(display(info), "—")

    def test_session_vs_bin(self):
        info = classify(
            [event(10, ["shell"]), event(10, ["hyprland"])],
            config=CONFIG,
        )
        self.assertEqual(info["label"], "Session")
        info = classify([event(10, ["commands"])], config=CONFIG)
        self.assertEqual(info["label"], "Bin")

    def test_migrations_is_its_own_bucket(self):
        info = classify(
            [event(40, ["migrations"]), event(20, ["shell"])],
            config=CONFIG,
        )
        self.assertEqual(info["primary"], "migrations")
        self.assertEqual(info["secondary"], "session")

    def test_secondary_at_thirty_percent(self):
        info = classify(
            [event(70, ["themes"]), event(30, ["manual"])],
            config=CONFIG,
        )
        self.assertEqual(info["label"], "Themes")
        self.assertEqual(info["secondary_label"], "Docs")
        self.assertEqual(display(info), "Themes / Docs")

    def test_no_secondary_below_thirty(self):
        info = classify(
            [event(80, ["themes"]), event(20, ["manual"])],
            config=CONFIG,
        )
        self.assertEqual(info["label"], "Themes")
        self.assertIsNone(info["secondary"])

    def test_split_across_areas_on_one_event(self):
        info = classify([event(10, ["themes", "manual"])], config=CONFIG)
        self.assertEqual(info["label"], "Themes")
        self.assertEqual(info["secondary_label"], "Docs")

    def test_other_does_not_classify(self):
        info = classify([event(10, ["other"])], config=CONFIG)
        self.assertIsNone(info["primary"])


class PersonSource(unittest.TestCase):
    def test_season_beats_lifetime(self):
        person = {
            "combat_log": [
                {
                    "points": 10,
                    "areas": ["themes"],
                    "merged_at": "2026-08-12T00:00:00Z",
                },
                {
                    "points": 50,
                    "areas": ["shell"],
                    "merged_at": "2026-01-01T00:00:00Z",
                },
            ]
        }
        info = for_person(person, lambda stamp: stamp.startswith("2026-08"))
        self.assertEqual(info["label"], "Themes")
        self.assertEqual(info["source"], "season")

    def test_lifetime_when_no_season_events(self):
        person = {
            "combat_log": [
                {
                    "points": 10,
                    "areas": ["docs"],
                    "merged_at": "2026-01-01T00:00:00Z",
                }
            ]
        }
        info = for_person(person, lambda stamp: False)
        self.assertEqual(info["label"], "Docs")
        self.assertEqual(info["source"], "lifetime")


if __name__ == "__main__":
    unittest.main()
