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

import CLIParse # type: ignore
from typing import Any

import apm.log as log
from .package import NPackage
from .case.case import getCaseInsensitivePath


class e404(Exception):
    pass


def error(*text: str) -> None:
    log.error(*text)
    quit()


def copyFile(src: str, dst: str) -> None:
    "Copy a file only if files are not the same or the destination does not exist"
    if not os.path.dirname(dst).strip() == "":
        os.makedirs(os.path.dirname(dst), exist_ok=True)

    if os.path.isfile(src):
        if not os.path.exists(dst) or not filecmp.cmp(src, dst):
            shutil.copy2(src, dst)
    else:
        if os.path.exists(src):
            for file in os.listdir(src):
                copyFile(src + "/" + file, dst + "/" + file)


def getRepos(user: str, cache: bool =True) -> Any:
    if cache:
        pass
    
    else:
        pass

    r = requests.request(
        "GET", "https://api.github.com/users/" + user + "/repos"
    ).json()

    return r


def getInstalledRepos(paths: list[str]) -> list[str]:
    "Get all installed programs"
    programs = []

    for user in os.listdir(paths[0]):
        for repo in os.listdir(paths[0] + "/" + user):
            programs.append(f"{user}/{repo}")

    return programs


def getVersion(paths: list[str], repo: str) -> str | bool:
    "Get version of package"

    pkg = getCachedPackageRepoInfo(paths[2], paths[0], repo)

    if pkg:
        if "version" in pkg:
            return str(pkg["version"])
        
        else:
            return False
        
    else:
        return False


def getInstalled(paths: list[str]) -> list[str]:
    "Get all installed programs with versions"
    programs = []

    for repo in getInstalledRepos(paths):
        v = getVersion(paths, repo)
        
        if v:
            programs.append(f"{repo}=={v}")
            
        else:
            programs.append(repo)

    return programs


def getCachedPackageMainRepoInfo(cacheFolder: str, srcFolder: str, pkgname: str) -> Any:
    if os.path.exists(getCaseInsensitivePath(f"{cacheFolder}/{pkgname}/package")):
        with open(
            getCaseInsensitivePath(f"{cacheFolder}/{pkgname}/package"), "r"
        ) as pkgfile:
            try:
                return json.loads(pkgfile.read())
            
            except Exception as e:
                log.debug(pkgfile.read())
                raise e
            
    else:
        return False


def getCachedPackageRepoInfo(cacheFolder: str, srcFolder: str, pkgname: str) -> Any:
    if os.path.exists(f"{srcFolder}/{pkgname}/.avalon/package"):
        with open(f"{srcFolder}/{pkgname}/.avalon/package", "r") as pkgfile:
            try:
                return json.loads(pkgfile.read())
            
            except Exception as e:
                log.debug("Content: " + pkgfile.read())
                raise e
            
    else:
        return False


def getCachedPackageInfo(cacheFolder: str, srcFolder: str, pkgname: str) -> Any:
    if getCachedPackageMainRepoInfo(cacheFolder, srcFolder, pkgname):
        return getCachedPackageMainRepoInfo(cacheFolder, srcFolder, pkgname)
    
    elif getCachedPackageRepoInfo(cacheFolder, srcFolder, pkgname):
        return getCachedPackageRepoInfo(cacheFolder, srcFolder, pkgname)
    
    else:
        log.debug("Not cached")
        return False


def getRepoPackageInfo(pkgname: str, commit: str | None = None, branch: str | None = None) -> Any:
    if not branch and not commit:
        r = requests.get(
            f"https://raw.githubusercontent.com/{pkgname}/master/.avalon/package"
        )
        log.debug(
            f"https://raw.githubusercontent.com/{pkgname}/master/.avalon/package"
        )
        log.debug(r.text)

        if r.status_code == 404:
            r = requests.get(
                f"https://raw.githubusercontent.com/{pkgname}/main/.avalon/package"
            )
            log.debug(
                f"https://raw.githubusercontent.com/{pkgname}/main/.avalon/package"
            )
            log.debug(r.text)

            if r.status_code == 404:
                raise e404("Repo")

            return r.json()

        return r.json()

    else:
        if branch:
            r = requests.get(
                f"https://raw.githubusercontent.com/{pkgname}/{branch}/.avalon/package"
            )
            log.debug(
                f"https://raw.githubusercontent.com/{pkgname}/{branch}/.avalon/package"
            )
            log.debug(r.text)

            if r.status_code == 404:
                raise e404("Branch")

            return r.json()

        elif commit:
            r = requests.get(
                f"https://raw.githubusercontent.com/{pkgname}/{commit}/.avalon/package"
            )
            log.debug(
                f"https://raw.githubusercontent.com/{pkgname}/{commit}/.avalon/package"
            )
            log.debug(r.text)

            if r.status_code == 404:
                raise e404("Branch")

            return r.json()


def getMainRepoPackageInfo(pkgname: str) -> Any:
    r = requests.get(
        f"https://raw.githubusercontent.com/R2Boyo25/AvalonPMPackages/master/{pkgname}/package"
    )
    log.debug(
        f"https://raw.githubusercontent.com/R2Boyo25/AvalonPMPackages/master/{pkgname}/package"
    )
    log.debug(r.text)

    if r.status_code == 404:
        raise e404("Main")

    return r.json()


def getPackageInfo(paths: list[str], pkgname: str, commit: str | None = None, branch: str | None = None) -> NPackage:
    log.debug(pkgname)
    log.debug(str(paths))
    
    if getCachedPackageInfo(paths[2], paths[0], pkgname):
        return NPackage(getCachedPackageInfo(paths[2], paths[0], pkgname))
    
    else:
        try:
            return NPackage(getRepoPackageInfo(pkgname, commit=commit, branch=branch))
        
        except:
            return NPackage(getMainRepoPackageInfo(pkgname))


def isInMainRepo(pkgname: str, paths: list[str]) -> bool:
    if getCachedPackageMainRepoInfo(paths[2], paths[0], pkgname):
        log.debug("Found in main repo cache")
        return True
    
    else:
        log.debug("Not found in main repo cache")
        return False


def downloadMainRepo(cacheDir: str) -> None:
    if os.path.exists(f"{cacheDir}/R2Boyo25"):
        log.debug(f"cd {cacheDir}; git pull")
        os.system(f"cd {cacheDir}; git pull")
        
    else:
        log.debug(
            f'git clone --depth 1 https://github.com/r2boyo25/AvalonPMPackages "{cacheDir}" -q'
        )
        os.system(
            f'git clone --depth 1 https://github.com/r2boyo25/AvalonPMPackages "{cacheDir}" -q'
        )


def moveMainRepoToAvalonFolder(cacheFolder: str, pkgname: str, srcFolder: str, paths: list[str]) -> None:
    log.debug(pkgname)
    log.debug("Moving to .avalon folder")
    log.debug(srcFolder + "/" + pkgname + "/.avalon")
    shutil.rmtree(srcFolder + "/" + pkgname + "/.avalon", ignore_errors=True)
    
    if isInMainRepo(pkgname, paths):
        log.debug(
            getCaseInsensitivePath(cacheFolder + "/" + pkgname),
            srcFolder + "/" + pkgname + "/.avalon",
        )
        shutil.copytree(
            getCaseInsensitivePath(cacheFolder + "/" + pkgname),
            srcFolder + "/" + pkgname + "/.avalon",
        )


def isAvalonPackage(repo: str, srcFolder: str, pkgname: str) -> bool:
    return bool(getCachedPackageRepoInfo(repo, srcFolder, pkgname))


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
        log.warn(
            "Supported arches not specified, assuming this arch is supported....."
        )
        return True


def checkReqs(paths: list[str], pkgname: str, force: bool) -> None:
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
        deletePackage(paths[0], paths[1], pkgname, paths)
        error(f"Arch {getArch()} not supported by package")

    if not distroIsSupported(pkg):
        deletePackage(paths[0], paths[1], pkgname, paths)
        error(f"Distro {getDistro()} not supported by package")


def downloadPackage(srcFolder: str, packageUrl: str, packagename: str | None = None, branch: str | None = None, commit: str | None = None) -> None:
    if not packagename:
        packagename = packageUrl.lstrip("https://github.com/")
        
    log.debug(packagename)
    os.chdir(srcFolder)
    
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
    srcFolder: str, binFolder: str, packagename: str, paths: list[str], cfg: Any | None = None, commit: str | None = None, branch: str | None = None
) -> None:
    rmFromSrc(srcFolder, packagename)
    
    if cfg:
        rmFromBin(binFolder, packagename, paths, cfg, branch=branch, commit=commit)
        
    else:
        rmFromBin(binFolder, packagename, paths, branch=branch, commit=commit)
        
    rmFromFiles(paths[4], packagename)


def rmFromSrc(srcFolder: str, packagename: str) -> None:
    if os.path.exists(f"{srcFolder}/{packagename}"):
        shutil.rmtree(f"{srcFolder}/{packagename}", ignore_errors=True)


def rmFromBin(binFolder: str, packagename: str, paths: list[str], pkg: Any | None = None, commit: str | None = None, branch: str | None = None) -> None:
    log.debug("RMBIN:", packagename)
    
    if not pkg:
        pkg = getPackageInfo(paths, packagename, commit, branch)
        
    if "binname" in pkg.keys():
        log.debug(f"{binFolder}/{pkg['binname']}")
        
        if os.path.exists(f"{binFolder}/{pkg['binname']}"):
            log.debug("Deleting", f"{binFolder}/{pkg['binname']}")
            os.remove(f"{binFolder}/{pkg['binname']}")


def rmFromFiles(fileFolder: str, packagename: str) -> None:
    if os.path.exists(f"{fileFolder}/{packagename}"):
        shutil.rmtree(f"{fileFolder}/{packagename}", ignore_errors=True)


def mvBinToBin(binFolder: str, fileFolder: str, srcFolder: str, binFile: str, binName: str) -> None:
    try:
        shutil.copyfile(
            srcFolder + "/" + binFile, fileFolder + "/" + binName.split("/")[-1]
        )
        
    except:
        pass

    if os.path.exists(binFolder + binName.split("/")[-1]) or os.path.lexists(
        binFolder + binName.split("/")[-1]
    ):
        os.remove(binFolder + binName.split("/")[-1])

    b = binName.split("/")[-1]

    os.symlink(fileFolder + "/" + binFile, binFolder + binName.split("/")[-1])

    log.debug(f"chmod +x {fileFolder + '/' + b}")
    os.system(f"chmod +x {fileFolder + '/' + b}")


def copyFilesToFiles(paths: list[str], pkgname: str, files: list[str] = ["all"]) -> None:
    log.debug(str(files))
    
    if files != ["all"]:
        for file in files:
            copyFile(
                paths[0] + "/" + pkgname + "/" + file,
                paths[4] + "/" + pkgname + "/" + file,
            )
            
    else:
        for file in os.listdir(paths[0] + "/" + pkgname + "/"):
            copyFile(
                paths[0] + "/" + pkgname + "/" + file,
                paths[4] + "/" + pkgname + "/" + file,
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
    '''Filter out installed packages'''
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
                log.debug(f"sudo apt install -y {depss}")
                os.system(f"sudo apt install -y {depss}")
                
            else:
                log.debug(f"apt install -y {depss}")
                os.system(f"apt install -y {depss}")


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
            log.debug(f"sudo apt build-dep -y {depss}")
            
            if os.system(f"sudo apt build-dep -y {depss}"):
                error("apt error")
                
        else:
            log.debug(f"apt build-dep -y {depss}")
            
            if os.system(f"apt build-dep -y {depss}"):
                error("apt error")


def installAvalonDeps(flags: CLIParse.flags.Flags, paths: list[str], args: list[str], deps: dict[str, list[str]]) -> None:
    try:
        deps["avalon"]
        
    except:
        return
    
    args = args.copy()
    
    if deps["avalon"]:
        log.note("Found avalon dependencies, installing.....")
        
        for dep in deps["avalon"]:
            if not os.path.exists(paths[0] + dep.lower()) or flags.update:
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
    log.debug(
        f"python3 -m pip install{' --user' if os.path.exists('/etc/portage') else ''} {depss}"
    )
    os.system(
        f"python3 -m  install{' --user' if os.path.exists('/etc/portage') else ''} {depss}"
    )


def reqTxt(pkgname: str, paths: list[str]) -> None:
    log.debug(paths[0] + "/" + pkgname + "/" + "requirements.txt")
    log.debug(os.curdir)
    
    if os.path.exists(paths[0] + "/" + pkgname + "/" + "requirements.txt"):
        log.note("Requirements.txt found, installing.....")
        os.system(
            f"python3 -m pip --disable-pip-version-check -q install{' --user' if os.path.exists('/etc/portage') else ''} -r {paths[0]}/{pkgname}/requirements.txt"
        )


def installDeps(flags: CLIParse.flags.Flags, paths: list[str], args: list[str]) -> None:
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


def runScript(script: str, *args: str) -> int:
    langs = {"py": "python3", "sh": "bash"}

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

    if script.split(".")[-1].lower() in langs:
        log.debug(f"{langs[script.split('.')[-1]]} {script} {argss}")
        return os.system(f"{langs[script.split('.')[-1]]} {script} {argss}")
    
    else:
        log.debug(f'{langs["sh"]} {script} {argss}')
        return os.system(f'{langs["sh"]} {script} {argss}')


def compilePackage(srcFolder: str, binFolder: str, packagename: str, paths: list[str], flags: CLIParse.flags.Flags) -> None:
    pkg = getPackageInfo(paths, packagename)
    os.chdir(f"{srcFolder}/{packagename}")

    os.makedirs(f"{paths[4]}/{packagename}", exist_ok=True)

    if pkg["needsCompiled"]:

        if not pkg["binname"]:

            log.warn(
                "Package needs compiled but there is no binname for Avalon to install, assuming installed by compile script....."
            )

        if pkg["compileScript"]:
            log.note("Compile script found, compiling.....")
            
            if runScript(
                pkg["compileScript"],
                f"\"{srcFolder+f'/{packagename}'}\" \"{pkg['binname']}\" \"{paths[4]+packagename}\"",
            ):
                error("Compile script failed!")

        else:
            error(
                "Program needs compiling but no compilation script found... exiting....."
            )

    else:
        log.warn("Program does not need to be compiled, moving to installation.....")

    if pkg["binname"] and not pkg["mvBinAfterInstallScript"]:
        rmFromBin(binFolder, packagename, paths)

        if pkg["binfile"]:
            mvBinToBin(
                binFolder,
                paths[4] + packagename,
                srcFolder + "/" + packagename + "/",
                pkg["binfile"],
                pkg["binname"],
            )

        else:
            mvBinToBin(
                binFolder,
                paths[4] + packagename,
                srcFolder + "/" + packagename + "/",
                pkg["binname"],
                pkg["binname"],
            )

    if pkg["installScript"]:
        log.note("Installing.....")
        
        if pkg["needsCompiled"] or pkg["compileScript"] or pkg["binname"]:
            if runScript(
                pkg["installScript"],
                f"\"{paths[4]+ '/' + packagename + '/' + str(pkg['binname'])}\" \"{paths[4]+packagename}\" \"{binFolder}\" \"{srcFolder}\"",
            ):
                error("Install script failed!")

        else:
            if runScript(
                pkg["installScript"],
                f"\"{paths[4] + '/' + packagename}\" \"{srcFolder}\" \"{packagename}\"",
            ):
                error("Install script failed!")

    if pkg["toCopy"]:
        log.note("Copying files needed by program.....")
        copyFilesToFiles(paths, packagename, pkg["toCopy"])

    if pkg["mvBinAfterInstallScript"] and pkg["binname"]:
        rmFromBin(binFolder, packagename, paths)

        if pkg["binfile"]:
            mvBinToBin(
                binFolder,
                paths[4] + packagename,
                srcFolder + "/" + packagename + "/",
                pkg["binfile"],
                pkg["binname"],
            )

        else:
            mvBinToBin(
                binFolder,
                paths[4] + packagename,
                srcFolder + "/" + packagename + "/",
                pkg["binname"],
                pkg["binname"],
            )

    else:
        log.warn(
            "No installation script found... Assuming installation beyond APM's autoinstaller isn't neccessary"
        )


def installLocalPackage(flags: CLIParse.flags.Flags, paths: list[str], args: list[str]) -> None:
    tmppath = paths[5]

    shutil.rmtree(tmppath)

    if not os.path.exists(tmppath):
        os.mkdir(tmppath)

    log.isDebug = flags.debug

    log.note("Unpacking package.....")
    
    if not os.path.exists(args[0]):
        error(f"{args[0]} does not exist")
        
    elif os.path.isdir(args[0]):
        log.debug(f"cp -r {args[0]}/./ {tmppath}")
        
        if os.system(f"cp -r {args[0]}/./ {tmppath}"):
            error("Failed to copy files")
            
    else:
        log.debug(f"tar -xf {args[0]} -C {tmppath}")
        
        if os.system(f"tar -xf {args[0]} -C {tmppath}"):
            error("Error unpacking package, not a tar.gz file")

    cfgfile = json.load(open(f"{tmppath}/.avalon/package", "r"))
    
    try:
        args[0] = (cfgfile["author"] + "/" + cfgfile["repo"]).lower()
        
    except:
        error("Package's package file need 'author' and 'repo'")

    log.note("Deleting old binaries and source files.....")
    deletePackage(paths[0], paths[1], args[0], paths, cfgfile)

    log.note("Copying package files....")
    log.debug(f"mkdir -p {paths[0]}/{args[0]}")
    
    if os.system(f"mkdir -p {paths[0]}/{args[0]}"):
        error("Failed to make src folder")
        
    log.debug(f"cp -a {tmppath}/. {paths[0]}/{args[0]}")
    
    if os.system(f"cp -a {tmppath}/. {paths[0]}/{args[0]}"):
        error("Failed to copy files from temp folder to src folder")

    shutil.rmtree(tmppath)

    checkReqs(paths, args[0], flags.force)

    installDeps(flags, paths, args)

    if not flags.noinstall:
        log.note("Beginning compilation/installation.....")
        compilePackage(paths[0], paths[1], args[0], paths, flags)
        log.success("Done!")
        
    else:
        log.warn("-ni specified, skipping installation/compilation")


def installPackage(flags: CLIParse.flags.Flags, paths: list[str], args: list[str]) -> None:
    if os.path.exists(args[0]):
        installLocalPackage(flags, paths, args)
        return

    if os.path.exists(f"{paths[0]}/{args[0].lower()}") and not flags.fresh:
        updatePackage(flags, paths, *args)
        return

    log.isDebug = flags.debug

    args[0] = args[0].lower()

    if not os.path.exists(f"{paths[2]}/R2Boyo25"):
        downloadMainRepo(paths[2])

    packagename = args[0]

    if ":" in packagename: # commit
        branch = None
        commit = packagename.split(":")[-1]
        packagename = packagename.split(":")[0]
        
    elif packagename.count("/") > 1: # branch
        branch = packagename.split("/")[-1]
        packagename = "/".join(packagename.split(":")[:-1])
        commit = None
        
    elif (":" in packagename) and (packagename.count("/") > 1): # branch and commit
        commit = packagename.split(":")[-1]
        packagename = packagename.split(":")[0]
        branch = packagename.split("/")[-1]
        packagename = "/".join(packagename.split(":")[:-1])
        
    else: # no branch or commit specified
        branch = None
        commit = None

    args[0] = packagename

    log.note("Deleting old binaries and source files.....")
    deletePackage(paths[0], paths[1], args[0], paths, branch=branch, commit=commit)
    log.note("Downloading from github.....")
    log.debug(paths[0], "https://github.com/" + args[0], args[0])
    downloadPackage(
        paths[0],
        "https://github.com/" + packagename,
        packagename,
        branch=branch,
        commit=commit,
    )

    if isInMainRepo(packagename, paths) and not isAvalonPackage(
        packagename, paths[0], packagename
    ):
        log.note(
            "Package is not an Avalon package, but it is in the main repository... installing from there....."
        )
        moveMainRepoToAvalonFolder(paths[2], packagename, packagename, paths)
        
    else:
        log.debug("Not in the main repo")

    checkReqs(paths, packagename, flags.force)

    installDeps(flags, paths, args)

    if not flags.noinstall:
        log.note("Beginning compilation/installation.....")
        compilePackage(paths[0], paths[1], packagename, paths, flags)
        log.success("Done!")
        
    else:
        log.warn("-ni specified, skipping installation/compilation")


def updatePackage(flags: CLIParse.flags.Flags, paths: list[str], *args_: str) -> None:
    "Update to newest version of a repo, then recompile + reinstall program"

    args: list[str] = list(args)

    if len(args) == 0:
        args.append("r2boyo25/avalonpackagemanager")

    if not os.path.exists(f"{paths[2]}/R2Boyo25"):
        downloadMainRepo(paths[2])

    log.isDebug = flags.debug

    args[0] = args[0].lower()

    log.note("Pulling from github.....")

    if os.system(f"cd {paths[0]}/{args[0]}; git pull"):
        if os.system(f"cd {paths[0]}/{args[0]}; git reset --hard; git pull"):
            error("Git error")

    if isInMainRepo(args[0], paths):
        log.note(
            "Package is not an Avalon package, but it is in the main repository... installing from there....."
        )
        moveMainRepoToAvalonFolder(paths[2], args[0], paths[0], paths)
        
    else:
        log.debug("Not in the main repo")

    checkReqs(paths, args[0], flags.force)

    installDeps(flags, paths, args)

    if not flags.noinstall:
        log.note("Beginning compilation/installation.....")
        compilePackage(paths[0], paths[1], args[0], paths, flags)
        log.success("Done!")
        
    else:
        log.warn("-ni specified, skipping installation/compilation")


def redoBin(flags: CLIParse.flags.Flags, paths: list[str], *args_: str) -> None:
    "Redo making of symlinks without recompiling program"
    args: list[str] = list(args)

    log.isDebug = flags.debug

    args[0] = args[0].lower()

    packagename = args[0]
    binFolder = paths[1]
    srcFolder = paths[0]
    pkg: NPackage = getPackageInfo(paths, packagename)
    log.debug(packagename, binFolder, srcFolder, str(pkg))
    rmFromBin(binFolder, packagename, paths, pkg=pkg)

    if pkg["binfile"]:
        mvBinToBin(
            binFolder,
            paths[4] + packagename,
            srcFolder + "/" + packagename + "/",
            str(pkg["binfile"]),
            str(pkg["binname"]),
        )

    else:
        mvBinToBin(
            binFolder,
            paths[4] + packagename,
            srcFolder + "/" + packagename + "/",
            str(pkg["binname"]),
            str(pkg["binname"]),
        )


def uninstallPackage(flags: CLIParse.flags.Flags, paths: list[str], args: list[str]) -> None:
    log.isDebug = flags.debug

    args[0] = args[0].lower()

    if not os.path.exists(f"{paths[2]}/R2Boyo25"):
        downloadMainRepo(paths[2])

    if isInMainRepo(args[0], paths) and not isAvalonPackage(args[0], paths[0], args[0]):
        log.note(
            "Package is not an Avalon package, but it is in the main repository... uninstalling from there....."
        )
        moveMainRepoToAvalonFolder(paths[2], args[0], paths[0], paths)

    checkReqs(paths, args[0], flags.force)

    pkg = getPackageInfo(paths, args[0])
    log.note("Uninstalling.....")
    if not pkg["uninstallScript"]:
        log.warn(
            "Uninstall script not found... Assuming uninstall not required and deleting files....."
        )
        deletePackage(paths[0], paths[1], args[0], paths)

    else:
        log.note("Uninstall script found, running.....")
        os.chdir(paths[1])
        
        if runScript(
            paths[0] + "/" + args[0] + "/" + pkg["uninstallScript"],
            paths[0],
            paths[1],
            args[0],
            str(pkg["binname"]),
            paths[4] + args[0],
        ):
            log.error("Uninstall script failed! Deleting files anyways.....")

        deletePackage(paths[0], paths[1], args[0], paths)

    log.success("Successfully uninstalled package!")


def installed(flags: CLIParse.flags.Flags, paths: list[str], *args: str) -> None:
    "List installed packages"

    log.isDebug = flags.debug

    print("\n".join(getInstalled(paths)).title())


def dlSrc(flags: CLIParse.flags.Flags, paths: list[str], *args: str) -> None:
    "Download repo into folder"

    if len(args) == 1:
        os.system(f"git clone https://github.com/{args[0].lower()}")
        
    elif len(args) == 2:
        os.system(f"git clone https://github.com/{args[0].lower()} {args[1]}")
        
    else:
        os.system("git pull")


def updateCache(flags: CLIParse.flags.Flags, paths: list[str], *args: str) -> None:
    "Update cache"

    downloadMainRepo(paths[2])
