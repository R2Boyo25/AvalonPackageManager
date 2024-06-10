"""
Functions for retrieving and interacting with package metadata.
"""

import json
import os
import shutil

import requests
from apm.path import Paths
import kazparse
import kazparse.flags

from apm import log
from apm.log import fatal_error
from apm.package import Package
from .case.case import get_case_insensitive_path


def get_local_package_metadata(paths: Paths, package_name: str) -> Package | None:
    "Attempt to retrieve metadata locally, if possible."

    locations = [
        paths.source / package_name / ".avalon/package",
        paths.metadata / package_name / "package",
    ]

    for location in locations:
        if not location.exists():
            continue

        try:
            with location.open("r") as metadata_file:
                return Package(**dict(json.load(metadata_file)))

        except json.decoder.JSONDecodeError as exception:
            log.warn(
                "Failed to parse package metadata at",
                location,
                "reason:\n" + str(exception),
            )

    log.debug(f"The metadata for {package_name} is not available locally.")
    return None


def get_remote_package_metadata(
    package_name: str, commit: str | None = None, branch: str | None = None
) -> Package | None:
    "Attempt to retrive metadata from GitHub, if possible."

    package_url = "https://raw.githubusercontent.com/{package}/{branch}/.avalon/package"

    package_urls = [
        f"https://raw.githubusercontent.com/R2Boyo25/AvalonPMPackages/master/{package_name}/package",  # pylint: disable=C0301
        package_url.format(package=package_name, branch="main"),
        package_url.format(package=package_name, branch="master"),
    ]

    if branch and commit:
        raise NotImplementedError(
            "Branch and commit cannot be specified, fix this later."
        )

    if branch:
        package_urls.append(package_url.format(package=package_name, branch=branch))

    if commit:
        package_urls.append(package_url.format(package=package_name, branch=commit))

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
            return Package(**dict(result.json()))

        except json.decoder.JSONDecodeError as exception:
            log.warn(
                "Failed to parse package metadata at",
                url,
                "reason:\n" + str(exception),
            )

    return None


def get_package_metadata(
    paths: Paths,
    package_name: str,
    commit: str | None = None,
    branch: str | None = None,
) -> Package:
    "Attempt to retrive the package's metadata"

    log.debug("Getting package info for:", package_name)

    info = get_local_package_metadata(paths, package_name)

    if info is None:
        info = get_remote_package_metadata(package_name, commit=commit, branch=branch)

    if info is None:
        fatal_error("No valid metadata available for", package_name)

    return info


def is_in_metadata_repository(package_name: str, paths: Paths) -> bool:
    "Check if the metadata is available in the metadata repository."

    status = (paths.metadata / package_name / "package").exists()

    if status:
        log.debug(f"{package_name} was found in the main repository cache.")

    else:
        log.debug(f"{package_name} was not found in the main repository cache.")

    return status


def download_metadata_repository(paths: Paths, do_not_update: bool = True) -> None:
    "Download the metadata repository using git. If if_missing"

    if not do_not_update and (paths.metadata / "R2Boyo25").exists():
        os.system(log.debug(f"cd {paths.metadata}; git pull"))
        return

    os.system(
        log.debug(
            f'git clone --depth 1 https://github.com/r2boyo25/AvalonPMPackages "{paths.metadata}" -q'  # pylint: disable=C0301
        )
    )


def get_installed_repos(paths: Paths) -> list[str]:
    "Get all installed programs"

    return [
        f"{user}/{repo}"
        for user in os.listdir(paths.files)
        for repo in os.listdir(paths.files / user)
    ]


def get_package_version(paths: Paths, repo: str) -> str | None:
    "Get version of package"

    package = get_local_package_metadata(paths, repo)

    if package is None or package.version is None:
        return None

    return package.version


def get_installed_packages_and_versions(paths: Paths) -> list[str]:
    "Get all installed programs with versions"
    programs = []

    for repo in get_installed_repos(paths):
        version = get_package_version(paths, repo)

        if version is not None:
            programs.append(f"{repo}=={version}")

        else:
            programs.append(repo)

    return programs


def is_avalon_package(paths: Paths, package_name: str) -> bool:
    """Checks whether metadata is accessible for the package."""

    return bool(get_package_metadata(paths, package_name))


def move_metadata_to_dot_avalon_folder(package_name: str, paths: Paths) -> None:
    """Copy metadata for package to {source_dir}/packagename/.avalon"""

    log.debug(
        "Copying package metadata from the metadata repo for",
        package_name,
        "into the package.",
    )

    shutil.rmtree(
        log.debug(paths.source / package_name / ".avalon"), ignore_errors=True
    )

    if is_in_metadata_repository(package_name, paths):
        log.debug(
            "Copying metadata from",
            get_case_insensitive_path(paths.metadata / package_name),
            "to",
            paths.source / package_name / ".avalon",
        )
        shutil.copytree(
            get_case_insensitive_path(paths.metadata / package_name),
            paths.source / package_name / ".avalon",
        )


def update_metadata_cache(
    _flags: kazparse.flags.Flags, paths: Paths, *_args: str
) -> None:
    "Update cache"

    download_metadata_repository(paths, do_not_update=False)


def list_installed(flags: kazparse.flags.Flags, paths: Paths, *_args: str) -> None:
    "List installed packages"

    log.IS_DEBUG = flags.debug

    print("\n".join(get_installed_packages_and_versions(paths)).title())
