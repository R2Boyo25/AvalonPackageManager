import requests, json
from os import path
import os, sys

from package import Package
from pmUtil import *
from path import *

def helpCommand(args):
    if len(args) == 1:
        for func in functions:
            print()
    else:
        print(functions[args[0]]['help'])

def main(args):
    if len(args) == 0:
        return
    
    elif args[0] == "--help" or "-h":
        helpCommand(args)
    
    elif args[0] in functions:
        functions[args[0]]["func"]()