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

from pathlib import Path

import kazparse
import kazparse.flags

from apm import log
from apm.log import fatal_error
from .path import Paths
from .package import Package
from .metadata import (
    is_in_metadata_repository,
    get_package_metadata,
    download_metadata_repository,
    is_avalon_package,
    move_metadata_to_dot_avalon_folder,
)
from .requirements import check_for_satisfied_package_requirements


def copy_file(src: Path, dst: Path) -> None:
    """Copy a file only if files are not the same or the destination does not exist"""
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
    paths: Paths,
    package_url: str,
    package_name: str | None = None,
    branch: str | None = None,
    commit: str | None = None,
) -> None:
    """Downloads a specfic commit and branch of a package."""

    if not package_name:
        package_name = package_url.lstrip("https://github.com/")

    log.debug(package_name)
    os.chdir(paths.source)

    if commit and branch:
        os.system("git clone " + package_url + " " + package_name + " -q")
        os.system(f"cd {package_name}; git reset --hard {commit}")

    elif branch:
        package_name = "/".join(package_name.split(":")[:-1])
        os.system(
            "git clone --depth 1 "
            + package_url
            + " "
            + package_name
            + " -q -b "
            + branch
        )

    elif commit:
        os.system("git clone " + package_url + " " + package_name + " -q")
        os.system(f"cd {package_name}; git reset --hard {commit}")

    else:
        os.system("git clone --depth 1 " + package_url + " " + package_name + " -q")


def delete_package(
    paths: Paths,
    package_name: str,
    package: Package | None = None,
    commit: str | None = None,
    branch: str | None = None,
) -> None:
    """Deletes the package."""

    remove_package_source(paths, package_name)

    if package:
        remove_package_binary_symlink(
            paths, package_name, package, branch=branch, commit=commit
        )

    else:
        remove_package_binary_symlink(paths, package_name, branch=branch, commit=commit)

    remove_package_files(paths, package_name)


def remove_package_source(paths: Paths, package_name: str) -> None:
    """Deletes the source code of a package."""

    if (paths.source / package_name).exists():
        shutil.rmtree(paths.source / package_name, ignore_errors=True)


def remove_package_binary_symlink(
    paths: Paths,
    package_name: str,
    package: Package | None = None,
    commit: str | None = None,
    branch: str | None = None,
) -> None:
    """Deletes the symlink for a package."""

    log.debug("Removing symlink for:", package_name)

    if package is None:
        package = get_package_metadata(paths, package_name, commit, branch)

    if package.binname:
        package_bin_dir = paths.binaries / package.binname

        if package_bin_dir.exists():
            log.debug("Deleting", package_bin_dir)
            os.remove(package_bin_dir)


def remove_package_files(paths: Paths, package_name: str) -> None:
    """Remove's a package's installed files."""

    if (package_files_dir := paths.files / package_name).exists():
        shutil.rmtree(package_files_dir, ignore_errors=True)


def symlink_binary_for_package(
    paths: Paths, package_name: str, bin_file: str, bin_name: Path
) -> None:
    """Symlinks a binary for the package."""

    try:
        shutil.copyfile(
            paths.source / package_name / bin_file,
            paths.files / package_name / bin_name,
        )

    except shutil.Error:
        log.warn(f"Failed to copy binary to {paths.files}")

    if (paths.binaries / bin_name).exists():
        os.remove(paths.binaries / bin_name)

    os.symlink(paths.files / package_name / bin_file, paths.binaries / bin_name)

    (paths.files / package_name / bin_name).chmod(0o755)


def copy_package_files_to_files_dir(
    paths: Paths, package_name: str, files: list[str] | None = None
) -> None:
    """Copies a package's files from its source directory to its files directory."""

    if files in (["all"], None):
        files = os.listdir(paths.source / package_name)

    log.debug("Copying files", str(files), "from src to files for", package_name)

    for file in files:
        copy_file(
            paths.source / package_name / file,
            paths.files / package_name / file,
        )


def get_installed_apt_packages() -> list[str]:
    """Returns a list of the installed apt packages"""

    aptinstalled = []

    dpkg_output = subprocess.check_output("dpkg -l".split()).decode()  # nosec B603

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
    paths: Paths,
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
        if not (paths.files / dep.lower()).exists() or flags.update:
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


def install_requirements_dot_txt(package_name: str, paths: Paths) -> None:
    """Installs a package's pip depdencies as specified in `requirements.txt`."""

    log.debug(paths.source / package_name / "requirements.txt")
    log.debug(os.curdir)

    if (paths.source / package_name / "requirements.txt").exists():
        log.note("Requirements.txt found, installing.....")

        on_gentoo = os.path.exists("/etc/portage")
        user_flag = " --user" if on_gentoo else ""

        req_txt = paths.source / package_name / "requirements.txt"

        os.system(
            log.debug(
                f"python3 -m pip --disable-pip-version-check -q install{user_flag} -r {req_txt}"
            )
        )


def install_package_dependencies(
    flags: kazparse.flags.Flags, paths: Paths, args: list[str]
) -> None:
    """Installs a package's dependencies."""

    package = get_package_metadata(paths, args[0])

    if package.deps:
        log.note("Found dependencies, installing.....")
        dependencies = package.deps

        if os.path.exists("/usr/bin/apt") and not os.path.exists(
            "/usr/libexec/eselect-java/run-java-tool.bash"
        ):
            install_apt_dependencies(dependencies)
            install_apt_build_dep_dependencies(dependencies)

        install_avalon_dependencies(flags, paths, args, dependencies)
        install_pip_dependencies(dependencies)

    install_requirements_dot_txt(args[0], paths)
    # TODO: install_poetry_dependencies


def run_script(script_file: Path, *args: str | Path) -> int:
    """Runs a script with its specific interpreter based on the extension."""

    langs = {".py": "python3", ".sh": "bash"}

    if os.path.exists("/etc/portage"):
        with open(script_file, "r", encoding="utf-8") as script:
            contents = script.read()

            with open(script_file, "w", encoding="utf-8") as script_write:
                script_write.write(
                    contents.replace("pip3 install", "pip3 install --user").replace(
                        "pip install", "pip install --user"
                    )
                )

    joined_args = " ".join([str(arg) for arg in args])

    if script_file.suffix.lower() in langs:
        return os.system(
            log.debug(
                f"{langs[script_file.suffix.lower()]} {script_file} {joined_args}"
            )
        )

    return os.system(log.debug(f'{langs[".sh"]} {script_file} {joined_args}'))


def compile_package(
    package_name: str,
    paths: Paths,
    _flags: kazparse.flags.Flags,
) -> None:
    """Compiles a package."""

    package = get_package_metadata(paths, package_name)
    os.chdir(paths.source / package_name)

    (paths.files / package_name).mkdir(parents=True, exist_ok=True)

    if package.needsCompiled:
        if not package.binname:
            log.warn(
                "Package needs compiled but there is no binname for Avalon to install, \
                assuming installed by compile script....."
            )

        if package.compileScript:
            log.note("Compile script found, compiling.....")

            if run_script(
                paths.source / package_name / package.compileScript,
                f'"{paths.source / package_name}" "{package.binname}" \
                "{paths.files / package_name}"',
            ):
                fatal_error("Compile script failed!")

        else:
            fatal_error(
                "Program needs compiling but no compilation script found... exiting....."
            )

    else:
        log.warn("Program does not need to be compiled, moving to installation.....")

    if package.binname and not package.mvBinAfterInstallScript:
        remove_package_binary_symlink(paths, package_name)

        symlink_binary_for_package(
            paths,
            package_name,
            package.binfile or package.binname,
            Path(package.binname),
        )

    if package.installScript:
        log.note("Installing.....")

        if (package.needsCompiled or package.compileScript) and package.binname:
            if run_script(
                paths.source / package_name / package.installScript,
                f'"{paths.files / package_name / package.binname}" \
                "{paths.files / package_name}" \
                "{paths.binaries}" "{paths.source}"',
            ):
                fatal_error("Install script failed!")

        else:
            if run_script(
                paths.source / package_name / package.installScript,
                f'"{paths.files / package_name}" "{paths.source}" "{package_name}"',
            ):
                fatal_error("Install script failed!")

    if package.toCopy:
        log.note("Copying files needed by program.....")
        copy_package_files_to_files_dir(paths, package_name, package.toCopy)

    if package.mvBinAfterInstallScript and package.binname:
        remove_package_binary_symlink(paths, package_name)

        symlink_binary_for_package(
            paths,
            package_name,
            package.binfile or package.binname,
            Path(package.binname),
        )

    else:
        log.warn(
            "No installation script found... Assuming \
            installation beyond APM's autoinstaller isn't neccessary"
        )


def install_package_from_directory(
    flags: kazparse.flags.Flags, paths: Paths, args: list[str]
) -> None:
    """Installs a package from a local directory."""

    tmppath = paths.temp
    package_dir = args[0]

    shutil.rmtree(tmppath)

    if not os.path.exists(tmppath):
        os.mkdir(tmppath)

    log.IS_DEBUG = flags.debug

    log.note("Unpacking package.....")

    if not os.path.exists(package_dir):
        fatal_error(f"{package_dir} does not exist")

    elif os.path.isdir(package_dir):
        if os.system(log.debug(f"cp -r {package_dir}/./ {tmppath}")):
            fatal_error("Failed to copy files")

    else:
        if os.system(log.debug(f"tar -xf {package_dir} -C {tmppath}")):
            fatal_error("Error unpacking package, not a tar.gz file")

    with (tmppath / ".avalon/package").open("r", encoding="utf-8") as package_file:
        cfgfile = json.load(package_file)

    try:
        package_name = args[0] = (cfgfile["author"] + "/" + cfgfile["repo"]).lower()

    except KeyError:
        fatal_error("Package's package file need 'author' and 'repo'")

    log.note("Deleting old binaries and source files.....")
    delete_package(paths, package_name, cfgfile)

    log.note("Copying package files....")

    if os.system(log.debug(f"mkdir -p {paths.source / package_name}")):
        fatal_error("Failed to make src folder")

    if os.system(log.debug(f"cp -a {tmppath}/. {paths.source / package_name}")):
        fatal_error("Failed to copy files from temp folder to src folder")

    shutil.rmtree(tmppath)

    (
        satisfied,
        constraint,
        unsupported,
    ) = check_for_satisfied_package_requirements(paths, package_name, flags.force)

    if not satisfied:
        fatal_error(f'{constraint} "{unsupported}" is not supported by {package_name}.')

    install_package_dependencies(flags, paths, args)

    if not flags.noinstall:
        log.note("Beginning compilation/installation.....")
        compile_package(package_name, paths, flags)
        log.success("Done!")

    else:
        log.warn("-ni specified, skipping installation/compilation")


def install_package(flags: kazparse.flags.Flags, paths: Paths, args: list[str]) -> None:
    """Installs a package."""

    if os.path.exists(args[0]):
        install_package_from_directory(flags, paths, args)
        return

    package_name = args[0].lower()

    if os.path.exists(f"{paths.source / package_name}") and not flags.fresh:
        update_package(flags, paths, *args)
        return

    log.IS_DEBUG = flags.debug

    download_metadata_repository(paths)

    if ":" in package_name:  # commit
        branch = None
        commit = package_name.split(":")[-1]
        package_name = package_name.split(":")[0]

    elif package_name.count("/") > 1:  # branch
        branch = package_name.split("/")[-1]
        package_name = "/".join(package_name.split(":")[:-1])
        commit = None

    elif (":" in package_name) and (package_name.count("/") > 1):  # branch and commit
        commit = package_name.split(":")[-1]
        package_name = package_name.split(":")[0]
        branch = package_name.split("/")[-1]
        package_name = "/".join(package_name.split(":")[:-1])

    else:  # no branch or commit specified
        branch = None
        commit = None

    args[0] = package_name

    log.note("Deleting old binaries and source files.....")
    delete_package(paths, package_name, branch=branch, commit=commit)
    log.note("Downloading from github.....")
    log.debug("Downloading https://github.com/" + package_name, "to", paths.source)
    download_package(
        paths,
        "https://github.com/" + package_name,
        package_name,
        branch=branch,
        commit=commit,
    )

    if is_in_metadata_repository(package_name, paths) and not is_avalon_package(
        paths, package_name
    ):
        log.note(
            "Package is not an Avalon package, but it is \
            in the main repository... installing from there....."
        )
        move_metadata_to_dot_avalon_folder(package_name, paths)

    else:
        log.debug("Not in the main repo")

    (
        satisfied,
        constraint,
        unsupported,
    ) = check_for_satisfied_package_requirements(paths, package_name, flags.force)

    if not satisfied:
        fatal_error(f'{constraint} "{unsupported}" is not supported by {package_name}.')

    install_package_dependencies(flags, paths, args)

    if not flags.noinstall:
        log.note("Beginning compilation/installation.....")
        compile_package(package_name, paths, flags)
        log.success("Done!")

    else:
        log.warn("--noinstall specified, skipping installation/compilation")


def update_package(flags: kazparse.flags.Flags, paths: Paths, *args_: str) -> None:
    "Update to newest version of a repo, then recompile + reinstall program"

    args: list[str] = list(args_)

    if len(args) == 0:
        args.append("r2boyo25/avalonpackagemanager")

    download_metadata_repository(paths)

    log.IS_DEBUG = flags.debug

    package_name = args[0] = args[0].lower()

    log.note("Pulling from github.....")

    if os.system(f"cd {paths.source / package_name}; git pull"):
        if os.system(f"cd {paths.source / package_name}; git reset --hard; git pull"):
            fatal_error("Git error")

    if is_in_metadata_repository(package_name, paths):
        log.note(
            "Package is not an Avalon package, but it is in \
            the main repository... installing from there....."
        )
        move_metadata_to_dot_avalon_folder(package_name, paths)

    else:
        log.debug("Not in the main repo")

    (
        satisfied,
        constraint,
        unsupported,
    ) = check_for_satisfied_package_requirements(paths, package_name, flags.force)

    if not satisfied:
        fatal_error(f'{constraint} "{unsupported}" is not supported by {package_name}.')

    install_package_dependencies(flags, paths, args)

    if not flags.noinstall:
        log.note("Beginning compilation/installation.....")
        compile_package(package_name, paths, flags)
        log.success("Done!")

    else:
        log.warn("-ni specified, skipping installation/compilation")


def redo_symlinks_for_package(
    flags: kazparse.flags.Flags, paths: Paths, *args_: str
) -> None:
    "Redo making of symlinks without recompiling program"
    args: list[str] = list(args_)

    log.IS_DEBUG = flags.debug

    package_name = args[0].lower()
    package = get_package_metadata(paths, package_name)

    if not package.binname:
        log.fatal_error(
            "Cannot remake symlinks due to the lack of a `binname` field in the package metadata."
        )

    log.debug(package_name, paths.binaries, paths.source, str(package))
    remove_package_binary_symlink(paths, package_name, package=package)

    symlink_binary_for_package(
        paths,
        package_name,
        package.binfile or package.binname,
        Path(package.binname),
    )


def uninstall_package(
    flags: kazparse.flags.Flags, paths: Paths, args: list[str]
) -> None:
    """Uninstalls a package."""

    log.IS_DEBUG = flags.debug

    package_name = args[0] = args[0].lower()

    download_metadata_repository(paths)

    if is_in_metadata_repository(package_name, paths) and not is_avalon_package(
        paths, package_name
    ):
        log.note(
            "Package is not an Avalon package, but it is in \
            the main repository... uninstalling from there....."
        )
        move_metadata_to_dot_avalon_folder(package_name, paths)

    (
        satisfied,
        constraint,
        unsupported,
    ) = check_for_satisfied_package_requirements(paths, package_name, flags.force)

    if not satisfied:
        fatal_error(f'{constraint} "{unsupported}" is not supported by {package_name}.')

    package = get_package_metadata(paths, package_name)
    log.note("Uninstalling.....")

    if not package.uninstallScript:
        log.warn(
            "Uninstall script not found... Assuming uninstall not required and deleting files....."
        )
        delete_package(paths, package_name)

    else:
        log.note("Uninstall script found, running.....")
        os.chdir(paths.binaries)

        if not package.binname:
            log.fatal_error(
                "Cannot uninstall package that lacks `binname` field in metadata."
            )

        if run_script(
            paths.source / package_name / package.uninstallScript,
            paths.source,
            paths.binaries,
            package_name,
            package.binname,
            paths.files / package_name,
        ):
            log.error("Uninstall script failed! Deleting files anyways.....")

        delete_package(paths, package_name)

    log.success("Successfully uninstalled package!")


def download_package_source(
    _flags: kazparse.flags.Flags, _paths: Paths, *args: str
) -> None:
    "Download repo into folder"

    package_name = args[0].lower()
    out_dir = args[1]

    if len(args) == 1:
        os.system(f"git clone https://github.com/{package_name}")

    elif len(args) == 2:
        os.system(f"git clone https://github.com/{package_name} {out_dir}")

    else:
        os.system("git pull")  # nosec: B607, B605
