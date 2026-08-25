#!/usr/bin/env python3
import unittest
from datetime import datetime, timezone

from achievements import TOTAL, earned_ids, score
from summarize import concentration, median, retention


NOW = datetime(2026, 8, 25, tzinfo=timezone.utc)


def pr(author, merged, areas, created=None, number=1):
    return {
        "number": number,
        "title": "x",
        "url": "https://example.com",
        "created_at": created or merged,
        "merged_at": merged,
        "author": author,
        "areas": areas,
        "paths": [],
    }


class MedianTests(unittest.TestCase):
    def test_odd_and_empty(self):
        self.assertEqual(median([3, 1, 2]), 2)
        self.assertIsNone(median([]))


class ConcentrationTests(unittest.TestCase):
    def test_top_share(self):
        prs = [pr("a", "2026-08-01T00:00:00Z", ["shell"], number=i) for i in range(3)]
        prs += [pr("b", "2026-08-01T00:00:00Z", ["shell"], number=10)]
        result = concentration(prs)
        self.assertEqual(result["top1"], 75.0)
        self.assertEqual(result["n"], 4)


class RetentionTests(unittest.TestCase):
    def test_stayed(self):
        prs = [
            pr("old", "2026-04-01T00:00:00Z", ["shell"], number=1),
            pr("kept", "2026-04-01T00:00:00Z", ["shell"], number=2),
            pr("kept", "2026-08-01T00:00:00Z", ["shell"], number=3),
            pr("new", "2026-08-01T00:00:00Z", ["shell"], number=4),
        ]
        result = retention(prs, NOW)
        self.assertEqual(result["prior"], 2)
        self.assertEqual(result["stayed"], 1)
        self.assertEqual(result["percent"], 50.0)


class AchievementTests(unittest.TestCase):
    def test_quantity_does_not_max_the_catalog(self):
        person = {
            "login": "farm",
            "prs": [
                pr("farm", "2026-08-01T00:00:00Z", ["commands"], number=i)
                for i in range(12)
            ],
            "areas": ["commands"],
            "last_merged_at": "2026-08-01T00:00:00Z",
        }
        got = set(earned_ids(person, now=NOW))
        self.assertIn("landed", got)
        self.assertIn("ten-merges", got)
        self.assertIn("area-commands", got)
        self.assertNotIn("three-areas", got)
        self.assertLess(len(got), TOTAL)

    def test_breadth_scores_higher_percent(self):
        areas = ["shell", "commands", "hyprland", "install", "tests"]
        wide = {
            "login": "wide",
            "prs": [
                pr("wide", "2026-08-01T00:00:00Z", [area], number=i)
                for i, area in enumerate(areas)
            ],
            "areas": areas,
            "last_merged_at": "2026-08-01T00:00:00Z",
        }
        farm = {
            "login": "farm",
            "prs": [
                pr("farm", "2026-08-01T00:00:00Z", ["commands"], number=i)
                for i in range(12)
            ],
            "areas": ["commands"],
            "last_merged_at": "2026-08-01T00:00:00Z",
        }
        self.assertGreater(
            score(wide, now=NOW)["percent"], score(farm, now=NOW)["percent"]
        )


if __name__ == "__main__":
    unittest.main()
