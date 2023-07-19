import json
import os
from .jsonobj import JsonObj


class Cache(JsonObj):
    def __init__(self, location: str, config: dict[str, str]):
        super().__init__(config["cache"] + location)
