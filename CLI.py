import os
import sys

from pmUtil import installPackage, uninstallPackage, installLocalPackage, redoBin, updatePackage, installed, dlSrc, updateCache
from path import binpath, srcpath, cachepath, configpath, tmppath, filepath
from CLIParse import Parse
from version import version, cyear

before = f"Avalon Package Manager V{version} Copyright (C) {cyear} R2Boyo25"

p = Parse("apm", before = before, flagsAsArgumentsAfterCommand = True)

p.flag("update", short = "U", long = "update", help = "Reinstall APM dependencies")
p.flag("fresh", short = "f", long = "fresh", help = "Reinstall instead of updating")
p.flag("noinstall", long = "noinstall", help = "Only download, skip compilation and installation (Debug)")
p.flag("debug", short = "d", long = "debug", help = "Print debug output (VERY large amount of text)")


@p.command("gen")
def genPackage(flags, paths, *args):
    'Generate a package using AvalonGen'
    os.system(binpath + '/avalongen ' + " ".join([f"\"{i}\"" for i in sys.argv[2:]]))

@p.command('install')
def installFunction(flags, paths, *args):
    'Installs a package'
    installPackage(flags, paths, list(args))

@p.command('uninstall')
def uninstallFunction(flags, paths, *args):
    'Uninstalls a package'
    uninstallPackage(flags, paths, list(args))

@p.command("update", hidden = True)
def updatePackageCLI(*args):
    "Update to newest version of a repo, then recompile + reinstall program"
    updatePackage(*args)

@p.command("refresh")
def refreshCacheFolder(*args):
    "Refresh main repo cache"

    updateCache(*args)

#@p.command('installf')
#def installFileFunction(flags, paths, *args):
#    'Installs a package from a .apm file or .tar.gz archive'
#    installLocalPackage(flags, paths, list(args))

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
