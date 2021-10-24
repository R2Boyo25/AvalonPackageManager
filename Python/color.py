import os

class colors:
    OK = 6
    WARN = 3
    SUCCESS = 2
    FAIL = 1
    DEBUG = 5

def colorprint(*text, color = colors.OK):
    os.system(f"tput setaf {color}")

    print(" ".join(text))

    os.system("tput sgr0")

def success(*text):
    colorprint(*text, color = colors.SUCCESS)

def error(*text):
    colorprint(*text, color = colors.FAIL)

def note(*text):
    colorprint(*text, color = colors.OK)

def warn(*text):
    colorprint(*text, color = colors.WARN)

def debug(*text):
    if isDebug:
        colorprint(*text, color = colors.DEBUG)

isDebug = False