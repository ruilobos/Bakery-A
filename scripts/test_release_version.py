"""Tests for the release step's version rule (task 1.10, ADR-042)."""
import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

from scripts.release_version import ReleaseError, main, next_release


class FirstTagTests(unittest.TestCase):
    def test_first_tag_is_v0_1_0(self):
        self.assertEqual(next_release('Release v0.1.0', []), ('v0.1.0', None))

    def test_first_tag_cannot_be_anything_else(self):
        for title in ('Release v1.0.0', 'Release v0.0.1', 'Release v0.2.0'):
            with self.subTest(title=title):
                with self.assertRaisesRegex(ReleaseError, r'first tag is v0\.1\.0'):
                    next_release(title, [])

    def test_tags_that_are_not_releases_leave_it_the_first(self):
        tags = ['v0.2.0-rc1', 'v01.0.0', '0.3.0', 'latest', 'v1.0']
        self.assertEqual(next_release('Release v0.1.0', tags), ('v0.1.0', None))


class NextReleaseTests(unittest.TestCase):
    def test_each_successor_is_accepted(self):
        for tag in ('v0.1.1', 'v0.2.0', 'v1.0.0'):
            with self.subTest(tag=tag):
                self.assertEqual(next_release(f'Release {tag}', ['v0.1.0']), (tag, 'v0.1.0'))

    def test_anything_else_is_rejected(self):
        # the same version, a lower one, a skipped one, and bumps that do not reset
        for tag in ('v0.1.0', 'v0.0.9', 'v0.3.0', 'v0.2.1', 'v1.1.0', 'v2.0.0'):
            with self.subTest(tag=tag):
                with self.assertRaisesRegex(ReleaseError, r'cannot follow v0\.1\.0'):
                    next_release(f'Release {tag}', ['v0.1.0'])

    def test_the_error_names_the_allowed_versions(self):
        with self.assertRaisesRegex(ReleaseError, r'v0\.1\.1, v0\.2\.0 or v1\.0\.0\.$'):
            next_release('Release v0.3.0', ['v0.1.0'])

    def test_latest_is_by_number_not_by_text(self):
        tags = ['v0.9.0', 'v0.10.0', 'v0.2.0']
        self.assertEqual(next_release('Release v0.10.1', tags), ('v0.10.1', 'v0.10.0'))
        with self.assertRaises(ReleaseError):
            next_release('Release v0.9.1', tags)

    def test_tags_that_are_not_releases_are_ignored(self):
        tags = ['v0.1.0', 'v0.2.0-rc1', 'v9.9.9-beta', 'nightly']
        self.assertEqual(next_release('Release v0.2.0', tags), ('v0.2.0', 'v0.1.0'))


class TitleTests(unittest.TestCase):
    def test_malformed_titles_are_rejected(self):
        titles = (
            '', 'v0.1.0', 'Release 0.1.0', 'release v0.1.0', 'Release v0.1',
            'Release v0.1.0 and more', 'Release v00.1.0', 'Release v0.1.0-rc1',
            'Release  v0.1.0',
            'Release v1٠.0.0',  # 1 then an Arabic-Indic zero: \d and int() would read 10
        )
        for title in titles:
            with self.subTest(title=title):
                with self.assertRaisesRegex(ReleaseError, 'Release vX.Y.Z'):
                    next_release(title, [])

    def test_surrounding_whitespace_is_ignored(self):
        self.assertEqual(next_release('  Release v0.1.0 ', []), ('v0.1.0', None))


class MainTests(unittest.TestCase):
    def run_main(self, title, tags):
        """Run the CLI; return its exit code, what it printed and what it wrote to $GITHUB_OUTPUT."""
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'github_output')
            printed = io.StringIO()
            with mock.patch.dict(os.environ, {'GITHUB_OUTPUT': path}), \
                    contextlib.redirect_stdout(printed):
                code = main(['--title', title], stdin=io.StringIO('\n'.join(tags) + '\n'))
            written = ''
            if os.path.exists(path):
                with open(path, encoding='utf-8') as handle:
                    written = handle.read()
        return code, printed.getvalue(), written

    def test_success_prints_and_writes_the_outputs(self):
        code, printed, written = self.run_main('Release v0.2.0', ['v0.1.0'])
        self.assertEqual(code, 0)
        self.assertEqual(written, 'tag=v0.2.0\nprevious=v0.1.0\n')
        self.assertEqual(printed, written)

    def test_first_tag_has_an_empty_previous(self):
        code, _, written = self.run_main('Release v0.1.0', [])
        self.assertEqual(code, 0)
        self.assertEqual(written, 'tag=v0.1.0\nprevious=\n')

    def test_failure_is_an_error_annotation_and_writes_nothing(self):
        code, printed, written = self.run_main('Release v0.3.0', ['v0.1.0'])
        self.assertEqual(code, 1)
        self.assertTrue(printed.startswith('::error title=Release PR::v0.3.0 cannot follow v0.1.0'))
        self.assertEqual(written, '')

    def test_the_annotation_escapes_what_a_title_can_carry(self):
        _, printed, _ = self.run_main('Release 100%', [])
        self.assertIn('Release 100%25', printed)


if __name__ == '__main__':
    unittest.main()
