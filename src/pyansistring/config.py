import os as _os
import platform as _platform
import re as _re
import sys as _sys
from dataclasses import dataclass as _dataclass
from typing import Literal as _Literal

from .constants import ColorSupportLevel as _ColorSupportLevel


def _get_flags() -> set[str]:
    """
    Retrieve command-line flags passed to the host process.

    Parses `sys.argv` to extract all arguments starting with a hyphen (`-`).
    Stops parsing if the double-hyphen terminator (`--`) is encountered,
    as subsequent arguments are treated as positional.

    Returns
    -------
    set[str]
        A set containing the extracted command-line flags in lowercase.
    """
    if not hasattr(_sys, "argv"):
        return set()
    try:
        term_pos = _sys.argv.index("--")
        args = _sys.argv[1:term_pos]
    except ValueError:
        args = _sys.argv[1:]

    return {arg.lower() for arg in args if arg.startswith("-")}

@_dataclass
class Config:
    format_mode: _Literal["standard", "compatible"] = "standard"

    def __post_init__(self):
        env_mode = _os.getenv("PYANSISTRING_FORMAT_MODE", self.format_mode)
        if env_mode in ("standard", "compatible"):
            self.format_mode = env_mode


config = Config()
