"""
Contains NPackage.
"""

from typing import Any, Iterable


class NPackage:
    """Wrapper around JSON."""

    def __init__(self, data: dict[Any, Any]):
        self.idict = data

    def __getitem__(self, item: Any) -> None | Any:
        try:
            return self.idict[item]

        except KeyError:
            return None

    def __setitem__(self, item: Any, value: Any) -> None:
        self.idict[item] = value

    def keys(self) -> Iterable[Any]:
        """Returns the keys of the internal dictionary."""
        return self.idict.keys()

    def get(self, key: Any, default: Any | None = None) -> None | Any:
        """Return the value for key or return default if it doesn't exist."""
        return self.idict.get(key, default)

    def __str__(self) -> str:
        return str(self.idict)
