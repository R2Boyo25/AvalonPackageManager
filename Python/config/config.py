import json
import os
from jsonobj import JsonObj

class Config(JsonObj):
    def __init__(self, text):
        super().__init__(text)