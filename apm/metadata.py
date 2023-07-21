"""
Functions for retrieving and interacting with package metadata.
"""

import json
import sys
import os

from pathlib import Path
from typing import Any

import requests
import kazparse

from apm import log
from apm.log import fatal_error
from apm.package import NPackage


def get_local_package_metadata(
    paths: dict[str, Path], pkgname: str
) -> dict[Any, Any] | None:
    "Attempt to retrieve metadata locally, if possible."

    locations = [
        paths["src"] / pkgname / ".avalon/package",
        paths["cache"] / pkgname / "package",
    ]

    for location in locations:
        if not location.exists():
            continue

        try:
            with location.open("r") as metadata_file:
                return dict(json.load(metadata_file))

        except json.decoder.JSONDecodeError as exception:
            log.warn(
                "Failed to parse package metadata at",
                str(location),
                "reason:\n" + str(exception),
            )

    log.debug(f"The metadata for {pkgname} is not available locally.")
    return None


def get_remote_package_metadata(
    pkgname: str, commit: str | None = None, branch: str | None = None
) -> dict[Any, Any] | None:
    "Attempt to retrive metadata from GitHub, if possible."

    package_url = (
        "https://raw.githubusercontent.com/{package}/{branch}/.avalon/package"
    )

    package_urls = [
        f"https://raw.githubusercontent.com/R2Boyo25/AvalonPMPackages/master/{pkgname}/package",  # pylint: disable=C0301
        package_url.format(package=pkgname, branch="main"),
        package_url.format(package=pkgname, branch="master"),
    ]

    if branch and commit:
        raise NotImplementedError(
            "Branch and commit cannot be specified, fix this later."
        )

    if branch:
        package_urls.append(package_url.format(package=pkgname, branch=branch))

    if commit:
        package_urls.append(package_url.format(package=pkgname, branch=commit))

    for url in package_urls:
        log.debug("Trying URL:", url)

        result = requests.get(
            url,
            timeout=10,
        )

        log.debug(result.text)

        if result.status_code == 404:
            continue

        try:
            return dict(result.json())

        except json.decoder.JSONDecodeError as exception:
            log.warn(
                "Failed to parse package metadata at",
                url,
                "reason:\n" + str(exception),
            )

    return None


def get_package_metadata(
    paths: dict[str, Path],
    pkgname: str,
    commit: str | None = None,
    branch: str | None = None,
) -> NPackage:
    "Attempt to retrive the package's metadata"

    log.debug("Getting package info for:", pkgname)

    info = get_local_package_metadata(paths, pkgname)

    if info is None:
        info = get_remote_package_metadata(
            pkgname, commit=commit, branch=branch
        )

    if info is None:
        fatal_error("No valid metadata available for", pkgname)
        sys.exit(1)

    return NPackage(info)


def is_in_metadata_repository(pkgname: str, paths: dict[str, Path]) -> bool:
    "Check if the metadata is available in the metadata repository."

    status = (paths["cache"] / pkgname / "package").exists()

    if status:
        log.debug(f"{pkgname} was found in the main repository cache.")

    else:
        log.debug(f"{pkgname} was not found in the main repository cache.")

    return status


def download_metadata_repository(
    paths: dict[str, Path], do_not_update: bool = True
) -> None:
    "Download the metadata repository using git. If if_missing"

    if not do_not_update and (paths["cache"] / "R2Boyo25").exists():
        os.system(log.debug(f"cd {paths['cache']}; git pull"))
        return

    os.system(
        log.debug(
            f'git clone --depth 1 https://github.com/r2boyo25/AvalonPMPackages "{paths["cache"]}" -q'  # pylint: disable=C0301
        )
    )


def get_installed_repos(paths: dict[str, Path]) -> list[str]:
    "Get all installed programs"
    programs = []

    for user in os.listdir(paths["files"]):
        for repo in os.listdir(paths["files"] / user):
            programs.append(f"{user}/{repo}")

    return programs


def get_package_version(paths: dict[str, Path], repo: str) -> str | None:
    "Get version of package"

    pkg = get_local_package_metadata(paths, repo)

    if not pkg:
        return None

    if "version" not in pkg:
        return None

    return str(pkg["version"])


def get_installed_packages_and_versions(paths: dict[str, Path]) -> list[str]:
    "Get all installed programs with versions"
    programs = []

    for repo in get_installed_repos(paths):
        version = get_package_version(paths, repo)

        if version is not None:
            programs.append(f"{repo}=={version}")

        else:
            programs.append(repo)

    return programs


def is_avalon_package(paths: dict[str, Path], pkgname: str) -> bool:
    """Checks whether metadata is accessible for the package."""

    return bool(get_package_metadata(paths, pkgname))


def update_metadata_cache(
    _flags: kazparse.flags.Flags, paths: dict[str, Path], *_args: str
) -> None:
    "Update cache"

    download_metadata_repository(paths, do_not_update=False)


def list_installed(
    flags: kazparse.flags.Flags, paths: dict[str, Path], *_args: str
) -> None:
    "List installed packages"

    log.IS_DEBUG = flags.debug

    print("\n".join(get_installed_packages_and_versions(paths)).title())
