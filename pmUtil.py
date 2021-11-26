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

def getRepoPackageInfo(pkgname):
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
        

def getMainRepoPackageInfo(pkgname):
    r = requests.get(f'https://raw.githubusercontent.com/R2Boyo25/AvalonPMPackages/master/{pkgname}/package')
    color.debug(f'https://raw.githubusercontent.com/R2Boyo25/AvalonPMPackages/master/{pkgname}/package')    
    color.debug(r.text)
    if not "404" in r.text:
        return r.json()
    else:
        raise e404("Main")

def getPackageInfo(paths, pkgname):
    color.debug(pkgname)
    color.debug(str(paths))
    if getCachedPackageInfo(paths[2], paths[0], pkgname):
        return NPackage(getCachedPackageInfo(paths[2], paths[0], pkgname))
    else:
        try:
            return NPackage(getRepoPackageInfo(pkgname))
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

def isAvalonPackage(repo):
    try:
        if not getRepoPackageInfo(repo):
            raise e404
        return True
    except e404:
        return False

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

def downloadPackage(srcFolder, packageUrl, packagename = None):
    if not packagename: 
        packagename = packageUrl.lstrip("https://github.com/")
    color.debug(packagename)
    os.chdir(srcFolder)
    os.system('git clone --depth 1 ' + packageUrl + ' ' + packagename + " -q")

def deletePackage(srcFolder, binFolder, packagename, paths, cfg = None):
    rmFromSrc(srcFolder, packagename)
    if cfg:
        rmFromBin(binFolder, packagename, paths, cfg)
    else:
        rmFromBin(binFolder, packagename, paths)
    rmFromFiles(paths[4], packagename)

def rmFromSrc(srcFolder, packagename):
    if os.path.exists(f"{srcFolder}/{packagename}"):
        shutil.rmtree(f"{srcFolder}/{packagename}", ignore_errors=True)

def rmFromBin(binFolder, packagename, paths, pkg = None):
    if not pkg:
        pkg = getPackageInfo(paths, packagename)
    if os.path.exists(f"{binFolder}/{pkg['binname']}"):
        os.remove(f"{binFolder}/{pkg['binname']}")

def rmFromFiles(fileFolder, packagename):
    if os.path.exists(f"{fileFolder}/{packagename}"):
        shutil.rmtree(f"{fileFolder}/{packagename}", ignore_errors=True)

def mvBinToBin(binFolder, fileFolder, binFile, binName):
    #if color.isDebug:
    #    error(str(binFolder), str(fileFolder), str(binFile), str(binName))
    try:
        shutil.copyfile(binFile, fileFolder+'/'+binName.split('/')[-1])
    except:
        pass
    os.symlink(fileFolder+'/'+binName, binFolder + binName.split('/')[-1])

    #with open(binFolder + binName, 'w') as f:
    #    f.write(f'#!/bin/bash\nOWD="$(pwd)"\ncd {fileFolder}\n./{binName}\ncd $OWD')
    #st = os.stat(binFolder + '/' + binName.split('/')[-1])
    #os.chmod(binFolder + '/' + binName.split('/')[-1], st.st_mode ^ 111)
    
    #os.chmod(fileFolder + '/' + binName.split('/')[-1], 755)
    color.debug(f"chmod +x {fileFolder + '/' + binName.split('/')[-1]}")
    os.system(f"chmod +x {fileFolder + '/' + binName.split('/')[-1]}")

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
        color.debug(" ".join([i for i in os.listdir(paths[0] + '/' + pkgname + '/')]))
        for file in os.listdir(paths[0] + '/' + pkgname + '/'):
            color.debug(file)
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

def installAvalonDeps(paths, args, deps):
    try:
        deps['avalon']
    except:
        return
    args = args.copy()
    if deps['avalon']:
        color.note("Found avalon dependencies, installing.....")
        for dep in deps['avalon']:
            if not os.path.exists(paths[0] + dep) or '--update' in args or '-U' in args:
                color.note("Installing", dep)
                color.silent()
                args[0] = dep
                installPackage(paths, args)
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

def installDeps(paths, args):
    pkg = getPackageInfo(paths, args[0])
    if pkg['deps']:
        color.note("Found dependencies, installing.....")
        pkgdeps = pkg['deps']
        installAptDeps(pkgdeps)
        installAvalonDeps(paths, args, pkgdeps)
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

def compilePackage(srcFolder, binFolder, packagename, paths):
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
            
        mvBinToBin(binFolder, paths[4]+packagename, srcFolder + "/" + packagename + "/" + pkg['binname'], pkg['binname'])

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

        mvBinToBin(binFolder, paths[4]+packagename, srcFolder + "/" + packagename + "/" + pkg['binname'], pkg['binname'])

    else:
        color.warn('No installation script found... Assuming installation beyond APM\'s autoinstaller isn\'t neccessary')

def installLocalPackage(paths, args):
    tmppath = paths[5]
    if '--debug' in args or '-d' in args:
        color.isDebug = True
    else:
        color.isDebug = False

    color.note("Unpacking package.....")
    color.debug(f"tar -xf {args[0]} -C {tmppath}")
    os.system(f"tar -xf {args[0]} -C {tmppath}")
    cfgfile = json.load(open(f"{tmppath}/.avalon/package", "r"))
    try:
        args[0] = (cfgfile["author"] + "/" + cfgfile["repo"]).lower()
    except:
        error("Package's package file need 'author' and 'repo'")

    color.note("Deleting old binaries and source files.....")
    deletePackage(paths[0], paths[1], args[0], paths, cfgfile)

    color.note("Copying package files....")
    color.debug(f"mkdir -p {paths[0]}/{args[0]}")
    os.system(f"mkdir -p {paths[0]}/{args[0]}")
    color.debug(f"cp -a {tmppath}/. {paths[0]}/{args[0]}")
    os.system(f"cp -a {tmppath}/. {paths[0]}/{args[0]}")
    shutil.rmtree(tmppath)
    
    checkReqs(paths, args[0])

    installDeps(paths, args)

    if not '-ni' in args:
        color.note("Beginning compilation/installation.....")
        compilePackage(paths[0], paths[1], args[0], paths)
        color.success("Done!")
    else:
        color.warn("-ni specified, skipping installation/compilation")

def installPackage(paths, args):
    if '--debug' in args or '-d' in args:
        color.isDebug = True
    else:
        color.isDebug = False

    args[0] = args[0].lower()
    
    downloadMainRepo(paths[2])

    color.note("Deleting old binaries and source files.....")
    deletePackage(paths[0], paths[1], args[0], paths)
    color.note("Downloading from github.....")
    color.debug(paths[0], "https://github.com/" + args[0], args[0])
    downloadPackage(paths[0], "https://github.com/" + args[0], args[0])
            
    if isInMainRepo(args[0], paths) and not isAvalonPackage(args[0]):
        color.note("Package is not an Avalon package, but it is in the main repository... installing from there.....")
        moveMainRepoToAvalonFolder(paths[2], args[0], paths[0], paths)
    else:
        color.debug("Not in the main repo")
    
    checkReqs(paths, args[0])

    installDeps(paths, args)

    if not '-ni' in args:
        color.note("Beginning compilation/installation.....")
        compilePackage(paths[0], paths[1], args[0], paths)
        color.success("Done!")
    else:
        color.warn("-ni specified, skipping installation/compilation")

def uninstallPackage(paths, args):
    if '--debug' in args or '-d' in args:
        color.isDebug = True
    else:
        color.isDebug = False
    
    args[0] = args[0].lower()

    downloadMainRepo(paths[2])

    if isInMainRepo(args[0]) and not isAvalonPackage(args[0]):
        color.note("Package is not an Avalon package, but it is in the main repository... uninstalling from there.....")
        moveMainRepoToAvalonFolder(paths[2], args[0], paths[0])

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
