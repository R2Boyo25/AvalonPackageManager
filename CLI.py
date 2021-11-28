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

def genPackage(*args):
    os.system(binpath + '/avalongen ' + " ".join([f"\"{i}\"" for i in sys.argv[2:]]))

def genAPM(*args):
    os.system(binpath + '/avalongen ' + "apm " + " ".join([f"\"{i}\"" for i in sys.argv[2:]]))

def unpackAPM(*args):
    raise NotImplementedError
    os.system(binpath + '/avalongen ' + "unpack " + " ".join([f"\"{i}\"" for i in sys.argv[2:]]))

functions = {
    "install":{
        "help":"Installs a package",
        "func":installPackage
    },
    "uninstall":{
        "help":"Uninstalls a package",
        "func":uninstallPackage
    },
    "installf": {
        "help": "Installs package from file",
        "func": installLocalPackage
    },
    "gen": {
        "help": "Generates a package",
        "func": genPackage
    },
    "pack": {
        "help": "Package a package into a .apm package",
        "func": genAPM
    },
    "unpack": {
        "help": "Unpack a .apm package",
        "func": unpackAPM
    }
}

def main(args):
    if len(args) == 0:
        return
    
    elif args[0] == "--help" or args[0] == "-h" or args[0] == "help":
        helpCommand(args)
    
    elif args[0] in functions:
        functions[args[0]]["func"]((srcpath, binpath, cachepath, configpath, filepath, tmppath), args[1:])