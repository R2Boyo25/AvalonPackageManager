import os
import sys
from pathlib import Path

binDir = sys.argv[1]
srcDir = sys.argv[2]
binf = "apm"
filesFolder = srcDir

# Create the bin directory if it doesn't exist
binPath = Path("bin")
binPath.mkdir(parents=True, exist_ok=True)

# Create the shell script file
scriptPath = binPath / binf
if not scriptPath.exists():
    with scriptPath.open("w") as scriptFile:
        filecontent = f'''#!/usr/bin/env bash\n\nPYTHONPATH="$PYTHONPATH:{filesFolder}/" python3 {filesFolder}/apm/__main__.py "$@"'''
        scriptFile.write(filecontent)
        # Set file permissions to be executable
        scriptPath.chmod(0o755)  

# Update the .bashrc file
bashrcPath = Path("~/.bashrc").expanduser()
if bashrcPath.exists():
    with bashrcPath.open("r") as bashrcFile:
        bashrc = bashrcFile.read()
        if binDir not in bashrc:
            nbashrc = bashrc + f"""\nexport PATH="$PATH:{binDir}"\n"""
        else:
            nbashrc = bashrc

    with bashrcPath.open("w") as bashrcFile:
        bashrcFile.write(nbashrc)
else:
    print(f"Failed to add {binDir} to PATH\nPlease add it yourself.")
