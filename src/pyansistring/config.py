import os as _os
import platform as _platform
import re as _re
import sys as _sys
from dataclasses import dataclass as _dataclass
from typing import Literal as _Literal

from .constants import ColorSupportLevel as _ColorSupportLevel

@_dataclass
class Config:
    format_mode: _Literal["standard", "compatible"] = "standard"

    def __post_init__(self):
        env_mode = _os.getenv("PYANSISTRING_FORMAT_MODE", self.format_mode)
        if env_mode in ("standard", "compatible"):
            self.format_mode = env_mode


config = Config()
