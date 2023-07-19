import json
import os
from .jsonobj import JsonObj


class Config(JsonObj):
    def __init__(self, location: str):
        super().__init__(location)
