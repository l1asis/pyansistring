"""
pyansistring - A library for string color styling using ANSI escape sequences.

This library provides a string class that inherits from Python's str and supports
ANSI styling while preserving string methods. It supports 4-, 8-, and 24-bit color
modes, per-word coloring, alignment, and automated coloring features.
"""

from importlib.metadata import PackageNotFoundError, version

__name__ = "pyansistring"

try:
    __version__ = version("pyansistring")
except PackageNotFoundError:
    __version__ = "unknown"

from .color import Color
from .config import Config, config
from .constants import (
    BIT8_TO_RGB,
    COLOR_THEMES,
    PUNCTUATION,
    PUNCTUATION_AND_WHITESPACE,
    SGR,
    UNIVERSAL_NEWLINES,
    WHITESPACE,
    Background,
    Bit8Index,
    Channel,
    ColorSupportLevel,
    Foreground,
    NamedColors,
    Regex,
    Underline,
    UnderlineMode,
)
from .core import ANSIString, Coordinate, CoordinateGroup, SliceGroup, SliceSpec
from .style import Style, StyleManager
from .targets import Chars, Coords, Pattern, Words

__all__ = [
    "__version__",
    "ANSIString",
    "Color",
    "Channel",
    "Style",
    "StyleManager",
    "ColorSupportLevel",
    "Foreground",
    "Background",
    "Underline",
    "UnderlineMode",
    "SGR",
    "NamedColors",
    "Bit8Index",
    "BIT8_TO_RGB",
    "COLOR_THEMES",
    "WHITESPACE",
    "UNIVERSAL_NEWLINES",
    "PUNCTUATION",
    "PUNCTUATION_AND_WHITESPACE",
    "Regex",
    "SliceSpec",
    "SliceGroup",
    "Coordinate",
    "CoordinateGroup",
    "Chars",
    "Coords",
    "Pattern",
    "Words",
    "Config",
    "config",
]
