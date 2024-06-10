"""
Logging utilities for Avalon.
"""

import os
import sys

from enum import Enum
from pathlib import Path
from typing import NoReturn

IS_SILENT = False
IS_DEBUG = False


class Colors(Enum):
    "tput setaf colors"

    OK = 6  # White, by default
    WARN = 3  # Orange, by default
    SUCCESS = 2  # Green, by default
    FAIL = 1  # Red, by default
    DEBUG = 5  # Purple, by default


def colorprint(*text: str | Path, color: Colors = Colors.OK) -> str:
    "Print `text` with the color `color` using `tput`"

    joined_text = " ".join(map(str, text))

    if not IS_SILENT:
        os.system(
            f"tput setaf {color.value}"
        )  # Set the text color using `tput`  # nosec

        print(joined_text)

        os.system("tput sgr0")  # Reset the text color using `tput`  # nosec

    return joined_text


# Helper functions for printing different types of messages with specific colors
def success(*text: str | Path) -> str:
    "Print a successful message"

    return colorprint(*text, color=Colors.SUCCESS)


def error(*text: str | Path) -> str:
    "Print an error"

    return colorprint(*text, color=Colors.FAIL)


def fatal_error(*text: str | Path) -> NoReturn:
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
