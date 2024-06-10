from pathlib import Path
from typing import Any, cast


def _get_case_insensitive_path_internal(
    path: str, RET_FOUND: bool = False
) -> str | tuple[str, bool]:
    """
    Get a case insensitive path on a case sensitive system

    RET_FOUND is for internal use only, to avoid too many calls to
    os.path.exists

    from https://code.activestate.com/recipes/576571-case-insensitive-filename-on-nix-systems-return-th/  # noqa
    """

    import os

    if path == "" or os.path.exists(path):
        if RET_FOUND:
            return path, True

        else:
            return path

    f = os.path.basename(path)  # f may be a directory or a file
    d = os.path.dirname(path)

    suffix = ""

    if not f:  # dir ends with a slash?
        if len(d) < len(path):
            suffix = path[: len(path) - len(d)]

        f = os.path.basename(d)
        d = os.path.dirname(d)

    if not os.path.exists(d):
        d, found = _get_case_insensitive_path_internal(d, True)

        if not found:
            if RET_FOUND:
                return path, False
            else:
                return path

    # at this point, the directory exists but not the file

    try:  # we are expecting 'd' to be a directory, but it could be a file
        files = os.listdir(d)

    except Exception:
        if RET_FOUND:
            return path, False

        else:
            return path

    f_low = f.lower()

    try:
        f_nocase = [fl for fl in files if fl.lower() == f_low][0]

    except Exception:
        f_nocase = None

    if f_nocase:
        if RET_FOUND:
            return os.path.join(d, f_nocase) + suffix, True

        else:
            return os.path.join(d, f_nocase) + suffix

    else:
        if RET_FOUND:
            return path, False

        else:
            return path  # cant find the right one, just return the path as is.


def get_case_insensitive_path(path: str | Path) -> Path:
    """
    Get a case insensitive path on a case sensitive system

    # Example usage
    get_case_insensitive_path('/hOmE/mE/sOmEpAtH.tXt')
    """

    return Path(cast(str, _get_case_insensitive_path_internal(str(path))))
