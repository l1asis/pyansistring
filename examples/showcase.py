#!/usr/bin/env python3
"""showcase.py — Print a visual tour of pyansistring's terminal capabilities.

Run with:
    python examples/showcase.py
"""

from pyansistring import (
    ANSIString,
    Channel,
    Chars,
    Coords,
    Pattern,
    Words,
)
from pyansistring.color import ColorMap, ColorScale, SegmentedColorMap
from pyansistring.constants import (
    SGR,
    Background,
    Foreground,
    NamedColors,
    UnderlineMode,
)

# ── Helpers ───────────────────────────────────────────────────────────────

DIVIDER_CHAR = "─"
DIVIDER_LEN = 80
WALL = "\x1b[100m \x1b[0m"


def section(title: str) -> None:
    """Print a section header."""
    line = ANSIString(f" {title} ".center(DIVIDER_LEN, DIVIDER_CHAR))
    line.fg((180, 180, 180))
    print(f"\n{line}\n")


def show(label: str, value: ANSIString | str) -> None:
    """Print a labelled example with visual framing."""
    print(f"  {label:<48} {WALL}{value}{WALL}")


# ── Main showcase ─────────────────────────────────────────────────────────


def main() -> None:
    # ── Plain text (no styling) ────────────────────────────────────────
    section("Plain text (no styling)")
    show("ANSIString('Hello, World!')", ANSIString("Hello, World!"))

    # ── SGR attributes ─────────────────────────────────────────────────
    section("SGR attributes via style()")
    attrs = {
        "BOLD": SGR.BOLD,
        "DIM": SGR.DIM,
        "ITALIC": SGR.ITALIC,
        "UNDERLINE": SGR.UNDERLINE,
        "SLOW_BLINK": SGR.SLOW_BLINK,
        "INVERT": SGR.INVERT,
        "STRIKETHROUGH": SGR.STRIKETHROUGH,
        "OVERLINED": SGR.OVERLINED,
    }
    for name, sgr in attrs.items():
        show(f".style(SGR.{name})", ANSIString("Hello, World!").style(sgr))

    # ── Stacking attributes ────────────────────────────────────────────
    section("Stacking multiple attributes")
    show(
        ".style(BOLD).style(ITALIC).style(UNDERLINE)",
        ANSIString("Hello, World!")
        .style(SGR.BOLD)
        .style(SGR.ITALIC)
        .style(SGR.UNDERLINE),
    )

    # ── Unified Foreground / Background ────────────────────────────────
    section("Unified Color Routing (Infers depth automatically)")

    # 4-bit (Enums)
    show(
        ".fg(Foreground.BRIGHT_RED)",
        ANSIString("Hello, World!").fg(Foreground.BRIGHT_RED),
    )
    show(".bg(Background.BLUE)", ANSIString("Hello, World!").bg(Background.BLUE))

    # 8-bit (Integers)
    show(".fg(135)", ANSIString("Hello, World!").fg(135))
    show(".bg(202)", ANSIString("Hello, World!").bg(202))

    # 24-bit (Tuples & Hex Strings)
    show(".fg((0, 128, 255))", ANSIString("Hello, World!").fg((0, 128, 255)))
    show(".bg('#15202B')", ANSIString("Hello, World!").bg("#15202B"))

    # ── Target Selectors ───────────────────────────────────────────────
    section("Precision Targeting with Selectors")

    show(
        "Slices: .fg((0, 255, 0), (7, 12))",
        ANSIString("Hello, World!").fg((0, 255, 0), (7, 12)),
    )

    show(
        "Words:  .fg(RED, Words(('Hello',)))",
        ANSIString("Hello, World!").fg(Foreground.BRIGHT_RED, Words(("Hello",))),
    )

    show(
        "Pattern: .style(BOLD, Pattern(r'\\d+'))",
        ANSIString("Error 404: Not Found!")
        .fg((255, 50, 50), Pattern(r"\d+"))
        .style(SGR.BOLD, Pattern(r"\d+")),
    )

    show(
        "",
        ANSIString("Login: [WARN] User 'admin' failed from 192.168.1.50")
        .fg(Foreground.YELLOW, Pattern(r"\[WARN\]"))
        .fg(Foreground.CYAN, Pattern(r"'.*?'"))
        .style(SGR.UNDERLINE, Pattern(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")),
    )

    # ── Underline colours & modes ──────────────────────────────────────
    section("Underline colours and modes")
    show(".ul(135)", ANSIString("Hello, World!").ul(135))
    show(".ul((0, 200, 100))", ANSIString("Hello, World!").ul((0, 200, 100)))

    modes = [
        ("SINGLE", UnderlineMode.SINGLE),
        ("DOUBLE", UnderlineMode.DOUBLE),
        ("CURLY", UnderlineMode.CURLY),
        ("DOTTED", UnderlineMode.DOTTED),
        ("DASHED", UnderlineMode.DASHED),
    ]
    for name, mode in modes:
        show(
            f".ul((255,100,0)).style({name})",
            ANSIString("Hello, World!").ul((255, 100, 0)).style(mode),
        )

    # ── Removing styles ───────────────────────────────────────────────
    section("Removing styles")
    show(
        ".style(BOLD).unstyle()",
        ANSIString("Hello, World!").style(SGR.BOLD).unstyle(),
    )
    show(
        ".style(BOLD).unstyle(Words(('Hello',)))",
        ANSIString("Hello, World!").style(SGR.BOLD).unstyle(Words(("Hello",))),
    )

    # ── Rainbow Effect ────────────────────────────────────────────────
    section("Rainbow effect")
    show(
        ".rainbow()",
        ANSIString("abcdefghijklmnopqrstuvwxyz").rainbow(),
    )
    show(
        ".rainbow(channel=Channel.BG)",
        ANSIString("abcdefghijklmnopqrstuvwxyz").rainbow(channel=Channel.BG),
    )
    show(
        ".rainbow(Chars(skip_whitespace=True))",
        ANSIString("Hello, World! Rainbow text!").rainbow(Chars(skip_whitespace=True)),
    )

    # ── Gradients ─────────────────────────────────────────────────────
    section("Gradients")
    show(
        ".gradient([(84,161,255), (255,255,255)])",
        ANSIString("abcdefghijklmnopqrstuvwxyz").gradient(
            [(84, 161, 255), (255, 255, 255)]
        ),
    )
    show(
        ".gradient(..., channel=Channel.BG)",
        ANSIString("abcdefghijklmnopqrstuvwxyz").gradient(
            [(34, 34, 34), (84, 161, 255), (255, 255, 255)],
            channel=Channel.BG,
        ),
    )
    show(
        ".gradient(..., Words(('Hello', 'world')))",
        ANSIString("Hello, colorful gradient world!").gradient(
            [(255, 99, 71), (255, 215, 0)],
            Words(("Hello", "world"), ignore_case=True),
        ),
    )
    show(
        ".gradient(..., Coords(...))",
        ANSIString("HELLO\nworld").gradient(
            [(255, 0, 120), (0, 200, 255)],
            Coords(((1, 1), (2, 1), (3, 1), (4, 1), (5, 1)), index_base=1),
        ),
    )

    # ── Data-Driven Colormaps ─────────────────────────────────────────
    section("Data-Driven Colormaps (Segmented vs Continuous)")

    ramp_text = "".join(f"{n:<5}" for n in range(0, 101, 10))
    block_pattern = Pattern(r"\d+\s*")
    cmap_seg = SegmentedColorMap(
        {0: NamedColors.LIME, 60: NamedColors.YELLOW, 90: NamedColors.RED}
    )

    show(
        "Segmented (Snaps at 60 and 90)",
        ANSIString(ramp_text)
        .colormap(cmap_seg, block_pattern, channel=Channel.BG)
        .fg(0),
    )

    scale = ColorScale([(0, 255, 255), (255, 255, 0), (255, 0, 0)], space="hsl")
    cmap_cont = ColorMap(scale, vmin=0, vmax=100)

    show(
        "Continuous (Smooth interpolation)",
        ANSIString(ramp_text)
        .colormap(cmap_cont, block_pattern, channel=Channel.BG)
        .fg(0),
    )

    # ── SVG Vector Export ─────────────────────────────────────────────
    section("SVG Vector Export")

    show(
        ".to_svg('font.ttf', 16, output_file='out.svg')",
        ANSIString("Styled vector graphic!").fg((100, 255, 100)),
    )

    # ── String operations preserve styles ─────────────────────────────
    section("String operations that preserve styles")

    styled = ANSIString("Hello, World!").fg((0, 128, 255))
    show(".upper()", styled.upper())
    show(".lower()", styled.lower())
    show(".swapcase()", styled.swapcase())
    show(".title()", ANSIString("hello, world!").fg((0, 128, 255)).title())

    section("Slicing preserves styles")
    show("[2:-2]", styled[2:-2])
    show("[::2]", styled[::2])

    section("Concatenation preserves styles")
    a = ANSIString("Hello").fg((255, 0, 0))
    b = ANSIString(", World!").fg((0, 255, 0))
    show("ANSIString + ANSIString", a + b)
    show("str + ANSIString", ">>> " + b)

    section("Alignment preserves styles")
    short = ANSIString("Hi").fg((255, 100, 0)).style(SGR.BOLD)
    show(".ljust(10, '.')", short.ljust(10, "."))
    show(".rjust(10, '.')", short.rjust(10, "."))
    show(".center(10, '.')", short.center(10, "."))

    section("Split / join preserve styles")
    parts = ANSIString("Hello, World!").fg((0, 128, 255)).split(", ")
    show(".split(', ')", " | ".join(str(p) for p in parts))
    joined = ANSIString(" + ").style(SGR.BOLD).join(parts)
    show(".join(parts)", joined)

    # ── f-string support ──────────────────────────────────────────────
    section("f-string support")
    s = ANSIString("Hi").fg(Foreground.RED)
    show("f'{s}'", f"{s}")
    show("f'{s:>5}'", f"{s:>5}")
    show("f'{s:^10}'", f"{s:^10}")

    # ── from_ansi parsing ─────────────────────────────────────────────
    section("from_ansi — parse raw ANSI back to ANSIString")
    raw = "\x1b[38;2;0;128;255mHello\x1b[0m, \x1b[1mWorld!\x1b[0m"
    parsed = ANSIString.from_ansi(raw)
    show("Input raw ANSI", raw)
    show("Parsed .plain_text", parsed.plain_text)
    show("Parsed .styled_text", parsed)

    # ── Done ──────────────────────────────────────────────────────────────
    print(f"\n{'':─^{DIVIDER_LEN}}")
    print("  Showcase complete!  All features above are provided by pyansistring.")
    print(f"{'':─^{DIVIDER_LEN}}\n")


if __name__ == "__main__":
    main()
