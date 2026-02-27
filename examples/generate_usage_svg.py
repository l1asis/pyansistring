"""
Generate example SVG images from the ANSIString usage examples in the README.
"""

from fontTools.ttLib import TTFont

from pyansistring.constants import SGR, Background, Foreground, UnderlineMode
from pyansistring.pyansistring import ANSIString

font = TTFont("C:\\Windows\\Fonts\\consola.ttf")
font_bold = TTFont("C:\\Windows\\Fonts\\consolab.ttf")
font_ital = TTFont("C:\\Windows\\Fonts\\consolai.ttf")
font_bi = TTFont("C:\\Windows\\Fonts\\consolaz.ttf")
base_path = "images\\usage"

path_to_ansistring = {
    f"{base_path}\\unstyled.svg": ANSIString("Hello, World!"),
    f"{base_path}\\whole.svg": (
        ANSIString("Hello, World!")
        .fg_4b(Foreground.YELLOW)
        .bg_4b(Background.BLUE)
        .fm(SGR.BOLD)
    ),
    f"{base_path}\\slice.svg": (
        ANSIString("Hello, World!")
        .fg_4b(Foreground.YELLOW, (0, 5), (7, 12))  # "Hello" and "World"
        .bg_4b(Background.BLUE, (7, 12))  # "World"
        .fm(SGR.BOLD, (7, 12))  # "World"
    ),
    f"{base_path}\\words.svg": (
        ANSIString("Hello, World!")
        .fg_4b_w(Foreground.YELLOW, "Hello", "World")
        .bg_4b_w(Background.BLUE, "World")
        .fm_w(SGR.BOLD, "Hello", "World")
    ),
    f"{base_path}\\sgr.svg": (
        ANSIString("Hello, World!").fm(SGR.BOLD).fm(SGR.UNDERLINE)
    ),
    f"{base_path}\\4bit.svg": (
        ANSIString("Hello, World!").fg_4b(Foreground.YELLOW).bg_4b(Background.BLUE)
    ),
    f"{base_path}\\8bit.svg": (
        ANSIString("Hello, World!")
        .fg_8b(11)  # Bright Yellow
        .bg_8b(4)  # Blue
        .ul_8b(74)  # Muted Sky Blue
    ),
    f"{base_path}\\rgb.svg": (
        ANSIString("Hello, World!")
        .fg_24b(255, 255, 0)  # Bright Yellow
        .bg_24b(0, 0, 238)  # Blue
        .ul_24b(135, 175, 215)  # Light Steel Blue
    ),
    f"{base_path}\\underline.svg": (
        ANSIString("Hello, World!")
        .bg_24b(255, 255, 255)  # White
        .ul_24b(255, 0, 0)  # Red
        .fm(UnderlineMode.DOUBLE)
    ),
    f"{base_path}\\rainbow.svg": (
        ANSIString("Hello, World! This is rainbow text!").rainbow(fg=True)
    ),
    f"{base_path}\\multicolor.svg": (
        ANSIString("Hello, World! This is multicolor text!").multicolor(
            (
                "r=0:|g=0:|b=255:   $ "  # Start with blue
                "b>0:repeat(auto)   # "  # Decrease blue
                "r>255:repeat(auto) | "  # Increase green and combine with...
                "g>255:repeat(auto)   "  # Increase red
                "                   &*"  # Cycle & Start without apply flags
            )
        )
    ),
}

for path, ansistr in path_to_ansistring.items():
    ansistr.to_svg(
        font,
        16,
        convert_text_to_path=True,
        output_file=path,
        font_bold=font_bold,
        font_italic=font_ital,
        font_bold_italic=font_bi,
    )
