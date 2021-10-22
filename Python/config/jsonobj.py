import json
import os

class JsonObj:
    def __init__(self, text):
        self.location = text
        self.load(text)

    def __getitem__(self, item):
        self.load()
        return self.config[item]
    
    def __setitem__(self, item, value):
        self.load()
        self.config[item] = value
        self.dump()
    
    def load(self):
        with open(self.location, "r") as file:
            self.config = json.loads( file.read() )
    
    def dump(self):
        with open(self.location, "w") as file:
            file.write(
                json.dumps(
                    self.config, 
                    indent=4
                )
            )
    
    def keys(self):
        self.load()
        return self.config.keys()
