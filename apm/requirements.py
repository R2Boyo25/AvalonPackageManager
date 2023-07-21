"""
Functions for checking that Linux distributions and CPU architectures are supported.
"""

import platform
from typing import Any
from pathlib import Path

import distro

from apm import log
from .metadata import get_package_metadata


def get_linux_distribution() -> str:
    """Returns the name of the current Linux distribution."""

    return distro.linux_distribution()[0]


def linux_distribution_is_supported(pkg: Any) -> bool:
    """Check if Linux distribution is supported by the package."""
    log.debug(get_linux_distribution())

    if pkg["distros"]:
        return (get_linux_distribution() in pkg["distros"]) or (
            pkg["distros"] == ["all"]
        )

    log.warn(
        "Supported Linux distributions have not been specified, \
        assuming this Linux distribution is supported..."
    )
    return True


def get_architecture() -> str:
    """Returns the current CPU architecture."""

    return platform.machine()


def architecture_is_supported(pkg: Any) -> bool:
    """Checks if the CPU architecture is supported by the package."""

    log.debug("Package metadata:", str(pkg))
    log.debug("Architecture:", get_architecture())

    if pkg["arches"]:
        return (get_architecture() in pkg["arches"]) or (
            pkg["arches"] == ["all"]
        )

    log.warn(
        "Supported architectures have not been specified, \
        assuming that this architecture is supported..."
    )
    return True


def check_for_satisfied_package_requirements(
    paths: dict[str, Path], pkgname: str, force: bool
) -> tuple[bool, str | None, str | None]:
    """Checks that the package's requirements are satisfied"""
    pkg = get_package_metadata(paths, pkgname)

    if force:
        if not architecture_is_supported(pkg):
            log.warn(
                f"Arch {get_architecture()} not supported by \
                package, continuing anyway due to forced mode"
            )

        if not linux_distribution_is_supported(pkg):
            log.warn(
                f"Distro {get_linux_distribution()} not supported by package, \
                continuing anyway due to forced mode"
            )

        return True, None, None

    if not architecture_is_supported(pkg):
        return False, "CPU Architecture", get_architecture()

    if not linux_distribution_is_supported(pkg):
        return False, "Linux distribution", get_linux_distribution()

    return True, None, None
