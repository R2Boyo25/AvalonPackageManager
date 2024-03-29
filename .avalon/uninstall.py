import os
import sys

binDir = sys.argv[3]

with open(os.path.expanduser("~/.bashrc"), "r") as rbc:
    bashrc = rbc.read()
    if binDir in bashrc:
        nbashrc = bashrc.replace(f'''\nexport PATH="$PATH:{binDir}"''', "")
    else:
        nbashrc = bashrc

    with open(os.path.expanduser("~/.bashrc"), "w") as wbc:
        wbc.write(nbashrc)

os.remove(binDir + "/apm")

os.system(f"rm -rf {os.path.expanduser('~/.avalonPM')}")
