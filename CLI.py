import requests, json
from os import path
import os, sys

from package import Package
from pmUtil import *
from path import *
from cfg import *

def getLongest(things):
    longestThing = 0
    for thing in things:
        if len(thing) > longestThing:
            longestThing = len(thing)
    return longestThing

def getPadded(thing, longest):
    padamount = ( longest ) - len(thing)
    return thing + ( " " * padamount )

def helpCommand(args):
    if len(args) == 1:
        longest = getLongest(functions)
        for func in functions:
            print(getPadded(func, longest), ":", functions[func]['help'])
    else:
        print(functions[args[0]]['help'])

def genPackage():
    os.system('avalongen ' + " ".join([f"\"{i}\"" for i in sys.argv[2:]]))

functions = {
    "install":{
        "help":"Installs a package",
        "func":installPackage
    },
    "uninstall":{
        "help":"Uninstalls a package",
        "func":uninstallPackage
    },
    "gen": {
        "help": "Generates a package",
        "func": genPackage
    }
}

def main(args):
    if len(args) == 0:
        return
    
    elif args[0] == "--help" or args[0] == "-h":
        helpCommand(args)
    
    elif args[0] in functions:
        functions[args[0]]["func"]((srcpath, binpath, cachepath, configpath, filepath), args[1:])