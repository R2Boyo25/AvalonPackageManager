In `package` in `.avalon` in the program's repo, or `package` in `user/repo` in my main repo, this a list of the options:
```json
{
    "author": "R2Boyo25", # name of the author of the repo (required for installing from local)
    "repo": "AvalonPackageManager" # name of the repo (required for installing from local)
    "needsCompiled": true, # set to false if compilation not required (optional)
    "binname": "name_of_the_binary", # name of binary to be copied to ~/.config/avalonpm/bin/ (optional)
    "binfile": "path/to/the/binary/file" # (optional)
    "compileScript": "compile.sh", # name of script to be used to compile, run from root of repo, so if the file is in .avalon, use .avalon/compile.sh (can also be a python script) (optional)
    "installScript": "install.sh", # name of script to be used to install, run from root of repo, so if the file is in .avalon, use .avalon/install.sh (can also be a python script) (optional)
    "mvBinAfterInstallScript": false, # if needsCompiled, moves binary after install script instead of before, default is false (optional)
    "toCopy": [
        "file1",
        "file2",
        "dir1",
        "dir2"
    ], # files to be copied to the program's files folder (optional) (run after installScript)
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
