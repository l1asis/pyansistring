from __future__ import annotations

__all__ = [
    "ArtDefinition",
    "ArtMetadata",
    "ArtRegistry",
    "DEFAULT_ART_REGISTRY",
    "register_color_generator",
    "unregister_color_generator",
    "load_art_pack_toml",
    "normalize_art_coloring",
]

import tomllib as _tomllib
from collections.abc import (
    Iterable as _Iterable,
    Mapping as _Mapping,
    Sequence as _Sequence,
)
from importlib import resources as _resources
from pathlib import Path as _Path
from typing import Any as _Any, Literal as _Literal, cast as _cast

from pyansistring import _art_engine as _art_engine
from pyansistring._types import (
    ArtColoring,
    ArtDefinition,
    ArtMetadata,
    ColorGeneratorFn,
    ColorSource,
    Coordinate,
    CoordinateGroup,
    SliceGroup,
    SliceSpec,
)
from pyansistring.core import ANSIString as _ANSIString

_COLOR_SPACES = frozenset({"rgb", "hsl"})
_COORDINATE_SYSTEMS = frozenset({"terminal", "cartesian"})
_OUT_OF_BOUNDS_MODES = frozenset({"ignore", "clamp", "raise"})


def _is_int_sequence(value: object, length: int | None = None) -> bool:
    if not isinstance(value, _Sequence) or isinstance(value, (str, bytes)):
        return False

    sequence = _cast(_Sequence[_Any], value)

    if length is not None and len(sequence) != length:
        return False

    return all(isinstance(item, int) for item in sequence)


def _normalize_colors(colors: ColorSource) -> ColorSource:
    return _art_engine.normalize_colors(colors)


def _normalize_coordinate(value: object) -> Coordinate:
    if not _is_int_sequence(value, 2):
        raise TypeError("Expected an (x, y) coordinate")

    x, y = _cast(tuple[int, int], value)
    return (int(x), int(y))


def _normalize_coordinate_group(value: object) -> CoordinateGroup:
    if _is_int_sequence(value, 2):
        return _normalize_coordinate(value)

    if not isinstance(value, _Iterable) or isinstance(value, (str, bytes)):
        raise TypeError("Expected a coordinate or a group of coordinates")

    coordinates: list[Coordinate] = []
    for item in _cast(_Iterable[_Any], value):
        coordinates.append(_normalize_coordinate(item))
    return tuple(coordinates)


def _normalize_slice_spec(value: object) -> SliceSpec:
    if isinstance(value, slice):
        return _cast(SliceSpec, value)

    if not _is_int_sequence(value):
        raise TypeError("Expected a slice tuple or a slice object")

    sequence = _cast(_Sequence[_Any], value)
    if len(sequence) == 2:
        start, stop = sequence
        return (int(start), int(stop))

    if len(sequence) == 3:
        start, stop, step = sequence
        return (int(start), int(stop), int(step))

    raise TypeError("Expected a slice tuple or a slice object")


def _normalize_slice_group(value: object) -> SliceGroup:
    if isinstance(value, slice):
        return _cast(SliceGroup, value)

    if _is_int_sequence(value):
        return _normalize_slice_spec(value)

    if not isinstance(value, _Iterable) or isinstance(value, (str, bytes)):
        raise TypeError("Expected a slice or a group of slices")

    items = tuple(_cast(_Iterable[_Any], value))
    if not items:
        raise TypeError("Expected at least one slice in the group")

    normalized_slices: list[SliceSpec] = []
    for item in items:
        if isinstance(item, slice):
            normalized_slices.append(_cast(SliceSpec, item))
            continue

        if _is_int_sequence(item):
            normalized_slices.append(_normalize_slice_spec(_cast(object, item)))
            continue
        raise TypeError("Expected a slice or a group of slices")

    return tuple(normalized_slices)


def _normalize_space(value: object) -> _Literal["rgb", "hsl"]:
    if value not in _COLOR_SPACES:
        raise TypeError("Expected color space to be 'rgb' or 'hsl'")
    return _cast(_Literal["rgb", "hsl"], value)


def _normalize_origin(value: object) -> tuple[int, int]:
    if not _is_int_sequence(value, 2):
        raise TypeError("Expected origin to be an (x, y) coordinate")
    x, y = _cast(tuple[int, int], value)
    return (int(x), int(y))


def _normalize_coordinate_system(value: object) -> _Literal["terminal", "cartesian"]:
    if value not in _COORDINATE_SYSTEMS:
        raise TypeError("Expected system to be 'terminal' or 'cartesian'")
    return _cast(_Literal["terminal", "cartesian"], value)


def _normalize_on_out_of_bounds(
    value: object,
) -> _Literal["ignore", "clamp", "raise"]:
    if value not in _OUT_OF_BOUNDS_MODES:
        raise TypeError(
            "Expected on_out_of_bounds to be one of 'ignore', 'clamp', or 'raise'"
        )
    return _cast(_Literal["ignore", "clamp", "raise"], value)


def normalize_art_coloring(coloring: _Mapping[str, _Any]) -> ArtColoring:
    mode = coloring["mode"]

    if mode == "gradient_coordinates":
        space = _normalize_space(coloring.get("space", "hsl"))

        index_base = coloring.get("index_base", 0)
        if not isinstance(index_base, int):
            raise TypeError("Expected index_base to be an integer")

        return _cast(
            ArtColoring,
            {
                "mode": mode,
                "colors": _normalize_colors(coloring["colors"]),
                "coordinates": tuple(
                    _normalize_coordinate_group(group)
                    for group in _cast(_Iterable[_Any], coloring.get("coordinates", ()))
                ),
                "fg": bool(coloring.get("fg", True)),
                "bg": bool(coloring.get("bg", False)),
                "ul": bool(coloring.get("ul", False)),
                "space": space,
                "index_base": index_base,
                "origin": _normalize_origin(coloring.get("origin", (0, 0))),
                "system": _normalize_coordinate_system(
                    coloring.get("system", "terminal")
                ),
                "on_out_of_bounds": _normalize_on_out_of_bounds(
                    coloring.get("on_out_of_bounds", "raise")
                ),
            },
        )

    if mode == "gradient":
        space = _normalize_space(coloring.get("space", "hsl"))

        return _cast(
            ArtColoring,
            {
                "mode": mode,
                "colors": _normalize_colors(coloring["colors"]),
                "slices": tuple(
                    _normalize_slice_group(group)
                    for group in _cast(_Iterable[_Any], coloring.get("slices", ()))
                ),
                "skip_whitespace": bool(coloring.get("skip_whitespace", False)),
                "fg": bool(coloring.get("fg", True)),
                "bg": bool(coloring.get("bg", False)),
                "ul": bool(coloring.get("ul", False)),
                "space": space,
            },
        )

    raise ValueError(f"Unsupported art coloring mode: {mode!r}")


class ArtRegistry:
    def __init__(
        self,
        arts: _Mapping[str, ArtDefinition] | None = None,
    ) -> None:
        self._arts: dict[str, ArtDefinition] = {}
        if arts:
            for name, definition in arts.items():
                self.register_definition(name, definition)

    @classmethod
    def from_builtin(cls) -> "ArtRegistry":
        resource = _resources.files("pyansistring").joinpath("data/builtins.toml")
        with resource.open("rb") as file:
            data = _tomllib.load(file)

        registry = cls.from_mapping(data)

        # TOML multiline strings include a trailing newline before the
        # closing delimiter. Trim exactly one newline to keep plain art stable.
        for name in registry.names():
            definition = registry.definition(name)
            plain_art = definition["plain_art"].removesuffix("\n")
            registry.register(
                name,
                plain_art,
                colorings=definition["colorings"],
                metadata=definition.get("metadata"),
            )

        return registry

    @classmethod
    def from_toml(cls, path: str | _Path) -> "ArtRegistry":
        with _Path(path).open("rb") as file:
            data = _tomllib.load(file)
        return cls.from_mapping(data)

    @classmethod
    def from_mapping(cls, data: _Mapping[str, _Any]) -> "ArtRegistry":
        registry = cls()
        arts = data.get("arts", ())
        if not isinstance(arts, _Iterable) or isinstance(arts, (str, bytes)):
            raise TypeError("Expected 'arts' to be an array of art definitions")

        for item in _cast(_Iterable[_Any], arts):
            if not isinstance(item, _Mapping):
                raise TypeError("Each art definition must be a mapping")

            item_mapping = _cast(_Mapping[str, _Any], item)
            name = item_mapping.get("name")
            plain_art = item_mapping.get("plain_art")
            colorings = item_mapping.get("colorings", ())
            metadata = item_mapping.get("metadata")

            if not isinstance(name, str):
                raise TypeError("Each art definition must include a string 'name'")
            if not isinstance(plain_art, str):
                raise TypeError("Each art definition must include a string 'plain_art'")
            if not isinstance(colorings, _Iterable) or isinstance(
                colorings, (str, bytes)
            ):
                raise TypeError("'colorings' must be an iterable of coloring mappings")
            if metadata is not None and not isinstance(metadata, _Mapping):
                raise TypeError("'metadata' must be a mapping when provided")

            normalized_colorings = tuple(
                normalize_art_coloring(_cast(_Mapping[str, _Any], coloring))
                for coloring in _cast(_Iterable[_Any], colorings)
            )

            registry.register(
                name,
                plain_art,
                colorings=normalized_colorings,
                metadata=_cast(ArtMetadata | None, metadata),
            )

        return registry

    def register_definition(self, name: str, definition: ArtDefinition) -> None:
        self.register(
            name,
            definition["plain_art"],
            colorings=definition["colorings"],
            metadata=definition.get("metadata"),
        )

    def register(
        self,
        name: str,
        plain_art: str,
        *,
        colorings: _Iterable[ArtColoring] = (),
        metadata: ArtMetadata | None = None,
    ) -> None:
        definition = _cast(
            ArtDefinition,
            {
                "plain_art": plain_art,
                "colorings": tuple(
                    normalize_art_coloring(coloring) for coloring in colorings
                ),
                **({"metadata": metadata} if metadata is not None else {}),
            },
        )
        self._arts[name] = definition

    def names(self) -> tuple[str, ...]:
        return tuple(self._arts)

    def definition(self, name: str) -> ArtDefinition:
        return self._arts[name]

    def get_plain_art(self, name: str) -> str:
        return self._arts[name]["plain_art"]

    def get_colorings(self, name: str) -> tuple[ArtColoring, ...]:
        return self._arts[name]["colorings"]

    def get_metadata(self, name: str) -> ArtMetadata | None:
        return self._arts[name].get("metadata")

    def get_colored_art(self, name: str) -> _ANSIString:
        definition = self._arts[name]
        return _art_engine.color_art(definition["plain_art"], definition["colorings"])

    def build_colored_arts(self) -> dict[str, _ANSIString]:
        return {name: self.get_colored_art(name) for name in self._arts}


DEFAULT_ART_REGISTRY = ArtRegistry.from_builtin()


def load_art_pack_toml(path: str | _Path) -> ArtRegistry:
    return ArtRegistry.from_toml(path)


def register_color_generator(name: str, generator: ColorGeneratorFn) -> None:
    _art_engine.register_color_generator(name, generator)


def unregister_color_generator(name: str) -> None:
    _art_engine.unregister_color_generator(name)
