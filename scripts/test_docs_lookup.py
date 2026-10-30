"""Tests for the planning-docs lookup (ADR-051)."""

import io
import os
import tempfile
import unittest

from scripts.docs_lookup import NotFound, adr, main, next_task, run_order, section, task

# The shapes the lookup reads: the glance table, task rows (one with an escaped pipe),
# the Run order table, the ADR index and entries, a roadmap row and plain sections.
PLAN = """\
# Plan

## Backlog at a glance

| Epic | Name | Branch | Status | Tasks | Blocked by |
|---|---|---|---|---|---|
| [1](#epic-1) | Stabilize | `phase-1-repo-cleanup` | **Done** | 2 | — |
| [2](#epic-2) | Security | `phase-2-security-hardening` | Not started | 3 | — |

### Run order

| # | Task | Why here |
|---|---|---|
| 1 | 1.2 | Pulled forward (ADR-047) |
| 2 | 2.1 | |
| 3 | 2.2 | |

## Epic 1 — Stabilize

| ID | Task | Status | Notes |
|---|---|---|---|
| 1.1 | Guard `a\\|b` | **Done** 2026-10-09 | ADR-038 · PR #36 |
| 1.2 | Template | **Done** 2026-10-16 | ADR-037 · PR #38 |

## Epic 2 — Security

| ID | Task | Status | Notes |
|---|---|---|---|
| 2.1 | Secrets | Blocked | Waits on roadmap 11.1 (ADR-049) |
| 2.2 | Validate input | Not started | Business-rule validation is 4.8 |
| 2.11 | Not 2.1 | Not started | ADR-028 |
"""

DECISIONS = """\
# Decisions

## Index

| # | Title | Status | Decision |
|---|---|---|---|
| [001](#adr-001) | Branching | **Superseded by 010** | — |
| [010](#adr-010) | Branch model | Accepted (supersedes 001; amended by 037) | main integrates |
| [037](#adr-037) | One task, one PR | Accepted | One PR per task |

## ADR-001: Branching

**Superseded by 010.**

## ADR-010: Branch model

- **Decision:** main integrates.
- **Rejected:** GitFlow — too much ceremony.

## ADR-037: One task, one PR

- **Decision:** one PR per task.
"""

ROADMAP = """\
| # | Question | Why |
|---|---|---|
| 11.1 | What is personal data? | Blocks 2.1 |
"""

REQUIREMENTS = """\
# Requirements

## User roles

Three roles.

### Owner

Owns the tenant.

## Business rules

Costs in Decimal.
"""


class TaskTests(unittest.TestCase):
    def test_row_is_returned_verbatim_with_its_branch(self):
        found = task(PLAN, "1.1")
        self.assertIn("branch phase-1-repo-cleanup-1.1", found)
        self.assertIn("Task:   Guard `a\\|b`", found)
        self.assertIn("Notes:  ADR-038 · PR #36", found)

    def test_an_id_matches_exactly_not_as_a_prefix(self):
        self.assertIn("Task:   Secrets", task(PLAN, "2.1"))
        self.assertIn("Task:   Not 2.1", task(PLAN, "2.11"))

    def test_blocked_and_no_adr_are_flagged(self):
        self.assertIn("! Blocked", task(PLAN, "2.1"))
        self.assertIn("cite no ADR", task(PLAN, "2.2"))
        self.assertNotIn("!", task(PLAN, "1.1"))

    def test_a_missing_task_is_not_found(self):
        with self.assertRaises(NotFound):
            task(PLAN, "9.9")


class NextTaskTests(unittest.TestCase):
    def test_run_order_is_read_in_order(self):
        self.assertEqual(
            [task_id for task_id, _ in run_order(PLAN)], ["1.2", "2.1", "2.2"]
        )

    def test_the_first_entry_not_done_is_returned_even_when_blocked(self):
        found = next_task(PLAN)
        self.assertIn("Task 2.1", found)
        self.assertIn("! Blocked", found)

    def test_an_exhausted_run_order_stops(self):
        done = PLAN.replace("| Blocked |", "| **Done** |").replace(
            "| Not started | Business", "| Done | Business"
        )
        with self.assertRaises(NotFound):
            next_task(done)


class AdrTests(unittest.TestCase):
    def test_an_entry_is_returned_in_full(self):
        found = adr(DECISIONS, 37)
        self.assertTrue(found.startswith("## ADR-037: One task, one PR"))
        self.assertNotIn("ADR-010", found)

    def test_supersession_is_followed(self):
        found = adr(DECISIONS, 1)
        self.assertIn("superseded by ADR-010", found)
        self.assertIn("GitFlow — too much ceremony", found)

    def test_related_adrs_from_the_index_are_named(self):
        self.assertIn("Related: 001, 037", adr(DECISIONS, 10))

    def test_a_missing_adr_is_not_found(self):
        with self.assertRaises(NotFound):
            adr(DECISIONS, 999)


class SectionTests(unittest.TestCase):
    def test_a_section_runs_to_its_next_sibling_and_keeps_subsections(self):
        found = section(REQUIREMENTS, "user roles", "req")
        self.assertIn("Owns the tenant.", found)
        self.assertNotIn("Business rules", found)

    def test_a_missing_heading_lists_the_headings(self):
        with self.assertRaises(NotFound) as caught:
            section(REQUIREMENTS, "nothing", "req")
        self.assertIn("## Business rules", str(caught.exception))


class MainTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, "docs"))
        for name, text in (
            ("PRODUCTION_UPDATE_PLAN.md", PLAN),
            ("docs/decisions.md", DECISIONS),
            ("docs/roadmap.md", ROADMAP),
            ("docs/project_requirements.md", REQUIREMENTS),
        ):
            with open(os.path.join(self.root, name), "w", encoding="utf-8") as file:
                file.write(text)

    def run_main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        import scripts.docs_lookup as module

        original = module.ROOT
        module.ROOT = self.root
        try:
            code = main(list(argv), out, err)
        finally:
            module.ROOT = original
        return code, out.getvalue(), err.getvalue()

    def test_roadmap_row(self):
        code, out, _ = self.run_main("roadmap", "11.1")
        self.assertEqual(code, 0)
        self.assertIn("What is personal data?", out)

    def test_not_found_exits_1_with_a_reason(self):
        code, out, err = self.run_main("roadmap", "11.9")
        self.assertEqual((code, out), (1, ""))
        self.assertIn("no open question 11.9", err)


if __name__ == "__main__":
    unittest.main()
