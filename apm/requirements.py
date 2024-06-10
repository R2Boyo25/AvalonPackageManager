"""
Functions for checking that Linux distributions and CPU architectures are supported.
"""

import platform

import distro

from apm import log
from apm.package import Package
from apm.path import Paths
from .metadata import get_package_metadata


def get_linux_distribution() -> str:
    """Returns the name of the current Linux distribution."""

    return distro.linux_distribution()[0]


def linux_distribution_is_supported(package: Package) -> bool:
    """Check if Linux distribution is supported by the package."""
    log.debug(get_linux_distribution())

    if package.distros:
        return (get_linux_distribution() in package.distros) or (
            package.distros == ["all"]
        )

    log.warn(
        "Supported Linux distributions have not been specified, \
        assuming this Linux distribution is supported..."
    )
    return True


def get_architecture() -> str:
    """Returns the current CPU architecture."""

    return platform.machine()


def architecture_is_supported(package: Package) -> bool:
    """Checks if the CPU architecture is supported by the package."""

    log.debug("Package metadata:", str(package))
    log.debug("Architecture:", get_architecture())

    if package.arches:
        return (get_architecture() in package.arches) or (package.arches == ["all"])

    log.warn(
        "Supported architectures have not been specified, \
        assuming that this architecture is supported..."
    )
    return True


def check_for_satisfied_package_requirements(
    paths: Paths, package_name: str, force: bool
) -> tuple[bool, str | None, str | None]:
    """Checks that the package's requirements are satisfied"""
    package = get_package_metadata(paths, package_name)

    if force:
        if not architecture_is_supported(package):
            log.warn(
                f"Arch {get_architecture()} not supported by \
                package, continuing anyway due to forced mode"
            )

        if not linux_distribution_is_supported(package):
            log.warn(
                f"Distro {get_linux_distribution()} not supported by package, \
                continuing anyway due to forced mode"
            )

        return True, None, None

    if not architecture_is_supported(package):
        return False, "CPU Architecture", get_architecture()

    if not linux_distribution_is_supported(package):
        return False, "Linux distribution", get_linux_distribution()

    return True, None, None
