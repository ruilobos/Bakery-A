"""
Choose the version a release PR publishes: the release step (task 1.10, ADR-042).

Every merge to `production` is tagged `vX.Y.Z` and published as a GitHub Release
(ADR-010). The version comes from the release PR's title, `Release vX.Y.Z`. It
must be the next patch, minor or major release after the latest tag, and the
first tag is `v0.1.0`. The rule demands a successor rather than any higher
version so that a typo such as `v0.20.0` for `v0.2.0` fails before it is
published, and not after every later version has had to follow it.

`.github/workflows/release.yml` runs this twice: on an open release PR, as a
check, and after the merge, to choose the tag it publishes.

    git tag --list 'v*' | python3 scripts/release_version.py --title "Release v0.2.0"

The existing tags arrive on stdin, one per line. On success it prints `tag=` and
`previous=` lines, and also appends them to `$GITHUB_OUTPUT` when that is set.
On failure it prints a GitHub Actions error annotation and exits 1.

Standard library only, so the runner's own `python3` runs it with no install step.
"""
import argparse
import os
import re
import sys

# No leading zeros (semver forbids them, and `v01.0.0` would read as `v1.0.0`),
# and [0-9] rather than \d, which also matches non-ASCII digits.
_NUMBER = r'(0|[1-9][0-9]*)'
_VERSION = r'v' + r'\.'.join([_NUMBER] * 3)
TAG = re.compile(_VERSION)
TITLE = re.compile(r'Release ' + _VERSION)

FIRST = (0, 1, 0)


class ReleaseError(Exception):
    """The release PR does not name a version this step may publish."""


def tag_name(version):
    return 'v%d.%d.%d' % version


def parse_tag(tag):
    """
    Return `(major, minor, patch)` for a strict `vX.Y.Z` tag, or None.

    Anything else (`v0.2.0-rc1`, `0.3.0`, `latest`) is not a release this step
    made, so it neither blocks a version nor sets the next one.
    """
    match = TAG.fullmatch(tag.strip())
    return tuple(int(part) for part in match.groups()) if match else None


def successors(version):
    """The versions allowed to follow `version`: its next patch, minor and major."""
    major, minor, patch = version
    return [(major, minor, patch + 1), (major, minor + 1, 0), (major + 1, 0, 0)]


def next_release(title, tags):
    """
    Return `(tag, previous_tag)` for a release PR titled `title`.

    `previous_tag` is None for the first tag. Raises ReleaseError, with a
    message for whoever opened the PR, when the title is not `Release vX.Y.Z` or
    names a version that cannot follow the latest tag.
    """
    match = TITLE.fullmatch(title.strip())
    if not match:
        raise ReleaseError(f'Title the release PR "Release vX.Y.Z", not "{title}" (ADR-042).')
    wanted = tuple(int(part) for part in match.groups())

    released = sorted(version for version in map(parse_tag, tags) if version)
    if not released:
        if wanted != FIRST:
            raise ReleaseError(
                f'The first tag is {tag_name(FIRST)}, not {tag_name(wanted)} (ADR-042).'
            )
        return tag_name(wanted), None

    latest = released[-1]
    allowed = successors(latest)
    if wanted not in allowed:
        patch, minor, major = (tag_name(version) for version in allowed)
        raise ReleaseError(
            f'{tag_name(wanted)} cannot follow {tag_name(latest)}: '
            f'the next release is {patch}, {minor} or {major}.'
        )
    return tag_name(wanted), tag_name(latest)


def _escape(message):
    # A workflow-command message may not carry these raw.
    return message.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')


def main(argv=None, stdin=None):
    parser = argparse.ArgumentParser(description='Choose the version a release PR publishes.')
    parser.add_argument('--title', required=True, help="the release PR's title")
    args = parser.parse_args(argv)

    tags = (stdin or sys.stdin).read().split()
    try:
        tag, previous = next_release(args.title, tags)
    except ReleaseError as error:
        print(f'::error title=Release PR::{_escape(str(error))}')
        return 1

    outputs = f'tag={tag}\nprevious={previous or ""}\n'
    sys.stdout.write(outputs)
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a', encoding='utf-8') as handle:
            handle.write(outputs)
    return 0


if __name__ == '__main__':
    sys.exit(main())
