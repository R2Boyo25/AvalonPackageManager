import json
import os
from config.jsonobj import JsonObj

class Cache(JsonObj):
    def __init__(self, text, config):
        super().__init__(config['cache'] + text)