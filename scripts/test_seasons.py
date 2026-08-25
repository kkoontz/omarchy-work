#!/usr/bin/env python3
import unittest

from seasons import current


class Seasons(unittest.TestCase):
    def test_beta_is_current(self):
        season = current()
        self.assertEqual(season["id"], "beta")
        self.assertEqual(season["start"], "2026-08-25")
        self.assertEqual(season["end"], "2026-12-31")


if __name__ == "__main__":
    unittest.main()
