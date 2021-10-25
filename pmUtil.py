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
def getCachedPackageInfo(cacheFolder, srcFolder, pkgname):
    if os.path.exists(f"{cacheFolder}/{pkgname}/package"):
        color.debug("Loading from cache")
        with open(f"{cacheFolder}/{pkgname}/package", 'r') as pkgfile:
            try:
                return json.loads(pkgfile.read())
            except:
                return False
    elif os.path.exists(f"{srcFolder}/{pkgname}/.avalon/package"):
        color.debug("Loading from src")
        with open(f"{srcFolder}/{pkgname}/.avalon/package", 'r') as pkgfile:
            try:
                return json.loads(pkgfile.read())
            except:
                return False
    else:
        color.debug("Not cached")
        return False

def getRepoPackageInfo(pkgname):
    try:
        r = requests.get(f'https://raw.githubusercontent.com/{pkgname}/main/.avalon/package')
        try:
            return r.json()
        except:
            raise e404()
    except:
        r = requests.get(f'https://raw.githubusercontent.com/{pkgname}/master/.avalon/package')
        try:
            return r.json()
        except:
            raise e404()
        

def getMainRepoPackageInfo(pkgname):
    color.debug(f'https://raw.githubusercontent.com/R2Boyo25/AvalonPMPackages/master/{pkgname}/package')    
    r = requests.get(f'https://raw.githubusercontent.com/R2Boyo25/AvalonPMPackages/master/{pkgname}/package')
    try:
        return r.json()
    except:
        raise e404()

def getPackageInfo(paths, pkgname):
    try:
        return NPackage(getCachedPackageInfo(paths[2], paths[0], pkgname))
    except:
        try:
            return NPackage(getRepoPackageInfo(pkgname))
        except:
            return NPackage(getMainRepoPackageInfo(pkgname))
            

def isInMainRepo(pkgname):
    r = requests.get(f'https://raw.githubusercontent.com/r2boyo25/AvalonPMPackages/master/{pkgname}/package')
    try:
        r.json()
        return True
    except:
        return False

def downloadMainRepo(cacheDir):
    shutil.rmtree(cacheDir)
    color.debug(f"git clone https://github.com/r2boyo25/AvalonPMPackages \"{cacheDir}\" -q")
    os.system(f"git clone https://github.com/r2boyo25/AvalonPMPackages \"{cacheDir}\" -q")
    
def moveMainRepoToAvalonFolder(cacheFolder, pkgname, srcFolder):
    color.debug(srcFolder + "/" + pkgname + "/.avalon")
    shutil.rmtree(srcFolder + "/" + pkgname + "/.avalon", ignore_errors = True)
    if isInMainRepo(pkgname):
        color.debug(cacheFolder + "/" + pkgname, srcFolder + "/" + pkgname + '/.avalon')
        shutil.copytree(cacheFolder + "/" + pkgname, srcFolder + "/" + pkgname + '/.avalon')

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
    archIsSupported(pkg)
    distroIsSupported(pkg)

def downloadPackage(srcFolder, packageUrl, packagename = None):
    if not packagename: 
        packagename = packageUrl.lstrip("https://github.com/")
    color.debug(packagename)
    os.chdir(srcFolder)
    os.system('git clone ' + packageUrl + ' ' + packagename + " -q")

def deletePackage(srcFolder, binFolder, packagename, paths):
    rmFromSrc(srcFolder, packagename)
    rmFromBin(binFolder, packagename, paths)

def rmFromSrc(srcFolder, packagename):
    if os.path.exists(f"{srcFolder}/{packagename}"):
        shutil.rmtree(f"{srcFolder}/{packagename}", ignore_errors=True)

def rmFromBin(binFolder, packagename, paths):
    pkg = getPackageInfo(paths, packagename)
    if os.path.exists(f"{binFolder}/{pkg['binname']}"):
        os.remove(f"{binFolder}/{pkg['binname']}")
        #shutil.rmtree(f"{binFolder}/{packagename}", ignore_errors=True)

def mvBinToBin(binFolder, binFile, binName):
    os.rename(binFile, binFolder+'/'+binName)

def installAptDeps(deps):
    try:
        deps['apt']
    except:
        return
    if deps['apt']:
        color.note("Found apt dependencies, installing..... (this will require your password)")
        depss = " ".join( deps['apt'] )

        if getpass.getuser() not in ['root', "u0_a196"]:
            color.debug(f'sudo apt install {depss}')
            os.system(f'sudo apt install {depss}')
        else:
            color.debug(f'apt install {depss}')
            os.system(f'apt install {depss}')

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
                args[0] = dep
                installPackage(paths, args)

def installPipDeps(deps):
    try:
        deps['pip']
    except:
        return
    color.note('Found pip dependencies, installing.....')
    depss = " ".join( deps['pip'] )
    color.debug(f"pip3 install {depss}")
    os.system(f"pip3 install {depss}")

def reqTxt(pkgname):
    if os.path.exists(pkgname + '/' + 'requirements.txt'):
        color.note("Requirements.txt found, installing.....")
        os.system(f'pip3 --disable-pip-version-check install -r {pkgname}/requirements.txt')

def installDeps(paths, args):
    pkg = getPackageInfo(paths, args[0])
    if pkg['deps']:
        color.note("Found dependencies, installing.....")
        pkgdeps = pkg['deps']
        installAptDeps(pkgdeps)
        installAvalonDeps(paths, args, pkgdeps)
        installPipDeps(pkgdeps)
    reqTxt(args[0])

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

    if pkg['needsCompiled']:

        if not pkg['binname']:

            color.warn("Package needs compiled but there is no binname for Avalon to install, assuming installed by compile script.....")

        if pkg['compileScript']:

            color.note("Compile script found, compiling.....")
            if runScript(pkg['compileScript'], f"\"{srcFolder+f'/{packagename}'}\" \"{pkg['binname']}\""):

                error("Compile script failed!")

            mvBinToBin(binFolder, srcFolder + "/" + packagename + "/" + pkg['binname'], pkg['binname'])

        else:
            error("Program needs compiling but no compilation script found... exiting.....")

    else:
        color.warn("Program does not need to be compiled, moving to installation.....")

    if pkg['installScript']:

        color.note("Installing.....")
        if pkg['needsCompiled'] or pkg['compileScript']:

            if runScript(pkg['installScript'], f"\"{binFolder+ '/' + pkg['binname']}\""):

                error("Install script failed!")
        
        else:
            
            if runScript(pkg['installScript'], f"\"{binFolder}\" \"{srcFolder}\" \"{packagename}\""):

                error("Install script failed!")

    else:
        color.warn('No installation script found... Assuming installation beyond APM\'s autoinstaller isn\'t neccessary')

def installPackage(paths, args):
    if '--debug' in args or '-d' in args:
        color.isDebug = True
    else:
        color.isDebug = False
    
    downloadMainRepo(paths[2])

    color.note("Deleting old binaries and source files.....")
    deletePackage(paths[0], paths[1], args[0], paths)
    color.note("Downloading from github.....")
    color.debug(paths[0], "https://github.com/" + args[0], args[0])
    downloadPackage(paths[0], "https://github.com/" + args[0], args[0])
            
    if isInMainRepo(args[0]) and not isAvalonPackage(args[0]):
        color.note("Package is not an Avalon package, but it is in the main repository... installing from there.....")
        moveMainRepoToAvalonFolder(paths[2], args[0], paths[0])
    
    checkReqs(args[0], paths)

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
    
    downloadMainRepo(paths[2])

    if isInMainRepo(args[0]) and not isAvalonPackage(args[0]):
        color.note("Package is not an Avalon package, but it is in the main repository... uninstalling from there.....")
        moveMainRepoToAvalonFolder(paths[2], args[0], paths[0])

    checkReqs(args[0], paths)

    pkg = getPackageInfo(paths, args[0])
    color.note("Uninstalling.....")
    if not pkg['uninstallScript']:

        color.warn("Uninstall script not found... Assuming uninstall not required and deleting files.....")
        deletePackage(paths[0], paths[1], args[0], paths)

    else:

        color.note("Uninstall script found, running.....")

        os.chdir(paths[1])
        if runScript(paths[0] + "/" + args[0] + '/' + pkg['uninstallScript'], paths[0], paths[1], args[0], pkg['binname']):
            
            color.error("Uninstall script failed! Deleting files anyways.....")

        deletePackage(paths[0], paths[1], args[0], paths)
    
    color.success("Successfully uninstalled package!")