from __future__ import annotations

from collections.abc import (
    Iterable as _Iterable,
    Mapping as _Mapping,
    Sequence as _Sequence,
)
from random import Random as _Random
from typing import Any as _Any, Literal as _Literal, cast as _cast

from ._types import (
    ArtColoring,
    ColorGeneratorContext,
    ColorGeneratorFn,
    ColorSource,
    ColorStop,
    CoordinateGroup,
    SliceGroup,
)
from .color import Color as _Color, ColorScale as _ColorScale
from .core import ANSIString as _ANSIString

_COLOR_GENERATORS: dict[str, ColorGeneratorFn] = {}


def _is_rgb_triplet(value: object) -> bool:
    if not isinstance(value, (list, tuple)):
        return False

    sequence = _cast(_Sequence[_Any], value)
    return len(sequence) == 3 and all(isinstance(channel, int) for channel in sequence)


def _generate_banner_tree_colors(
    *,
    step_count: int,
    mode: _Literal["random", "seeded"],
    seed: int | None,
) -> list[tuple[int, int, int]]:
    rng = _Random(seed) if mode == "seeded" else _Random()
    return [
        (40 + rng.randint(-40, 0), 189 + rng.randint(-50, 50), 38)
        for _ in range(step_count)
    ]


def register_color_generator(name: str, generator: ColorGeneratorFn) -> None:
    _COLOR_GENERATORS[name] = generator


def unregister_color_generator(name: str) -> None:
    _COLOR_GENERATORS.pop(name, None)


def _derive_step_count(
    *,
    requested: int | None,
    art_mode: _Literal["gradient_coordinates", "gradient"],
    text: str | None,
    coordinates_count: int,
    slices_count: int,
    skip_whitespace: bool,
) -> int:
    if requested is not None:
        return max(2, requested)

    if art_mode == "gradient_coordinates":
        return max(2, coordinates_count)

    if slices_count:
        return max(2, slices_count)

    if text is not None:
        if skip_whitespace:
            derived = sum(1 for char in text if not char.isspace())
        else:
            derived = len(text)
        return max(2, derived)

    return 60


def _resolve_generator(
    *,
    colors: _Mapping[str, _Any],
    art_mode: _Literal["gradient_coordinates", "gradient"],
    text: str | None,
    coordinates_count: int,
    slices_count: int,
    skip_whitespace: bool,
) -> _ColorScale | list[ColorStop]:
    generator_name = colors.get("generator")
    if not isinstance(generator_name, str):
        raise TypeError("Expected color generator name to be a string")

    generator = _COLOR_GENERATORS.get(generator_name)
    if generator is None:
        raise ValueError(f"Unsupported color generator: {generator_name!r}")

    generator_mode = _cast(_Literal["random", "seeded"], colors.get("mode", "random"))
    if generator_mode not in {"random", "seeded"}:
        raise TypeError("Generator mode must be 'random' or 'seeded'")

    step_count_raw = colors.get("step_count")
    requested_step_count = (
        _cast(int | None, step_count_raw) if isinstance(step_count_raw, int) else None
    )
    seed_raw = colors.get("seed")
    if seed_raw is not None and not isinstance(seed_raw, int):
        raise TypeError("Generator seed must be an integer")

    step_count = _derive_step_count(
        requested=requested_step_count,
        art_mode=art_mode,
        text=text,
        coordinates_count=coordinates_count,
        slices_count=slices_count,
        skip_whitespace=skip_whitespace,
    )

    context: ColorGeneratorContext = {
        "generator": generator_name,
        "art_mode": art_mode,
        "generator_mode": generator_mode,
        "step_count": step_count,
        "text_length": len(text) if text is not None else 0,
        "skip_whitespace": skip_whitespace,
        "coordinates_count": coordinates_count,
        "slices_count": slices_count,
    }
    if seed_raw is not None:
        context["seed"] = seed_raw

    generated = generator(context)
    return _cast(_ColorScale | list[ColorStop], normalize_colors(generated))


def _normalize_static_colors(
    colors: ColorSource,
) -> _ColorScale | list[ColorStop]:
    if isinstance(colors, _ColorScale):
        return colors

    if isinstance(colors, _Color):
        return [colors]

    if _is_rgb_triplet(colors):
        return [_cast(tuple[int, int, int], tuple(colors))]

    normalized: list[ColorStop] = []
    for stop in _cast(_Iterable[_Any], colors):
        if isinstance(stop, _Color):
            normalized.append(stop)
            continue
        if _is_rgb_triplet(stop):
            normalized.append(_cast(tuple[int, int, int], tuple(stop)))
            continue
        raise TypeError("Expected color stop to be Color or an RGB tuple of 3 integers")

    return normalized


def normalize_colors(
    colors: ColorSource,
) -> ColorSource:
    if isinstance(colors, _Mapping):
        mapping = _cast(_Mapping[str, _Any], colors)

        generator_name = mapping.get("generator")
        if generator_name is not None:
            if not isinstance(generator_name, str):
                raise TypeError("Expected color generator name to be a string")
            if generator_name not in _COLOR_GENERATORS:
                raise ValueError(f"Unsupported color generator: {generator_name!r}")

            mode = mapping.get("mode", "random")
            if mode not in {"random", "seeded"}:
                raise TypeError("Expected generator mode to be 'random' or 'seeded'")

            step_count = mapping.get("step_count")
            if step_count is not None and not isinstance(step_count, int):
                raise TypeError("Expected generator step_count to be an integer")

            seed = mapping.get("seed")
            if seed is not None and not isinstance(seed, int):
                raise TypeError("Expected generator seed to be an integer")

            normalized_generator: dict[str, _Any] = {
                "generator": generator_name,
                "mode": mode,
            }
            if step_count is not None:
                normalized_generator["step_count"] = step_count
            if seed is not None:
                normalized_generator["seed"] = seed

            return _cast(ColorSource, normalized_generator)

        if "stops" in mapping:
            space = mapping.get("space", "hsl")
            if space not in {"rgb", "hsl"}:
                raise TypeError("Expected color scale space to be 'rgb' or 'hsl'")

            stops = mapping.get("stops")
            if not isinstance(stops, _Iterable) or isinstance(stops, (str, bytes)):
                raise TypeError("Expected color scale stops to be an iterable")

            parsed_stops: list[ColorStop] = []
            for stop in _cast(_Iterable[_Any], stops):
                if isinstance(stop, _Color):
                    parsed_stops.append(stop)
                    continue
                if _is_rgb_triplet(stop):
                    red, green, blue = _cast(tuple[int, int, int], tuple(stop))
                    parsed_stops.append((red, green, blue))
                    continue
                raise TypeError("Expected each color stop to be a Color or RGB triplet")

            return _ColorScale(parsed_stops, _cast(_Literal["rgb", "hsl"], space))

        raise TypeError("Expected colors mapping to include 'stops' or 'generator'")

    return _normalize_static_colors(colors)


def apply_coloring(text: _ANSIString, coloring: ArtColoring) -> _ANSIString:
    mode = coloring["mode"]
    coordinates: tuple[CoordinateGroup, ...] = _cast(
        tuple[CoordinateGroup, ...],
        coloring.get("coordinates", ()),
    )
    slices: tuple[SliceGroup, ...] = _cast(
        tuple[SliceGroup, ...],
        coloring.get("slices", ()),
    )
    skip_whitespace = bool(coloring.get("skip_whitespace", False))

    normalized_colors = normalize_colors(coloring["colors"])

    if isinstance(normalized_colors, _Mapping):
        normalized_colors = _resolve_generator(
            colors=_cast(_Mapping[str, _Any], normalized_colors),
            art_mode=mode,
            text=text.plain_text,
            coordinates_count=len(coordinates),
            slices_count=len(slices),
            skip_whitespace=skip_whitespace,
        )

    static_colors = _cast(_ColorScale | list[ColorStop], normalized_colors)

    if mode == "gradient_coordinates":
        text.gradient_coordinates(
            static_colors,
            *coordinates,
            fg=coloring.get("fg", True),
            bg=coloring.get("bg", False),
            ul=coloring.get("ul", False),
            space=coloring.get("space", "hsl"),
            index_base=coloring.get("index_base", 0),
            origin=coloring.get("origin", (0, 0)),
            system=coloring.get("system", "terminal"),
            on_out_of_bounds=coloring.get("on_out_of_bounds", "raise"),
        )
        return text

    text.gradient(
        static_colors,
        *slices,
        skip_whitespace=skip_whitespace,
        fg=coloring.get("fg", True),
        bg=coloring.get("bg", False),
        ul=coloring.get("ul", False),
        space=coloring.get("space", "hsl"),
    )
    return text


def color_art(plain_art: str, colorings: _Iterable[ArtColoring]) -> _ANSIString:
    art = _ANSIString(plain_art)
    for coloring in colorings:
        apply_coloring(art, coloring)
    return art


def build_colored_arts(
    plain_arts: _Mapping[str, str],
    art_colorings: _Mapping[str, _Iterable[ArtColoring]],
) -> dict[str, _ANSIString]:
    return {
        name: color_art(plain_art, art_colorings.get(name, ()))
        for name, plain_art in plain_arts.items()
    }


def _banner_tree_generator(
    context: ColorGeneratorContext,
) -> list[tuple[int, int, int]]:
    return _generate_banner_tree_colors(
        step_count=context["step_count"],
        mode=context["generator_mode"],
        seed=context.get("seed"),
    )


register_color_generator("banner_tree_v1", _banner_tree_generator)
