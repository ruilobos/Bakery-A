"""Tests for the template static-reference check (task 1.13, ADR-045)."""

import io
import unittest

from scripts.check_static_refs import check, run

FILES = {"css/site.css", "js/app.js", "img/logo.png"}


def outcome(html, static_url="/static/"):
    return check([("page.html", html)], FILES.__contains__, static_url)


class AcceptedFormTests(unittest.TestCase):
    def test_every_form_in_use_resolves(self):
        html = (
            '<link href="/static/css/site.css" rel="stylesheet">\n'
            '<script src="../../static/js/app.js"></script>\n'
            '<img src="static/img/logo.png">\n'
            '<script src="../static/js/app.js"></script>\n'
            "<img src=\"{% static 'img/logo.png' %}\">\n"
        )
        self.assertEqual(outcome(html), (5, []))

    def test_quotes_and_case_do_not_matter(self):
        self.assertEqual(outcome("<IMG SRC='/static/img/logo.png'>"), (1, []))

    def test_a_query_string_or_fragment_is_not_part_of_the_file(self):
        html = (
            '<link href="/static/css/site.css?v=2"><img src="/static/img/logo.png#top">'
        )
        self.assertEqual(outcome(html), (2, []))

    def test_the_prefix_follows_static_url(self):
        html = '<link href="/assets/css/site.css"><a href="static/notes/">'
        self.assertEqual(outcome(html, static_url="/assets/"), (1, []))


class ProblemTests(unittest.TestCase):
    def test_a_mangled_prefix_is_reported_with_its_line(self):
        html = '<footer>\n<script src="../..php/static/js/app.js"></script>'
        self.assertEqual(
            outcome(html),
            (
                1,
                [
                    "page.html:2: unrecognised static prefix in '../..php/static/js/app.js'"
                ],
            ),
        )

    def test_a_static_segment_under_another_path_is_reported(self):
        count, problems = outcome('<img src="/control/static/img/logo.png">')
        self.assertEqual(count, 1)
        self.assertIn("unrecognised static prefix", problems[0])

    def test_a_missing_file_is_reported(self):
        html = '<link href="/static/css/gone.css">\n<img src="{% static \'img/gone.png\' %}">'
        self.assertEqual(
            outcome(html),
            (
                2,
                [
                    "page.html:1: no static file named 'css/gone.css'",
                    "page.html:2: no static file named 'img/gone.png'",
                ],
            ),
        )


class IgnoredTests(unittest.TestCase):
    def test_links_that_name_no_static_file_are_ignored(self):
        html = (
            '<a href="https://www.example.com/static/x.png">\n'
            '<script src="//cdn.example.com/static/x.js"></script>\n'
            "<a href=\"{% url 'control:dashboard' %}\">\n"
            '<a href="#">\n'
            '<a href="../delete/">\n'
            '<a href="mailto:baker@example.com">\n'
            '<img src="/ecstatic/x.png">\n'
            '<img src="/staticky/x.png">\n'
        )
        self.assertEqual(outcome(html), (0, []))

    def test_a_static_tag_with_a_variable_cannot_be_checked(self):
        self.assertEqual(outcome('<img src="{% static logo %}">'), (0, []))

    def test_a_tag_inside_an_attribute_counts_once(self):
        self.assertEqual(
            outcome("<script src=\"{% static 'js/app.js' %}\"></script>"), (1, [])
        )


class RunTests(unittest.TestCase):
    def run_check(self, templates):
        out = io.StringIO()
        return run(templates, FILES.__contains__, out=out), out.getvalue()

    def test_resolving_references_pass_with_a_summary(self):
        code, output = self.run_check(
            [("page.html", '<img src="/static/img/logo.png">')]
        )
        self.assertEqual(code, 0)
        self.assertEqual(output, "All 1 static references in 1 templates resolve.\n")

    def test_problems_fail_and_are_each_listed(self):
        code, output = self.run_check(
            [("page.html", '<img src="/static/img/gone.png">')]
        )
        self.assertEqual(code, 1)
        self.assertEqual(
            output.splitlines(),
            [
                "page.html:1: no static file named 'img/gone.png'",
                "1 of 1 static references in 1 templates do not resolve.",
            ],
        )

    def test_no_templates_fails(self):
        code, output = self.run_check([])
        self.assertEqual(code, 1)
        self.assertIn("nothing was checked", output)
