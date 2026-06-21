from __future__ import annotations

__all__ = [
    "FgInput",
    "BgInput",
    "UlInput",
    "ColorInput",
    "ColorStop",
    "Coordinate",
    "CoordinateGroup",
    "SliceGroup",
    "SliceSpec",
]

from typing import (
    TypeAlias as _TypeAlias,
)

from .color import Color as _Color
from .constants import (
    Background as _Background,
    Foreground as _Foreground,
    Palette8Bit as _Palette8Bit,
    Underline as _Underline,
)

ColorInput: _TypeAlias = _Color | tuple[int | int | int] | str | _Palette8Bit | int
FgInput: _TypeAlias = (
    _Foreground | _Palette8Bit | int | tuple[int, int, int] | str | _Color
)
BgInput: _TypeAlias = (
    _Background | _Palette8Bit | int | tuple[int, int, int] | str | _Color
)
UlInput: _TypeAlias = (
    _Underline | _Palette8Bit | int | tuple[int, int, int] | str | _Color
)
ColorStop: _TypeAlias = _Color | tuple[int, int, int]
Coordinate: _TypeAlias = tuple[int, int]
CoordinateGroup: _TypeAlias = Coordinate | tuple[Coordinate, ...]
SliceSpec: _TypeAlias = tuple[int, int] | tuple[int, int, int] | slice
SliceGroup: _TypeAlias = SliceSpec | tuple[SliceSpec, ...]
