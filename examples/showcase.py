#!/usr/bin/env python3
"""showcase.py — Print a visual tour of pyansistring's terminal capabilities.

Run with:
    python examples/showcase.py
"""

from pyansistring import (
    ANSIString,
    ArtRegistry,
    ColorGeneratorContext,
    register_color_generator,
    unregister_color_generator,
)
from pyansistring.constants import (
    SGR,
    Background,
    Foreground,
    UnderlineMode,
)

# ── Helpers ───────────────────────────────────────────────────────────────

DIVIDER_CHAR = "─"
DIVIDER_LEN = 72
WALL = "\x1b[100m \x1b[0m"


def section(title: str) -> None:
    """Print a section header."""
    line = ANSIString(f" {title} ".center(DIVIDER_LEN, DIVIDER_CHAR))
    line.fg_24b(180, 180, 180)
    print(f"\n{line}\n")


def show(label: str, value: ANSIString | str) -> None:
    """Print a labelled example with visual framing."""
    print(f"  {label:<40} {WALL}{value}{WALL}")


def zigzag_generator(context: ColorGeneratorContext) -> list[tuple[int, int, int]]:
    """Return a mirrored zigzag palette sized to the requested step count."""
    palette = [
        (84, 161, 255),
        (255, 99, 71),
        (255, 215, 0),
        (120, 220, 160),
    ]
    out: list[tuple[int, int, int]] = []
    for index in range(max(2, context["step_count"])):
        phase = (index // len(palette)) % 2
        slot = index % len(palette)
        out.append(palette[slot] if phase == 0 else palette[-slot - 1])
    return out


# ── Main showcase ─────────────────────────────────────────────────────────


def main() -> None:
    # ── 1. Plain text (no styling) ────────────────────────────────────────
    section("Plain text (no styling)")
    show("ANSIString('Hello, World!')", ANSIString("Hello, World!"))

    # ── 2. SGR attributes ─────────────────────────────────────────────────
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

    # ── 3. Stacking attributes ────────────────────────────────────────────
    section("Stacking multiple attributes")
    show(
        ".style(BOLD).style(ITALIC).style(UNDERLINE)",
        ANSIString("Hello, World!")
        .style(SGR.BOLD)
        .style(SGR.ITALIC)
        .style(SGR.UNDERLINE),
    )

    # ── 4. 4-bit foreground ───────────────────────────────────────────────
    section("4-bit foreground colours")
    colors_4bit = [
        ("BLACK", Foreground.BLACK),
        ("RED", Foreground.RED),
        ("GREEN", Foreground.GREEN),
        ("YELLOW", Foreground.YELLOW),
        ("BLUE", Foreground.BLUE),
        ("MAGENTA", Foreground.MAGENTA),
        ("CYAN", Foreground.CYAN),
        ("WHITE", Foreground.WHITE),
        ("BRIGHT_BLACK", Foreground.BRIGHT_BLACK),
        ("BRIGHT_RED", Foreground.BRIGHT_RED),
        ("BRIGHT_GREEN", Foreground.BRIGHT_GREEN),
        ("BRIGHT_YELLOW", Foreground.BRIGHT_YELLOW),
        ("BRIGHT_BLUE", Foreground.BRIGHT_BLUE),
        ("BRIGHT_MAGENTA", Foreground.BRIGHT_MAGENTA),
        ("BRIGHT_CYAN", Foreground.BRIGHT_CYAN),
        ("BRIGHT_WHITE", Foreground.BRIGHT_WHITE),
    ]
    for name, color in colors_4bit:
        show(f".fg_4b(Foreground.{name})", ANSIString("Hello, World!").fg_4b(color))

    # ── 5. 4-bit background ───────────────────────────────────────────────
    section("4-bit background colours")
    bg_colors = [
        ("RED", Background.RED),
        ("GREEN", Background.GREEN),
        ("BLUE", Background.BLUE),
        ("YELLOW", Background.YELLOW),
        ("BRIGHT_WHITE", Background.BRIGHT_WHITE),
    ]
    for name, color in bg_colors:
        show(f".bg_4b(Background.{name})", ANSIString("Hello, World!").bg_4b(color))

    # ── 6. 8-bit colours ─────────────────────────────────────────────────
    section("8-bit foreground colours (sample)")
    for n in (21, 46, 82, 135, 196, 208, 226):
        show(f".fg_8b({n})", ANSIString("Hello, World!").fg_8b(n))

    section("8-bit background colours (sample)")
    for n in (17, 52, 94, 130, 202):
        show(f".bg_8b({n})", ANSIString("Hello, World!").bg_8b(n))

    # ── 7. 24-bit (true colour) ──────────────────────────────────────────
    section("24-bit (true colour) foreground")
    show(
        ".fg_24b(0, 128, 255)",
        ANSIString("Hello, World!").fg_24b(0, 128, 255),
    )
    show(
        ".fg_24b(255, 64, 0)",
        ANSIString("Hello, World!").fg_24b(255, 64, 0),
    )

    section("24-bit (true colour) background")
    show(
        ".bg_24b(40, 40, 40)",
        ANSIString("Hello, World!").bg_24b(40, 40, 40),
    )

    # ── 8. Per-range / per-word styling ──────────────────────────────────
    section("Per-range styling")
    show(
        "fg_24b blue(0,5) + yellow(7,12)",
        ANSIString("Hello, World!")
        .fg_24b(0, 0, 255, (0, 5))
        .fg_24b(255, 255, 0, (7, 12)),
    )

    section("Per-word styling (_w methods)")
    show(
        ".fg_4b_words(BLUE, 'Hello')",
        ANSIString("Hello, World!").fg_4b_words(Foreground.BRIGHT_BLUE, "Hello"),
    )
    show(
        ".style_words(BOLD, 'World')",
        ANSIString("Hello, World!").style_words(SGR.BOLD, "World"),
    )
    show(
        ".fg_4b_words(CYAN) + .bg_4b_words(YELLOW)",
        ANSIString("Hello, World!")
        .fg_4b_words(Foreground.BRIGHT_CYAN, "Hello")
        .bg_4b_words(Background.BRIGHT_YELLOW, "World"),
    )

    # ── 9. Underline colours & modes ──────────────────────────────────────
    section("Underline colours and modes")
    show(
        ".ul_8b(135)",
        ANSIString("Hello, World!").ul_8b(135),
    )
    show(
        ".ul_24b(0, 200, 100)",
        ANSIString("Hello, World!").ul_24b(0, 200, 100),
    )
    modes = [
        ("SINGLE", UnderlineMode.SINGLE),
        ("DOUBLE", UnderlineMode.DOUBLE),
        ("CURLY", UnderlineMode.CURLY),
        ("DOTTED", UnderlineMode.DOTTED),
        ("DASHED", UnderlineMode.DASHED),
    ]
    for name, mode in modes:
        show(
            f".ul_24b(255,100,0).style({name})",
            ANSIString("Hello, World!").ul_24b(255, 100, 0).style(mode),
        )

    # ── 10. Removing styles ───────────────────────────────────────────────
    section("Removing styles (unstyle / unstyle_words)")
    show(
        ".style(BOLD).unstyle()",
        ANSIString("Hello, World!").style(SGR.BOLD).unstyle(),
    )
    show(
        ".style(BOLD).unstyle((0,5))",
        ANSIString("Hello, World!").style(SGR.BOLD).unstyle((0, 5)),
    )
    show(
        ".style_words(BOLD,'Hello').unstyle_words('Hello')",
        ANSIString("Hello, World!")
        .style_words(SGR.BOLD, "Hello")
        .unstyle_words("Hello"),
    )

    # ── 11. Rainbow ───────────────────────────────────────────────────────
    section("Rainbow effect")
    show(
        ".rainbow()",
        ANSIString("abcdefghijklmnopqrstuvwxyz").rainbow(),
    )
    show(
        ".rainbow(bg=True)",
        ANSIString("abcdefghijklmnopqrstuvwxyz").rainbow(bg=True),
    )
    show(
        ".rainbow(skip_whitespace=True)",
        ANSIString("Hello, World! Rainbow text!").rainbow(skip_whitespace=True),
    )

    # ── 12. Gradient API ──────────────────────────────────────────────────
    section("Gradients (gradient, gradient_words, gradient_coordinates)")
    show(
        ".gradient([(84,161,255),(255,255,255)])",
        ANSIString("abcdefghijklmnopqrstuvwxyz").gradient(
            [(84, 161, 255), (255, 255, 255)]
        ),
    )
    show(
        ".gradient(..., bg=True)",
        ANSIString("abcdefghijklmnopqrstuvwxyz").gradient(
            [(34, 34, 34), (84, 161, 255), (255, 255, 255)],
            bg=True,
        ),
    )
    show(
        ".gradient_words(..., 'Hello', 'World')",
        ANSIString("Hello, colorful gradient world!").gradient_words(
            [(255, 99, 71), (255, 215, 0)],
            "Hello",
            "world",
            case_sensitive=False,
        ),
    )
    show(
        ".gradient_coordinates(..., (1,1)..(5,1), index_base=1)",
        ANSIString("HELLO\nworld").gradient_coordinates(
            [(255, 0, 120), (0, 200, 255)],
            (1, 1),
            (2, 1),
            (3, 1),
            (4, 1),
            (5, 1),
            index_base=1,
            fg=True,
        ),
    )

    # ── 13. Art registry and generators ───────────────────────────────────
    section("ArtRegistry and custom generators")

    register_color_generator("zigzag_showcase_v1", zigzag_generator)
    try:
        custom_registry = ArtRegistry()
        custom_registry.register(
            "ZIGZAG",
            " /\\/\\/\\/\\\n \\/\\/\\/\\/",
            colorings=(
                {
                    "mode": "gradient",
                    "colors": {
                        "generator": "zigzag_showcase_v1",
                        "mode": "seeded",
                        "seed": 7,
                    },
                    "skip_whitespace": True,
                    "fg": True,
                },
            ),
        )
        show(
            "Custom ArtRegistry + zigzag generator",
            custom_registry.get_colored_art("ZIGZAG"),
        )
    finally:
        unregister_color_generator("zigzag_showcase_v1")

    # ── 14. String operations preserve styles ─────────────────────────────
    section("String operations that preserve styles")

    styled = ANSIString("Hello, World!").fg_24b(0, 128, 255)
    show(".upper()", styled.upper())
    show(".lower()", styled.lower())
    show(".capitalize()", ANSIString("hello, world!").fg_24b(0, 128, 255).capitalize())
    show(".swapcase()", styled.swapcase())
    show(".title()", ANSIString("hello, world!").fg_24b(0, 128, 255).title())

    section("Slicing preserves styles")
    show("[2:-2]", styled[2:-2])
    show("[::2]", styled[::2])

    section("Concatenation preserves styles")
    a = ANSIString("Hello").fg_24b(255, 0, 0)
    b = ANSIString(", World!").fg_24b(0, 255, 0)
    show("ANSIString + ANSIString", a + b)
    show("str + ANSIString", ">>> " + b)

    section("Alignment preserves styles")
    short = ANSIString("Hi").fg_24b(255, 100, 0).style(SGR.BOLD)
    show(".ljust(10, '.')", short.ljust(10, "."))
    show(".rjust(10, '.')", short.rjust(10, "."))
    show(".center(10, '.')", short.center(10, "."))

    section("Split / join preserve styles")
    parts = ANSIString("Hello, World!").fg_24b(0, 128, 255).split(", ")
    show(".split(', ')", " | ".join(str(p) for p in parts))
    joined = ANSIString(" + ").style(SGR.BOLD).join(parts)
    show(".join(parts)", joined)

    # ── 15. f-string support ──────────────────────────────────────────────
    section("f-string support")
    s = ANSIString("Hi").fg_4b(Foreground.RED)
    show("f'{s}'", f"{s}")
    show("f'{s:>5}'", f"{s:>5}")
    show("f'{s:^10}'", f"{s:^10}")

    # ── 16. from_ansi parsing ─────────────────────────────────────────────
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
