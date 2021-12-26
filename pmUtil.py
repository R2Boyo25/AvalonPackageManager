#!/usr/bin/python3

from package import Package, NPackage
import requests
import os
import shutil
import color
import json
import getpass
import platform
import distro

import case.case

class e404(Exception):
    pass

def error(*text):
    color.error(*text)
    quit()

def getRepos(user, cache = True):
    if cache:
        pass
    else:
        pass

    r = requests.request("GET", "https://api.github.com/users/"+user+"/repos").json()

    return r

def getCachedPackageMainRepoInfo(cacheFolder, srcFolder, pkgname):
    color.debug(f"{cacheFolder}/{pkgname}/package")
    color.debug(case.case.getCaseInsensitivePath(f"{cacheFolder}/{pkgname}/package"))
    if os.path.exists(case.case.getCaseInsensitivePath(f"{cacheFolder}/{pkgname}/package")):
        color.debug("Loading from main repo cache")
        with open(case.case.getCaseInsensitivePath(f"{cacheFolder}/{pkgname}/package"), 'r') as pkgfile:
            try:
                return json.loads(pkgfile.read())
            except Exception as e:
                color.debug(pkgfile.read())
                raise e
    else:
        return False

def getCachedPackageRepoInfo(cacheFolder, srcFolder, pkgname):
    if os.path.exists(f"{srcFolder}/{pkgname}/.avalon/package"):
        color.debug("Loading from src;", f"{srcFolder}/{pkgname}/.avalon/package")
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

def getRepoPackageInfo(pkgname, commit = None, branch = None):
    if not branch and not commit:
        r = requests.get(f'https://raw.githubusercontent.com/{pkgname}/master/.avalon/package')
        color.debug(f'https://raw.githubusercontent.com/{pkgname}/master/.avalon/package')
        color.debug(r.text)
        if not "404" in r.text:
            return r.json()
        else:
            r = requests.get(f'https://raw.githubusercontent.com/{pkgname}/main/.avalon/package')
            color.debug(f'https://raw.githubusercontent.com/{pkgname}/main/.avalon/package')
            color.debug(r.text)
            if not "404" in r.text:
                return r.json()
            else:
                raise e404("Repo")
    else:
        if branch:
            r = requests.get(f'https://raw.githubusercontent.com/{pkgname}/{branch}/.avalon/package')
            color.debug(f'https://raw.githubusercontent.com/{pkgname}/{branch}/.avalon/package')
            color.debug(r.text)
            if not "404" in r.text:
                return r.json()
            else:
                raise e404("Branch")
        elif commit:
            r = requests.get(f'https://raw.githubusercontent.com/{pkgname}/{commit}/.avalon/package')
            color.debug(f'https://raw.githubusercontent.com/{pkgname}/{commit}/.avalon/package')
            color.debug(r.text)
            if not "404" in r.text:
                return r.json()
            else:
                raise e404("Branch")

def getMainRepoPackageInfo(pkgname):
    r = requests.get(f'https://raw.githubusercontent.com/R2Boyo25/AvalonPMPackages/master/{pkgname}/package')
    color.debug(f'https://raw.githubusercontent.com/R2Boyo25/AvalonPMPackages/master/{pkgname}/package')    
    color.debug(r.text)
    if not "404" in r.text:
        return r.json()
    else:
        raise e404("Main")

def getPackageInfo(paths, pkgname, commit = None, branch = None):
    color.debug(pkgname)
    color.debug(str(paths))
    if getCachedPackageInfo(paths[2], paths[0], pkgname):
        return NPackage(getCachedPackageInfo(paths[2], paths[0], pkgname))
    else:
        try:
            return NPackage(getRepoPackageInfo(pkgname, commit = commit, branch = branch))
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
    shutil.rmtree(cacheDir)
    color.debug(f"git clone --depth 1 https://github.com/r2boyo25/AvalonPMPackages \"{cacheDir}\" -q")
    os.system(f"git clone --depth 1 https://github.com/r2boyo25/AvalonPMPackages \"{cacheDir}\" -q")
    
def moveMainRepoToAvalonFolder(cacheFolder, pkgname, srcFolder, paths):
    color.debug(pkgname)
    color.debug("Moving to .avalon folder")
    color.debug(srcFolder + "/" + pkgname + "/.avalon")
    shutil.rmtree(srcFolder + "/" + pkgname + "/.avalon", ignore_errors = True)
    if isInMainRepo(pkgname, paths):
        color.debug(case.case.getCaseInsensitivePath(cacheFolder + "/" + pkgname), srcFolder + "/" + pkgname + '/.avalon')
        shutil.copytree(case.case.getCaseInsensitivePath(cacheFolder + "/" + pkgname), srcFolder + "/" + pkgname + '/.avalon')

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
        return getDistro() in pkg['distros']
    else:
        color.warn("Supported distros not specified, assuming this distro is supported.....")
        return True

def getArch():
    return platform.machine()

def archIsSupported(pkg):
    color.debug(str(pkg))
    color.debug(getArch())
    if pkg['arches']:
        return getArch() in pkg['arches']
    else:
        color.warn("Supported arches not specified, assuming this arch is supported.....")
        return True

def checkReqs(paths, pkgname):
    pkg = getPackageInfo(paths, pkgname)
    if not archIsSupported(pkg):
        deletePackage(paths[0], paths[1], pkgname, paths)
        error(f"Arch {getArch()} not supported by package")
    if not distroIsSupported(pkg):
        deletePackage(paths[0], paths[1], pkgname, paths)
        error(f"Distro {getDistro()} not supported by package")

def downloadPackage(srcFolder, packageUrl, packagename = None, branch = None, commit = None):
    if not packagename: 
        packagename = packageUrl.lstrip("https://github.com/")
    color.debug(packagename)
    os.chdir(srcFolder)
    if commit and branch:
        os.system('git clone ' + packageUrl + ' ' + packagename + " -q")
        os.system(f"cd {packagename}; git reset --hard {commit}")
    elif branch:
        packagename = "/".join(packagename.split(":")[:-1])
        os.system('git clone --depth 1 ' + packageUrl + ' ' + packagename + " -q -b " + branch)
    elif commit:
        os.system('git clone ' + packageUrl + ' ' + packagename + " -q")
        os.system(f"cd {packagename}; git reset --hard {commit}")
    else:
        os.system('git clone --depth 1 ' + packageUrl + ' ' + packagename + " -q")

def deletePackage(srcFolder, binFolder, packagename, paths, cfg = None, commit = None, branch = None):
    rmFromSrc(srcFolder, packagename)
    if cfg:
        rmFromBin(binFolder, packagename, paths, cfg, branch = branch, commit = commit)
    else:
        rmFromBin(binFolder, packagename, paths, branch = branch, commit = commit)
    rmFromFiles(paths[4], packagename)

def rmFromSrc(srcFolder, packagename):
    if os.path.exists(f"{srcFolder}/{packagename}"):
        shutil.rmtree(f"{srcFolder}/{packagename}", ignore_errors=True)

def rmFromBin(binFolder, packagename, paths, pkg = None, commit = None, branch = None):
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
    #if color.isDebug:
    #    error(str(binFolder), str(fileFolder), str(binFile), str(binName))
    try:
        shutil.copyfile(srcFolder + "/" + binFile, fileFolder+'/'+binName.split('/')[-1])
    except:
        pass
    
    #os.symlink(fileFolder+'/'+binName, binFolder + binName.split('/')[-1])
    os.symlink(fileFolder+'/'+binFile, binFolder + binName.split('/')[-1])

    #with open(binFolder + binName, 'w') as f:
    #    f.write(f'#!/bin/bash\nOWD="$(pwd)"\ncd {fileFolder}\n./{binName}\ncd $OWD')
    #st = os.stat(binFolder + '/' + binName.split('/')[-1])
    #os.chmod(binFolder + '/' + binName.split('/')[-1], st.st_mode ^ 111)
    
    #os.chmod(fileFolder + '/' + binName.split('/')[-1], 755)
    #color.debug(f"chmod +x {fileFolder + '/' + binName.split('/')[-1]}")
    #os.system(f"chmod +x {fileFolder + '/' + binName.split('/')[-1]}")
    color.debug(f"chmod +x {fileFolder + '/' + binFile}")
    os.system(f"chmod +x {fileFolder + '/' + binFile}")

def copyFilesToFiles(paths, pkgname, files = ['all']):
    color.debug(str(files))
    if files != ['all']:
        for file in files:
            color.debug(file)
            os.makedirs(paths[4] + '/' + pkgname + '/' + os.path.dirname(file), exist_ok=True)
            try:
                shutil.copy2(paths[0] + '/' + pkgname + '/' + file, paths[4] + '/' + pkgname + '/' + file)
            except:
                shutil.copytree(paths[0] + '/' + pkgname + '/' + file, paths[4] + '/' + pkgname + '/' + file)

    else:
        color.debug(paths[0] + '/' + pkgname + '/')
        #color.debug(" ".join([i for i in os.listdir(paths[0] + '/' + pkgname + '/')]))
        for file in os.listdir(paths[0] + '/' + pkgname + '/'):
            #color.debug(file)
            try:
                shutil.copy2(paths[0] + '/' + pkgname + '/' + file, paths[4] + '/' + pkgname + '/' + file)
            except:
                shutil.copytree(paths[0] + '/' + pkgname + '/' + file, paths[4] + '/' + pkgname + '/' + file)

def installAptDeps(deps):
    try:
        deps['apt']
    except:
        return
    if deps['apt']:
        color.note("Found apt dependencies, installing..... (this will require your password)")
        depss = " ".join( deps['apt'] )

        if getpass.getuser() not in ['root', "u0_a196"]:
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
        color.note("Found build-dep (apt) dependencies, installing..... (this will require your password)")
        depss = " ".join( deps['build-dep'] )

        if getpass.getuser() not in ['root', "u0_a196"]:
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
    depss = " ".join( deps['pip'] )
    color.debug(f"pip3 install {depss}")
    os.system(f"pip3 install {depss}")

def reqTxt(pkgname, paths):
    color.debug(paths[0] + "/" + pkgname + '/' + 'requirements.txt')
    color.debug(os.curdir)
    if os.path.exists(paths[0] + "/" + pkgname + '/' + 'requirements.txt'):
        color.note("Requirements.txt found, installing.....")
        os.system(f'pip3 --disable-pip-version-check install -r {paths[0]}/{pkgname}/requirements.txt')

def installDeps(flags, paths, args):
    pkg = getPackageInfo(paths, args[0])
    if pkg['deps']:
        color.note("Found dependencies, installing.....")
        pkgdeps = pkg['deps']
        installAptDeps(pkgdeps)
        installBuildDepDeps(pkgdeps)
        installAvalonDeps(flags, paths, args, pkgdeps)
        installPipDeps(pkgdeps)
    reqTxt(args[0], paths)

def runScript(script, *args):
    langs = {
        'py':'python3',
        'sh':'bash'
    }

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

    os.makedirs(f"{paths[4]}/{packagename}")
    
    if pkg['needsCompiled']:

        if not pkg['binname']:

            color.warn("Package needs compiled but there is no binname for Avalon to install, assuming installed by compile script.....")

        if pkg['compileScript']:

            color.note("Compile script found, compiling.....")
            if runScript(pkg['compileScript'], f"\"{srcFolder+f'/{packagename}'}\" \"{pkg['binname']}\" \"{paths[4]+packagename}\""):

                error("Compile script failed!")

        else:
            error("Program needs compiling but no compilation script found... exiting.....")

    else:
        color.warn("Program does not need to be compiled, moving to installation.....")

    if pkg['binname'] and not pkg['mvBinAfterInstallScript']:
        if pkg['binfile']:

            mvBinToBin(binFolder, paths[4]+packagename, srcFolder + "/" + packagename + "/", pkg['binfile'], pkg['binname'])
        
        else:

            mvBinToBin(binFolder, paths[4]+packagename, srcFolder + "/" + packagename + "/", pkg['binname'], pkg['binname'])

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
        if pkg['binfile']:

            mvBinToBin(binFolder, paths[4]+packagename, srcFolder + "/" + packagename + "/", pkg['binfile'], pkg['binname'])
        
        else:

            mvBinToBin(binFolder, paths[4]+packagename, srcFolder + "/" + packagename + "/", pkg['binname'], pkg['binname'])

    else:
        color.warn('No installation script found... Assuming installation beyond APM\'s autoinstaller isn\'t neccessary')

def installLocalPackage(flags, paths, args):
    tmppath = paths[5]

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
    if os.path.exists(args[0]) or flags.fromfile:
        installLocalPackage(flags, paths, args)
        quit()

    color.isDebug = flags.debug

    args[0] = args[0].lower()
    
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
    elif ( ":" in packagename ) and ( packagename.count("/") > 1 ):
        commit = packagename.split(":")[-1]
        packagename = packagename.split(":")[0]
        branch = packagename.split("/")[-1]
        packagename = "/".join(packagename.split(":")[:-1])
    else:
        branch = None
        commit = None
    
    args[0] = packagename

    color.note("Deleting old binaries and source files.....")
    deletePackage(paths[0], paths[1], args[0], paths, branch = branch, commit = commit)
    color.note("Downloading from github.....")
    color.debug(paths[0], "https://github.com/" + args[0], args[0])
    downloadPackage(paths[0], "https://github.com/" + args[0], args[0], branch = branch, commit = commit)
            
    if isInMainRepo(args[0], paths) and not isAvalonPackage(args[0], paths[0], args[0]):
        color.note("Package is not an Avalon package, but it is in the main repository... installing from there.....")
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
    rmFromBin(binFolder, packagename, paths, pkg = pkg)

    if pkg['binfile']:

        mvBinToBin(binFolder, paths[4]+packagename, srcFolder + "/" + packagename + "/", pkg['binfile'], pkg['binname'])
        
    else:

        mvBinToBin(binFolder, paths[4]+packagename, srcFolder + "/" + packagename + "/", pkg['binname'], pkg['binname'])

def uninstallPackage(flags, paths, args):

    color.isDebug = flags.debug
    
    args[0] = args[0].lower()

    downloadMainRepo(paths[2])

    if isInMainRepo(args[0], paths) and not isAvalonPackage(args[0], paths[0], args[0]):
        color.note("Package is not an Avalon package, but it is in the main repository... uninstalling from there.....")
        moveMainRepoToAvalonFolder(paths[2], args[0], paths[0], paths)

    checkReqs(paths, args[0])

    pkg = getPackageInfo(paths, args[0])
    color.note("Uninstalling.....")
    if not pkg['uninstallScript']:

        color.warn("Uninstall script not found... Assuming uninstall not required and deleting files.....")
        deletePackage(paths[0], paths[1], args[0], paths)

    else:

        color.note("Uninstall script found, running.....")

        os.chdir(paths[1])
        if runScript(paths[0] + "/" + args[0] + '/' + pkg['uninstallScript'], paths[0], paths[1], args[0], pkg['binname'], paths[4]+args[0]):
            
            color.error("Uninstall script failed! Deleting files anyways.....")

        deletePackage(paths[0], paths[1], args[0], paths)
    
    color.success("Successfully uninstalled package!")
