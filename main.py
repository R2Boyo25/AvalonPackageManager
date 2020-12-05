import requests, json
from os import path
import os

from consolemenu import *
from consolemenu.items import *

menu = ConsoleMenu( "GitHub Repo Installer" )

def getrawuser(user):

    r = requests.request("GET", "https://api.github.com/users/"+user+"/repos")

    rjson = r.json()

    return rjson

def cacheuserdata(data, filename):

    json.dump(data, open(filename, "w+"), indent=4)

def loadparseddata(filename):

    return json.load(open(filename, "r"))

def getpath(filename):

    return "/".join(path.abspath(__file__).split("/")[:-1])+"/"+filename

if __name__ == "__main__":

    rjn = getrawuser("r2boyo25")

    cacheuserdata(rjn, getpath("cache.json"))

    data = loadparseddata(getpath("cache.json"))

    divider = "#-----------------------------------------#"

    #repos

    for repo in data:

        #print("\n" + divider)

        menu.append_item(CommandItem(repo["name"], "git clone {}".format(repo["html_url"])))

        #print(divider)

    menu.show()
