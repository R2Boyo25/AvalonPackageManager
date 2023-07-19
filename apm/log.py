import os
import sys
from typing import Optional

issilent = False
isDebug = False


class colors:
    OK = 6
    WARN = 3
    SUCCESS = 2
    FAIL = 1
    DEBUG = 5


def colorprint(*text: str, color: int = colors.OK) -> None:
    if not issilent:
        os.system(f"tput setaf {color}")

        print(" ".join(text))

        os.system("tput sgr0")


def success(*text: str) -> str:
    colorprint(*text, color=colors.SUCCESS)

    return " ".join(text)


def error(*text: str) -> str:
    colorprint(*text, color=colors.FAIL)

    return " ".join(text)


def note(*text: str) -> str:
    colorprint(*text, color=colors.OK)

    return " ".join(text)


def warn(*text: str) -> str:
    colorprint(*text, color=colors.WARN)

    return " ".join(text)


def debug(*text: str) -> str:
    if isDebug:
        colorprint(*text, color=colors.DEBUG)

    return " ".join(text)


def silent(toset: Optional[bool] = None) -> None:
    global issilent

    if toset is None:

        issilent = not issilent
        return

    issilent = toset
