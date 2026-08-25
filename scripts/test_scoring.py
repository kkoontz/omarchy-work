#!/usr/bin/env python3
import unittest

from scoring import frag_for_count, raw_points, score_events, week_multiplier


def pr(n, merged, areas, files, author="a"):
    return {
        "number": n,
        "title": f"pr-{n}",
        "url": f"https://example.com/{n}",
        "merged_at": merged,
        "author": author,
        "areas": areas,
        "paths": [f"bin/x{i}" for i in range(files)] if files else [],
    }


class Formula(unittest.TestCase):
    def test_core_beats_other(self):
        core, _ = raw_points(pr(1, "2026-08-01T00:00:00Z", ["shell"], 3))
        other, _ = raw_points(pr(2, "2026-08-01T00:00:00Z", ["other"], 3))
        self.assertGreater(core, other)

    def test_one_file_is_reduced_not_zero(self):
        small, _ = raw_points(pr(1, "2026-08-01T00:00:00Z", ["commands"], 1))
        mid, _ = raw_points(pr(2, "2026-08-01T00:00:00Z", ["commands"], 3))
        self.assertGreater(mid, small)
        self.assertGreater(small, 0)

    def test_week_diminishes_but_never_stops(self):
        self.assertEqual(week_multiplier(0), 1.0)
        self.assertEqual(week_multiplier(1), 0.85)
        self.assertEqual(week_multiplier(20), 0.25)
        later = [
            pr(i, f"2026-08-03T{i:02d}:00:00Z", ["commands"], 3)
            for i in range(8)
        ]
        events, total = score_events(later)
        self.assertEqual(len(events), 8)
        self.assertGreater(total, 0)
        newest_week_indexes = sorted(e["week_index"] for e in events)
        self.assertEqual(newest_week_indexes[-1], 8)


class Frags(unittest.TestCase):
    def test_monster_kill(self):
        self.assertEqual(frag_for_count(6), "Monster Kill")
        self.assertEqual(frag_for_count(2), "Double Kill")
        self.assertIsNone(frag_for_count(1))

    def test_streak_from_timestamps(self):
        burst = [
            pr(i, f"2026-08-01T0{i}:00:00Z", ["shell"], 2)
            for i in range(3)
        ]
        events, _ = score_events(burst)
        # newest first: the third merge is Triple Kill
        self.assertEqual(events[0]["frag"], "Triple Kill")
        self.assertEqual(events[1]["frag"], "Double Kill")
        self.assertIsNone(events[2]["frag"])


if __name__ == "__main__":
    unittest.main()
