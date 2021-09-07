from package import Package
import requests

class e404(Exception):
    pass

def getPackageInfo(pkgname):
    r = requests.get(f'https://raw.githubusercontent.com/{pkgname}/main/.avalon/package')
    try:
        return r.json()
    except:
        raise e404()

def isAvalonPackage(jsonobj):
    try:
        getPackageInfo(jsonobj['full_name'])
        return True
    except e404:
        return False