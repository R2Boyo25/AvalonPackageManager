import os
import sys
import semver  # type: ignore
from typing import Any
from pathlib import Path

from .pmUtil import (
    installPackage,
    uninstallPackage,
    installLocalPackage,
    redoBin,
    updatePackage,
    installed,
    dlSrc,
    updateCache,
    getInstalledRepos,
)
from .path import paths
from kazparse import Parse
import kazparse
from .version import version, cyear
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
before = f"Avalon Package Manager V{version} Copyright (C) {cyear} R2Boyo25"

# Create an instance of the 'Parse' class from the 'kazparse' module with specific configurations
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
    help="Disable user-facing features. Use in scripts and wrappers or things might break.",
)

# Fetch the versions of all installed packages and store in 'freeze_changelogs'
freeze_changelogs = get_package_versions(getInstalledRepos(paths))

# Define a function to display changelogs for installed packages
def display_changes(machine: bool = False) -> None:
    if not machine:
        display_changelogs_packages(freeze_changelogs)

# Define a function to create a changelog file at the specified path (if it doesn't exist)
def create_changelog(path: str) -> None:
    path = getCaseInsensitivePath(path)
    path += "/CHANGELOG.MD"

    dname = os.path.dirname(path)

    chlog = getCaseInsensitivePath(dname + "/CHANGELOG.MD")
    while not os.path.exists(chlog) and os.path.dirname(dname) != "/":
        dname = os.path.dirname(dname)
        chlog = getCaseInsensitivePath(dname + "/CHANGELOG.MD")
        if os.path.exists(chlog):
            return

    if os.path.exists(path):
        return

    with open(path, "w") as f:
        f.write(
            """
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
""".strip()
            + "\n"
        )



# Define a command function for the 'release' submenu
@p.command("release")
def releaseSubmenu(_: Any, __: Any, *args: str) -> None:
    "Submenu for interacting with changelogs"

    # Create a new Parse instance for the 'apm release' command with specific configurations
    rp = Parse("apm release", before=before)

    # Define a command function 'releaseBump' within the 'release' submenu
    @rp.command("bump")
    def releaseBump(flags: kazparse.flags.Flags, *args: str) -> None:
        "Bump `CHANGELOG.MD`'s version: major, minor, or patch\nIf `part` not specified, guess based off of `[Unreleased]`"

        # Ensure that the 'CHANGELOG.MD' file exists in the current working directory
        create_changelog(os.getcwd())

        # Call 'bump_version' function to update the version in the 'CHANGELOG.MD' file
        bump_version(*args)

    # Define a command function 'releaseChange' within the 'release' submenu
    @rp.command("change")
    def releaseChange(flags: kazparse.flags.Flags, *args: str) -> None:
        "Edit `CHANGELOG.MD` w/ `$VISUAL_EDITOR`"

        # Ensure that the 'CHANGELOG.MD' file exists in the current working directory
        create_changelog(os.getcwd())

        # Get the preferred text editor from the environment variables (fallback to 'nano' if not set)
        visual_editor = os.environ.get(
            "VISUAL_EDITOR", os.environ.get("EDITOR", "nano")
        )

        # Open the 'CHANGELOG.MD' file with the specified text editor
        exit(os.system(f"{visual_editor} {get_changelog_path(Path('.'))}"))

    # Execute the 'apm release' command with the provided arguments
    rp.run(args=args)

# Define a command function for the 'changes' command
@p.command("changes")
def packageChanges(
    flags: kazparse.flags.Flags, paths: dict[str, Path], *args: str
) -> None:
    "View changes in `package` since `version`\nchanges [version]\nchanges [package]\nchanges <package> [version]"

    # If no arguments are provided, show changes since version '0.0.0'
    if not len(args):
        changes = get_changes_after(Path("."), semver.VersionInfo.parse("0.0.0"))
        display_changelogs([("", changes)])
        return

    # If two arguments are provided, show changes for a specific package and version
    if len(args) == 2:
        version = semver.VersionInfo.parse(args[1])
        display_changelogs_packages([(args[0], version)])
        return

    # If the first argument is 'all', show changes for all installed packages
    if args[0] == "all":
        display_all_changelogs(getInstalledRepos(paths))
        return

    # If the first argument is a version, show changes since that version
    if not "/" in args[0]:
        version = semver.VersionInfo.parse(args[0])
        changes = get_changes_after(Path("."), version)
        display_changelogs([("", changes)])
        return

    # If a package name and version are provided, show changes since that version for the specific package
    pkgpath = paths["src"] / str(args[0])
    changes = get_changes_after(pkgpath, semver.VersionInfo.parse("0.0.0"))
    display_changelogs([(args[0], changes)])

# Define a command function for the 'gen' command
@p.command("gen")
def genPackage(flags: kazparse.flags.Flags, paths: dict[str, Path], *args: str) -> None:
    "Generate a package using AvalonGen"
    os.system(str(paths["bin"]) + "/avalongen " + " ".join([f'"{i}"' for i in args]))

# Define a command function for the 'install' command
@p.command("install")
def installFunction(
    flags: kazparse.flags.Flags, paths: dict[str, Path], *args: str
) -> None:
    "Installs a package"

    # Call the 'installPackage' function to install the package specified by the arguments
    installPackage(flags, paths, list(args))

    # Display changelogs for installed packages
    display_changes(flags.machine)

# Define a command function for the 'uninstall' command
@p.command("uninstall")
def uninstallFunction(
    flags: kazparse.flags.Flags, paths: dict[str, Path], *args: str
) -> None:
    "Uninstalls a package"
    # Call the 'uninstallPackage' function to uninstall the package specified by the arguments
    uninstallPackage(flags, paths, list(args))

# Define a command function for the 'update' command (hidden)
@p.command("update", hidden=True)
def updatePackageCLI(
    flags: kazparse.flags.Flags, paths: dict[str, Path], *args: str
) -> None:
    "Update to the newest version of a repo, then recompile + reinstall program"

    # Call the 'updatePackage' function to update and reinstall the package specified by the arguments
    updatePackage(flags, paths, *args)

    # Display changelogs for installed packages
    display_changes(flags.machine)

# Define a command function for the 'refresh' command
@p.command("refresh")
def refreshCacheFolder(
    flags: kazparse.flags.Flags, paths: dict[str, Path], *args: str
) -> None:
    "Refresh the main repo cache"

    # Call the 'updateCache' function to refresh the main repository cache
    updateCache(flags, paths, *args)

# Define a command function for the 'pack' command
@p.command("pack")
def genAPM(flags: kazparse.flags.Flags, paths: dict[str, Path], *args: str) -> None:
    "Generate .apm file with AvalonGen"
    os.system(
        str(paths["bin"])
        + "/avalongen "
        + "package "
        + " ".join([f'"{i}"' for i in args])
    )

# Define a command function for the 'unpack' command
@p.command("unpack")
def unpackAPM(flags: kazparse.flags.Flags, paths: dict[str, Path], *args: str) -> None:
    "Unpack .apm file with AvalonGen"
    raise NotImplementedError
    # os.system(binpath + '/avalongen ' + "unpack " + " ".join([f"\"{i}\"" for i in sys.argv[2:]]))

# Define a command function for the 'redobin' command (hidden)
@p.command("redobin", hidden=True)
def redoBinCopy(
    flags: kazparse.flags.Flags, paths: dict[str, Path], *args: str
) -> None:
    redoBin(flags, paths, *args)

# Define a command function for the 'installed' command
@p.command("installed")
def listInstalled(
    flags: kazparse.flags.Flags, paths: dict[str, Path], *args: str
) -> None:
    "List installed packages"

    # Call the 'installed' function to list installed packages
    installed(flags, paths, *args)

# Define a command function for the 'src' command
@p.command("src")
def dlSrcCli(flags: kazparse.flags.Flags, paths: dict[str, Path], *args: str) -> None:
    "Download a repo into a folder"

    # Call the 'dlSrc' function to download a repository into a specified folder
    dlSrc(flags, paths, *args)


# Define the main function that serves as the entry point of the script
def main() -> None:

    # Run the 'p.run' method to start the execution of the Avalon Package Manager (APM)
    # The 'extras' parameter is used to provide additional context or data to the command-line parser
    # In this case, 'paths' contains a dictionary with various paths used by the APM script
    # This allows the CLI commands to access and utilize these paths as needed during execution
    p.run(extras=paths)

