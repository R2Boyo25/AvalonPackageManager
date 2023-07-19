import os
import sys


binDir = sys.argv[1]
srcDir = sys.argv[2]
binf = "apm"
filesFolder = srcDir


if not os.path.exists("bin"):
    os.mkdir("bin")


with open(f"bin/{binf}", "w") as avalonStarter:
    filecontent = f'''#!/usr/bin/env bash\n\nPYTHONPATH="$PYTHONPATH:{filesFolder}/" python3 {filesFolder}/apm/__main__.py "$@"'''
    avalonStarter.write(filecontent)
    os.system(f"chmod +x bin/{binf}")

try:
    with open(os.path.expanduser("~/.bashrc"), "r") as rbc:
        bashrc = rbc.read()
        if not binDir in bashrc:
            nbashrc = bashrc + f"""\nexport PATH="$PATH:{binDir}"\n"""
        else:
            nbashrc = bashrc

        with open(os.path.expanduser("~/.bashrc"), "w") as wbc:
            wbc.write(nbashrc)
except:
    print(f"Failed to add {binDir} to PATH\nPlease add it yourself.")
