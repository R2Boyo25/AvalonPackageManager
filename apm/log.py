"""
Logging utilities for Avalon.
"""

import os
from typing import Optional
from enum import Enum

IS_SILENT = False
IS_DEBUG = False


class Colors(Enum):
    "tput setaf colors"

    OK = 6
    WARN = 3
    SUCCESS = 2
    FAIL = 1
    DEBUG = 5


def colorprint(*text: str, color: Colors = Colors.OK) -> None:
    "Print `text` with the color `color` using `tput`"

    if not IS_SILENT:
        os.system(f"tput setaf {color.value}")  # nosec

        print(" ".join(text))

        os.system("tput sgr0")  # nosec


def success(*text: str) -> str:
    "Print a successful message"

    colorprint(*text, color=Colors.SUCCESS)

    return " ".join(text)


def error(*text: str) -> str:
    "Print an error"

    colorprint(*text, color=Colors.FAIL)

    return " ".join(text)


def note(*text: str) -> str:
    "Print a note"

    colorprint(*text, color=Colors.OK)

    return " ".join(text)


def warn(*text: str) -> str:
    "Print a warning"

    colorprint(*text, color=Colors.WARN)

    return " ".join(text)


def debug(*text: str) -> str:
    "Print a debug message, hidden if IS_DEBUG is False"

    if IS_DEBUG:
        colorprint(*text, color=Colors.DEBUG)

    return " ".join(text)


def silent(toset: Optional[bool] = None) -> None:
    "Silence the output."

    global IS_SILENT

    if toset is None:

        IS_SILENT = not IS_SILENT
        return

    IS_SILENT = toset
