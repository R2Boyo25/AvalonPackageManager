from package import Package
import requests

class e404(Exception):
    pass

def getRepos(user, cache = True):
    if cache:

    else:
        

    r = requests.request("GET", "https://api.github.com/users/"+user+"/repos").json()

    return r

def getRepoPackageInfo(pkgname):
    r = requests.get(f'https://raw.githubusercontent.com/{pkgname}/main/.avalon/package')
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
        return getRepoPackageInfo(pkgname)
    except:
        return getMainRepoPackageInfo(pkgname)

def isAvalonPackage(jsonobj):
    try:
        getPackageInfo(jsonobj['full_name'])
        return True
    except e404:
        return False
        