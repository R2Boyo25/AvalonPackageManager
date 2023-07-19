import os

avalonpath = os.path.expanduser("~/.config/avalonpm/")

configpath = avalonpath + "config/"
binpath = avalonpath + "bin/"
filepath = avalonpath + "files/"

srcpath = os.path.expanduser("~/.cache/avalonpm/src/")
cachepath = os.path.expanduser("~/.cache/avalonpm/cache/")
tmppath = os.path.expanduser("~/.cache/avalonpm/tmp/")

_paths = [avalonpath, srcpath, binpath, cachepath, configpath, filepath, tmppath]

for _path in _paths:
    if not os.path.exists(_path):
        os.makedirs(_path)
