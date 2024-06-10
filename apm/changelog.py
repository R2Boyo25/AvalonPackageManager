"""
Functions for interacting with package changelogs using the keepachangelog format.
"""

import subprocess  # nosec B404
import re
import datetime
import sys

from pathlib import Path
from typing import Optional, Generator, Dict, List, Any, Tuple, Union, Iterable

import keepachangelog  # type: ignore
import semver

from apm import path, log
from .case.case import get_case_insensitive_path
from .log import debug, error

# Define a custom type for the changelog data
Changelog = Dict[str, Union[str, List[str], Dict[str, Optional[int]]]]


def get_changelog_path(package_dir: Path) -> Optional[Path]:
    """
    Get case insensitive path to `CHANGELOG.MD` in `package_dir`.

    Recursively traverses upwards in the directory tree until
    it finds the file.
    """

    changelog_path = get_case_insensitive_path(
        (package_dir / "CHANGELOG.MD").absolute()
    )

    dname = changelog_path.parent
    chlog = get_case_insensitive_path(dname / "CHANGELOG.MD")

    while not chlog.exists() and dname.parent != "/":
        dname = dname.parent
        chlog = get_case_insensitive_path(dname / "CHANGELOG.MD")

        if not chlog.exists():
            chlog = Path("/238ghdfg9832hnbjwhgfdsi783rkjf/uwjfgehfsguydsdf")

    if not chlog.exists():
        return None

    return chlog


# Function to parse the changelog at 'package_dir/CHANGELOG.MD'
def get_parsed_changelog(package_dir: Path) -> Optional[Dict[str, Any]]:
    "Parse changelog at `package_dir/CHANGELOG.MD`"

    changelog_path = get_changelog_path(package_dir)

    if not changelog_path:
        debug(f"[Changelog] CHANGELOG.MD does not exist in {package_dir}.")

        return None

    return keepachangelog.to_dict(changelog_path, show_unreleased=True)  # type: ignore  # noqa


def current_version(package_dir: Path) -> Optional[semver.VersionInfo]:
    "Get latest version from `package_dir/CHANGELOG.MD`"

    chlog = get_parsed_changelog(package_dir)

    if not chlog:
        return None

    versions = list(chlog.keys())

    if len(versions) == 0:
        debug("[Changelog] CHANGELOG.MD has no versions.")

        return None

    if versions[0] == "unreleased":
        del versions[0]

    return semver.VersionInfo.parse(versions[0])


def get_changes_after(
    package_dir: Path, compare_version: semver.VersionInfo
) -> Generator[Changelog, None, None]:
    "Get versions from `package_dir/CHANGELOG.MD` that are later than\
    `compare_version`"

    chlog = get_parsed_changelog(package_dir)

    if not chlog:
        return

    for version, value in chlog.items():
        if version == "unreleased":
            continue

        if semver.VersionInfo.parse(version) > compare_version:
            yield value


def inline_code(match: re.Match[str]) -> str:
    "Helper function to format inline code in changelog entries"
    return "\033[35;7m" + match[1] + "\033[27;39m"


# Function to prettify changelogs for display
def prettify_changelogs(logs: Iterable[Tuple[str, Iterable[Changelog]]]) -> bytes:
    """Prettify changelogs for display"""

    buf = ""
    end_section = "\033[0m\n\n"

    for program in logs:
        if not program[1]:
            continue

        if program[0]:
            buf += "\033[1;4m"
            buf += program[0]
            buf += end_section

        for version in program[1]:
            buf += "\033[1;4m"
            buf += str(version["version"])
            buf += " \033[2m"
            buf += str(version["release_date"]).replace(
                "[yanked]", "\033[31m[YANKED]\033[37m"
            )
            buf += end_section

            for changes in [
                "deprecated",
                "added",
                "changed",
                "removed",
                "fixed",
                "security",
            ]:
                if changes in version:
                    buf += "\033[4m"
                    buf += changes.title()
                    buf += "\033[0m\n"

                    for change in version[changes]:
                        buf += " - "
                        buf += re.sub("`(.*?)`", inline_code, change)
                        buf += "\n"

                    buf += "\n"

    return bytes(buf, "utf-8")


def display_changelogs(logs: Iterable[Tuple[str, Iterable[Changelog]]]) -> None:
    """display changelogs in a paginated view using 'less'."""

    i = prettify_changelogs(logs)

    if len(i) <= 0:
        return

    with subprocess.Popen(
        ["/bin/less", "-r"], stdin=subprocess.PIPE
    ) as less_process:  # nosec B603
        less_process.communicate(input=i)

        less_process.wait()


def get_package_versions(
    packages: List[str],
) -> List[Tuple[str, semver.VersionInfo]]:
    """Retrieve the latest version for a list of packages."""

    out = []

    for package in packages:
        ver = current_version(path.paths.source / package.lower())
        out.append((package, ver if ver else semver.VersionInfo.parse("0.0.0")))

    return out


def display_changelogs_packages(
    packages: Iterable[Tuple[str, semver.VersionInfo]]
) -> None:
    """Display changelogs for specific packages and versions."""

    display_changelogs(
        [
            (
                package,
                list(get_changes_after(path.paths.source / package.lower(), startver)),
            )
            for package, startver in packages
        ]
    )


def bump_version(part: Optional[str] = None) -> None:
    """Bumps the version in the `CHANGELOG.MD` file based on the `Unreleased` section"""

    if not part:
        changelog_path = get_changelog_path(Path("."))

        if changelog_path is None:
            log.fatal_error("`CHANGELOG.md` missing for the current package.")

        try:
            keepachangelog.release(str(changelog_path))

        except Exception:
            # FIXME: only catch Exceptions for Unreleased section:
            #   "Release content must be provided within changelog
            #   Unreleased section."

            log.fatal_error(
                "No changes provided in `Unreleased` section of `CHANGELOG.MD`"
            )

        return

    error("`release bump` does not support `part` yet (`keepachangelog` issue).")
    sys.exit(1)

    if part not in ["major", "minor", "patch"]:
        error(f"{part} must be `major`, `minor`, or `patch`")
        sys.exit(1)

    parsed_changelog = get_parsed_changelog(".")

    if parsed_changelog is not None:
        error("There exists no parseable `CHANGELOG.MD` in the current project.")
        sys.exit(1)

    next_version = current_version(".").next_version(part=part)

    parsed_changelog[str(next_version)] = {
        "version": str(next_version),
        "release_date": datetime.datetime.utcnow().isoformat(" ").split(" ")[0],
    }

    # TODO: save to file


def display_all_changelogs(packages: List[str]) -> None:
    """Display all changelogs for a list of packages."""

    display_changelogs(
        [
            (
                package,
                list(
                    get_changes_after(
                        path.paths.source / package.lower(),
                        semver.VersionInfo.parse("0.0.0"),
                    )
                ),
            )
            for package in packages
        ]
    )
