"""
XDG-relative paths for various purposes.
"""


import os
from pathlib import Path

# https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest#variables

xdg_path = Path(os.environ.get("HOME", "~")).expanduser()
xdg_config_dir = Path(
    os.environ.get("XDG_CONFIG_HOME", xdg_path / ".config")
).expanduser()
xdg_cache_dir = Path(os.environ.get("XDG_CACHE_HOME", xdg_path / ".cache")).expanduser()
temp_dir = Path(
    os.environ.get(
        "TMPDIR", os.environ.get("TEMP", os.environ.get("TMP", "/tmp"))
    )  # nosec B108
).expanduser()

avalon_root = xdg_config_dir / "avalonpm"
avalon_cache = xdg_cache_dir / "avalonpm"

paths = {
    "root": avalon_root,
    "src": avalon_cache / "src",
    "bin": Path(os.environ.get("AVALON_BIN", avalon_root / "bin")),
    "cache": avalon_cache / "cache",
    "files": avalon_root / "files",
    "tmp": temp_dir / "avalonpm",
}

for _, path in paths.items():
    path.mkdir(parents=True, exist_ok=True)
