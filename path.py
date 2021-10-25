import os

avalonpath = os.path.expanduser('~/.avalonPM/')
srcpath = os.path.expanduser(avalonpath + 'src/')
binpath = os.path.expanduser(avalonpath + 'bin/')
cachepath = os.path.expanduser(avalonpath + 'cache/')
configpath = os.path.expanduser(avalonpath + "config/")
filepath = os.path.expanduser(avalonpath + 'files/')

_paths = [avalonpath, srcpath, binpath, cachepath, configpath, filepath]

for _path in _paths:
    if not os.path.exists(_path):
        os.mkdir(_path)
