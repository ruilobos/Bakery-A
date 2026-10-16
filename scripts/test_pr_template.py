"""Tests for the pull request template (task 1.16, ADR-037)."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / ".github" / "pull_request_template.md"
SKILL = ROOT / ".claude" / "skills" / "next-task" / "SKILL.md"

# A repo path the template names in backticks; placeholders like `<epic-branch>` never match.
NAMED_PATH = re.compile(r"`([\w./-]+\.(?:md|yml))`")


class PullRequestTemplateTests(unittest.TestCase):
    def test_it_is_where_github_reads_the_default_template(self):
        self.assertTrue(TEMPLATE.is_file())

    def test_every_repo_path_it_names_exists(self):
        named = NAMED_PATH.findall(TEMPLATE.read_text(encoding="utf-8"))
        self.assertTrue(named)
        self.assertEqual([path for path in named if not (ROOT / path).is_file()], [])

    def test_the_next_task_skill_points_at_it(self):
        skill = SKILL.read_text(encoding="utf-8")
        self.assertIn(".github/pull_request_template.md", skill)
