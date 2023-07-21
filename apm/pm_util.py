"""
Main utilities for the package manager.

TODO: separate into smaller files
"""

#!/usr/bin/python3

import os
import sys
import shutil
import json
import getpass
import platform
import filecmp
import subprocess  # nosec B404

from typing import Any, Literal
from pathlib import Path

import distro
import requests
import kazparse

from apm import log
from .package import NPackage
from .case.case import getCaseInsensitivePath


# class e404(Exception):
#    pass


def error(*text: str) -> None:
    "Print an error and exit."
    log.error(*text)
    sys.exit(1)


def copy_file(src: Path, dst: Path) -> None:
    "Copy a file only if files are not the same or the destination\
    does not exist"
    if not os.path.dirname(dst).strip() == "":
        os.makedirs(os.path.dirname(dst), exist_ok=True)

    if os.path.isfile(src):
        if not os.path.exists(dst) or not filecmp.cmp(src, dst):
            shutil.copy2(src, dst)
    else:
        if os.path.exists(src):
            for file in os.listdir(src):
                copy_file(src / file, dst / file)


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

    package_url = "https://raw.githubusercontent.com/{package}/{branch}/.avalon/package"

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
        info = get_remote_package_metadata(pkgname, commit=commit, branch=branch)

    if info is None:
        error("No valid metadata available for", pkgname)
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


def moveMainRepoToAvalonFolder(pkgname: str, paths: dict[str, Path]) -> None:
    log.debug(
        "Copying package metadata from the metadata repo for",
        pkgname,
        "into the package.",
    )

    shutil.rmtree(
        log.debug(str(paths["src"] / pkgname / ".avalon")), ignore_errors=True
    )

    if is_in_metadata_repository(pkgname, paths):
        log.debug(
            "Copying metadata from",
            getCaseInsensitivePath(str(paths["cache"] / pkgname)),
            "to",
            str(paths["src"] / pkgname / ".avalon"),
        )
        shutil.copytree(
            getCaseInsensitivePath(str(paths["cache"] / pkgname)),
            str(paths["src"] / pkgname / ".avalon"),
        )


def isAvalonPackage(paths: dict[str, Path], pkgname: str) -> bool:
    return bool(get_package_metadata(paths, pkgname))


def getDistro() -> str:
    return distro.linux_distribution()[0]


def distroIsSupported(pkg: Any) -> bool:
    log.debug(getDistro())

    if pkg["distros"]:
        return (getDistro() in pkg["distros"]) or (pkg["distros"] == ["all"])

    else:
        log.warn(
            "Supported distros not specified, assuming this distro is supported....."
        )
        return True


def getArch() -> str:
    return platform.machine()


def archIsSupported(pkg: Any) -> bool:
    log.debug(str(pkg))
    log.debug(getArch())

    if pkg["arches"]:
        return (getArch() in pkg["arches"]) or (pkg["arches"] == ["all"])

    else:
        log.warn("Supported arches not specified, assuming this arch is supported.....")
        return True


def checkReqs(paths: dict[str, Path], pkgname: str, force: bool) -> None:
    pkg = get_package_metadata(paths, pkgname)

    if force:
        if not archIsSupported(pkg):
            log.warn(
                f"Arch {getArch()} not supported by package, continuing anyway due to forced mode"
            )

        if not distroIsSupported(pkg):
            log.warn(
                f"Distro {getDistro()} not supported by package, \
                continuing anyway due to forced mode"
            )

        return

    if not archIsSupported(pkg):
        deletePackage(paths, pkgname)
        error(f"Arch {getArch()} not supported by package")

    if not distroIsSupported(pkg):
        deletePackage(paths, pkgname)
        error(f"Distro {getDistro()} not supported by package")


def downloadPackage(
    paths: dict[str, Path],
    packageUrl: str,
    packagename: str | None = None,
    branch: str | None = None,
    commit: str | None = None,
) -> None:
    if not packagename:
        packagename = packageUrl.lstrip("https://github.com/")

    log.debug(packagename)
    os.chdir(paths["src"])

    if commit and branch:
        os.system("git clone " + packageUrl + " " + packagename + " -q")
        os.system(f"cd {packagename}; git reset --hard {commit}")

    elif branch:
        packagename = "/".join(packagename.split(":")[:-1])
        os.system(
            "git clone --depth 1 " + packageUrl + " " + packagename + " -q -b " + branch
        )

    elif commit:
        os.system("git clone " + packageUrl + " " + packagename + " -q")
        os.system(f"cd {packagename}; git reset --hard {commit}")

    else:
        os.system("git clone --depth 1 " + packageUrl + " " + packagename + " -q")


def deletePackage(
    paths: dict[str, Path],
    packagename: str,
    cfg: Any | None = None,
    commit: str | None = None,
    branch: str | None = None,
) -> None:
    rmFromSrc(paths, packagename)

    if cfg:
        rmFromBin(paths, packagename, cfg, branch=branch, commit=commit)

    else:
        rmFromBin(paths, packagename, branch=branch, commit=commit)

    rmFromFiles(paths, packagename)


def rmFromSrc(paths: dict[str, Path], packagename: str) -> None:
    if (paths["src"] / packagename).exists():
        shutil.rmtree(paths["src"] / packagename, ignore_errors=True)


def rmFromBin(
    paths: dict[str, Path],
    packagename: str,
    pkg: Any | None = None,
    commit: str | None = None,
    branch: str | None = None,
) -> None:
    log.debug("RMBIN:", packagename)

    if not pkg:
        pkg = get_package_metadata(paths, packagename, commit, branch)

    if "binname" in pkg.keys():
        log.debug(str(paths["bin"] / str(pkg["binname"])))

        if (paths["bin"] / str(pkg["binname"])).exists():
            log.debug("Deleting", str(paths["bin"] / str(pkg["binname"])))
            os.remove(paths["bin"] / str(pkg["binname"]))


def rmFromFiles(paths: dict[str, Path], packagename: str) -> None:
    if (paths["files"] / packagename).exists():
        shutil.rmtree(paths["files"] / packagename, ignore_errors=True)


def mvBinToBin(
    paths: dict[str, Path], package_name: str, bin_file: str, bin_name: Path
) -> None:
    try:
        shutil.copyfile(
            paths["src"] / package_name / bin_file,
            paths["files"] / package_name / bin_name,
        )

    except Exception:
        log.warn(f"Failed to copy binary to {paths['files']}")

    if (paths["bin"] / bin_name).exists():
        os.remove(paths["bin"] / bin_name)

    os.symlink(paths["files"] / package_name / bin_file, paths["bin"] / bin_name)

    (paths["files"] / package_name / bin_name).chmod(0o755)


def copyFilesToFiles(
    paths: dict[str, Path], pkgname: str, files: list[str] = ["all"]
) -> None:
    log.debug("Copying files", str(files), "from src to files for", pkgname)

    if files != ["all"]:
        for file in files:
            copy_file(
                paths["src"] / pkgname / file,
                paths["files"] / pkgname / file,
            )

    else:
        for file in os.listdir(paths["src"] / pkgname):
            copy_file(
                paths["src"] / pkgname / file,
                paths["files"] / pkgname / file,
            )


def getAptInstalled() -> list[str]:
    aptinstalled = []

    dpkg_output = subprocess.check_output("dpkg -l".split()).decode()  # nosec B603

    for i in dpkg_output.split("\n"):
        if i.strip() != "" and i.startswith("ii"):
            try:
                i = i.split("  ")[1]

                if i.strip() not in aptinstalled:
                    aptinstalled.append(i.strip())

            except Exception:
                error(i)

    return aptinstalled


def aptFilter(deps: list[str]) -> list[str]:
    """Filter out installed packages"""
    aptinstalled = getAptInstalled()

    return list(filter(lambda dep: dep not in aptinstalled, deps))


def am_not_root() -> bool:
    username = getpass.getuser()

    return username != "root" and not username.startswith("u0_a")


def installAptDeps(deps: dict[str, list[str]]) -> None:
    if "apt" not in deps:
        return None

    if deps["apt"]:
        filtered_deps = aptFilter(deps["apt"])

        if len(filtered_deps) > 0:
            log.note(
                "Found apt dependencies, installing..... (this will require your password)"
            )

            joined_deps = " ".join(filtered_deps)

            sudo = "sudo " if am_not_root() else ""

            if os.system(log.debug(f"{sudo}apt install -y {joined_deps}")):
                error("apt subprocess encountered an error.")


def installBuildDepDeps(deps: dict[str, list[str]]) -> None:
    try:
        deps["build-dep"]

    except:
        return

    if deps["build-dep"]:
        log.note(
            "Found build-dep (apt) dependencies, installing..... (this will require your password)"
        )

        joined_deps = " ".join(deps["build-dep"])
        username = getpass.getuser()

        sudo = "sudo " if am_not_root() else ""

        if os.system(log.debug(f"{sudo}apt build-dep -y {joined_deps}")):
            error("apt subprocess encountered an error.")


def installAvalonDeps(
    flags: kazparse.flags.Flags,
    paths: dict[str, Path],
    args: list[str],
    deps: dict[str, list[str]],
) -> None:
    try:
        deps["avalon"]

    except:
        return

    args = args.copy()

    if deps["avalon"]:
        log.note("Found avalon dependencies, installing.....")

        for dep in deps["avalon"]:
            if not (paths["files"] / dep.lower()).exists() or flags.update:
                log.note("Installing", dep)
                log.silent(True)
                args[0] = dep
                installPackage(flags, paths, args)
                log.silent(False)
                log.note("Installed", dep)


def installPipDeps(deps: dict[str, list[str]]) -> None:
    try:
        deps["pip"]

    except:
        return

    log.note("Found pip dependencies, installing.....")
    joined_deps = " ".join(deps["pip"])

    on_gentoo = os.path.exists("/etc/portage")
    user_flag = " --user" if on_gentoo else ""

    os.system(log.debug(f"python3 -m pip install{user_flag} {joined_deps}"))


def reqTxt(pkgname: str, paths: dict[str, Path]) -> None:
    log.debug(str(paths["src"] / pkgname / "requirements.txt"))
    log.debug(os.curdir)

    if (paths["src"] / pkgname / "requirements.txt").exists():
        log.note("Requirements.txt found, installing.....")

        on_gentoo = os.path.exists("/etc/portage")
        user_flag = " --user" if on_gentoo else ""

        req_txt = paths["src"] / pkgname / "requirements.txt"

        os.system(
            log.debug(
                f"python3 -m pip --disable-pip-version-check -q install{user_flag} -r {req_txt}"
            )
        )


def installDeps(
    flags: kazparse.flags.Flags, paths: dict[str, Path], args: list[str]
) -> None:
    pkg = get_package_metadata(paths, args[0])

    if pkg["deps"]:
        log.note("Found dependencies, installing.....")
        pkgdeps = pkg["deps"]

        if os.path.exists("/usr/bin/apt") and not os.path.exists(
            "/usr/libexec/eselect-java/run-java-tool.bash"
        ):
            installAptDeps(pkgdeps)
            installBuildDepDeps(pkgdeps)

        installAvalonDeps(flags, paths, args, pkgdeps)
        installPipDeps(pkgdeps)

    reqTxt(args[0], paths)


def runScript(script: Path, *args: str) -> int:
    langs = {".py": "python3", ".sh": "bash"}

    if os.path.exists("/etc/portage"):
        with open(script, "r") as r:
            e = r.read()

            with open(script, "w") as w:
                w.write(
                    e.replace("pip3 install", "pip3 install --user").replace(
                        "pip install", "pip install --user"
                    )
                )

    argss = " ".join([f"{arg}" for arg in args])

    if script.suffix.lower() in langs:
        return os.system(log.debug(f"{langs[script.suffix.lower()]} {script} {argss}"))

    else:
        return os.system(log.debug(f'{langs[".sh"]} {script} {argss}'))


def compilePackage(
    packagename: str,
    paths: dict[str, Path],
    flags: kazparse.flags.Flags,
) -> None:
    pkg = get_package_metadata(paths, packagename)
    os.chdir(paths["src"] / packagename)

    (paths["files"] / packagename).mkdir(parents=True, exist_ok=True)

    if pkg["needsCompiled"]:
        if not pkg["binname"]:
            log.warn(
                "Package needs compiled but there is no binname for Avalon to install, \
                assuming installed by compile script....."
            )

        if pkg["compileScript"]:
            log.note("Compile script found, compiling.....")

            if runScript(
                paths["src"] / packagename / pkg["compileScript"],
                f"\"{paths['src'] / packagename}\" \"{pkg['binname']}\" \
                \"{paths['files'] / packagename}\"",
            ):
                error("Compile script failed!")

        else:
            error(
                "Program needs compiling but no compilation script found... exiting....."
            )

    else:
        log.warn("Program does not need to be compiled, moving to installation.....")

    if pkg["binname"] and not pkg["mvBinAfterInstallScript"]:
        rmFromBin(paths, packagename)

        mvBinToBin(
            paths,
            packagename,
            str(pkg.get("binfile", pkg["binname"])),
            Path(pkg["binname"]),
        )

    if pkg["installScript"]:
        log.note("Installing.....")

        if pkg["needsCompiled"] or pkg["compileScript"] or pkg["binname"]:
            if runScript(
                paths["src"] / packagename / pkg["installScript"],
                f"\"{paths['files'] / packagename / str(pkg['binname'])}\" \
                \"{paths['files'] / packagename}\" \
                \"{paths['bin']}\" \"{paths['src']}\"",
            ):
                error("Install script failed!")

        else:
            if runScript(
                paths["src"] / packagename / pkg["installScript"],
                f"\"{paths['files'] / packagename}\" \"{paths['src']}\" \"{packagename}\"",
            ):
                error("Install script failed!")

    if pkg["toCopy"]:
        log.note("Copying files needed by program.....")
        copyFilesToFiles(paths, packagename, pkg["toCopy"])

    if pkg["mvBinAfterInstallScript"] and pkg["binname"]:
        rmFromBin(paths, packagename)

        mvBinToBin(
            paths,
            packagename,
            str(pkg.get("binfile", pkg["binname"])),
            Path(pkg["binname"]),
        )

    else:
        log.warn(
            "No installation script found... Assuming \
            installation beyond APM's autoinstaller isn't neccessary"
        )


def installLocalPackage(
    flags: kazparse.flags.Flags, paths: dict[str, Path], args: list[str]
) -> None:
    tmppath = paths["tmp"]

    shutil.rmtree(tmppath)

    if not os.path.exists(tmppath):
        os.mkdir(tmppath)

    log.IS_DEBUG = flags.debug

    log.note("Unpacking package.....")

    if not os.path.exists(args[0]):
        error(f"{args[0]} does not exist")

    elif os.path.isdir(args[0]):
        if os.system(log.debug(f"cp -r {args[0]}/./ {tmppath}")):
            error("Failed to copy files")

    else:
        if os.system(log.debug(f"tar -xf {args[0]} -C {tmppath}")):
            error("Error unpacking package, not a tar.gz file")

    cfgfile = json.load(open(f"{tmppath}/.avalon/package", "r"))

    try:
        args[0] = (cfgfile["author"] + "/" + cfgfile["repo"]).lower()

    except:
        error("Package's package file need 'author' and 'repo'")

    log.note("Deleting old binaries and source files.....")
    deletePackage(paths, args[0], cfgfile)

    log.note("Copying package files....")

    if os.system(log.debug(f"mkdir -p {paths['src'] / args[0]}")):
        error("Failed to make src folder")

    if os.system(log.debug(f"cp -a {tmppath}/. {paths['src'] / args[0]}")):
        error("Failed to copy files from temp folder to src folder")

    shutil.rmtree(tmppath)

    checkReqs(paths, args[0], flags.force)

    installDeps(flags, paths, args)

    if not flags.noinstall:
        log.note("Beginning compilation/installation.....")
        compilePackage(args[0], paths, flags)
        log.success("Done!")

    else:
        log.warn("-ni specified, skipping installation/compilation")


def installPackage(
    flags: kazparse.flags.Flags, paths: dict[str, Path], args: list[str]
) -> None:
    if os.path.exists(args[0]):
        installLocalPackage(flags, paths, args)
        return

    if os.path.exists(f"{paths['src'] / args[0].lower()}") and not flags.fresh:
        updatePackage(flags, paths, *args)
        return

    log.IS_DEBUG = flags.debug

    args[0] = args[0].lower()

    download_metadata_repository(paths)

    packagename = args[0]

    if ":" in packagename:  # commit
        branch = None
        commit = packagename.split(":")[-1]
        packagename = packagename.split(":")[0]

    elif packagename.count("/") > 1:  # branch
        branch = packagename.split("/")[-1]
        packagename = "/".join(packagename.split(":")[:-1])
        commit = None

    elif (":" in packagename) and (packagename.count("/") > 1):  # branch and commit
        commit = packagename.split(":")[-1]
        packagename = packagename.split(":")[0]
        branch = packagename.split("/")[-1]
        packagename = "/".join(packagename.split(":")[:-1])

    else:  # no branch or commit specified
        branch = None
        commit = None

    args[0] = packagename

    log.note("Deleting old binaries and source files.....")
    deletePackage(paths, args[0], branch=branch, commit=commit)
    log.note("Downloading from github.....")
    log.debug("Downloading https://github.com/" + args[0], "to", str(paths["src"]))
    downloadPackage(
        paths,
        "https://github.com/" + packagename,
        packagename,
        branch=branch,
        commit=commit,
    )

    if is_in_metadata_repository(packagename, paths) and not isAvalonPackage(
        paths, packagename
    ):
        log.note(
            "Package is not an Avalon package, but it is \
            in the main repository... installing from there....."
        )
        moveMainRepoToAvalonFolder(packagename, paths)

    else:
        log.debug("Not in the main repo")

    checkReqs(paths, packagename, flags.force)

    installDeps(flags, paths, args)

    if not flags.noinstall:
        log.note("Beginning compilation/installation.....")
        compilePackage(packagename, paths, flags)
        log.success("Done!")

    else:
        log.warn("--noinstall specified, skipping installation/compilation")


def updatePackage(
    flags: kazparse.flags.Flags, paths: dict[str, Path], *args_: str
) -> None:
    "Update to newest version of a repo, then recompile + reinstall program"

    args: list[str] = list(args_)

    if len(args) == 0:
        args.append("r2boyo25/avalonpackagemanager")

    download_metadata_repository(paths)

    log.IS_DEBUG = flags.debug

    args[0] = args[0].lower()

    log.note("Pulling from github.....")

    if os.system(f"cd {paths['src'] / args[0]}; git pull"):
        if os.system(f"cd {paths['src'] / args[0]}; git reset --hard; git pull"):
            error("Git error")

    if is_in_metadata_repository(args[0], paths):
        log.note(
            "Package is not an Avalon package, but it is in \
            the main repository... installing from there....."
        )
        moveMainRepoToAvalonFolder(args[0], paths)

    else:
        log.debug("Not in the main repo")

    checkReqs(paths, args[0], flags.force)

    installDeps(flags, paths, args)

    if not flags.noinstall:
        log.note("Beginning compilation/installation.....")
        compilePackage(args[0], paths, flags)
        log.success("Done!")

    else:
        log.warn("-ni specified, skipping installation/compilation")


def redoBin(flags: kazparse.flags.Flags, paths: dict[str, Path], *args_: str) -> None:
    "Redo making of symlinks without recompiling program"
    args: list[str] = list(args_)

    log.IS_DEBUG = flags.debug

    args[0] = args[0].lower()

    packagename = args[0]
    pkg: NPackage = get_package_metadata(paths, packagename)
    log.debug(packagename, str(paths["bin"]), str(paths["src"]), str(pkg))
    rmFromBin(paths, packagename, pkg=pkg)

    mvBinToBin(
        paths,
        packagename,
        str(pkg.get("binfile", pkg["binname"])),
        Path(str(pkg["binname"])),
    )


def uninstallPackage(
    flags: kazparse.flags.Flags, paths: dict[str, Path], args: list[str]
) -> None:
    log.IS_DEBUG = flags.debug

    args[0] = args[0].lower()

    download_metadata_repository(paths)

    if is_in_metadata_repository(args[0], paths) and not isAvalonPackage(
        paths, args[0]
    ):
        log.note(
            "Package is not an Avalon package, but it is in \
            the main repository... uninstalling from there....."
        )
        moveMainRepoToAvalonFolder(args[0], paths)

    checkReqs(paths, args[0], flags.force)

    pkg = get_package_metadata(paths, args[0])
    log.note("Uninstalling.....")
    if not pkg["uninstallScript"]:
        log.warn(
            "Uninstall script not found... Assuming uninstall not required and deleting files....."
        )
        deletePackage(paths, args[0])

    else:
        log.note("Uninstall script found, running.....")
        os.chdir(paths["bin"])

        if runScript(
            paths["src"] / args[0] / pkg["uninstallScript"],
            str(paths["src"]),
            str(paths["bin"]),
            args[0],
            str(pkg["binname"]),
            str(paths["files"] / args[0]),
        ):
            log.error("Uninstall script failed! Deleting files anyways.....")

        deletePackage(paths, args[0])

    log.success("Successfully uninstalled package!")


def installed(flags: kazparse.flags.Flags, paths: dict[str, Path], *args: str) -> None:
    "List installed packages"

    log.IS_DEBUG = flags.debug

    print("\n".join(get_installed_packages_and_versions(paths)).title())


def download_package_source(
    flags: kazparse.flags.Flags, paths: dict[str, Path], *args: str
) -> None:
    "Download repo into folder"

    if len(args) == 1:
        os.system(f"git clone https://github.com/{args[0].lower()}")

    elif len(args) == 2:
        os.system(f"git clone https://github.com/{args[0].lower()} {args[1]}")

    else:
        os.system("git pull")  # nosec: B607, B605


def update_metadata_cache(
    _flags: kazparse.flags.Flags, paths: dict[str, Path], *_args: str
) -> None:
    "Update cache"

    download_metadata_repository(paths, do_not_update=False)
