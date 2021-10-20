import os

avalonpath = os.path.expanduser('~/.avalonPM')

if not os.path.exists(avalonpath):
    os.mkdir(avalonpath)