"""
Logging utilities for Avalon.
"""

import os
import sys

from enum import Enum
from pathlib import Path

IS_SILENT = False # Flag to control whether to print messages or not
IS_DEBUG = False # Flag to control whether to print debug messages or not


# Enum class to represent text colors
class Colors(Enum):
    "tput setaf colors"

    OK = 6       # Success color
    WARN = 3     # Warning color
    SUCCESS = 2  # Successful message color
    FAIL = 1     # Error color
    DEBUG = 5    # Debug message color


# Function to print colored text
def colorprint(*text: str | Path, color: Colors = Colors.OK) -> str:
    "Print `text` with the color `color` using `tput`"

    if not IS_SILENT:  # Only print if not in silent mode
        os.system(f"tput setaf {color.value}")  # Set the text color using `tput`  # nosec

        joined_text = " ".join(map(str, text))  # Convert the input arguments to a single string

        print(joined_text)  # Print the colored text

        os.system("tput sgr0")  # Reset the text color using `tput`  # nosec

        return joined_text  # Return the colored text

    return ""  # Return an empty string if in silent mode


# Helper functions for printing different types of messages with specific colors
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

    if IS_DEBUG: # Only print debug messages if in debug mode
        return colorprint(*text, color=Colors.DEBUG)

    return " ".join(map(str, text)) # If not in debug mode, return the input arguments as a single string
