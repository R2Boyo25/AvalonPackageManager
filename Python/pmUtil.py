from package import Package, NPackage
import requests
import os
import shutil
import color

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
    r = requests.get(f'https://raw.githubusercontent.com/r2boyo25/avalonpmpackages/main/{pkgname}/package')
    try:
        return r.json()
    except:
        raise e404()

def getPackageInfo(pkgname):
    try:
        return NPackage(getRepoPackageInfo(pkgname))
    except:
        return NPackage(getMainRepoPackageInfo(pkgname))

def isAvalonPackage(jsonobj):
    try:
        getPackageInfo(jsonobj['full_name'])
        return True
    except e404:
        return False

def downloadPackage(srcFolder, packageUrl, packagename = None):
    if not packagename: packagename = packageUrl.lstrip("https://github.com/")
    os.chdir(srcFolder)
    os.system('git clone ' + packageUrl + ' ' + packagename)

def deletePackage(srcFolder, binFolder, packagename):
    rmFromSrc(srcFolder, packagename)
    rmFromBin(binFolder, packagename)

def rmFromSrc(srcFolder, packagename):
    if os.path.exists(f"{srcFolder}/{packagename}"):
        shutil.rmtree(f"{srcFolder}/{packagename}", ignore_errors=True)

def rmFromBin(binFolder, packagename):
    pkg = getPackageInfo(packagename)
    if os.path.exists(f"{binFolder}/{pkg['binname']}"):
        os.remove(f"{binFolder}/{pkg['binname']}")
        #shutil.rmtree(f"{binFolder}/{packagename}", ignore_errors=True)

def mvBinToBin(binFolder, binFile, binName):
    os.rename(binFile, binFolder+'/'+binName)

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

def compilePackage(srcFolder, binFolder, packagename):
    pkg = getPackageInfo(packagename)
    os.chdir(f"{srcFolder}/{packagename}")
    if not os.path.exists(binFolder+f'/{packagename}'):

        os.makedirs(binFolder+f'/{packagename}')

    if pkg['needsCompiled']:

        if not pkg['binname']:

            error("Package needs compiled but there is no binname for Avalon to install.....")

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
        error('No installation script found.....')

def installPackage(paths, args):
    if '--debug' in args or '-d' in args:
        color.isDebug = True
    else:
        color.isDebug = False
    color.note("Deleting old binaries and source files.....")
    deletePackage(paths[0], paths[1], args[0])
    color.note("Downloading from github.....")
    downloadPackage(paths[0], "https://github.com/" + args[0])
    color.note("Beginning compilation/installation.....")
    compilePackage(paths[0], paths[1], args[0])
    color.success("Done!")