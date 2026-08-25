#!/usr/bin/env python3
import unittest

from areas import area_for_path, areas_for_paths


class AreaMapping(unittest.TestCase):
    def test_agent_skill_beats_other_default(self):
        self.assertEqual(area_for_path("default/agents/skills/omarchy/SKILL.md"), "agent-skill")

    def test_hyprland(self):
        self.assertEqual(area_for_path("default/hypr/bindings.lua"), "hyprland")

    def test_pr_spans_two_areas(self):
        self.assertEqual(
            areas_for_paths(["shell/bar.qml", "bin/omarchy-theme-set"]),
            ["shell", "commands"],
        )

    def test_unknown_is_other(self):
        self.assertEqual(areas_for_paths(["README.md"]), ["other"])

    def test_docs_and_tests(self):
        self.assertEqual(area_for_path("docs/testing.md"), "docs")
        self.assertEqual(area_for_path("test/cli"), "tests")


if __name__ == "__main__":
    unittest.main()
