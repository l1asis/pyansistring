from __future__ import annotations

__all__ = [
    "ArtColoring",
    "ArtDefinition",
    "ArtMetadata",
    "ColorGeneratorContext",
    "ColorGeneratorFn",
    "ColorGeneratorSpec",
    "ColorScaleSpec",
    "ColorSource",
    "ColorStop",
    "Coordinate",
    "CoordinateGroup",
    "GradientCoordinatesColoring",
    "GradientSliceColoring",
    "SliceGroup",
    "SliceSpec",
]

from collections.abc import Callable as _Callable, Iterable as _Iterable
from typing import (
    Literal as _Literal,
    NotRequired as _NotRequired,
    TypeAlias as _TypeAlias,
    TypedDict as _TypedDict,
)

from .color import Color as _Color, ColorScale as _ColorScale

ColorStop: _TypeAlias = _Color | tuple[int, int, int]
Coordinate: _TypeAlias = tuple[int, int]
CoordinateGroup: _TypeAlias = Coordinate | tuple[Coordinate, ...]
SliceSpec: _TypeAlias = tuple[int, int] | tuple[int, int, int] | slice
SliceGroup: _TypeAlias = SliceSpec | tuple[SliceSpec, ...]


class GradientCoordinatesColoring(_TypedDict):
    mode: _Literal["gradient_coordinates"]
    colors: "ColorSource"
    coordinates: tuple[CoordinateGroup, ...]
    fg: _NotRequired[bool]
    bg: _NotRequired[bool]
    ul: _NotRequired[bool]
    space: _NotRequired[_Literal["rgb", "hsl"]]
    index_base: _NotRequired[int]
    origin: _NotRequired[tuple[int, int]]
    system: _NotRequired[_Literal["cartesian", "terminal"]]
    on_out_of_bounds: _NotRequired[_Literal["ignore", "clamp", "raise"]]


class GradientSliceColoring(_TypedDict):
    mode: _Literal["gradient"]
    colors: "ColorSource"
    slices: _NotRequired[tuple[SliceGroup, ...]]
    skip_whitespace: _NotRequired[bool]
    fg: _NotRequired[bool]
    bg: _NotRequired[bool]
    ul: _NotRequired[bool]
    space: _NotRequired[_Literal["rgb", "hsl"]]


ArtColoring: _TypeAlias = GradientCoordinatesColoring | GradientSliceColoring


class ColorScaleSpec(_TypedDict):
    space: _Literal["rgb", "hsl"]
    stops: list[tuple[int, int, int]] | list[list[int]]


class ColorGeneratorSpec(_TypedDict, total=False):
    generator: str
    mode: _NotRequired[_Literal["random", "seeded"]]
    seed: _NotRequired[int]
    step_count: _NotRequired[int]


class ColorGeneratorContext(_TypedDict):
    generator: str
    art_mode: _Literal["gradient_coordinates", "gradient"]
    generator_mode: _Literal["random", "seeded"]
    step_count: int
    text_length: int
    skip_whitespace: bool
    coordinates_count: int
    slices_count: int
    seed: _NotRequired[int]


ColorGeneratorFn: _TypeAlias = _Callable[
    [ColorGeneratorContext],
    _ColorScale | ColorStop | _Iterable[ColorStop] | ColorScaleSpec,
]


ColorSource: _TypeAlias = (
    _ColorScale | ColorStop | _Iterable[ColorStop] | ColorScaleSpec | ColorGeneratorSpec
)


class ArtMetadata(_TypedDict, total=False):
    name: str
    description: str
    source: str
    tags: list[str]
    version: str


class ArtDefinition(_TypedDict):
    plain_art: str
    colorings: tuple[ArtColoring, ...]
    metadata: _NotRequired[ArtMetadata]
