import os

avalonpath = os.path.expanduser('~/.avalonPM')
srcpath = os.path.expanduser('~/.avalonPM/src')
binpath = os.path.expanduser('~/.avalonPM/bin')
cachepath = os.path.expanduser('~/.avalonPM/cache')

_paths = [avalonpath, srcpath, binpath, cachepath]

for _path in _paths:
    if not os.path.exists(_path):
        os.mkdir(_path)
