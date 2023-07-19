import requests, json

from typing import Any, Iterable


class NPackage:
    def __init__(self, d: dict[Any, Any]):
        self.idict = d

    def __getitem__(self, item: Any) -> None | Any:
        try:
            return self.idict[item]
        except:
            return None

    def __setitem__(self, item: Any, value: Any) -> None:
        self.idict[item] = value

    def keys(self) -> Iterable[Any]:
        return self.idict.keys()

    def __str__(self) -> str:
        return str(self.idict)
