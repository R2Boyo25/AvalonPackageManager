import os
import sys

from pmUtil import installPackage, uninstallPackage, installLocalPackage, redoBin, updatePackage, installed, dlSrc, updateCache, getInstalledRepos
from path import binpath, srcpath, cachepath, configpath, tmppath, filepath
from CLIParse import Parse # type: ignore
from version import version, cyear
from changelog import get_package_versions, display_changelogs_packages

before = f"Avalon Package Manager V{version} Copyright (C) {cyear} R2Boyo25\nNOTE: options MUST be before command!"

p = Parse("apm", before = before, flagsAsArgumentsAfterCommand = True)

p.flag("update", short = "U", long = "update", help = "Reinstall APM dependencies")
p.flag("fresh", short = "f", long = "fresh", help = "Reinstall instead of updating")
p.flag("noinstall", long = "noinstall", help = "Only download, skip compilation and installation (Debug)")
p.flag("debug", short = "d", long = "debug", help = "Print debug output (VERY large amount of text)")
p.flag("machine", short = "m", long = "machine", help = "Disable user-facing features. Use in scripts and wrappers or things might break.")


freeze_changelogs = get_package_versions(getInstalledRepos([srcpath]))


def display_changes(machine: bool = False):
    if not machine:
        display_changelogs_packages(freeze_changelogs)


@p.command("gen")
def genPackage(flags, paths, *args):
    'Generate a package using AvalonGen'
    os.system(binpath + '/avalongen ' + " ".join([f"\"{i}\"" for i in sys.argv[2:]]))

@p.command('install')
def installFunction(flags, paths, *args):
    'Installs a package'
    
    installPackage(flags, paths, list(args))

    display_changes(flags.machine)

@p.command('uninstall')
def uninstallFunction(flags, paths, *args):
    'Uninstalls a package'
    uninstallPackage(flags, paths, list(args))

@p.command("update", hidden = True)
def updatePackageCLI(*args):
    "Update to newest version of a repo, then recompile + reinstall program"
    updatePackage(*args)

    display_changes(args[0].machine)

@p.command("refresh")
def refreshCacheFolder(*args):
    "Refresh main repo cache"

    updateCache(*args)

@p.command("pack")
def genAPM(*args):
    'Generate .apm file with AvalonGen'
    os.system(binpath + '/avalongen ' + "apm " + " ".join([f"\"{i}\"" for i in sys.argv[2:]]))

@p.command("unpack")
def unpackAPM(*args):
    'Unpack .apm file with AvalonGen'
    raise NotImplementedError
    #os.system(binpath + '/avalongen ' + "unpack " + " ".join([f"\"{i}\"" for i in sys.argv[2:]]))

@p.command("redobin", hidden = True)
def redoBinCopy(*args):
    redoBin(*args)

@p.command("installed")
def listInstalled(*args):
    "List installed packages"

    installed(*args)

@p.command("src")
def dlSrcCli(*args):
    "Download repo into folder"

    dlSrc(*args)

def main():

    p.run(extras = [srcpath, binpath, cachepath, configpath, filepath, tmppath])
