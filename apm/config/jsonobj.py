import json
import os

from typing import Any


class JsonObj:
    def __init__(self, location: str):
        self.location = location
        self.load()

    def __getitem__(self, item: Any) -> Any:
        self.load()

        try:
            return self.config[item]

        except:
            return False

    def __setitem__(self, item: Any, value: Any) -> None:
        self.load()
        self.config[item] = value
        self.dump()

    def load(self) -> None:
        with open(self.location, "r") as file:
            self.config = json.loads(file.read())

    def dump(self) -> None:
        with open(self.location, "w") as file:
            file.write(json.dumps(self.config, indent=4))

    def keys(self) -> Any:
        self.load()

        return self.config.keys()
