"""
Definition of APM's CommandLine Interface
"""

from typing import Any
from pathlib import Path

import os
import sys
import semver

from kazparse import Parse
import kazparse
from apm import path
from .pm_util import (
    install_package,
    uninstall_package,
    redo_symlinks_for_package,
    update_package,
    download_package_source,
)
from .metadata import (
    update_metadata_cache,
    get_installed_repos,
    list_installed,
)
from .version import VERSION, COPYRIGHT_YEAR
from .changelog import (
    get_package_versions,
    display_changelogs_packages,
    bump_version,
    get_changelog_path,
    get_changes_after,
    display_changelogs,
    display_all_changelogs,
)
from .case.case import getCaseInsensitivePath

# Set up some initial information and configurations
before = f"Avalon Package Manager V{VERSION} Copyright (C) {COPYRIGHT_YEAR} R2Boyo25"

# initalize KazParse parser
p = Parse(
    "apm",
    before=before,
    after="NOTE: flags MUST be before command!",
    flagsAsArgumentsAfterCommand=True,
)

# Define various command-line flags and their corresponding help messages
p.flag("update", short="U", long="update", help="Reinstall APM dependencies")
p.flag("fresh", short="F", long="fresh", help="Reinstall instead of updating")
p.flag("force", short="f", long="force", help="Force install package.")
p.flag(
    "debug",
    short="d",
    long="debug",
    help="Print debug output (VERY large amount of text)",
)
p.flag(
    "noinstall",
    long="noinstall",
    help="Only download, skip compilation and installation (Debug)",
)
p.flag(
    "machine",
    short="m",
    long="machine",
    help="Disable user-facing features. Use in scripts and wrappers\
    or things might break.",
)

# Fetch the versions of all installed packages and store in 'freeze_changelogs'
freeze_changelogs = get_package_versions(get_installed_repos(path.paths))


def display_changes(machine: bool = False) -> None:
    "Display changelogs for installed packages"

    if not machine:
        display_changelogs_packages(freeze_changelogs)


def create_changelog(changelog_path: str) -> None:
    "Create a changelog file at the specified path\
    (if it doesn't exist)"

    changelog_path = getCaseInsensitivePath(changelog_path)
    changelog_path += "/CHANGELOG.MD"

    dname = os.path.dirname(changelog_path)

    chlog = getCaseInsensitivePath(dname + "/CHANGELOG.MD")
    while not os.path.exists(chlog) and os.path.dirname(dname) != "/":
        dname = os.path.dirname(dname)
        chlog = getCaseInsensitivePath(dname + "/CHANGELOG.MD")
        if os.path.exists(chlog):
            return

    if os.path.exists(changelog_path):
        return

    with open(changelog_path, "w", encoding="utf-8") as changelog_file:
        changelog_file.write(
            """
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog]\
(https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic \
Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
""".strip()
            + "\n"
        )


# Define a command function for the 'release' submenu
@p.command("release")
def release_submenu(_: Any, __: Any, *args: str) -> None:
    "Submenu for interacting with changelogs"

    # Create a new Parse instance for the 'apm release' command with
    # specific configurations
    release_parser = Parse("apm release", before=before)

    # Define a command function 'releaseBump' within the 'release' submenu
    @release_parser.command("bump")
    def release_bump_version(_flags: kazparse.flags.Flags, *args: str) -> None:
        "Bump `CHANGELOG.MD`'s version: major, minor, or patch\nIf \
        `part` not specified, guess based off of `[Unreleased]`"

        # Ensure that the 'CHANGELOG.MD' file exists in the current
        # working directory
        create_changelog(os.getcwd())

        # Call 'bump_version' function to update the version in the
        # 'CHANGELOG.MD' file
        bump_version(*args)

    # Define a command function 'releaseChange' within the 'release' submenu
    @release_parser.command("change")
    def release_edit_changelog(
        _flags: kazparse.flags.Flags, _args: str
    ) -> None:
        "Edit `CHANGELOG.MD` w/ `$VISUAL_EDITOR`"

        # Ensure that the 'CHANGELOG.MD' file exists in the current
        # working directory
        create_changelog(os.getcwd())

        # Get the preferred text editor from the environment variables
        # (fallback to 'nano' if not set)
        visual_editor = os.environ.get(
            "VISUAL_EDITOR", os.environ.get("EDITOR", "nano")
        )

        # Open the 'CHANGELOG.MD' file with the specified text editor
        sys.exit(os.system(f"{visual_editor} {get_changelog_path(Path('.'))}"))

    # Execute the 'apm release' command with the provided arguments
    release_parser.run(args=args)


# Define a command function for the 'changes' command
@p.command("changes")
def package_view_changes(
    _flags: kazparse.flags.Flags, paths: dict[str, Path], *args: str
) -> None:
    """
    View changes in `package` since `version`
    changes [version]
    changes [package]
    changes <package> [version]
    """

    # If no arguments are provided, show changes since version '0.0.0'
    if len(args) == 0:
        changes = get_changes_after(
            Path("."), semver.VersionInfo.parse("0.0.0")
        )
        display_changelogs([("", changes)])
        return

    # If two arguments are provided, show changes for a specific
    # package and version
    if len(args) == 2:
        package_version = semver.VersionInfo.parse(args[1])
        display_changelogs_packages([(args[0], package_version)])
        return

    # If the first argument is 'all', show changes for all installed
    # packages
    if args[0] == "all":
        display_all_changelogs(get_installed_repos(paths))
        return

    # If the first argument is not a package - so, a version - show
    # changes since that version
    if "/" not in args[0]:
        package_version = semver.VersionInfo.parse(args[0])
        changes = get_changes_after(Path("."), package_version)
        display_changelogs([("", changes)])
        return

    # If a package name and version are provided, show changes since
    # that version for the specific package
    pkgpath = paths["src"] / str(args[0])
    changes = get_changes_after(pkgpath, semver.VersionInfo.parse("0.0.0"))
    display_changelogs([(args[0], changes)])


# Define a command function for the 'gen' command
@p.command("gen")
def generate_package(
    _flags: kazparse.flags.Flags, paths: dict[str, Path], *args: str
) -> None:
    "Generate a package using AvalonGen"
    os.system(
        str(paths["bin"]) + "/avalongen " + " ".join([f'"{i}"' for i in args])
    )


# Define a command function for the 'install' command
@p.command("install")
def cli_install_package(
    flags: kazparse.flags.Flags, paths: dict[str, Path], *args: str
) -> None:
    "Installs a package"

    install_package(flags, paths, list(args))

    # Display changelogs for installed packages
    display_changes(flags.machine)


# Define a command function for the 'uninstall' command
@p.command("uninstall")
def cli_uninstall_package(
    flags: kazparse.flags.Flags, paths: dict[str, Path], *args: str
) -> None:
    "Uninstalls a package"

    uninstall_package(flags, paths, list(args))


# Define a command function for the 'update' command (hidden)
@p.command("update", hidden=True)
def cli_update_package(
    flags: kazparse.flags.Flags, paths: dict[str, Path], *args: str
) -> None:
    "Update to the newest version of a repo, \
    then recompile + reinstall program"

    update_package(flags, paths, *args)

    # Display changelogs for installed packages
    display_changes(flags.machine)


# Define a command function for the 'refresh' command
@p.command("refresh")
def cli_refresh_cache_folder(
    flags: kazparse.flags.Flags, paths: dict[str, Path], *args: str
) -> None:
    "Refresh the main repository cache"

    update_metadata_cache(flags, paths, *args)


# Define a command function for the 'pack' command
@p.command("pack")
def create_apm(
    _flags: kazparse.flags.Flags, paths: dict[str, Path], *args: str
) -> None:
    "Generate .apm file with AvalonGen"
    os.system(
        str(paths["bin"])
        + "/avalongen "
        + "package "
        + " ".join([f'"{i}"' for i in args])
    )


# Define a command function for the 'unpack' command
@p.command("unpack")
def unpack_apm(
    _flags: kazparse.flags.Flags, paths: dict[str, Path], *args: str
) -> None:
    "Unpack .apm file with AvalonGen"
    raise NotImplementedError
    # os.system(
    #     str(paths["bin"])
    #     + "/avalongen "
    #     + "unpack "
    #     + " ".join([f'"{i}"' for i in args])
    # )


# Define a command function for the 'redobin' command (hidden)
@p.command("redobin", hidden=True)
def cli_redo_bin(
    flags: kazparse.flags.Flags, paths: dict[str, Path], *args: str
) -> None:
    "Regenerate symlinks for a package"
    redo_symlinks_for_package(flags, paths, *args)


# Define a command function for the 'installed' command
@p.command("installed")
def cli_list_nstalled(
    flags: kazparse.flags.Flags, paths: dict[str, Path], *args: str
) -> None:
    "List installed packages"

    # Call the 'installed' function to list installed packages
    list_installed(flags, paths, *args)


# Define a command function for the 'src' command
@p.command("src")
def cli_download_source(
    flags: kazparse.flags.Flags, paths: dict[str, Path], *args: str
) -> None:
    "Download a repo into a folder"

    download_package_source(flags, paths, *args)


def main() -> None:
    "The main function, it does things. (like calling the parser.\
    Actually, no. That's all it does.)"

    # Run the 'p.run' method to start the execution of the Avalon
    # Package Manager (APM). The 'extras' parameter is used to provide
    # additional context or data to the command-line parser. In this
    # case, 'paths' contains a dictionary with various paths used by
    # the APM script. This allows the CLI commands to access and
    # utilize these paths as needed during execution
    p.run(extras=path.paths)
