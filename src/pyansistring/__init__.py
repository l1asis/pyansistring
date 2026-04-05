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

from .art_registry import DEFAULT_ART_REGISTRY, ArtRegistry, load_art_pack_toml
from .color import Color
from .constants import (
    COLOR_THEMES,
    COLORS_8BIT,
    DEFAULT_THEME,
    PUNCTUATION,
    PUNCTUATION_AND_WHITESPACE,
    SGR,
    UNIVERSAL_NEWLINES,
    WHITESPACE,
    Background,
    ColorDepth,
    Foreground,
    Regex,
    Underline,
    UnderlineMode,
)
from .core import ANSIString, Coordinate, CoordinateGroup, SliceGroup, SliceSpec
from .style import Style, StyleManager

__all__ = [
    "ANSIString",
    "Color",
    "ArtRegistry",
    "DEFAULT_ART_REGISTRY",
    "load_art_pack_toml",
    "Style",
    "StyleManager",
    "ColorDepth",
    "Foreground",
    "Background",
    "Underline",
    "UnderlineMode",
    "SGR",
    "COLORS_8BIT",
    "COLOR_THEMES",
    "DEFAULT_THEME",
    "WHITESPACE",
    "UNIVERSAL_NEWLINES",
    "PUNCTUATION",
    "PUNCTUATION_AND_WHITESPACE",
    "Regex",
    "SliceSpec",
    "SliceGroup",
    "Coordinate",
    "CoordinateGroup",
]
