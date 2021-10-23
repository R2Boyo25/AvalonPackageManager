import os
import sys

binDir = sys.argv[1]
srcDir = sys.argv[2]
pkgName = sys.argv[3]

with open(f"{binDir}/avalon", "w") as avalonStarter:
    filecontent = f'''python3 {srcDir}/{pkgName}/Python/main.py "$@"'''

with open(os.path.expanduser('~/.bashrc'), 'r') as rbc:
    bashrc = rbc.read()
    if not binDir in bashrc:
        nbashrc = bashrc + f"\nexport $PATH=\"$PATH:{binDir}\""
    else:
        nbashrc = bashrc

    with open(os.path.expanduser('~/.bashrc'), 'w') as wbc:
        wbc.write(nbashrc)