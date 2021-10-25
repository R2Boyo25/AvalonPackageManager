In `package` in `.avalon` in the program's repo, or `package` in `user/repo` in my main repo, this a list of the options:
```json
{
    "needsCompiled": true, # set to false if compilation not required (optional)
    "binname": "bintobecopiedtobinfolderaftercompilation", # name of binary to be copied to ~/.avalonPM/bin/ (optional)
    "compileScript": "compile.sh", # name of script to be used to compile, run from root of repo, so if the file is in .avalon, use .avalon/compile.sh (can also be a python script) (optional)
    "installScript": "install.sh", # name of script to be used to install, run from root of repo, so if the file is in .avalon, use .avalon/install.sh (can also be a python script) (optional)
    "deps": {
        "apt": [
            "packagename",
            "packagename"
        ], # apt dependencies (optional)
        "avalon": [
            "user/repo",
            "user/repo"
        ] # avalon dependencies (optional)
    }, # (optional)
    "distros": [
        "Debian",
        "Ubuntu" # list supported distros, will not install on unsupported distros (optional) 
    ],
    "arches": [
        "amd64",
        "i386" # list supported CPU arches, will not install on unsupported arches (optional)
    ]
}
```