"""
Main utilities for the package manager.

TODO: separate into smaller files
"""


import os
import shutil
import json
import getpass
import filecmp
import subprocess  # nosec B404

from typing import Any
from pathlib import Path

import kazparse

from apm import log
from apm.log import fatal_error
from .package import NPackage
from .metadata import (
    is_in_metadata_repository,
    get_package_metadata,
    download_metadata_repository,
    is_avalon_package,
    move_metadata_to_dot_avalon_folder,
)
from .requirements import check_for_satisfied_package_requirements


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


def download_package(
    paths: dict[str, Path],
    package_url: str,
    packagename: str | None = None,
    branch: str | None = None,
    commit: str | None = None,
) -> None:
    """Downloads a specfic commit and branch of a package."""

    if not packagename:
        packagename = package_url.lstrip("https://github.com/")

    log.debug(packagename)
    os.chdir(paths["src"])

    if commit and branch:
        os.system("git clone " + package_url + " " + packagename + " -q")
        os.system(f"cd {packagename}; git reset --hard {commit}")

    elif branch:
        packagename = "/".join(packagename.split(":")[:-1])
        os.system(
            "git clone --depth 1 "
            + package_url
            + " "
            + packagename
            + " -q -b "
            + branch
        )

    elif commit:
        os.system("git clone " + package_url + " " + packagename + " -q")
        os.system(f"cd {packagename}; git reset --hard {commit}")

    else:
        os.system(
            "git clone --depth 1 " + package_url + " " + packagename + " -q"
        )


def delete_package(
    paths: dict[str, Path],
    packagename: str,
    cfg: Any | None = None,
    commit: str | None = None,
    branch: str | None = None,
) -> None:
    """Deletes the package."""

    remove_package_source(paths, packagename)

    if cfg:
        remove_package_binary_symlink(
            paths, packagename, cfg, branch=branch, commit=commit
        )

    else:
        remove_package_binary_symlink(
            paths, packagename, branch=branch, commit=commit
        )

    remove_package_files(paths, packagename)


def remove_package_source(paths: dict[str, Path], packagename: str) -> None:
    """Deletes the source code of a package."""

    if (paths["src"] / packagename).exists():
        shutil.rmtree(paths["src"] / packagename, ignore_errors=True)


def remove_package_binary_symlink(
    paths: dict[str, Path],
    packagename: str,
    pkg: Any | None = None,
    commit: str | None = None,
    branch: str | None = None,
) -> None:
    """Deletes the symlink for a package."""

    log.debug("Removing symlink for:", packagename)

    if not pkg:
        pkg = get_package_metadata(paths, packagename, commit, branch)

    if "binname" in pkg.keys():
        log.debug(str(paths["bin"] / str(pkg["binname"])))

        if (paths["bin"] / str(pkg["binname"])).exists():
            log.debug("Deleting", str(paths["bin"] / str(pkg["binname"])))
            os.remove(paths["bin"] / str(pkg["binname"]))


def remove_package_files(paths: dict[str, Path], packagename: str) -> None:
    """Remove's a package's installed files."""

    if (paths["files"] / packagename).exists():
        shutil.rmtree(paths["files"] / packagename, ignore_errors=True)


def symlink_binary_for_package(
    paths: dict[str, Path], package_name: str, bin_file: str, bin_name: Path
) -> None:
    """Symlinks a binary for the package."""

    try:
        shutil.copyfile(
            paths["src"] / package_name / bin_file,
            paths["files"] / package_name / bin_name,
        )

    except shutil.Error:
        log.warn(f"Failed to copy binary to {paths['files']}")

    if (paths["bin"] / bin_name).exists():
        os.remove(paths["bin"] / bin_name)

    os.symlink(
        paths["files"] / package_name / bin_file, paths["bin"] / bin_name
    )

    (paths["files"] / package_name / bin_name).chmod(0o755)


def copy_package_files_to_files_dir(
    paths: dict[str, Path], pkgname: str, files: list[str] | None = None
) -> None:
    """Copies a package's files from its source directory to its files directory."""

    if files is None:
        files = ["all"]

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


def get_installed_apt_packages() -> list[str]:
    """Returns a list of the installed apt packages"""

    aptinstalled = []

    dpkg_output = subprocess.check_output(
        "dpkg -l".split()
    ).decode()  # nosec B603

    for i in dpkg_output.split("\n"):
        if i.strip() != "" and i.startswith("ii"):
            try:
                i = i.split("  ")[1]

                if i.strip() not in aptinstalled:
                    aptinstalled.append(i.strip())

            except IndexError:
                fatal_error(i)

    return aptinstalled


def apt_filter_uninstalled(deps: list[str]) -> list[str]:
    """Filter out installed packages"""
    aptinstalled = get_installed_apt_packages()

    return list(filter(lambda dep: dep not in aptinstalled, deps))


def am_not_root() -> bool:
    """Returns whether the user needs to use `sudo`."""

    username = getpass.getuser()

    return username != "root" and not username.startswith("u0_a")


def install_apt_dependencies(deps: dict[str, list[str]]) -> None:
    """Installs a package's apt dependencies."""

    if "apt" not in deps:
        return

    if deps["apt"] is None:
        return

    filtered_deps = apt_filter_uninstalled(deps["apt"])

    if len(filtered_deps) > 0:
        log.note(
            "Found apt dependencies, installing..... (this will require your password)"
        )

        joined_deps = " ".join(filtered_deps)
        sudo = "sudo " if am_not_root() else ""

        if os.system(log.debug(f"{sudo}apt install -y {joined_deps}")):
            fatal_error("apt subprocess encountered an error.")


def install_apt_build_dep_dependencies(deps: dict[str, list[str]]) -> None:
    """Install's a packages `apt build-dep` dependencies."""

    if "build-dep" not in deps:
        return

    if deps["build-dep"]:
        log.note(
            "Found build-dep (apt) dependencies, installing..... (this will require your password)"
        )

        joined_deps = " ".join(deps["build-dep"])
        sudo = "sudo " if am_not_root() else ""

        if os.system(log.debug(f"{sudo}apt build-dep -y {joined_deps}")):
            fatal_error("apt subprocess encountered an error.")


def install_avalon_dependencies(
    flags: kazparse.flags.Flags,
    paths: dict[str, Path],
    args: list[str],
    deps: dict[str, list[str]],
) -> None:
    """Installs a package's Avalon dependencies."""

    if "avalon" not in deps:
        return

    if deps["avalon"] is None:
        return

    args = args.copy()

    log.note("Found avalon dependencies, installing.....")

    for dep in deps["avalon"]:
        if not (paths["files"] / dep.lower()).exists() or flags.update:
            log.note("Installing", dep)
            log.IS_SILENT = True
            args[0] = dep
            install_package(flags, paths, args)
            log.IS_SILENT = False
            log.note("Installed", dep)


def install_pip_dependencies(deps: dict[str, list[str]]) -> None:
    """Installs a package's `pip` dependencies."""

    if "pip" not in deps:
        return

    if deps["pip"] is None:
        return

    log.note("Found pip dependencies, installing.....")
    joined_deps = " ".join(deps["pip"])

    on_gentoo = os.path.exists("/etc/portage")
    user_flag = " --user" if on_gentoo else ""

    os.system(log.debug(f"python3 -m pip install{user_flag} {joined_deps}"))


def install_requirements_dot_txt(pkgname: str, paths: dict[str, Path]) -> None:
    """Installs a package's pip depdencies as specified in `requirements.txt`."""

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


def install_package_dependencies(
    flags: kazparse.flags.Flags, paths: dict[str, Path], args: list[str]
) -> None:
    """Installs a package's dependencies."""

    pkg = get_package_metadata(paths, args[0])

    if pkg["deps"]:
        log.note("Found dependencies, installing.....")
        pkgdeps = pkg["deps"]

        if os.path.exists("/usr/bin/apt") and not os.path.exists(
            "/usr/libexec/eselect-java/run-java-tool.bash"
        ):
            install_apt_dependencies(pkgdeps)
            install_apt_build_dep_dependencies(pkgdeps)

        install_avalon_dependencies(flags, paths, args, pkgdeps)
        install_pip_dependencies(pkgdeps)

    install_requirements_dot_txt(args[0], paths)
    # TODO: install_poetry_dependencies


def run_script(script_file: Path, *args: str) -> int:
    """Runs a script with its specific interpreter based on the extension."""

    langs = {".py": "python3", ".sh": "bash"}

    if os.path.exists("/etc/portage"):
        with open(script_file, "r", encoding="utf-8") as script:
            contents = script.read()

            with open(script_file, "w", encoding="utf-8") as script_write:
                script_write.write(
                    contents.replace(
                        "pip3 install", "pip3 install --user"
                    ).replace("pip install", "pip install --user")
                )

    argss = " ".join([f"{arg}" for arg in args])

    if script_file.suffix.lower() in langs:
        return os.system(
            log.debug(
                f"{langs[script_file.suffix.lower()]} {script_file} {argss}"
            )
        )

    return os.system(log.debug(f'{langs[".sh"]} {script_file} {argss}'))


def compile_package(
    packagename: str,
    paths: dict[str, Path],
    _flags: kazparse.flags.Flags,
) -> None:
    """Compiles a package."""

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

            if run_script(
                paths["src"] / packagename / pkg["compileScript"],
                f"\"{paths['src'] / packagename}\" \"{pkg['binname']}\" \
                \"{paths['files'] / packagename}\"",
            ):
                fatal_error("Compile script failed!")

        else:
            fatal_error(
                "Program needs compiling but no compilation script found... exiting....."
            )

    else:
        log.warn(
            "Program does not need to be compiled, moving to installation....."
        )

    if pkg["binname"] and not pkg["mvBinAfterInstallScript"]:
        remove_package_binary_symlink(paths, packagename)

        symlink_binary_for_package(
            paths,
            packagename,
            str(pkg.get("binfile", pkg["binname"])),
            Path(pkg["binname"]),
        )

    if pkg["installScript"]:
        log.note("Installing.....")

        if pkg["needsCompiled"] or pkg["compileScript"] or pkg["binname"]:
            if run_script(
                paths["src"] / packagename / pkg["installScript"],
                f"\"{paths['files'] / packagename / str(pkg['binname'])}\" \
                \"{paths['files'] / packagename}\" \
                \"{paths['bin']}\" \"{paths['src']}\"",
            ):
                fatal_error("Install script failed!")

        else:
            if run_script(
                paths["src"] / packagename / pkg["installScript"],
                f"\"{paths['files'] / packagename}\" \"{paths['src']}\" \"{packagename}\"",
            ):
                fatal_error("Install script failed!")

    if pkg["toCopy"]:
        log.note("Copying files needed by program.....")
        copy_package_files_to_files_dir(paths, packagename, pkg["toCopy"])

    if pkg["mvBinAfterInstallScript"] and pkg["binname"]:
        remove_package_binary_symlink(paths, packagename)

        symlink_binary_for_package(
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


def install_package_from_directory(
    flags: kazparse.flags.Flags, paths: dict[str, Path], args: list[str]
) -> None:
    """Installs a package from a local directory."""

    tmppath = paths["tmp"]

    shutil.rmtree(tmppath)

    if not os.path.exists(tmppath):
        os.mkdir(tmppath)

    log.IS_DEBUG = flags.debug

    log.note("Unpacking package.....")

    if not os.path.exists(args[0]):
        fatal_error(f"{args[0]} does not exist")

    elif os.path.isdir(args[0]):
        if os.system(log.debug(f"cp -r {args[0]}/./ {tmppath}")):
            fatal_error("Failed to copy files")

    else:
        if os.system(log.debug(f"tar -xf {args[0]} -C {tmppath}")):
            fatal_error("Error unpacking package, not a tar.gz file")

    with (tmppath / ".avalon/package").open(
        "r", encoding="utf-8"
    ) as package_file:
        cfgfile = json.load(package_file)

    try:
        args[0] = (cfgfile["author"] + "/" + cfgfile["repo"]).lower()

    except KeyError:
        fatal_error("Package's package file need 'author' and 'repo'")

    log.note("Deleting old binaries and source files.....")
    delete_package(paths, args[0], cfgfile)

    log.note("Copying package files....")

    if os.system(log.debug(f"mkdir -p {paths['src'] / args[0]}")):
        fatal_error("Failed to make src folder")

    if os.system(log.debug(f"cp -a {tmppath}/. {paths['src'] / args[0]}")):
        fatal_error("Failed to copy files from temp folder to src folder")

    shutil.rmtree(tmppath)

    (
        satisfied,
        constraint,
        unsupported,
    ) = check_for_satisfied_package_requirements(paths, args[0], flags.force)

    if not satisfied:
        fatal_error(
            f'{constraint} "{unsupported}" is not supported by {args[0]}.'
        )

    install_package_dependencies(flags, paths, args)

    if not flags.noinstall:
        log.note("Beginning compilation/installation.....")
        compile_package(args[0], paths, flags)
        log.success("Done!")

    else:
        log.warn("-ni specified, skipping installation/compilation")


def install_package(
    flags: kazparse.flags.Flags, paths: dict[str, Path], args: list[str]
) -> None:
    """Installs a package."""

    if os.path.exists(args[0]):
        install_package_from_directory(flags, paths, args)
        return

    if os.path.exists(f"{paths['src'] / args[0].lower()}") and not flags.fresh:
        update_package(flags, paths, *args)
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

    elif (":" in packagename) and (
        packagename.count("/") > 1
    ):  # branch and commit
        commit = packagename.split(":")[-1]
        packagename = packagename.split(":")[0]
        branch = packagename.split("/")[-1]
        packagename = "/".join(packagename.split(":")[:-1])

    else:  # no branch or commit specified
        branch = None
        commit = None

    args[0] = packagename

    log.note("Deleting old binaries and source files.....")
    delete_package(paths, args[0], branch=branch, commit=commit)
    log.note("Downloading from github.....")
    log.debug(
        "Downloading https://github.com/" + args[0], "to", str(paths["src"])
    )
    download_package(
        paths,
        "https://github.com/" + packagename,
        packagename,
        branch=branch,
        commit=commit,
    )

    if is_in_metadata_repository(packagename, paths) and not is_avalon_package(
        paths, packagename
    ):
        log.note(
            "Package is not an Avalon package, but it is \
            in the main repository... installing from there....."
        )
        move_metadata_to_dot_avalon_folder(packagename, paths)

    else:
        log.debug("Not in the main repo")

    (
        satisfied,
        constraint,
        unsupported,
    ) = check_for_satisfied_package_requirements(
        paths, packagename, flags.force
    )

    if not satisfied:
        fatal_error(
            f'{constraint} "{unsupported}" is not supported by {packagename}.'
        )

    install_package_dependencies(flags, paths, args)

    if not flags.noinstall:
        log.note("Beginning compilation/installation.....")
        compile_package(packagename, paths, flags)
        log.success("Done!")

    else:
        log.warn("--noinstall specified, skipping installation/compilation")


def update_package(
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
        if os.system(
            f"cd {paths['src'] / args[0]}; git reset --hard; git pull"
        ):
            fatal_error("Git error")

    if is_in_metadata_repository(args[0], paths):
        log.note(
            "Package is not an Avalon package, but it is in \
            the main repository... installing from there....."
        )
        move_metadata_to_dot_avalon_folder(args[0], paths)

    else:
        log.debug("Not in the main repo")

    (
        satisfied,
        constraint,
        unsupported,
    ) = check_for_satisfied_package_requirements(paths, args[0], flags.force)

    if not satisfied:
        fatal_error(
            f'{constraint} "{unsupported}" is not supported by {args[0]}.'
        )

    install_package_dependencies(flags, paths, args)

    if not flags.noinstall:
        log.note("Beginning compilation/installation.....")
        compile_package(args[0], paths, flags)
        log.success("Done!")

    else:
        log.warn("-ni specified, skipping installation/compilation")


def redo_symlinks_for_package(
    flags: kazparse.flags.Flags, paths: dict[str, Path], *args_: str
) -> None:
    "Redo making of symlinks without recompiling program"
    args: list[str] = list(args_)

    log.IS_DEBUG = flags.debug

    args[0] = args[0].lower()

    packagename = args[0]
    pkg: NPackage = get_package_metadata(paths, packagename)
    log.debug(packagename, str(paths["bin"]), str(paths["src"]), str(pkg))
    remove_package_binary_symlink(paths, packagename, pkg=pkg)

    symlink_binary_for_package(
        paths,
        packagename,
        str(pkg.get("binfile", pkg["binname"])),
        Path(str(pkg["binname"])),
    )


def uninstall_package(
    flags: kazparse.flags.Flags, paths: dict[str, Path], args: list[str]
) -> None:
    """Uninstalls a package."""

    log.IS_DEBUG = flags.debug

    args[0] = args[0].lower()

    download_metadata_repository(paths)

    if is_in_metadata_repository(args[0], paths) and not is_avalon_package(
        paths, args[0]
    ):
        log.note(
            "Package is not an Avalon package, but it is in \
            the main repository... uninstalling from there....."
        )
        move_metadata_to_dot_avalon_folder(args[0], paths)

    (
        satisfied,
        constraint,
        unsupported,
    ) = check_for_satisfied_package_requirements(paths, args[0], flags.force)

    if not satisfied:
        fatal_error(
            f'{constraint} "{unsupported}" is not supported by {args[0]}.'
        )

    pkg = get_package_metadata(paths, args[0])
    log.note("Uninstalling.....")
    if not pkg["uninstallScript"]:
        log.warn(
            "Uninstall script not found... Assuming uninstall not required and deleting files....."
        )
        delete_package(paths, args[0])

    else:
        log.note("Uninstall script found, running.....")
        os.chdir(paths["bin"])

        if run_script(
            paths["src"] / args[0] / pkg["uninstallScript"],
            str(paths["src"]),
            str(paths["bin"]),
            args[0],
            str(pkg["binname"]),
            str(paths["files"] / args[0]),
        ):
            log.error("Uninstall script failed! Deleting files anyways.....")

        delete_package(paths, args[0])

    log.success("Successfully uninstalled package!")


def download_package_source(
    _flags: kazparse.flags.Flags, _paths: dict[str, Path], *args: str
) -> None:
    "Download repo into folder"

    if len(args) == 1:
        os.system(f"git clone https://github.com/{args[0].lower()}")

    elif len(args) == 2:
        os.system(f"git clone https://github.com/{args[0].lower()} {args[1]}")

    else:
        os.system("git pull")  # nosec: B607, B605
