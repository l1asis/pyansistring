"""
Generate example SVG images from the ANSIString usage examples in the README.

Produces SVG files in images/usage/ that visualise each styling technique
described in the README.

Requires Consolas fonts installed at the standard Windows location.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fontTools.ttLib import TTFont  # type: ignore

from pyansistring import ANSIString
from pyansistring.constants import SGR, Background, Foreground, UnderlineMode

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
examples: dict[str, ANSIString] = {}

OUT = os.path.join(os.path.dirname(__file__), "..", "images", "usage")
os.makedirs(OUT, exist_ok=True)


def write(name: str, svg: str) -> None:
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"  {name}")


def add(name: str, s: ANSIString):
    examples[name] = s


# ── Unstyled text ─────────────────────────────────────────────────────────
add("unstyled.svg", ANSIString("Hello, World!"))

# ── Styling the whole string ──────────────────────────────────────────────
add(
    "whole.svg",
    ANSIString("Hello, World!")
    .fg_4b(Foreground.YELLOW)
    .bg_4b(Background.BLUE)
    .style(SGR.BOLD),
)

# ── Styling by index slice ────────────────────────────────────────────────
add(
    "slice.svg",
    ANSIString("Hello, World!")
    .fg_4b(Foreground.YELLOW, (0, 5), (7, 12))  # "Hello" and "World"
    .bg_4b(Background.BLUE, (7, 12))  # "World"
    .style(SGR.BOLD, (7, 12)),  # "World"
)

# ── Styling by word ───────────────────────────────────────────────────────
add(
    "words.svg",
    ANSIString("Hello, World!")
    .fg_4b_w(Foreground.YELLOW, "Hello", "World")
    .bg_4b_w(Background.BLUE, "World")
    .style_w(SGR.BOLD, "Hello", "World"),
)

# ── SGR formatting (bold + underline) ─────────────────────────────────────
add(
    "sgr.svg",
    ANSIString("Hello, World!").style(SGR.BOLD).style(SGR.UNDERLINE),
)

# ── 4-bit colour ──────────────────────────────────────────────────────────
add(
    "4bit.svg",
    ANSIString("Hello, World!").fg_4b(Foreground.YELLOW).bg_4b(Background.BLUE),
)

# ── 8-bit colour ──────────────────────────────────────────────────────────
add(
    "8bit.svg",
    ANSIString("Hello, World!")
    .fg_8b(11)  # Bright Yellow
    .bg_8b(4)  # Blue
    .ul_8b(74),  # Muted Sky Blue
)

# ── 24-bit (true colour) ──────────────────────────────────────────────────
add(
    "rgb.svg",
    ANSIString("Hello, World!")
    .fg_24b(255, 255, 0)  # Bright Yellow
    .bg_24b(0, 0, 238)  # Blue
    .ul_24b(135, 175, 215),  # Light Steel Blue
)

# ── Underline modes ───────────────────────────────────────────────────────
add(
    "underline.svg",
    ANSIString("Hello, World!")
    .bg_24b(255, 255, 255)  # White
    .ul_24b(255, 0, 0)  # Red
    .style(UnderlineMode.DOUBLE),
)

# ── Rainbow ───────────────────────────────────────────────────────────────
add(
    "rainbow.svg",
    ANSIString("Hello, World! This is rainbow text!").rainbow(fg=True),
)

# ── Multicolor ────────────────────────────────────────────────────────────
add(
    "multicolor.svg",
    ANSIString("Hello, World! This is multicolor text!").multicolor(
        (
            "r=0:|g=0:|b=255:   $ "  # Start with blue
            "b>0:repeat(auto)   # "  # Decrease blue
            "r>255:repeat(auto) | "  # Increase green and combine with...
            "g>255:repeat(auto)   "  # Increase red
            "                   &*"  # Cycle & Start without apply flags
        )
    ),
)


# ── Generate all SVGs ─────────────────────────────────────────────────────
print(f"Generating {len(examples)} SVG examples in {OUT}:")

for filename, ansistr in examples.items():
    svg = ansistr.to_svg(
        reg,
        font_size_px=FONT_PX,
        font_bold=bold,
        font_italic=ital,
        font_bold_italic=bi,
        convert_text_to_path=True,
    )
    write(filename, svg)

print(f"\nDone — {len(examples)} files written.")
