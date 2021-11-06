import os
import sys

try:
    binf = sys.argv[1]
    filesFolder = sys.argv[2]
    binDir = sys.argv[3]
    srcDir = sys.argv[4]
except:
    binDir = sys.argv[1]
    srcDir = sys.argv[2]
    binf = 'apm'
    filesFolder = srcDir
#pkgName = sys.argv[3]

with open(binf, "w") as avalonStarter:
    filecontent = f'''python3 {filesFolder}/main.py "$@"'''
    avalonStarter.write(filecontent)
    #os.system("chmod +x " + f"{binDir}/avalon")

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