"""Generate SVG images for README usage snippets.

Produces files in ``images/usage`` for commonly documented features,
including styling, underline modes, rainbow, gradients, and colormaps.

Requires Consolas fonts installed at the standard Windows location.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fontTools.ttLib import TTFont  # type: ignore

from pyansistring import (
    SGR,
    ANSIString,
    Background,
    Channel,
    Chars,
    Coords,
    Foreground,
    NamedColors,
    Pattern,
    UnderlineMode,
    Words,
)
from pyansistring.color import ColorMap, ColorScale, SegmentedColorMap

# ── Font paths (Consolas family, standard Windows location) ────────────────
FONT_DIR = "C:\\Windows\\Fonts"
FONT_REG = os.path.join(FONT_DIR, "consola.ttf")
FONT_BOLD = os.path.join(FONT_DIR, "consolab.ttf")
FONT_ITAL = os.path.join(FONT_DIR, "consolai.ttf")
FONT_BI = os.path.join(FONT_DIR, "consolaz.ttf")
FONT_PX = 16

for fpath in (FONT_REG, FONT_BOLD, FONT_ITAL, FONT_BI):
    if not os.path.exists(fpath):
        sys.exit(f"Font not found: {fpath}")

reg = TTFont(FONT_REG)
bold = TTFont(FONT_BOLD)
ital = TTFont(FONT_ITAL)
bi = TTFont(FONT_BI)
examples: dict[str, tuple[ANSIString, bool]] = {}

OUT = os.path.join(os.path.dirname(__file__), "..", "images", "usage")
os.makedirs(OUT, exist_ok=True)


def write(name: str, svg: str) -> None:
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"  {name}")


def add(name: str, s: ANSIString, to_path: bool = True) -> None:
    examples[name] = (s, to_path)


# ── Unstyled text ─────────────────────────────────────────────────────────
add("unstyled.svg", ANSIString("Hello, World!"))


# ── Whole string styling ──────────────────────────────────────────────────
add(
    "whole.svg",
    ANSIString("Hello, World!")
    .fg(Foreground.YELLOW)
    .bg(Background.BLUE)
    .style(SGR.BOLD),
)


# ── Target Selectors: Slices ──────────────────────────────────────────────
add(
    "slice.svg",
    ANSIString("Hello, World!")
    .fg(Foreground.YELLOW, (0, 5), (7, 12))  # "Hello" and "World"
    .bg(Background.BLUE, (7, 12))  # "World"
    .style(SGR.BOLD, (7, 12)),  # "World"
)


# ── Target Selectors: Words ───────────────────────────────────────────────
add(
    "words.svg",
    ANSIString("Hello, World!")
    .fg(Foreground.YELLOW, Words(("Hello", "World")))
    .bg(Background.BLUE, Words(("World",)))
    .style(SGR.BOLD, Words(("Hello", "World"))),
)


# ── Target Selectors: Chars ───────────────────────────────────────────────
add(
    "chars.svg",
    ANSIString("Hello, World!")
    .bg((200, 50, 50), Chars(skip_whitespace=True))
    .fg(0),  # Black text for contrast
)


# ── Target Selectors: Regex Patterns ──────────────────────────────────────
add(
    "pattern.svg",
    ANSIString("Error 404: Not Found!")
    .fg(NamedColors.RED, Pattern(r"\d+"))
    .style(SGR.BOLD, Pattern(r"\d+")),
)


# ── Advanced Regex (Log Parsing) ──────────────────────────────────────────
add(
    "pattern_advanced.svg",
    ANSIString("Login: [WARN] User 'admin' failed from 192.168.1.50")
    .fg(Foreground.YELLOW, Pattern(r"\[WARN\]"))
    .fg(Foreground.CYAN, Pattern(r"'.*?'"))
    .style(SGR.UNDERLINE, Pattern(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")),  # IP Address
)


# ── SGR attributes ────────────────────────────────────────────────────────
add(
    "sgr.svg",
    ANSIString("Hello, World!").style(SGR.BOLD).style(SGR.UNDERLINE),
)


# ── 4-bit, 8-bit, and 24-bit colors ───────────────────────────────────────
add(
    "4bit.svg",
    ANSIString("Hello, World!").fg(Foreground.YELLOW).bg(Background.BLUE),
)

add(
    "8bit.svg",
    ANSIString("Hello, World!")
    .fg(11)  # Bright Yellow
    .bg(4)  # Blue
    .ul(74),  # Muted Sky Blue
)

add(
    "rgb.svg",
    ANSIString("Hello, World!")
    .fg((255, 255, 0))  # Bright Yellow
    .bg((0, 0, 238))  # Blue
    .ul((135, 175, 215)),  # Light Steel Blue
)

add(
    "named_colors.svg",
    ANSIString("Hello, World!")
    .fg(NamedColors.GOLD)
    .bg(NamedColors.MIDNIGHT_BLUE)
    .ul(NamedColors.CRIMSON)
    .style(UnderlineMode.CURLY),
)


# ── Underline modes ───────────────────────────────────────────────────────
add(
    "underline.svg",
    ANSIString("Hello, World!")
    .bg((255, 255, 255))  # White
    .ul((255, 0, 0))  # Red
    .style(UnderlineMode.DOUBLE),
)


# ── Rainbow Effect ────────────────────────────────────────────────────────
add(
    "rainbow.svg",
    ANSIString("Hello, World! This is rainbow text!").rainbow(),
)


# ── Gradient APIs ─────────────────────────────────────────────────────────
add(
    "gradient.svg",
    ANSIString("Hello, World! This is gradient text!").gradient(
        [(84, 161, 255), (233, 200, 216)],
    ),
)

add(
    "gradient_words.svg",
    ANSIString("Hello, colorful gradient world!").gradient(
        [(255, 99, 71), (255, 215, 0)],
        Words(
            (
                "Hello",
                "world",
            ),
            ignore_case=True,
        ),
    ),
)

add(
    "gradient_coordinates.svg",
    ANSIString("HELLO\nworld").gradient(
        [(255, 0, 120), (0, 200, 255)],
        Coords(
            ((1, 1), (2, 1), (3, 1), (4, 1), (5, 1)),
            index_base=1,
        ),
    ),
)


# ── Data-Driven Colormaps ─────────────────────────────────────────────────
ramp_text = "".join(f"{n:<5}" for n in range(0, 101, 10))
block_pattern = Pattern(r"\d+\s*")
cmap_seg = SegmentedColorMap(
    {0: NamedColors.LIME, 60: NamedColors.YELLOW, 90: NamedColors.RED}
)

add(
    "colormap_segmented.svg",
    ANSIString(ramp_text).colormap(cmap_seg, block_pattern, channel=Channel.BG).fg(0),
)

scale = ColorScale([(0, 255, 255), (255, 255, 0), (255, 0, 0)], space="hsl")
cmap_cont = ColorMap(scale, vmin=0, vmax=100)

add(
    "colormap_continuous.svg",
    ANSIString(ramp_text).colormap(cmap_cont, block_pattern, channel=Channel.BG).fg(0),
)


# ── Generate all SVGs ─────────────────────────────────────────────────────
print(f"Generating {len(examples)} SVG examples in {OUT}:")

for filename, (ansistr, to_path) in examples.items():
    svg = ansistr.to_svg(
        reg,
        font_size_px=FONT_PX,
        font_bold=bold,
        font_italic=ital,
        font_bold_italic=bi,
        convert_text_to_path=to_path,
    )
    write(filename, svg)

print(f"\nDone — {len(examples)} files written.")
