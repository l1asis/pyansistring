from __future__ import annotations

__all__ = [
    "PLAIN_ARTS",
    "COLORED_ARTS",
    "ART_COLORINGS",
    "ArtColoring",
    "GradientCoordinatesColoring",
    "GradientSliceColoring",
    "apply_coloring",
    "color_art",
    "build_colored_arts",
]

from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from random import randint as _randint
from typing import Any as _Any, cast as _cast

from pyansistring._types import (
    ArtColoring,
    ColorStop,
    GradientCoordinatesColoring,
    GradientSliceColoring,
)
from pyansistring.color import Color as _Color, ColorScale as _ColorScale
from pyansistring.core import ANSIString as _ANSIString

PLAIN_ARTS = {
    "BANNER": (
        "                 ^___^           ░░░                                            \n"
        "                ╱ . .│          ░*░░░░░                                         \n"
        "           /‾\\__╱   ╲         ░░░░╲ ░.░░                ▄                       \n"
        "           ╰    ╲   ╱       ░░░░._╱╲╱░░░_                                       \n"
        "      ___________╲_╱ ╔▄▄▄▄▄   ░░░░\\*╲  ╱╱        ╭────╮  █▄-.-.---.--.-         \n"
        "     ╱     ╱         ║█╝  █╗    __ ╱ ╲╱╱*░░░     │   .╯ -.█▄---.-.----.-        \n"
        "    ╱     ╱ ╱    ╱   ║█▄▄▄█║   ╱╱╲╲  ╱╱╲ ╲░░     ╰────╮ ---█▄-.---.--.-- string \n"
        "   ╱ ‾‾‾‾‾ ╱    ╱    ╚█░  █║  ╱╱ ╱╲╲╱╱ ╱╲╱░░░░        │ -.-██▄ .----.--.        \n"
        "  ╱        ╲___╱      █░  █╝ ╱╱ ╱  ‾‾ ╱  ╲_.░░░ ╭─────╯ --.-███--.----.-        \n"
        " ╱            ╱              ‾ *   ░░╱╲_*░░░░░  ╰─.                             \n"
        "             ╱                    ░░.░░░░░░                                     \n"
        "            ╱                      ░░░ ░░░                                      "
    ),
    "MESSAGE": (
        "       .....    .     .    . . .     . . .    . . .     .     .      ....  ..   .\n"
        "        .      . .   .   .      .  .      .  .     .     .     .    ..    .. .   .\n"
        "       .      .   . .   . . . .   . . . .   .     .       .     .  .  .    .  .   .\n"
        "      .      .     .   .         .         .     .         .  .  ..   ..   ..  .   .\n"
        "     .      .           . . .     . . .   .    .                 ..    ..   ..  .   .  .\n"
        "  .....    .                             . . .                  .  .      ...     ... .\n"
        "                                                               .    .\n"
        "                                                               .    .\n"
        "                                                                 . .\n"
        "                  /\\___/__./      .....   .    .  ...\n"
        "                ./ /  /   /      /____/  / \\  /  /   \\\n"
        "               /  /  /   /      /    /  /   \\/  /    /\n"
        "               \\ /  /  ./      /    /  /    /  / .. /\n"
        "                .\\_/_ /.                          __\n"
        "                  /          /      ///   /   /  /\n"
        "                 /.         /     /   /  /   /  /__\n"
        "                /...       /     /   /  /   /  /\n"
        "            .../  ..      /___.  ///    ///   /___.\n"
        "          ... /                 ___\n"
        "             /          /   /  /   \\   /   /\n"
        "            /          /   /  /    /  /   /\n"
        "           /          /   /  /    /  /   /\n"
        "          .           \\__/   \\___/   \\__/\\_/\n"
        "                     __ /\n"
        "                    /  /\n"
        "                    \\./"
    ),
}


def _random_tree_gradient(step_count: int = 60) -> list[tuple[int, int, int]]:
    return [
        (40 + _randint(-40, 0), 189 + _randint(-50, 50), 38) for _ in range(step_count)
    ]


def _normalize_colors(
    colors: _ColorScale | ColorStop | _Iterable[ColorStop],
) -> _ColorScale | list[ColorStop]:
    if isinstance(colors, _ColorScale):
        return colors

    if isinstance(colors, _Color):
        return [colors]

    if (
        isinstance(colors, tuple)
        and len(colors) == 3
        and all(isinstance(channel, int) for channel in colors)
    ):
        return [_cast(tuple[int, int, int], colors)]

    normalized: list[ColorStop] = []
    for stop in colors:
        if isinstance(stop, _Color):
            normalized.append(stop)
            continue
        if isinstance(stop, tuple):
            normalized.append(stop)
            continue
        raise TypeError("Expected color stop to be Color or an RGB tuple of 3 integers")

    return normalized


def apply_coloring(text: _ANSIString, coloring: ArtColoring) -> _ANSIString:
    mode = coloring["mode"]
    normalized_colors = _normalize_colors(coloring["colors"])

    if mode == "gradient_coordinates":
        text.gradient_coordinates(
            normalized_colors,
            *coloring.get("coordinates", ()),
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
        normalized_colors,
        *coloring.get("slices", ()),
        skip_whitespace=coloring.get("skip_whitespace", False),
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


def _style_group_to_coloring(
    style_group: tuple[_Any, ...],
) -> ArtColoring:
    if len(style_group) == 2:
        colors, coordinates = style_group
        options: _Mapping[str, _Any] = {}
    elif len(style_group) == 3:
        colors, coordinates, raw_options = style_group
        if not isinstance(raw_options, _Mapping):
            raise TypeError("Expected style group options to be a mapping")
        options = _cast(_Mapping[str, _Any], raw_options)
    else:
        raise TypeError(
            "Expected style group as (colors, coordinates) or "
            "(colors, coordinates, options)"
        )

    return _cast(
        ArtColoring,
        {
            "mode": "gradient_coordinates",
            "colors": colors,
            "coordinates": coordinates,
            "fg": bool(options.get("fg", True)),
            "bg": bool(options.get("bg", False)),
            "ul": bool(options.get("ul", False)),
            "space": _cast(str, options.get("space", "hsl")),
            "on_out_of_bounds": _cast(str, options.get("on_out_of_bounds", "raise")),
        },
    )


ART_STYLE_CONFIGURATIONS = {
    "BANNER": (
        # /-----------/ CAT: CURRENT STYLING (BLACK CAT, GRADIENT BG)
        (
            _ColorScale([(255, 170, 50), (255, 70, 10)], "rgb"),
            (
                # Line 0 (including eyes for background)
                (17, 0), (18, 0), (19, 0), (20, 0), (21, 0),
                # Line 1 
                (16, 1), (17, 1), (18, 1), (19, 1), (20, 1), (21, 1),
                # Line 2
                (11, 2), (12, 2), (13, 2), (14, 2), (15, 2), (16, 2), (17, 2), (18, 2), (19, 2), (20, 2),
                # Line 3
                (11, 3), (12, 3), (16, 3), (17, 3), (20, 3),
                # Line 4
                (17, 4), (18, 4), (19, 4),
            ),
            {"bg": True, "fg": False},
        ),

        # /-----------/ CAT: GRAY BELLY
        (
            (231, 231, 231),
            (
                # Line 3
                (18, 3), (19, 3),
            ),
            {"bg": True, "fg": False},
        ),

        # /-----------/ CAT: BLACK OUTLINE
        (
            (0, 0, 0),
            (
                (17, 0), (18, 0), (19, 0), (20, 0), (21, 0),
                (16, 1), (21, 1),
                (11, 2), (12, 2), (13, 2), (14, 2), (15, 2), (16, 2), (20, 2),
                (11, 3), (16, 3), (20, 3),
                (17, 4), (18, 4), (19, 4),
            ),
            {"fg": True},
        ),

        # /-----------/ CAT: CYAN EYES
        (
            (0, 255, 255),
            (
                (18, 1), (20, 1),
            ),
            {"fg": True},
        ),

        # /-----------/ P LETTER: BLUE
        (
            _ColorScale([(0, 0, 255), (112, 196, 255)], "hsl"),
            (
                (1, 9),
                (2, 8),
                ((3, 7), (5, 7)),
                ((4, 6), (6, 7)),
                ((5, 5), (7, 7)),
                ((6, 4), (8, 7)),
                ((7, 4), (9, 7)),
                ((8, 4), (10, 6)),
                ((9, 4), (11, 5)),
                (10, 4),
                (11, 4),
                (12, 4),
                (13, 4),
                (14, 4),
                (15, 4),
                (16, 4),
            ),
        ),
        # /-----------/ Y LETTER: YELLOW
        (
            _ColorScale([(165, 125, 2), (213, 176, 56)], "hsl"),
            (
                (12, 11),
                (13, 10),
                (14, 9),
                ((15, 8), (14, 8)),
                ((16, 7), (13, 8)),
                ((17, 6), (12, 8)),
                (11, 8),
                (11, 7),
                (12, 6),
            ),
        ),
        # /-----------/ A LETTER: LEFT CELL
        (
            _ColorScale([(255, 166, 166), (255, 126, 126)], "hsl"),
            (
                (23, 5),
                (21, 4),
                (21, 5),
                (21, 6),
                (21, 7),
            ),
        ),
        # /-----------/ A LETTER: RIGHT CELL
        (
            _ColorScale([(255, 218, 110), (255, 233, 185)], "hsl"),
            ((27, 8), (27, 7), (27, 6), (27, 5)),
        ),
        # /-----------/ A LETTER: GRAY
        (
            _ColorScale([(100, 100, 100), (196, 184, 172)], "hsl"),
            (
                (22, 8),
                (22, 7),
                (22, 6),
                (22, 5),
                (22, 4),
                ((23, 4), (23, 6)),
                ((24, 4), (24, 6)),
                ((25, 4), (25, 6)),
                (26, 4),
                (26, 5),
                (26, 6),
                (26, 7),
                (26, 8),
            ),
        ),
        # /-----------/ N LETTER: TREE
        (
            _random_tree_gradient(),
            (
                (33, 0),
                (34, 0),
                (35, 0),
                (32, 1),
                (34, 1),
                (35, 1),
                (36, 1),
                (37, 1),
                (38, 1),
                (30, 2),
                (31, 2),
                (32, 2),
                (33, 2),
                (36, 2),
                (38, 2),
                (39, 2),
                (28, 3),
                (29, 3),
                (30, 3),
                (31, 3),
                (37, 3),
                (38, 3),
                (39, 3),
                (30, 4),
                (31, 4),
                (32, 4),
                (33, 4),
                (41, 5),
                (42, 5),
                (43, 5),
                (42, 6),
                (43, 6),
                (42, 7),
                (43, 7),
                (44, 7),
                (45, 7),
                (44, 8),
                (45, 8),
                (46, 8),
                (35, 9),
                (36, 9),
                (41, 9),
                (42, 9),
                (43, 9),
                (44, 9),
                (45, 9),
                (34, 10),
                (35, 10),
                (37, 10),
                (38, 10),
                (39, 10),
                (40, 10),
                (41, 10),
                (42, 10),
                (35, 11),
                (36, 11),
                (37, 11),
                (39, 11),
                (40, 11),
                (41, 11),
            ),
        ),
        # /-----------/ N LETTER: APPLES AND CHERRIES
        (
            (255, 46, 81),
            (
                (33, 1),
                (37, 2),
                (32, 3),
                (35, 4),
                (40, 5),
                (43, 8),
                (40, 9),
                (36, 10),
                (31, 9),
            ),
        ),
        # /-----------/ N LETTER: TREE BRANCHES
        (
            (150, 91, 35),
            (
                (34, 2),
                (33, 3),
                (34, 3),
                (35, 3),
                (36, 3),
                (34, 4),
                (36, 4),
                (35, 5),
                (37, 5),
                (39, 6),
                (41, 6),
                (33, 7),
                (39, 7),
                (40, 7),
                (41, 7),
                (32, 8),
                (38, 8),
                (41, 8),
                (42, 8),
                (37, 9),
                (38, 9),
                (39, 9),
            ),
        ),
        # /-----------/ N LETTER: CYAN
        (
            _ColorScale([(229, 255, 185), (114, 255, 185)], "hsl"),
            (
                (29, 8),
                (30, 7),
                (31, 6),
                (32, 5),
                (33, 5),
                (34, 6),
                (35, 7),
                (36, 7),
                (37, 6),
                (38, 5),
                (39, 4),
                (40, 3),
                (40, 4),
                (39, 5),
                (38, 6),
                (37, 7),
                (36, 8),
                (35, 8),
                (34, 7),
                (33, 6),
                (32, 6),
                (31, 7),
                (30, 8),
                (29, 9),
            ),
        ),
        # /-----------/ S LETTER: SNAKE
        (
            _ColorScale([(100, 100, 150), (225, 100, 150)], "hsl"),
            (
                (50, 9),
                (49, 9),
                (48, 9),
                (48, 8),
                (49, 8),
                (50, 8),
                (51, 8),
                (52, 8),
                (53, 8),
                (54, 8),
                (54, 7),
                (54, 6),
                (53, 6),
                (52, 6),
                (51, 6),
                (50, 6),
                (49, 6),
                (49, 5),
                (49, 4),
                (50, 4),
                (51, 4),
                (52, 4),
                (53, 4),
                (54, 4),
                (54, 5),
                (53, 5),
            ),
        ),
        # /-----------/ I LETTER: DOTS
        (
            (176, 226, 255),
            (
                (60, 4),
                (62, 4),
                (66, 4),
                (69, 4),
                (57, 5),
                (63, 5),
                (65, 5),
                (70, 5),
                (62, 6),
                (66, 6),
                (69, 6),
                (57, 7),
                (63, 7),
                (68, 7),
                (71, 7),
                (58, 8),
                (65, 8),
                (70, 8),
            ),
        ),
        # /-----------/ I LETTER: WATER
        (
            (22, 113, 217),
            (
                (59, 4),
                (61, 4),
                (63, 4),
                (64, 4),
                (65, 4),
                (67, 4),
                (68, 4),
                (70, 4),
                (56, 5),
                (60, 5),
                (61, 5),
                (62, 5),
                (64, 5),
                (66, 5),
                (67, 5),
                (68, 5),
                (69, 5),
                (71, 5),
                (56, 6),
                (57, 6),
                (58, 6),
                (61, 6),
                (63, 6),
                (64, 6),
                (65, 6),
                (67, 6),
                (68, 6),
                (70, 6),
                (71, 6),
                (56, 7),
                (58, 7),
                (64, 7),
                (65, 7),
                (66, 7),
                (67, 7),
                (69, 7),
                (70, 7),
                (56, 8),
                (57, 8),
                (59, 8),
                (63, 8),
                (64, 8),
                (66, 8),
                (67, 8),
                (68, 8),
                (69, 8),
                (71, 8),
            ),
        ),
        # /-----------/ I LETTER: MOON AND REFLECTION
        (
            _ColorScale([(84, 161, 255), (192, 209, 255)], "hsl"),
            (
                (56, 2),
                (57, 4),
                (58, 4),
                (58, 5),
                (59, 5),
                (59, 6),
                (60, 6),
                (59, 7),
                (60, 7),
                (61, 7),
                (60, 8),
                (61, 8),
                (62, 8),
            ),
        ),
    )
}

ART_COLORINGS: dict[str, tuple[ArtColoring, ...]] = {
    art_name: tuple(
        _style_group_to_coloring(style_group) for style_group in style_groups
    )
    for art_name, style_groups in ART_STYLE_CONFIGURATIONS.items()
}

COLORED_ARTS = build_colored_arts(PLAIN_ARTS, ART_COLORINGS)

if __name__ == "__main__":
    print(COLORED_ARTS["BANNER"])
