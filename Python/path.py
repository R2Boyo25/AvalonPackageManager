import os

avalonpath = os.path.expanduser('~/.avalonPM')
srcpath = os.path.expanduser('~/.avalonPM/src')
binpath = os.path.expanduser('~/.avalonPM/bin')

_paths = [avalonpath, srcpath, binpath]

for _path in _paths:
    if not os.path.exists(_path)
    os.mkdir(_path)
