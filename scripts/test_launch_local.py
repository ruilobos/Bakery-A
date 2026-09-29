"""Tests for the local launcher (task 1.12, ADR-014, ADR-043)."""
import contextlib
import io
import subprocess
import unittest
import urllib.error
from unittest import mock

from scripts.launch_local import GIT_STATUS, ROOT, URL, commands, main, serving

DOCKER_INFO = ['docker', 'info']
SWITCH = ['git', 'switch', 'main']
PULL = ['git', 'pull', '--ff-only', 'origin', 'main']
BUILD = ['docker', 'compose', 'build', '--pull']
MIGRATE = ['docker', 'compose', 'run', '--rm', 'web', 'python', 'manage.py', 'migrate']
UP = ['docker', 'compose', 'up', '--detach', '--wait']
WAIT = ['wait for', URL]  # not a command: where the launcher polls the app


class FakeRun:
    """
    Stands in for `subprocess.run` and for the HTTP wait: records each call in
    order, and fails the ones it is told to.
    """

    def __init__(self, status='', exit_codes=None, docker_missing=False, answers=True):
        self.status = status
        self.exit_codes = exit_codes or {}
        self.docker_missing = docker_missing
        self.answers = answers
        self.calls = []

    def __call__(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        if argv == DOCKER_INFO and self.docker_missing:
            raise FileNotFoundError('docker')
        stdout = self.status if argv == GIT_STATUS else None
        return subprocess.CompletedProcess(argv, self.exit_codes.get(tuple(argv), 0), stdout)

    def serving(self, url):
        self.calls.append((['wait for', url], {}))
        return self.answers

    @property
    def commands(self):
        return [argv for argv, _ in self.calls]


def launch(argv, fake):
    out, err = io.StringIO(), io.StringIO()
    with mock.patch('scripts.launch_local.subprocess.run', fake), \
            mock.patch('scripts.launch_local.serving', fake.serving), \
            contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


class OrderTests(unittest.TestCase):
    def test_a_full_run_pulls_main_rebuilds_migrates_launches_then_waits(self):
        fake = FakeRun()
        code, out, _ = launch([], fake)
        self.assertEqual(code, 0)
        self.assertEqual(
            fake.commands, [DOCKER_INFO, GIT_STATUS, SWITCH, PULL, BUILD, MIGRATE, UP, WAIT]
        )
        self.assertIn(f'Bakery is running at {URL}', out)

    def test_migrate_runs_once_in_a_one_off_container_before_up(self):
        # Until 7.11 the image's CMD migrates on boot too; the two must never overlap (ADR-015).
        steps = commands()
        labels = [label for label, _ in steps]
        self.assertLess(labels.index('migrate'), labels.index('launch'))
        migrating = [argv for _, argv in steps if 'migrate' in argv]
        self.assertEqual(migrating, [MIGRATE])
        self.assertNotIn('--build', dict(steps)['launch'])

    def test_every_command_runs_from_the_repo_root(self):
        fake = FakeRun()
        launch([], fake)
        run = [kwargs for argv, kwargs in fake.calls if argv != WAIT]
        self.assertTrue(run and all(kwargs.get('cwd') == ROOT for kwargs in run))


class NoPullTests(unittest.TestCase):
    def test_no_pull_launches_the_checkout_without_touching_git(self):
        fake = FakeRun()
        code, _, _ = launch(['--no-pull'], fake)
        self.assertEqual(code, 0)
        self.assertEqual(fake.commands, [DOCKER_INFO, BUILD, MIGRATE, UP, WAIT])

    def test_no_pull_does_not_care_about_uncommitted_changes(self):
        fake = FakeRun(status=' M CLAUDE.md\n')
        code, _, _ = launch(['--no-pull'], fake)
        self.assertEqual(code, 0)
        self.assertNotIn(GIT_STATUS, fake.commands)


class RefusalTests(unittest.TestCase):
    def test_uncommitted_changes_refuse_before_switching_branch(self):
        fake = FakeRun(status=' M CLAUDE.md\n')
        code, _, err = launch([], fake)
        self.assertEqual(code, 1)
        self.assertEqual(fake.commands, [DOCKER_INFO, GIT_STATUS])
        self.assertIn('Refusing to switch to main', err)
        self.assertIn('CLAUDE.md', err)

    def test_docker_not_running_stops_before_anything_else(self):
        fake = FakeRun(exit_codes={tuple(DOCKER_INFO): 1})
        code, _, err = launch([], fake)
        self.assertEqual(code, 1)
        self.assertEqual(fake.commands, [DOCKER_INFO])
        self.assertIn('Docker is not running', err)

    def test_docker_not_installed_reads_the_same(self):
        fake = FakeRun(docker_missing=True)
        code, _, err = launch([], fake)
        self.assertEqual(code, 1)
        self.assertIn('Docker is not running', err)

    def test_a_failing_git_status_stops_the_run(self):
        fake = FakeRun(exit_codes={tuple(GIT_STATUS): 128})
        code, _, _ = launch([], fake)
        self.assertEqual(code, 128)
        self.assertEqual(fake.commands, [DOCKER_INFO, GIT_STATUS])


class FailureTests(unittest.TestCase):
    def test_a_failing_step_stops_the_run_with_its_exit_code(self):
        for failing in (SWITCH, PULL, BUILD, MIGRATE, UP):
            with self.subTest(step=' '.join(failing)):
                fake = FakeRun(exit_codes={tuple(failing): 17})
                code, out, err = launch([], fake)
                self.assertEqual(code, 17)
                self.assertEqual(fake.commands[-1], failing)
                self.assertIn('failed with exit code 17', err)
                self.assertNotIn('Bakery is running', out)

    def test_a_failed_build_never_migrates_or_launches(self):
        fake = FakeRun(exit_codes={tuple(BUILD): 1})
        launch([], fake)
        self.assertNotIn(MIGRATE, fake.commands)
        self.assertNotIn(UP, fake.commands)

    def test_an_app_that_never_answers_is_a_failure(self):
        fake = FakeRun(answers=False)
        code, out, err = launch([], fake)
        self.assertEqual(code, 1)
        self.assertIn('docker compose logs web', err)
        self.assertNotIn('Bakery is running', out)


@mock.patch('scripts.launch_local.time.sleep')
@mock.patch('scripts.launch_local.urllib.request.urlopen')
class ServingTests(unittest.TestCase):
    def test_an_answer_is_serving(self, urlopen, sleep):
        self.assertTrue(serving(URL))
        urlopen.assert_called_once_with(URL, timeout=5)
        sleep.assert_not_called()

    def test_an_error_page_is_still_serving(self, urlopen, sleep):
        urlopen.side_effect = urllib.error.HTTPError(URL, 500, 'Server Error', {}, None)
        self.assertTrue(serving(URL))

    def test_it_retries_until_gunicorn_listens(self, urlopen, sleep):
        # Refused while the boot migrate runs, then reset while gunicorn binds, then an answer.
        urlopen.side_effect = [
            urllib.error.URLError(ConnectionRefusedError()), ConnectionResetError(), mock.Mock()
        ]
        self.assertTrue(serving(URL))
        self.assertEqual(urlopen.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    def test_it_gives_up_after_its_attempts(self, urlopen, sleep):
        urlopen.side_effect = ConnectionRefusedError()
        self.assertFalse(serving(URL, attempts=3))
        self.assertEqual(urlopen.call_count, 3)


if __name__ == '__main__':
    unittest.main()
