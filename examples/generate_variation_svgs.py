"""
Generate example SVG images for various ANSIString styling scenarios.

Produces a set of SVG files in tests/untracked/svg_output/ that demonstrate:
- Regular, bold, italic, bold-italic, dim text
- Faux bold/italic fallback vs dedicated font files
- Variable spacing, underline modes, colours
- Mixed styles on a single string
- Rainbow and multicolor effects

Requires Consolas fonts installed at the standard Windows location.
"""

import os
import sys
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fontTools.ttLib import TTFont  # type: ignore

from pyansistring import ANSIString
from pyansistring.constants import SGR, UnderlineMode

# ---------------------------------------------------------------------------
# Font paths (Consolas family, standard Windows location)
# ---------------------------------------------------------------------------
FONT_DIR = r"C:\Windows\Fonts"
FONT_REG = os.path.join(FONT_DIR, "consola.ttf")
FONT_BOLD = os.path.join(FONT_DIR, "consolab.ttf")
FONT_ITAL = os.path.join(FONT_DIR, "consolai.ttf")
FONT_BI = os.path.join(FONT_DIR, "consolaz.ttf")
FONT_PX = 20

for fpath in (FONT_REG, FONT_BOLD, FONT_ITAL, FONT_BI):
    if not os.path.exists(fpath):
        sys.exit(f"Font not found: {fpath}")

reg = TTFont(FONT_REG)
bold = TTFont(FONT_BOLD)
ital = TTFont(FONT_ITAL)
bi = TTFont(FONT_BI)
examples: dict[str, tuple[ANSIString, dict[str, Any]]] = {}

OUT = os.path.join(os.path.dirname(__file__), "images", "svg")
os.makedirs(OUT, exist_ok=True)


def write(name: str, svg: str) -> None:
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"  {name}")


def add(name: str, s: ANSIString, /, **kw: Any) -> None:
    examples[name] = (s, kw)


# ── 1. Basic text styles (path mode, faux fallback) ───────────────────────
add("01_regular.svg", ANSIString("Hello, World!"))

add("02_bold_faux.svg", ANSIString("Hello, World!").style(SGR.BOLD))

add("03_italic_faux.svg", ANSIString("Hello, World!").style(SGR.ITALIC))

add(
    "04_bold_italic_faux.svg",
    ANSIString("Hello, World!").style(SGR.BOLD).style(SGR.ITALIC),
)

add("05_dim_faux.svg", ANSIString("Hello, World!").style(SGR.DIM))


# ── 2. Dedicated font files ───────────────────────────────────────────────
add("06_bold_font.svg", ANSIString("Hello, World!").style(SGR.BOLD), font_bold=bold)

add(
    "07_italic_font.svg",
    ANSIString("Hello, World!").style(SGR.ITALIC),
    font_italic=ital,
)

add(
    "08_bold_italic_font.svg",
    ANSIString("Hello, World!").style(SGR.BOLD).style(SGR.ITALIC),
    font_bold=bold,
    font_italic=ital,
    font_bold_italic=bi,
)

add("09_dim_same_as_regular.svg", ANSIString("Hello, World!").style(SGR.DIM))


# ── 3. Mixed styles in one string ─────────────────────────────────────────
add(
    "10_mixed_bold_italic.svg",
    ANSIString("Bold Italic Normal").style(SGR.BOLD, (0, 4)).style(SGR.ITALIC, (5, 11)),
    font_bold=bold,
    font_italic=ital,
)

add(
    "11_partial_bold.svg",
    ANSIString("Hello, World!").style(SGR.BOLD, (7, 12)),
    font_bold=bold,
)


# ── 4. Foreground colours ─────────────────────────────────────────────────
add("12_fg_red.svg", ANSIString("Hello, World!").fg_24b(255, 50, 50))

add(
    "13_fg_partial.svg",
    ANSIString("Hello, World!")
    .fg_24b(255, 50, 50, (0, 5))
    .fg_24b(50, 50, 255, (7, 12)),
)

add(
    "14_fg_bold_coloured.svg",
    ANSIString("Hello, World!").style(SGR.BOLD).fg_24b(0, 180, 0),
    font_bold=bold,
)


# ── 5. Background colours ─────────────────────────────────────────────────
add("15_bg_yellow.svg", ANSIString("Hello, World!").bg_24b(255, 255, 100))

add(
    "16_fg_bg_combined.svg",
    ANSIString("Hello, World!").fg_24b(255, 255, 255).bg_24b(40, 40, 40),
)


# ── 6. Underline styles (path mode) ───────────────────────────────────────
add("17_underline_single.svg", ANSIString("Underlined text").style(SGR.UNDERLINE))

add(
    "18_underline_double.svg",
    ANSIString("Double underline").style(SGR.DOUBLE_UNDERLINE).fg_24b(0, 0, 0),
)

add(
    "19_underline_coloured_curly.svg",
    ANSIString("Curly underline").ul_24b(255, 0, 0).style(UnderlineMode.CURLY),
)

add(
    "20_underline_coloured_dotted.svg",
    ANSIString("Dotted underline").ul_24b(0, 128, 255).style(UnderlineMode.DOTTED),
)

add(
    "21_underline_coloured_dashed.svg",
    ANSIString("Dashed underline").ul_24b(200, 100, 0).style(UnderlineMode.DASHED),
)


# ── 7. Combined attributes ────────────────────────────────────────────────
add(
    "22_bold_underline.svg",
    ANSIString("Bold + Underline")
    .style(SGR.BOLD)
    .style(SGR.UNDERLINE)
    .fg_24b(0, 100, 200),
    font_bold=bold,
)

add(
    "23_italic_curly_underline.svg",
    ANSIString("Italic + Curly")
    .style(SGR.ITALIC)
    .ul_24b(255, 80, 80)
    .style(UnderlineMode.CURLY),
    font_italic=ital,
)

add(
    "24_full_combo.svg",
    ANSIString("Full combo!")
    .style(SGR.BOLD)
    .style(SGR.ITALIC)
    .fg_24b(255, 200, 0)
    .bg_24b(30, 30, 60)
    .ul_24b(255, 100, 100)
    .style(UnderlineMode.DOUBLE),
    font_bold_italic=bi,
)


# ── 8. Background options ─────────────────────────────────────────────────
add(
    "25_opaque_bg.svg",
    ANSIString("Opaque background").fg_24b(255, 255, 255),
    transparent_background=False,
    background_color=(30, 30, 30),
)


# ── 9. Faux weight / skew overrides ───────────────────────────────────────
add(
    "26_faux_weight_900.svg", ANSIString("Extra Bold (900)").style(SGR.BOLD), weight=900
)

add(
    "27_faux_skew_minus20.svg",
    ANSIString("Heavy Skew (-20)").style(SGR.ITALIC),
    skew=-20,
)

add(
    "28_faux_skew_plus10.svg",
    ANSIString("Reverse Skew (+10)").style(SGR.ITALIC),
    skew=10,
)


# ── 10. Rainbow & Multicolor ──────────────────────────────────────────────
add("29_rainbow.svg", ANSIString("Rainbow text example!").rainbow(fg=True))

add(
    "30_multicolor.svg",
    ANSIString("Multicolor gradient!").multicolor(
        (
            "r=0:|g=0:|b=255:   $ "
            "b>0:repeat(auto)   # "
            "r>255:repeat(auto) | "
            "g>255:repeat(auto)   "
            "                   &*"
        )
    ),
)


# ── 11. Multiline ─────────────────────────────────────────────────────────
add(
    "31_multiline.svg",
    ANSIString("Line 1: Bold\nLine 2: Italic\nLine 3: Normal")
    .style(SGR.BOLD, (0, 12))
    .style(SGR.ITALIC, (13, 27))
    .fg_24b(0, 150, 0, (0, 12))
    .fg_24b(150, 0, 0, (13, 27)),
    font_bold=bold,
    font_italic=ital,
)


# ── 12. Text mode equivalents ─────────────────────────────────────────────
add(
    "32_text_mode_bold.svg",
    ANSIString("Text-mode bold").style(SGR.BOLD).fg_24b(0, 0, 0),
    convert_text_to_path=False,
)

add(
    "33_text_mode_italic.svg",
    ANSIString("Text-mode italic").style(SGR.ITALIC).fg_24b(0, 0, 0),
    convert_text_to_path=False,
)

add(
    "34_text_mode_dim.svg",
    ANSIString("Text-mode dim").style(SGR.DIM).fg_24b(0, 0, 0),
    convert_text_to_path=False,
)

add(
    "35_text_mode_underline.svg",
    ANSIString("Text-mode underline").style(SGR.UNDERLINE).fg_24b(0, 0, 0),
    convert_text_to_path=False,
)


# ── 13. Side-by-side comparison: faux vs font ─────────────────────────────
add("36_comparison_faux_bold.svg", ANSIString("Faux Bold (stroke)").style(SGR.BOLD))

add(
    "37_comparison_real_bold.svg",
    ANSIString("Real Bold (font)").style(SGR.BOLD),
    font_bold=bold,
)

add("38_comparison_faux_italic.svg", ANSIString("Faux Italic (skew)").style(SGR.ITALIC))

add(
    "39_comparison_real_italic.svg",
    ANSIString("Real Italic (font)").style(SGR.ITALIC),
    font_italic=ital,
)


# ── Generate all SVGs ─────────────────────────────────────────────────────
print(f"Generating {len(examples)} SVG examples in {OUT}:")

for filename, (ansistr, kw) in sorted(examples.items()):
    if "convert_text_to_path" not in kw:
        kw["convert_text_to_path"] = True
    svg = ansistr.to_svg(reg, font_size_px=FONT_PX, **kw)
    write(filename, svg)

print(f"\nDone — {len(examples)} files written.")
