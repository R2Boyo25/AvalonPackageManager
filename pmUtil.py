#!/usr/bin/python3

from package import NPackage
import requests
import os
import shutil
import color
import json
import getpass
import platform
import distro
import filecmp
import subprocess

from case.case import getCaseInsensitivePath


class e404(Exception):
    pass


def error(*text):
    color.error(*text)
    quit()


def copyFile(src, dst):
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


def getRepos(user, cache=True):
    if cache:
        pass
    else:
        pass

    r = requests.request(
        "GET", "https://api.github.com/users/"+user+"/repos").json()

    return r


def getInstalledRepos(paths):
    "Gett all installed programs"
    programs = []

    for user in os.listdir(paths[0]):
        for repo in os.listdir(paths[0] + "/" + user):
            programs.append(f"{user}/{repo}")

    return programs


def getVersion(paths, repo):
    "Get version of package"

    pkg = getCachedPackageRepoInfo(paths[2], paths[0], repo)

    if pkg:
        if 'version' in pkg:
            return pkg["version"]
        else:
            return False
    else:
        return False


def getInstalled(paths):
    "Get all installed programs with versions"
    programs = []

    for repo in getInstalledRepos(paths):
        v = getVersion(paths, repo)
        if v:
            programs.append(f"{repo}=={v}")
        else:
            programs.append(repo)

    return programs


def getCachedPackageMainRepoInfo(cacheFolder, srcFolder, pkgname):
    if os.path.exists(getCaseInsensitivePath(f"{cacheFolder}/{pkgname}/package")):
        with open(getCaseInsensitivePath(f"{cacheFolder}/{pkgname}/package"), 'r') as pkgfile:
            try:
                return json.loads(pkgfile.read())
            except Exception as e:
                color.debug(pkgfile.read())
                raise e
    else:
        return False


def getCachedPackageRepoInfo(cacheFolder, srcFolder, pkgname):
    if os.path.exists(f"{srcFolder}/{pkgname}/.avalon/package"):
        with open(f"{srcFolder}/{pkgname}/.avalon/package", 'r') as pkgfile:
            try:
                return json.loads(pkgfile.read())
            except Exception as e:
                color.debug("Content: " + pkgfile.read())
                raise e
    else:
        return False


def getCachedPackageInfo(cacheFolder, srcFolder, pkgname):
    if getCachedPackageMainRepoInfo(cacheFolder, srcFolder, pkgname):
        return getCachedPackageMainRepoInfo(cacheFolder, srcFolder, pkgname)
    elif getCachedPackageRepoInfo(cacheFolder, srcFolder, pkgname):
        return getCachedPackageRepoInfo(cacheFolder, srcFolder, pkgname)
    else:
        color.debug("Not cached")
        return False


def getRepoPackageInfo(pkgname, commit=None, branch=None):
    if not branch and not commit:
        r = requests.get(
            f'https://raw.githubusercontent.com/{pkgname}/master/.avalon/package')
        color.debug(
            f'https://raw.githubusercontent.com/{pkgname}/master/.avalon/package')
        color.debug(r.text)

        if r.status_code == 404:
            r = requests.get(
                f'https://raw.githubusercontent.com/{pkgname}/main/.avalon/package')
            color.debug(
                f'https://raw.githubusercontent.com/{pkgname}/main/.avalon/package')
            color.debug(r.text)

            if r.status_code == 404:
                raise e404("Repo")

            return r.json()

        return r.json()

    else:
        if branch:
            r = requests.get(
                f'https://raw.githubusercontent.com/{pkgname}/{branch}/.avalon/package')
            color.debug(
                f'https://raw.githubusercontent.com/{pkgname}/{branch}/.avalon/package')
            color.debug(r.text)

            if r.status_code == 404:
                raise e404("Branch")

            return r.json()

        elif commit:
            r = requests.get(
                f'https://raw.githubusercontent.com/{pkgname}/{commit}/.avalon/package')
            color.debug(
                f'https://raw.githubusercontent.com/{pkgname}/{commit}/.avalon/package')
            color.debug(r.text)

            if r.status_code == 404:
                raise e404("Branch")

            return r.json()


def getMainRepoPackageInfo(pkgname):
    r = requests.get(
        f'https://raw.githubusercontent.com/R2Boyo25/AvalonPMPackages/master/{pkgname}/package')
    color.debug(
        f'https://raw.githubusercontent.com/R2Boyo25/AvalonPMPackages/master/{pkgname}/package')
    color.debug(r.text)

    if r.status_code == 404:
        raise e404("Main")

    return r.json()


def getPackageInfo(paths, pkgname, commit=None, branch=None):
    color.debug(pkgname)
    color.debug(str(paths))
    if getCachedPackageInfo(paths[2], paths[0], pkgname):
        return NPackage(getCachedPackageInfo(paths[2], paths[0], pkgname))
    else:
        try:
            return NPackage(getRepoPackageInfo(pkgname, commit=commit, branch=branch))
        except:
            return NPackage(getMainRepoPackageInfo(pkgname))


def isInMainRepo(pkgname, paths):
    if getCachedPackageMainRepoInfo(paths[2], paths[0], pkgname):
        color.debug("Found in main repo cache")
        return True
    else:
        color.debug("Not found in main repo cache")
        return False


def downloadMainRepo(cacheDir):
    if os.path.exists(f"{cacheDir}/R2Boyo25"):
        color.debug(f"cd {cacheDir}; git pull")
        os.system(f"cd {cacheDir}; git pull")
    else:
        color.debug(
            f"git clone --depth 1 https://github.com/r2boyo25/AvalonPMPackages \"{cacheDir}\" -q")
        os.system(
            f"git clone --depth 1 https://github.com/r2boyo25/AvalonPMPackages \"{cacheDir}\" -q")


def moveMainRepoToAvalonFolder(cacheFolder, pkgname, srcFolder, paths):
    color.debug(pkgname)
    color.debug("Moving to .avalon folder")
    color.debug(srcFolder + "/" + pkgname + "/.avalon")
    shutil.rmtree(srcFolder + "/" + pkgname + "/.avalon", ignore_errors=True)
    if isInMainRepo(pkgname, paths):
        color.debug(getCaseInsensitivePath(
            cacheFolder + "/" + pkgname), srcFolder + "/" + pkgname + '/.avalon')
        shutil.copytree(getCaseInsensitivePath(
            cacheFolder + "/" + pkgname), srcFolder + "/" + pkgname + '/.avalon')


def isAvalonPackage(repo, srcFolder, pkgname):
    if not getCachedPackageRepoInfo(repo, srcFolder, pkgname):
        return False
    else:
        return True


def getDistro():
    return distro.linux_distribution()[0]


def distroIsSupported(pkg):
    color.debug(getDistro())
    if pkg['distros']:
        return (getDistro() in pkg['distros']) or (pkg['distros'] == ["all"])
    else:
        color.warn(
            "Supported distros not specified, assuming this distro is supported.....")
        return True


def getArch():
    return platform.machine()


def archIsSupported(pkg):
    color.debug(str(pkg))
    color.debug(getArch())
    if pkg['arches']:
        return (getArch() in pkg['arches']) or (pkg['arches'] == ["all"])
    else:
        color.warn(
            "Supported arches not specified, assuming this arch is supported.....")
        return True


def checkReqs(paths, pkgname):
    pkg = getPackageInfo(paths, pkgname)
    if not archIsSupported(pkg):
        deletePackage(paths[0], paths[1], pkgname, paths)
        error(f"Arch {getArch()} not supported by package")
    if not distroIsSupported(pkg):
        deletePackage(paths[0], paths[1], pkgname, paths)
        error(f"Distro {getDistro()} not supported by package")


def downloadPackage(srcFolder, packageUrl, packagename=None, branch=None, commit=None):
    if not packagename:
        packagename = packageUrl.lstrip("https://github.com/")
    color.debug(packagename)
    os.chdir(srcFolder)
    if commit and branch:
        os.system('git clone ' + packageUrl + ' ' + packagename + " -q")
        os.system(f"cd {packagename}; git reset --hard {commit}")
    elif branch:
        packagename = "/".join(packagename.split(":")[:-1])
        os.system('git clone --depth 1 ' + packageUrl +
                  ' ' + packagename + " -q -b " + branch)
    elif commit:
        os.system('git clone ' + packageUrl + ' ' + packagename + " -q")
        os.system(f"cd {packagename}; git reset --hard {commit}")
    else:
        os.system('git clone --depth 1 ' +
                  packageUrl + ' ' + packagename + " -q")


def deletePackage(srcFolder, binFolder, packagename, paths, cfg=None, commit=None, branch=None):
    rmFromSrc(srcFolder, packagename)
    if cfg:
        rmFromBin(binFolder, packagename, paths,
                  cfg, branch=branch, commit=commit)
    else:
        rmFromBin(binFolder, packagename, paths, branch=branch, commit=commit)
    rmFromFiles(paths[4], packagename)


def rmFromSrc(srcFolder, packagename):
    if os.path.exists(f"{srcFolder}/{packagename}"):
        shutil.rmtree(f"{srcFolder}/{packagename}", ignore_errors=True)


def rmFromBin(binFolder, packagename, paths, pkg=None, commit=None, branch=None):
    color.debug("RMBIN:", packagename)
    if not pkg:
        pkg = getPackageInfo(paths, packagename, commit, branch)
    if 'binname' in pkg.keys():
        color.debug(f"{binFolder}/{pkg['binname']}")
        if os.path.exists(f"{binFolder}/{pkg['binname']}"):
            color.debug("Deleting", f"{binFolder}/{pkg['binname']}")
            os.remove(f"{binFolder}/{pkg['binname']}")


def rmFromFiles(fileFolder, packagename):
    if os.path.exists(f"{fileFolder}/{packagename}"):
        shutil.rmtree(f"{fileFolder}/{packagename}", ignore_errors=True)


def mvBinToBin(binFolder, fileFolder, srcFolder, binFile, binName):
    try:
        shutil.copyfile(srcFolder + "/" + binFile,
                        fileFolder+'/'+binName.split('/')[-1])
    except:
        pass

    if os.path.exists(binFolder + binName.split('/')[-1]) or os.path.lexists(binFolder + binName.split('/')[-1]):
        os.remove(binFolder + binName.split('/')[-1])

    b = binName.split('/')[-1]

    os.symlink(fileFolder+'/'+b, binFolder + binName.split('/')[-1])

    color.debug(f"chmod +x {fileFolder + '/' + b}")
    os.system(f"chmod +x {fileFolder + '/' + b}")


def copyFilesToFiles(paths, pkgname, files=['all']):
    color.debug(str(files))
    if files != ['all']:
        for file in files:
            copyFile(paths[0] + '/' + pkgname + '/' + file,
                     paths[4] + '/' + pkgname + '/' + file)
    else:
        for file in os.listdir(paths[0] + '/' + pkgname + '/'):
            copyFile(paths[0] + '/' + pkgname + '/' + file,
                     paths[4] + '/' + pkgname + '/' + file)


def getAptInstalled():
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


def aptFilter(deps):
    aptinstalled = getAptInstalled()

    return list(filter(lambda dep: dep not in aptinstalled, deps))


def installAptDeps(deps):
    try:
        deps['apt']
    except:
        return
    if deps['apt']:
        filtered_deps = aptFilter(deps['apt'])
        if len(filtered_deps) > 0:
            color.note(
                "Found apt dependencies, installing..... (this will require your password)")
            depss = " ".join(filtered_deps)

            username = getpass.getuser()

            if username != 'root' and not username.startswith("u0_a"):
                color.debug(f'sudo apt install -y {depss}')
                os.system(f'sudo apt install -y {depss}')
            else:
                color.debug(f'apt install -y {depss}')
                os.system(f'apt install -y {depss}')


def installBuildDepDeps(deps):
    try:
        deps['build-dep']
    except:
        return
    if deps['build-dep']:
        color.note(
            "Found build-dep (apt) dependencies, installing..... (this will require your password)")
        depss = " ".join(deps['build-dep'])

        username = getpass.getuser()

        if username != 'root' and not username.startswith("u0_a"):
            color.debug(f'sudo apt build-dep -y {depss}')
            if os.system(f'sudo apt build-dep -y {depss}'):
                error("apt error")
        else:
            color.debug(f'apt build-dep -y {depss}')
            if os.system(f'apt build-dep -y {depss}'):
                error("apt error")


def installAvalonDeps(flags, paths, args, deps):
    try:
        deps['avalon']
    except:
        return
    args = args.copy()
    if deps['avalon']:
        color.note("Found avalon dependencies, installing.....")
        for dep in deps['avalon']:
            if not os.path.exists(paths[0] + dep.lower()) or flags.update:
                color.note("Installing", dep)
                color.silent()
                args[0] = dep
                installPackage(flags, paths, args)
                color.silent()
                color.note("Installed", dep)


def installPipDeps(deps):
    try:
        deps['pip']
    except:
        return
    color.note('Found pip dependencies, installing.....')
    depss = " ".join(deps['pip'])
    color.debug(
        f"python3 -m pip install{' --user' if os.path.exists('/etc/portage') else ''} {depss}")
    os.system(
        f"python3 -m  install{' --user' if os.path.exists('/etc/portage') else ''} {depss}")


def reqTxt(pkgname, paths):
    color.debug(paths[0] + "/" + pkgname + '/' + 'requirements.txt')
    color.debug(os.curdir)
    if os.path.exists(paths[0] + "/" + pkgname + '/' + 'requirements.txt'):
        color.note("Requirements.txt found, installing.....")
        os.system(
            f"python3 -m pip --disable-pip-version-check -q install{' --user' if os.path.exists('/etc/portage') else ''} -r {paths[0]}/{pkgname}/requirements.txt")


def installDeps(flags, paths, args):
    pkg = getPackageInfo(paths, args[0])
    if pkg['deps']:
        color.note("Found dependencies, installing.....")
        pkgdeps = pkg['deps']
        if os.path.exists("/usr/bin/apt") and not os.path.exists("/usr/libexec/eselect-java/run-java-tool.bash"):
            installAptDeps(pkgdeps)
            installBuildDepDeps(pkgdeps)
        installAvalonDeps(flags, paths, args, pkgdeps)
        installPipDeps(pkgdeps)
    reqTxt(args[0], paths)


def runScript(script, *args):
    langs = {
        'py': 'python3',
        'sh': 'bash'
    }

    if os.path.exists('/etc/portage'):
        with open(script, "r") as r:
            e = r.read()
            with open(script, "w") as w:
                w.write(e.replace(
                    "pip3 install", "pip3 install --user").replace("pip install", "pip install --user"))

    argss = " ".join([f"{arg}" for arg in args])

    if script.split('.')[-1].lower() in langs:
        color.debug(f"{langs[script.split('.')[-1]]} {script} {argss}")
        return os.system(f"{langs[script.split('.')[-1]]} {script} {argss}")
    else:
        color.debug(f'{langs["sh"]} {script} {argss}')
        return os.system(f'{langs["sh"]} {script} {argss}')


def compilePackage(srcFolder, binFolder, packagename, paths, flags):
    pkg = getPackageInfo(paths, packagename)
    os.chdir(f"{srcFolder}/{packagename}")

    os.makedirs(f"{paths[4]}/{packagename}", exist_ok=True)

    if pkg['needsCompiled']:

        if not pkg['binname']:

            color.warn(
                "Package needs compiled but there is no binname for Avalon to install, assuming installed by compile script.....")

        if pkg['compileScript']:

            color.note("Compile script found, compiling.....")
            if runScript(pkg['compileScript'], f"\"{srcFolder+f'/{packagename}'}\" \"{pkg['binname']}\" \"{paths[4]+packagename}\""):

                error("Compile script failed!")

        else:
            error(
                "Program needs compiling but no compilation script found... exiting.....")

    else:
        color.warn(
            "Program does not need to be compiled, moving to installation.....")

    if pkg['binname'] and not pkg['mvBinAfterInstallScript']:

        rmFromBin(binFolder, packagename, paths)

        if pkg['binfile']:

            mvBinToBin(binFolder, paths[4]+packagename, srcFolder +
                       "/" + packagename + "/", pkg['binfile'], pkg['binname'])

        else:

            mvBinToBin(binFolder, paths[4]+packagename, srcFolder +
                       "/" + packagename + "/", pkg['binname'], pkg['binname'])

    if pkg['installScript']:

        color.note("Installing.....")
        if pkg['needsCompiled'] or pkg['compileScript'] or pkg['binname']:

            if runScript(pkg['installScript'], f"\"{paths[4]+ '/' + packagename + '/' + pkg['binname']}\" \"{paths[4]+packagename}\" \"{binFolder}\" \"{srcFolder}\""):

                error("Install script failed!")

        else:

            if runScript(pkg['installScript'], f"\"{paths[4] + '/' + packagename}\" \"{srcFolder}\" \"{packagename}\""):

                error("Install script failed!")

    if pkg['toCopy']:

        color.note("Copying files needed by program.....")
        copyFilesToFiles(paths, packagename, pkg['toCopy'])

    if pkg['mvBinAfterInstallScript'] and pkg['binname']:

        rmFromBin(binFolder, packagename, paths)

        if pkg['binfile']:

            mvBinToBin(binFolder, paths[4]+packagename, srcFolder +
                       "/" + packagename + "/", pkg['binfile'], pkg['binname'])

        else:

            mvBinToBin(binFolder, paths[4]+packagename, srcFolder +
                       "/" + packagename + "/", pkg['binname'], pkg['binname'])

    else:
        color.warn(
            'No installation script found... Assuming installation beyond APM\'s autoinstaller isn\'t neccessary')


def installLocalPackage(flags, paths, args):
    tmppath = paths[5]

    shutil.rmtree(tmppath)

    if not os.path.exists(tmppath):
        os.mkdir(tmppath)

    color.isDebug = flags.debug

    color.note("Unpacking package.....")
    if not os.path.exists(args[0]):
        error(f"{args[0]} does not exist")
    elif os.path.isdir(args[0]):
        color.debug(f"cp -r {args[0]}/./ {tmppath}")
        if os.system(f"cp -r {args[0]}/./ {tmppath}"):
            error("Failed to copy files")
    else:
        color.debug(f"tar -xf {args[0]} -C {tmppath}")
        if os.system(f"tar -xf {args[0]} -C {tmppath}"):
            error("Error unpacking package, not a tar.gz file")

    cfgfile = json.load(open(f"{tmppath}/.avalon/package", "r"))
    try:
        args[0] = (cfgfile["author"] + "/" + cfgfile["repo"]).lower()
    except:
        error("Package's package file need 'author' and 'repo'")

    color.note("Deleting old binaries and source files.....")
    deletePackage(paths[0], paths[1], args[0], paths, cfgfile)

    color.note("Copying package files....")
    color.debug(f"mkdir -p {paths[0]}/{args[0]}")
    if os.system(f"mkdir -p {paths[0]}/{args[0]}"):
        error("Failed to make src folder")
    color.debug(f"cp -a {tmppath}/. {paths[0]}/{args[0]}")
    if os.system(f"cp -a {tmppath}/. {paths[0]}/{args[0]}"):
        error("Failed to copy files from temp folder to src folder")

    shutil.rmtree(tmppath)

    checkReqs(paths, args[0])

    installDeps(flags, paths, args)

    if not flags.noinstall:
        color.note("Beginning compilation/installation.....")
        compilePackage(paths[0], paths[1], args[0], paths, flags)
        color.success("Done!")
    else:
        color.warn("-ni specified, skipping installation/compilation")


def installPackage(flags, paths, args):
    if os.path.exists(args[0]):
        installLocalPackage(flags, paths, args)
        quit()

    if os.path.exists(f"{paths[0]}/{args[0].lower()}") and not flags.fresh:
        updatePackage(flags, paths, *args)
        quit()

    color.isDebug = flags.debug

    args[0] = args[0].lower()

    if not os.path.exists(f"{paths[2]}/R2Boyo25"):
        downloadMainRepo(paths[2])

    packagename = args[0]

    if ":" in packagename:
        branch = None
        commit = packagename.split(":")[-1]
        packagename = packagename.split(":")[0]
    elif packagename.count("/") > 1:
        branch = packagename.split("/")[-1]
        packagename = "/".join(packagename.split(":")[:-1])
        commit = None
    elif (":" in packagename) and (packagename.count("/") > 1):
        commit = packagename.split(":")[-1]
        packagename = packagename.split(":")[0]
        branch = packagename.split("/")[-1]
        packagename = "/".join(packagename.split(":")[:-1])
    else:
        branch = None
        commit = None

    args[0] = packagename

    color.note("Deleting old binaries and source files.....")
    deletePackage(paths[0], paths[1], args[0], paths,
                  branch=branch, commit=commit)
    color.note("Downloading from github.....")
    color.debug(paths[0], "https://github.com/" + args[0], args[0])
    downloadPackage(paths[0], "https://github.com/" +
                    args[0], args[0], branch=branch, commit=commit)

    if isInMainRepo(args[0], paths) and not isAvalonPackage(args[0], paths[0], args[0]):
        color.note(
            "Package is not an Avalon package, but it is in the main repository... installing from there.....")
        moveMainRepoToAvalonFolder(paths[2], args[0], paths[0], paths)
    else:
        color.debug("Not in the main repo")

    checkReqs(paths, args[0])

    installDeps(flags, paths, args)

    if not flags.noinstall:
        color.note("Beginning compilation/installation.....")
        compilePackage(paths[0], paths[1], args[0], paths, flags)
        color.success("Done!")
    else:
        color.warn("-ni specified, skipping installation/compilation")


def updatePackage(flags, paths, *args):
    "Update to newest version of a repo, then recompile + reinstall program"

    args = list(args)

    if len(args) == 0:
        args.append("r2boyo25/avalonpackagemanager")

    if not os.path.exists(f"{paths[2]}/R2Boyo25"):
        downloadMainRepo(paths[2])

    color.isDebug = flags.debug

    args[0] = args[0].lower()

    color.note("Pulling from github.....")

    if os.system(f"cd {paths[0]}/{args[0]}; git pull"):
        if os.system(f"cd {paths[0]}/{args[0]}; git reset --hard; git pull"):
            error("Git error")

    if isInMainRepo(args[0], paths):
        color.note(
            "Package is not an Avalon package, but it is in the main repository... installing from there.....")
        moveMainRepoToAvalonFolder(paths[2], args[0], paths[0], paths)
    else:
        color.debug("Not in the main repo")

    checkReqs(paths, args[0])

    installDeps(flags, paths, args)

    if not flags.noinstall:
        color.note("Beginning compilation/installation.....")
        compilePackage(paths[0], paths[1], args[0], paths, flags)
        color.success("Done!")
    else:
        color.warn("-ni specified, skipping installation/compilation")


def redoBin(flags, paths, *args):
    "Redo making of symlinks without recompiling program"
    args = list(args)

    color.isDebug = flags.debug

    args[0] = args[0].lower()

    packagename = args[0]
    binFolder = paths[1]
    srcFolder = paths[0]
    pkg = getPackageInfo(paths, packagename)
    color.debug(packagename, binFolder, srcFolder, str(pkg))
    rmFromBin(binFolder, packagename, paths, pkg=pkg)

    if pkg['binfile']:

        mvBinToBin(binFolder, paths[4]+packagename, srcFolder +
                   "/" + packagename + "/", pkg['binfile'], pkg['binname'])

    else:

        mvBinToBin(binFolder, paths[4]+packagename, srcFolder +
                   "/" + packagename + "/", pkg['binname'], pkg['binname'])


def uninstallPackage(flags, paths, args):

    color.isDebug = flags.debug

    args[0] = args[0].lower()

    if not os.path.exists(f"{paths[2]}/R2Boyo25"):
        downloadMainRepo(paths[2])

    if isInMainRepo(args[0], paths) and not isAvalonPackage(args[0], paths[0], args[0]):
        color.note(
            "Package is not an Avalon package, but it is in the main repository... uninstalling from there.....")
        moveMainRepoToAvalonFolder(paths[2], args[0], paths[0], paths)

    checkReqs(paths, args[0])

    pkg = getPackageInfo(paths, args[0])
    color.note("Uninstalling.....")
    if not pkg['uninstallScript']:

        color.warn(
            "Uninstall script not found... Assuming uninstall not required and deleting files.....")
        deletePackage(paths[0], paths[1], args[0], paths)

    else:

        color.note("Uninstall script found, running.....")

        os.chdir(paths[1])
        if runScript(paths[0] + "/" + args[0] + '/' + pkg['uninstallScript'], paths[0], paths[1], args[0], pkg['binname'], paths[4]+args[0]):

            color.error("Uninstall script failed! Deleting files anyways.....")

        deletePackage(paths[0], paths[1], args[0], paths)

    color.success("Successfully uninstalled package!")


def installed(flags, paths, *args):
    "List installed packages"

    color.isDebug = flags.debug

    print("\n".join(getInstalled(paths)).title())


def dlSrc(flags, paths, *args):
    "Download repo into folder"

    if len(args) == 1:
        os.system(f"git clone https://github.com/{args[0].lower()}")
    elif len(args) == 2:
        os.system(f"git clone https://github.com/{args[0].lower()} {args[1]}")
    else:
        os.system("git pull")


def updateCache(flags, paths, *args):
    "Update cache"

    downloadMainRepo(paths[2])
