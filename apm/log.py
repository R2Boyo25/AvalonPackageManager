"""
Logging utilities for Avalon.
"""

import os
import sys

from enum import Enum
from pathlib import Path

IS_SILENT = False
IS_DEBUG = False


class Colors(Enum):
    "tput setaf colors"

    OK = 6
    WARN = 3
    SUCCESS = 2
    FAIL = 1
    DEBUG = 5


def colorprint(*text: str | Path, color: Colors = Colors.OK) -> str:
    "Print `text` with the color `color` using `tput`"

    if not IS_SILENT:
        os.system(f"tput setaf {color.value}")  # nosec

        joined_text = " ".join(map(str, text))

        print(joined_text)

        os.system("tput sgr0")  # nosec

        return joined_text

    return ""


def success(*text: str | Path) -> str:
    "Print a successful message"

    return colorprint(*text, color=Colors.SUCCESS)


def error(*text: str | Path) -> str:
    "Print an error"

    return colorprint(*text, color=Colors.FAIL)


def fatal_error(*text: str | Path) -> None:
    "Print an error and exit."
    error(*text)
    sys.exit(1)


def note(*text: str | Path) -> str:
    "Print a note"

    return colorprint(*text, color=Colors.OK)


def warn(*text: str | Path) -> str:
    "Print a warning"

    return colorprint(*text, color=Colors.WARN)


def debug(*text: str | Path) -> str:
    "Print a debug message, hidden if IS_DEBUG is False"

    if IS_DEBUG:
        return colorprint(*text, color=Colors.DEBUG)

    return " ".join(map(str, text))
