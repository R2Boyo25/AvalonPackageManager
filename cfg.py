from config.config import Config
from config.cache import Cache
from path import configpath, cachepath, srcpath, binpath

try:
    config = Config(configpath + '/config.json')
except:
    with open(configpath + '/config.json', "w") as f:
        f.write("{}")
    config = Config(configpath + '/config.json')
    
if config['cache'] != cachepath and config['cache']:
    cachepath = config['cache']
if config['src'] != srcpath and config['src']:
    srcpath = config['src']
if config['bin'] != binpath and config['bin']:
    binpath = config['bin']
