#!/usr/bin/env python3
import unittest
from datetime import datetime, timezone

from seasons import current, decay_multiplier, in_season, season_status


class Seasons(unittest.TestCase):
    def test_beta_is_current(self):
        season = current()
        self.assertEqual(season["id"], "beta")
        self.assertEqual(season["start"], "2026-08-25")
        self.assertEqual(season["end"], "2026-12-31")

    def test_in_season(self):
        season = current()
        self.assertTrue(in_season("2026-08-25T00:00:00Z", season))
        self.assertFalse(in_season("2026-08-24T23:00:00Z", season))

    def test_decay_has_a_floor(self):
        self.assertEqual(decay_multiplier(21), 1.0)
        self.assertLess(decay_multiplier(40), 1.0)
        self.assertEqual(decay_multiplier(200), 0.4)

    def test_placement(self):
        season = current()
        now = datetime(2026, 9, 1, tzinfo=timezone.utc)
        events = [
            {
                "merged_at": "2026-08-26T00:00:00Z",
                "points": 10,
            }
        ]
        status = season_status(events, season, now=now)
        self.assertTrue(status["placing"])
        self.assertEqual(status["points"], 10.0)

    def test_decay_applies_after_idle(self):
        season = current()
        now = datetime(2026, 11, 1, tzinfo=timezone.utc)
        events = [
            {
                "merged_at": "2026-08-26T00:00:00Z",
                "points": 100,
            }
        ]
        status = season_status(events, season, now=now)
        self.assertEqual(status["points"], 40.0)
        self.assertFalse(status["placing"])
