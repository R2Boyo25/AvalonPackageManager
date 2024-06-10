"""
Contains NPackage.
"""

from dataclasses import dataclass


@dataclass
class Package:
    version: str | None = None
    binname: str | None = None
    binfile: str | None = None

    deps: dict[str, list[str]] | None = None
    arches: list[str] | None = None
    distros: list[str] | None = None

    compileScript: str | None = None
    installScript: str | None = None
    uninstallScript: str | None = None

    toCopy: list[str] | None = None

    needsCompiled: bool | None = None
    mvBinAfterInstallScript: bool | None = None
