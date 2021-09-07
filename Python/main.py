import requests, json
from os import path
import os

from package import Package
from pmUtil import *

def getRepos(user):

    r = requests.request("GET", "https://api.github.com/users/"+user+"/repos").json()

    return r

if __name__ == "__main__":

    repos = getRepos("r2boyo25")
    for i in repos:
        if isAvalonPackage(i):
            print('-----')
            for ii in Package(i):
                print(ii)
            print('-----')

