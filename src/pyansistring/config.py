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


def _env_force_color() -> _ColorSupportLevel | None:
    """
    Determine the color support level from the FORCE_COLOR environment variable.

    Evaluates `FORCE_COLOR` according to community standards. "true" or an
    empty string defaults to 4-bit support. Numeric values 1, 2, and 3 map
    to 4-bit, 8-bit, and 24-bit TrueColor respectively. "false" or "0"
    disables color entirely.

    Returns
    -------
    ColorSupportLevel | None
        The corresponding color support level if `FORCE_COLOR` is present
        and valid, otherwise `None`.
    """
    if "FORCE_COLOR" not in _os.environ:
        return None

    val = _os.environ["FORCE_COLOR"]
    if val.lower() == "true":
        return _ColorSupportLevel.BIT4
    if val.lower() == "false":
        return _ColorSupportLevel.NONE
    if not val:
        return _ColorSupportLevel.BIT4

    try:
        level = min(int(val), 3)
        if level in [0, 1, 2, 3]:
            return _ColorSupportLevel(level)
    except ValueError:
        pass

    return None
@_dataclass
class Config:
    format_mode: _Literal["standard", "compatible"] = "standard"

    def __post_init__(self):
        env_mode = _os.getenv("PYANSISTRING_FORMAT_MODE", self.format_mode)
        if env_mode in ("standard", "compatible"):
            self.format_mode = env_mode


config = Config()
