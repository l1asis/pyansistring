from __future__ import annotations

__all__ = [
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

ColorStop: _TypeAlias = _Color | tuple[int, int, int]
Coordinate: _TypeAlias = tuple[int, int]
CoordinateGroup: _TypeAlias = Coordinate | tuple[Coordinate, ...]
SliceSpec: _TypeAlias = tuple[int, int] | tuple[int, int, int] | slice
SliceGroup: _TypeAlias = SliceSpec | tuple[SliceSpec, ...]
