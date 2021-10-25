import os
import sys

binDir = sys.argv[1]
srcDir = sys.argv[2]
pkgName = sys.argv[3]

with open(f"{binDir}/avalon", "w") as avalonStarter:
    filecontent = f'''python3 {srcDir}/{pkgName}/main.py "$@"'''
    avalonStarter.write(filecontent)
    os.system("chmod +x " + f"{binDir}/avalon")

try:
    with open(os.path.expanduser('~/.bashrc'), 'r') as rbc:
        bashrc = rbc.read()
        if not binDir in bashrc:
            nbashrc = f'''\nexport PATH="$PATH:{binDir}"\n''' + bashrc
        else:
            nbashrc = bashrc

        with open(os.path.expanduser('~/.bashrc'), 'w') as wbc:
            wbc.write(nbashrc)
except:
    print(f"Failed to add {binDir} to PATH\nPlease add it yourself.")