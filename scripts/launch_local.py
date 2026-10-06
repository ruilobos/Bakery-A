"""
Refresh and launch the local dev/test environment in one command (task 1.12).

Local docker-compose is the only integration-test environment (ADR-014): the
`web` image, built from the Dockerfile Railway deploys, beside PostgreSQL 17
(ADR-043). This brings it up to date in the order that avoids the usual
confusing local failure, code running against a schema it has moved past.

    python scripts/launch_local.py            # pull main, rebuild, migrate, launch
    python scripts/launch_local.py --no-pull  # the same, for the checkout as it is

1. Check that Docker is running.
2. Switch to `main` and fast-forward it. A checkout with uncommitted changes to
   tracked files is refused rather than stashed: `COPY . /code/` would build
   them into an image that claims to be `main`.
3. Rebuild, pulling a newer base image the way a fresh host build would.
4. Migrate from a one-off container of the new image, *before* `up`. Until 7.11
   the image's CMD also migrates on boot, and two concurrent runs race
   (ADR-015); run first, the boot migrate finds nothing left to do.
5. Start both services detached, then wait until the app answers HTTP: `web`
   has no healthcheck, so `up --wait` returns while gunicorn is still behind
   the boot migrate.

It stops at the first step that fails and exits with that step's code. Run it
by hand: GitHub cannot trigger a local machine.

`--no-pull` skips step 2. There is one local database, so a branch's migrations
stay applied after it; launching `main` again does not undo them.

Standard library only, so any Python 3 on the host runs it, on Windows as on
Linux or macOS.
"""

import argparse
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL = "http://localhost:8000/"

COMPOSE = ["docker", "compose"]
GIT_STATUS = ["git", "status", "--porcelain", "--untracked-files=no"]


def commands(pull=True):
    """The steps to run, in order, as `(label, argv)` pairs."""
    steps = []
    if pull:
        steps += [
            ("switch to main", ["git", "switch", "main"]),
            (
                "pull main",
                ["git", "pull", "--ff-only", "origin", "main"],
            ),  # not upstream config
        ]
    steps += [
        ("rebuild", COMPOSE + ["build", "--pull"]),
        ("migrate", COMPOSE + ["run", "--rm", "web", "python", "manage.py", "migrate"]),
        ("launch", COMPOSE + ["up", "--detach", "--wait"]),
    ]
    return steps


def _run(argv, **kwargs):
    # From the repo root whatever the caller's directory, so compose finds its file.
    # check=False: each caller reads the exit code, to name the step that failed.
    return subprocess.run(argv, cwd=ROOT, check=False, **kwargs)


def docker_running():
    try:
        quiet = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
        return _run(["docker", "info"], **quiet).returncode == 0
    except FileNotFoundError:
        return False


def serving(url, attempts=60):
    """Whether the app answers HTTP at `url` within about `attempts` seconds."""
    for attempt in range(attempts):
        if attempt:
            time.sleep(1)
        try:
            urllib.request.urlopen(url, timeout=5).close()
            return True
        except urllib.error.HTTPError:
            return True  # an error page is still the app answering
        except OSError:
            pass  # refused or reset: not listening yet
    return False


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Refresh and launch the local docker-compose environment."
    )
    parser.add_argument(
        "--no-pull",
        dest="pull",
        action="store_false",
        help="launch the checkout as it is (a feature branch, say) instead of pulling main",
    )
    args = parser.parse_args(argv)

    if not docker_running():
        print(
            "Docker is not running - start Docker Desktop and re-run.", file=sys.stderr
        )
        return 1

    if args.pull:
        status = _run(GIT_STATUS, stdout=subprocess.PIPE, text=True)
        if status.returncode:
            return status.returncode
        if status.stdout.strip():
            print(
                "Refusing to switch to main: commit or stash these changes first, "
                "or pass --no-pull to launch the checkout as it is.",
                file=sys.stderr,
            )
            print(status.stdout.rstrip(), file=sys.stderr)
            return 1

    for label, command in commands(args.pull):
        print(f"--> {label}: {' '.join(command)}", flush=True)
        code = _run(command).returncode
        if code:
            print(f'Stopped: "{label}" failed with exit code {code}.', file=sys.stderr)
            return code

    print(f"--> wait for {URL}", flush=True)
    if not serving(URL):
        print(
            f"Stopped: the containers are up, but nothing answers at {URL}. "
            "See: docker compose logs web",
            file=sys.stderr,
        )
        return 1

    print(f"\nBakery is running at {URL}")
    print("  logs: docker compose logs -f web")
    print("  stop: docker compose down")
    return 0


if __name__ == "__main__":
    sys.exit(main())
