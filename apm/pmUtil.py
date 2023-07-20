#!/usr/bin/python3

import requests
import os
import shutil
import json
import getpass
import platform
import distro
import filecmp
import subprocess

import kazparse
from typing import Any
from pathlib import Path

import apm.log as log
from .package import NPackage
from .case.case import getCaseInsensitivePath


class e404(Exception):
    pass


def error(*text: str) -> None:
    log.error(*text)
    quit()


def copyFile(src: Path, dst: Path) -> None:
    "Copy a file only if files are not the same or the destination does not exist"
    if not os.path.dirname(dst).strip() == "":
        os.makedirs(os.path.dirname(dst), exist_ok=True)

    if os.path.isfile(src):
        if not os.path.exists(dst) or not filecmp.cmp(src, dst):
            shutil.copy2(src, dst)
    else:
        if os.path.exists(src):
            for file in os.listdir(src):
                copyFile(src / file, dst / file)


def getRepos(user: str, cache: bool = True) -> Any:
    if cache:
        pass

    else:
        pass

    r = requests.request(
        "GET", "https://api.github.com/users/" + user + "/repos"
    ).json()

    return r


def getInstalledRepos(paths: dict[str, Path]) -> list[str]:
    "Get all installed programs"
    programs = []

    for user in os.listdir(paths["files"]):
        for repo in os.listdir(paths["files"] / user):
            programs.append(f"{user}/{repo}")

    return programs


def getVersion(paths: dict[str, Path], repo: str) -> str | bool:
    "Get version of package"

    pkg = getCachedPackageRepoInfo(paths, repo)

    if pkg:
        if "version" in pkg:
            return str(pkg["version"])

        else:
            return False

    else:
        return False


def getInstalled(paths: dict[str, Path]) -> list[str]:
    "Get all installed programs with versions"
    programs = []

    for repo in getInstalledRepos(paths):
        v = getVersion(paths, repo)

        if v:
            programs.append(f"{repo}=={v}")

        else:
            programs.append(repo)

    return programs


def getCachedPackageMainRepoInfo(paths: dict[str, Path], pkgname: str) -> Any:
    if Path(getCaseInsensitivePath(str(paths["cache"] / pkgname / "package"))).exists():
        with Path(
            getCaseInsensitivePath(str(paths["cache"] / pkgname / "package"))
        ).open("r") as pkgfile:
            try:
                return json.loads(pkgfile.read())

            except Exception as e:
                log.debug(pkgfile.read())
                raise e

    else:
        return False


def getCachedPackageRepoInfo(paths: dict[str, Path], pkgname: str) -> Any:
    if (paths["src"] / pkgname / ".avalon/package").exists():
        with (paths["src"] / pkgname / ".avalon/package").open("r") as pkgfile:
            try:
                return json.loads(pkgfile.read())

            except Exception as e:
                log.debug("Content: " + pkgfile.read())
                raise e

    else:
        return False


def getCachedPackageInfo(paths: dict[str, Path], pkgname: str) -> Any:
    if getCachedPackageMainRepoInfo(paths, pkgname):
        return getCachedPackageMainRepoInfo(paths, pkgname)

    elif a := getCachedPackageRepoInfo(paths, pkgname):
        return a

    log.debug(f"{pkgname} is not cached")
    return False


def getRepoPackageInfo(
    pkgname: str, commit: str | None = None, branch: str | None = None
) -> Any:
    if not branch and not commit:
        r = requests.get(
            log.debug(
                f"https://raw.githubusercontent.com/{pkgname}/master/.avalon/package"
            )
        )

        log.debug(r.text)

        if r.status_code == 404:
            r = requests.get(
                log.debug(
                    f"https://raw.githubusercontent.com/{pkgname}/main/.avalon/package"
                )
            )
            log.debug(r.text)

            if r.status_code == 404:
                raise e404("Repo")

            return r.json()

        return r.json()

    else:
        if branch:
            r = requests.get(
                log.debug(
                    f"https://raw.githubusercontent.com/{pkgname}/{branch}/.avalon/package"
                )
            )
            log.debug(r.text)

            if r.status_code == 404:
                raise e404("Branch")

            return r.json()

        elif commit:
            r = requests.get(
                log.debug(
                    f"https://raw.githubusercontent.com/{pkgname}/{commit}/.avalon/package"
                )
            )
            log.debug(r.text)

            if r.status_code == 404:
                raise e404("Branch")

            return r.json()


def getMainRepoPackageInfo(pkgname: str) -> Any:
    r = requests.get(
        log.debug(
            f"https://raw.githubusercontent.com/R2Boyo25/AvalonPMPackages/master/{pkgname}/package"
        )
    )
    log.debug(r.text)

    if r.status_code == 404:
        raise e404("Main")

    return r.json()


def getPackageInfo(
    paths: dict[str, Path],
    pkgname: str,
    commit: str | None = None,
    branch: str | None = None,
) -> NPackage:
    log.debug("Getting package info for:", pkgname)

    if getCachedPackageInfo(paths, pkgname):
        return NPackage(getCachedPackageInfo(paths, pkgname))

    else:
        try:  # TODO: WHY WOULD YOU USE EXCEPTIONS, PAST ME?
            return NPackage(getRepoPackageInfo(pkgname, commit=commit, branch=branch))

        except:
            return NPackage(getMainRepoPackageInfo(pkgname))


def isInMainRepo(pkgname: str, paths: dict[str, Path]) -> bool:
    if getCachedPackageMainRepoInfo(paths, pkgname):
        log.debug("Found in main repo cache")
        return True

    log.debug("Not found in main repo cache")
    return False


def downloadMainRepo(paths: dict[str, Path]) -> None:
    if (paths["cache"] / "R2Boyo25").exists():
        os.system(log.debug(f"cd {paths['cache']}; git pull"))

    else:
        cachedir = paths["cache"]
        os.system(
            log.debug(
                f'git clone --depth 1 https://github.com/r2boyo25/AvalonPMPackages "{cachedir}" -q'
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

    if isInMainRepo(pkgname, paths):
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
    return bool(getCachedPackageRepoInfo(paths, pkgname))


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
    pkg = getPackageInfo(paths, pkgname)

    if force:
        if not archIsSupported(pkg):
            log.warn(
                f"Arch {getArch()} not supported by package, continuing anyway due to forced mode"
            )

        if not distroIsSupported(pkg):
            log.warn(
                f"Distro {getDistro()} not supported by package, continuing anyway due to forced mode"
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
        pkg = getPackageInfo(paths, packagename, commit, branch)

    if "binname" in pkg.keys():
        log.debug(str(paths["bin"] / str(pkg["binname"])))

        if (paths["bin"] / str(pkg["binname"])).exists():
            log.debug("Deleting", str(paths["bin"] / str(pkg["binname"])))
            os.remove(paths["bin"] / str(pkg["binname"]))


def rmFromFiles(paths: dict[str, Path], packagename: str) -> None:
    if (paths["files"] / packagename).exists():
        shutil.rmtree(paths["files"] / packagename, ignore_errors=True)


def mvBinToBin(
    paths: dict[str, Path], packagename: str, binFile: str, binName: Path
) -> None:
    try:
        shutil.copyfile(
            paths["src"] / packagename / binFile, paths["files"] / packagename / binName
        )

    except:
        pass

    if (paths["bin"] / binName).exists():
        os.remove(paths["bin"] / binName)

    os.symlink(paths["files"] / packagename / binFile, paths["bin"] / binName)

    (paths["files"] / packagename / binName).chmod(0o755)


def copyFilesToFiles(
    paths: dict[str, Path], pkgname: str, files: list[str] = ["all"]
) -> None:
    log.debug("Copying files", str(files), "from src to files for", pkgname)

    if files != ["all"]:
        for file in files:
            copyFile(
                paths["src"] / pkgname / file,
                paths["files"] / pkgname / file,
            )

    else:
        for file in os.listdir(paths["src"] / pkgname):
            copyFile(
                paths["src"] / pkgname / file,
                paths["files"] / pkgname / file,
            )


def getAptInstalled() -> list[str]:
    aptinstalled = []
    o = subprocess.check_output("dpkg -l".split()).decode()
    for i in o.split("\n"):
        if i.strip() != "" and i.startswith("ii"):
            try:
                i = i.split("  ")[1]

                if i.strip() not in aptinstalled:
                    aptinstalled.append(i.strip())

            except:
                error(i)

    return aptinstalled


def aptFilter(deps: list[str]) -> list[str]:
    """Filter out installed packages"""
    aptinstalled = getAptInstalled()

    return list(filter(lambda dep: dep not in aptinstalled, deps))


def installAptDeps(deps: dict[str, list[str]]) -> None:
    try:
        deps["apt"]

    except:
        return

    if deps["apt"]:
        filtered_deps = aptFilter(deps["apt"])

        if len(filtered_deps) > 0:
            log.note(
                "Found apt dependencies, installing..... (this will require your password)"
            )

            depss = " ".join(filtered_deps)
            username = getpass.getuser()

            if username != "root" and not username.startswith("u0_a"):
                os.system(log.debug(f"sudo apt install -y {depss}"))

            else:
                os.system(log.debug(f"apt install -y {depss}"))


def installBuildDepDeps(deps: dict[str, list[str]]) -> None:
    try:
        deps["build-dep"]

    except:
        return

    if deps["build-dep"]:
        log.note(
            "Found build-dep (apt) dependencies, installing..... (this will require your password)"
        )

        depss = " ".join(deps["build-dep"])
        username = getpass.getuser()

        if username != "root" and not username.startswith("u0_a"):
            if os.system(log.debug(f"sudo apt build-dep -y {depss}")):
                error("apt error")

        else:
            if os.system(log.debug(f"apt build-dep -y {depss}")):
                error("apt error")


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
                log.silent()
                args[0] = dep
                installPackage(flags, paths, args)
                log.silent()
                log.note("Installed", dep)


def installPipDeps(deps: dict[str, list[str]]) -> None:
    try:
        deps["pip"]

    except:
        return

    log.note("Found pip dependencies, installing.....")
    depss = " ".join(deps["pip"])
    os.system(
        log.debug(
            f"python3 -m pip install{' --user' if os.path.exists('/etc/portage') else ''} {depss}"
        )
    )


def reqTxt(pkgname: str, paths: dict[str, Path]) -> None:
    log.debug(str(paths["src"] / pkgname / "requirements.txt"))
    log.debug(os.curdir)

    if (paths["src"] / pkgname / "requirements.txt").exists():
        log.note("Requirements.txt found, installing.....")
        os.system(
            log.debug(
                f"python3 -m pip --disable-pip-version-check -q install{' --user' if os.path.exists('/etc/portage') else ''} -r {paths['src']}/{pkgname}/requirements.txt"
            )
        )


def installDeps(
    flags: kazparse.flags.Flags, paths: dict[str, Path], args: list[str]
) -> None:
    pkg = getPackageInfo(paths, args[0])

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
    pkg = getPackageInfo(paths, packagename)
    os.chdir(paths["src"] / packagename)

    (paths["files"] / packagename).mkdir(parents=True, exist_ok=True)

    if pkg["needsCompiled"]:
        if not pkg["binname"]:
            log.warn(
                "Package needs compiled but there is no binname for Avalon to install, assuming installed by compile script....."
            )

        if pkg["compileScript"]:
            log.note("Compile script found, compiling.....")

            if runScript(
                paths["src"] / packagename / pkg["compileScript"],
                f"\"{paths['src'] / packagename}\" \"{pkg['binname']}\" \"{paths['files'] / packagename}\"",
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
                f"\"{paths['files'] / packagename / str(pkg['binname'])}\" \"{paths['files'] / packagename}\" \"{paths['bin']}\" \"{paths['src']}\"",
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
            "No installation script found... Assuming installation beyond APM's autoinstaller isn't neccessary"
        )


def installLocalPackage(
    flags: kazparse.flags.Flags, paths: dict[str, Path], args: list[str]
) -> None:
    tmppath = paths["tmp"]

    shutil.rmtree(tmppath)

    if not os.path.exists(tmppath):
        os.mkdir(tmppath)

    log.isDebug = flags.debug

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

    log.isDebug = flags.debug

    args[0] = args[0].lower()

    if not os.path.exists(f"{paths['cache']}/R2Boyo25"):
        downloadMainRepo(paths)

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

    if isInMainRepo(packagename, paths) and not isAvalonPackage(paths, packagename):
        log.note(
            "Package is not an Avalon package, but it is in the main repository... installing from there....."
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

    if not os.path.exists(f"{paths['cache']}/R2Boyo25"):
        downloadMainRepo(paths)

    log.isDebug = flags.debug

    args[0] = args[0].lower()

    log.note("Pulling from github.....")

    if os.system(f"cd {paths['src'] / args[0]}; git pull"):
        if os.system(f"cd {paths['src'] / args[0]}; git reset --hard; git pull"):
            error("Git error")

    if isInMainRepo(args[0], paths):
        log.note(
            "Package is not an Avalon package, but it is in the main repository... installing from there....."
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
    args: list[str] = list(args)

    log.isDebug = flags.debug

    args[0] = args[0].lower()

    packagename = args[0]
    pkg: NPackage = getPackageInfo(paths, packagename)
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
    log.isDebug = flags.debug

    args[0] = args[0].lower()

    if not (paths["cache"] / "R2Boyo25").exists():
        downloadMainRepo(paths)

    if isInMainRepo(args[0], paths) and not isAvalonPackage(paths, args[0]):
        log.note(
            "Package is not an Avalon package, but it is in the main repository... uninstalling from there....."
        )
        moveMainRepoToAvalonFolder(args[0], paths)

    checkReqs(paths, args[0], flags.force)

    pkg = getPackageInfo(paths, args[0])
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

    log.isDebug = flags.debug

    print("\n".join(getInstalled(paths)).title())


def dlSrc(flags: kazparse.flags.Flags, paths: dict[str, Path], *args: str) -> None:
    "Download repo into folder"

    if len(args) == 1:
        os.system(f"git clone https://github.com/{args[0].lower()}")

    elif len(args) == 2:
        os.system(f"git clone https://github.com/{args[0].lower()} {args[1]}")

    else:
        os.system("git pull")


def updateCache(
    flags: kazparse.flags.Flags, paths: dict[str, Path], *args: str
) -> None:
    "Update cache"

    downloadMainRepo(paths)
