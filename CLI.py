import os
import sys

from pmUtil import installPackage, uninstallPackage, installLocalPackage
from path import binpath, srcpath, cachepath, configpath, tmppath, filepath
from CLIParse import Parse
from version import version, cyear

before = f"Avalon Package Manager V{version} Copyright (C) {cyear} R2Boyo25"

p = Parse("apm", before = before)

p.flag("update", short = "U", long = "update", help = "Reinstall APM dependencies")
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

@p.command('installf')
def installFileFunction(flags, paths, *args):
    'Installs a package from a .apm file or .tar.gz archive'
    installLocalPackage(flags, paths, list(args))

@p.command("pack")
def genAPM(*args):
    'Generate .apm file with AvalonGen'
    os.system(binpath + '/avalongen ' + "apm " + " ".join([f"\"{i}\"" for i in sys.argv[2:]]))

@p.command("unpack")
def unpackAPM(*args):
    'Unpack .apm file with AvalonGen'
    raise NotImplementedError
    #os.system(binpath + '/avalongen ' + "unpack " + " ".join([f"\"{i}\"" for i in sys.argv[2:]]))

def main():

    p.run(extras = [srcpath, binpath, cachepath, configpath, filepath, tmppath])
