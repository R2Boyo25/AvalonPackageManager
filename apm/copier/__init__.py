"""
Parse include files and check if files match the given patterns.

Uses gitignore syntax but is functionally the opposite of `.gitignore`s.
"""

from gitignore_parser import parse_gitignore

def copy_files(include_file: str, src: str, dst: str) -> None:
    """
    Copy files from src to dst following the patterns in `include_file`.
    """
    
    parsed = parse_gitignore(include_file)

    # walk files and check if they match parsed
