#!/usr/bin/env python3
import unittest

from ranks import (
    absolute_tier,
    assign,
    higher_tier,
    percentile_tier,
    season_tier,
    top_percent,
)

CONFIG = {
    "order": [
        "newcomer",
        "contributor",
        "active",
        "core",
        "elite",
        "legend",
        "omakase",
    ],
    "labels": {
        "newcomer": "Newcomer",
        "contributor": "Contributor",
        "active": "Active",
        "core": "Core",
        "elite": "Elite",
        "legend": "Legend",
        "omakase": "Omakase",
    },
    "absolute": {"contributor": 20, "active": 40},
    "percentile": {"core": 50, "elite": 25, "legend": 10, "omakase": 5},
}


def player(login, points):
    return {"login": login, "season": {"points": points}}


class Floors(unittest.TestCase):
    def test_absolute(self):
        self.assertEqual(absolute_tier(0, CONFIG), "newcomer")
        self.assertEqual(absolute_tier(19.9, CONFIG), "newcomer")
        self.assertEqual(absolute_tier(20, CONFIG), "contributor")
        self.assertEqual(absolute_tier(39.9, CONFIG), "contributor")
        self.assertEqual(absolute_tier(40, CONFIG), "active")


class Percentiles(unittest.TestCase):
    def test_top_share(self):
        self.assertEqual(top_percent(1, 20), 5.0)
        self.assertEqual(top_percent(2, 20), 10.0)
        self.assertEqual(top_percent(5, 20), 25.0)
        self.assertEqual(top_percent(10, 20), 50.0)

    def test_cutoffs(self):
        self.assertEqual(percentile_tier(1, 20, CONFIG), "omakase")
        self.assertEqual(percentile_tier(2, 20, CONFIG), "legend")
        self.assertEqual(percentile_tier(5, 20, CONFIG), "elite")
        self.assertEqual(percentile_tier(10, 20, CONFIG), "core")
        self.assertIsNone(percentile_tier(11, 20, CONFIG))


class Combined(unittest.TestCase):
    def test_newcomer_does_not_skip(self):
        self.assertEqual(season_tier(12, 1, 20, CONFIG), "newcomer")

    def test_contributor_does_not_skip(self):
        self.assertEqual(season_tier(25, 1, 20, CONFIG), "contributor")

    def test_active_can_climb(self):
        self.assertEqual(season_tier(40, 1, 20, CONFIG), "omakase")
        self.assertEqual(season_tier(40, 11, 20, CONFIG), "active")

    def test_peak_keeps_the_higher(self):
        self.assertEqual(higher_tier("core", "elite", CONFIG), "elite")
        self.assertEqual(higher_tier("legend", "active", CONFIG), "legend")


class Ladder(unittest.TestCase):
    def test_order_and_ties(self):
        people = [player(f"n{i}", 12) for i in range(16)]
        people += [
            player("zero", 0),
            player("mid", 25),
            player("tie-b", 40),
            player("tie-a", 40),
            player("top", 200),
        ]
        ladder = assign(people, config=CONFIG)
        logins = [person["login"] for person in ladder[:5]]
        self.assertEqual(logins, ["top", "tie-a", "tie-b", "mid", "n0"])
        self.assertEqual(ladder[0]["tier"], "omakase")
        self.assertEqual(ladder[1]["rank"], 2)
        self.assertEqual(ladder[2]["rank"], 2)
        self.assertEqual(ladder[1]["tier"], "legend")
        self.assertEqual(ladder[3]["tier"], "contributor")
        self.assertEqual(ladder[4]["tier"], "newcomer")
        self.assertNotIn("rank", people[16])

    def test_peak_from_prior(self):
        people = [player("hero", 40)]
        ladder = assign(people, config=CONFIG, peaks={"hero": "omakase"})
        self.assertEqual(ladder[0]["tier"], "active")
        self.assertEqual(ladder[0]["peak_tier"], "omakase")


if __name__ == "__main__":
    unittest.main()
