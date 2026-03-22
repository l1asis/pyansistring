"""Tests for ANSIString styling methods (style, unstyle, fg_*, bg_*, ul_*, rainbow)."""

from typing import Any

import pytest

from pyansistring import ANSIString
from pyansistring.constants import (
    SGR,
    Background,
    Foreground,
    Underline,
    UnderlineMode,
)
from pyansistring.style import Style
from tests.conftest import RESET, ansi_wrap, style_ansi


class TestStyle:
    """ANSIString.style() — apply a style to ranges."""

    def test_whole_string(self, hello_world: ANSIString, bold_code: str):
        s = hello_world.style(SGR.BOLD)
        assert str(s) == ansi_wrap("Hello, World!", bold_code), (
            "style(BOLD) whole string"
        )

    def test_slice_range(self, hello_world: ANSIString, bold_code: str):
        s = hello_world.style(SGR.BOLD, (0, 5))
        assert str(s) == ansi_wrap("Hello", bold_code) + ", World!"

    def test_multiple_ranges(self, hello_world: ANSIString, bold_code: str):
        s = hello_world.style(SGR.BOLD, (0, 5), slice(7, 12))
        expected = f"{ansi_wrap('Hello', bold_code)}, {ansi_wrap('World', bold_code)}!"
        assert str(s) == expected, "style with multiple ranges should style each"

    def test_stacking_styles(
        self, hello_world: ANSIString, bold_code: str, italic_code: str
    ):
        s = hello_world.style(SGR.BOLD).style(SGR.ITALIC)
        combined = bold_code + italic_code
        assert str(s) == ansi_wrap("Hello, World!", combined), (
            "Stacked styles should combine"
        )


class TestStyleWords:
    """ANSIString.style_words() — word-targeted formatting."""

    def test_by_word(self, hello_world: ANSIString, bold_code: str):
        s = hello_world.style_words(SGR.BOLD, "Hello")
        assert str(s) == ansi_wrap("Hello", bold_code) + ", World!"

    def test_case_insensitive(self, hello_world: ANSIString, italic_code: str):
        s = hello_world.style_words(SGR.ITALIC, "world", case_sensitive=False)
        assert str(s) == "Hello, " + ansi_wrap("World", italic_code) + "!"


class TestUnstyle:
    """ANSIString.unstyle() — remove formatting."""

    def test_unstyle_whole_string(self, hello_world: ANSIString):
        s = hello_world.style(SGR.BOLD).unstyle()
        assert str(s) == "Hello, World!", "unstyle() should strip all formatting"

    @pytest.mark.parametrize(
        "ranges",
        [
            pytest.param(((0, 5),), id="single-range"),
            pytest.param(((0, 5), slice(7, 12)), id="multiple-ranges"),
        ],
    )
    def test_unstyle_ranges(self, hello_world: ANSIString, ranges: Any):
        s = hello_world.style(SGR.BOLD, *ranges).unstyle(*ranges)
        assert str(s) == "Hello, World!", f"unstyle{ranges} should clear those ranges"


class TestUnstyleWords:
    """ANSIString.unstyle_words() — remove formatting by word."""

    def test_unstyle_words(self, hello_world: ANSIString):
        s = hello_world.style_words(SGR.BOLD, "Hello").unstyle_words("Hello")
        assert str(s) == "Hello, World!"

    def test_unstyle_words_case_insensitive(self, hello_world: ANSIString):
        s = hello_world.style_words(
            SGR.ITALIC, "world", case_sensitive=False
        ).unstyle_words("world", case_sensitive=False)
        assert str(s) == "Hello, World!"


# Each tuple: (method_range, method_word, style_args, label)
_COLOR_METHOD_CASES = [
    pytest.param(
        "fg_4b",
        "fg_4b_words",
        (Foreground.BRIGHT_BLUE,),
        (Foreground.BRIGHT_BLUE,),
        id="fg-4b",
    ),
    pytest.param(
        "fg_8b",
        "fg_8b_words",
        (135,),
        (Foreground.SET, 135),
        id="fg-8b",
    ),
    pytest.param(
        "bg_4b",
        "bg_4b_words",
        (Background.BRIGHT_BLUE,),
        (Background.BRIGHT_BLUE,),
        id="bg-4b",
    ),
    pytest.param(
        "bg_8b",
        "bg_8b_words",
        (135,),
        (Background.SET, 135),
        id="bg-8b",
    ),
    pytest.param(
        "ul_8b",
        "ul_8b_words",
        (135,),
        (Underline.SET, 135),
        id="ul-8b",
    ),
]


class TestColorMethodsByRange:
    """Range-based color methods: fg_4b, fg_8b, bg_4b, bg_8b, ul_8b."""

    @pytest.mark.parametrize(
        "method_range, method_word, method_args, style_args",
        _COLOR_METHOD_CASES,
    )
    def test_range(
        self,
        method_range: str,
        method_word: str,
        method_args: tuple[Any, ...],
        style_args: tuple[Any, ...],
    ):
        code = style_ansi(*style_args)
        s = getattr(ANSIString("Hello, World!"), method_range)(*method_args, (0, 5))
        expected = ansi_wrap("Hello", code) + ", World!"
        assert str(s) == expected, f"{method_range} range mismatch"

    @pytest.mark.parametrize(
        "method_range, method_word, method_args, style_args",
        _COLOR_METHOD_CASES,
    )
    def test_by_word(
        self,
        method_range: str,
        method_word: str,
        method_args: tuple[Any, ...],
        style_args: tuple[Any, ...],
    ):
        code = style_ansi(*style_args)
        s = getattr(ANSIString("Hello, World!"), method_word)(*method_args, "Hello")
        expected = ansi_wrap("Hello", code) + ", World!"
        assert str(s) == expected, f"{method_word} word mismatch"


class TestColorMethods24bit:
    """24-bit color methods that take r,g,b — separate because of arg shape."""

    @pytest.mark.parametrize(
        "range_method, word_method, style_enum",
        [
            pytest.param("fg_24b", "fg_24b_words", Foreground.SET, id="fg-24b"),
            pytest.param("bg_24b", "bg_24b_words", Background.SET, id="bg-24b"),
            pytest.param("ul_24b", "ul_24b_words", Underline.SET, id="ul-24b"),
        ],
    )
    def test_range_two_colors(
        self, range_method: str, word_method: str, style_enum: Any
    ):
        blue = style_ansi(style_enum, 0, 0, 255)
        yellow = style_ansi(style_enum, 255, 255, 0)
        s = getattr(ANSIString("Hello, World!"), range_method)(0, 0, 255, (0, 5))
        s = getattr(s, range_method)(255, 255, 0, (7, 12))
        expected = ansi_wrap("Hello", blue) + ", " + ansi_wrap("World", yellow) + "!"
        assert str(s) == expected, f"{range_method} two-color range mismatch"

    @pytest.mark.parametrize(
        "range_method, word_method, style_enum",
        [
            pytest.param("fg_24b", "fg_24b_words", Foreground.SET, id="fg-24b"),
            pytest.param("bg_24b", "bg_24b_words", Background.SET, id="bg-24b"),
            pytest.param("ul_24b", "ul_24b_words", Underline.SET, id="ul-24b"),
        ],
    )
    def test_by_word_two_colors(
        self, range_method: str, word_method: str, style_enum: Any
    ):
        blue = style_ansi(style_enum, 0, 0, 255)
        yellow = style_ansi(style_enum, 255, 255, 0)
        s = getattr(ANSIString("Hello, World!"), word_method)(0, 0, 255, "Hello")
        s = getattr(s, word_method)(255, 255, 0, "World")
        expected = ansi_wrap("Hello", blue) + ", " + ansi_wrap("World", yellow) + "!"
        assert str(s) == expected, f"{word_method} two-color word mismatch"


class TestWholeStringColor:
    @pytest.mark.parametrize(
        "method, method_args, style_args",
        [
            pytest.param("fg_8b", (135,), (Foreground.SET, 135), id="fg-8b-whole"),
            pytest.param("bg_8b", (135,), (Background.SET, 135), id="bg-8b-whole"),
            pytest.param("ul_8b", (135,), (Underline.SET, 135), id="ul-8b-whole"),
        ],
    )
    def test_whole(
        self, method: str, method_args: tuple[Any, ...], style_args: tuple[Any, ...]
    ):
        code = style_ansi(*style_args)
        s = getattr(ANSIString("Hello, World!"), method)(*method_args)
        assert str(s) == ansi_wrap("Hello, World!", code), (
            f"{method} whole string mismatch"
        )

    @pytest.mark.parametrize(
        "method, method_args, style_args",
        [
            pytest.param(
                "fg_8b_words",
                (135, "Hello, ", "World!"),
                (Foreground.SET, 135),
                id="fg-8b-w-all",
            ),
            pytest.param(
                "bg_8b_words",
                (135, "Hello, ", "World!"),
                (Background.SET, 135),
                id="bg-8b-w-all",
            ),
        ],
    )
    def test_by_word_whole(
        self, method: str, method_args: tuple[Any, ...], style_args: tuple[Any, ...]
    ):
        code = style_ansi(*style_args)
        s = getattr(ANSIString("Hello, World!"), method)(*method_args)
        assert str(s) == ansi_wrap("Hello, World!", code), (
            f"{method} whole-word mismatch"
        )


class TestUlAttr:
    """SGR.UNDERLINE attribute via style()."""

    def test_whole(self, hello_world: ANSIString):
        ul = style_ansi(SGR.UNDERLINE)
        s = hello_world.style(SGR.UNDERLINE)
        assert str(s) == ansi_wrap("Hello, World!", ul)

    def test_range(self, hello_world: ANSIString):
        ul = style_ansi(SGR.UNDERLINE)
        s = hello_world.style(SGR.UNDERLINE, (0, 5))
        assert str(s) == ansi_wrap("Hello", ul) + ", World!"

    def test_multiple_ranges(self, hello_world: ANSIString):
        ul = style_ansi(SGR.UNDERLINE)
        s = hello_world.style(SGR.UNDERLINE, (0, 5), slice(7, 12))
        expected = ansi_wrap("Hello", ul) + ", " + ansi_wrap("World", ul) + "!"
        assert str(s) == expected


class TestUnderlineModes:
    """Underline mode variants combined with colour."""

    @pytest.mark.parametrize(
        "mode",
        [
            UnderlineMode.SINGLE,
            UnderlineMode.DOUBLE,
            UnderlineMode.CURLY,
            UnderlineMode.DOTTED,
            UnderlineMode.DASHED,
        ],
    )
    def test_mode_with_color(self, mode: UnderlineMode):
        ul_ansi = (
            Style().with_style(Underline.SET, 0, 128, 255).with_style(mode).to_ansi()
        )
        s = ANSIString("Hello, World!").ul_24b(0, 128, 255).style(mode)
        expected = f"{ul_ansi}Hello, World!{RESET}"
        assert str(s) == expected, f"Mode {mode.name} with color mismatch"

    def test_word_targeted_mode(self):
        mode = UnderlineMode.DOUBLE
        ul_ansi = Style().with_style(Underline.SET, 135).with_style(mode).to_ansi()
        s = (
            ANSIString("Hello, World!")
            .ul_8b_words(135, "World")
            .style_words(mode, "World")
        )
        expected = "Hello, " + f"{ul_ansi}World{RESET}" + "!"
        assert str(s) == expected, "Word-targeted underline mode mismatch"


class TestRainbow:
    def test_fg_rainbow_styles_all_chars(self):
        s = ANSIString("abcdefghij").rainbow()
        assert len(s.style_manager) == 10, "Rainbow should style every character"

    def test_bg_rainbow(self):
        s = ANSIString("abcdefghij").rainbow(bg=True)
        assert len(s.style_manager) == 10
        assert s.style_manager[0].background, "bg=True should set background colors"

    @pytest.mark.parametrize(
        "ws_index",
        [pytest.param(1, id="space-at-1"), pytest.param(3, id="space-at-3")],
    )
    def test_skip_whitespace(self, ws_index: int):
        s = ANSIString("a b c").rainbow(skip_whitespace=True)
        assert ws_index not in s.style_manager, (
            f"Index {ws_index} (whitespace) should be skipped"
        )

    def test_rainbow_matches_expected_palette(self):
        """Verify a known output for the builtin rainbow on the alphabet."""
        s = ANSIString("abcdefghijklmnopqrstuvwxyz").rainbow(skip_whitespace=True)
        expected = ANSIString(
            "abcdefghijklmnopqrstuvwxyz",
            {
                0: "\x1b[38;2;255;0;0m",
                1: "\x1b[38;2;255;60;0m",
                2: "\x1b[38;2;255;119;0m",
                3: "\x1b[38;2;255;178;0m",
                4: "\x1b[38;2;255;234;0m",
                5: "\x1b[38;2;217;255;0m",
                6: "\x1b[38;2;157;255;0m",
                7: "\x1b[38;2;98;255;0m",
                8: "\x1b[38;2;38;255;0m",
                9: "\x1b[38;2;0;255;21m",
                10: "\x1b[38;2;0;255;77m",
                11: "\x1b[38;2;0;255;136m",
                12: "\x1b[38;2;0;255;196m",
                13: "\x1b[38;2;0;255;255m",
                14: "\x1b[38;2;0;195;255m",
                15: "\x1b[38;2;0;136;255m",
                16: "\x1b[38;2;0;76;255m",
                17: "\x1b[38;2;0;21;255m",
                18: "\x1b[38;2;38;0;255m",
                19: "\x1b[38;2;98;0;255m",
                20: "\x1b[38;2;157;0;255m",
                21: "\x1b[38;2;217;0;255m",
                22: "\x1b[38;2;255;0;234m",
                23: "\x1b[38;2;255;0;178m",
                24: "\x1b[38;2;255;0;119m",
                25: "\x1b[38;2;255;0;59m",
            },
        )
        assert str(s) == str(expected), "Rainbow palette must match known output"
