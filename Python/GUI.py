import requests, json
from os import path
import os, sys
import PyQt5

from package import Package
from pmUtil import *
from path import *

def main():
    print("GUI not implemented. try --help for a list of commands")
    quit()
    repos = getRepos("r2boyo25")
    for i in repos:
        if isAvalonPackage(i):
            print('-----')
            for ii in Package(i):
                print(ii)
            print('-----')