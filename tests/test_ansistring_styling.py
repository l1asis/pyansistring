"""Tests for ANSIString styling methods (style, unstyle, fg, bg, ul, rainbow)."""

from typing import Any

import pytest

from pyansistring import ANSIString, Channel, Chars, Coords, Pattern, Words
from pyansistring.color import ColorMap, ColorScale, SegmentedColorMap
from pyansistring.constants import SGR, Background, Foreground, Underline, UnderlineMode
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


class TestStyleTargets:
    """ANSIString.style() with Target Selectors."""

    def test_by_word(self, hello_world: ANSIString, bold_code: str):
        s = hello_world.style(SGR.BOLD, Words(("Hello",)))
        assert str(s) == ansi_wrap("Hello", bold_code) + ", World!"

    def test_case_insensitive(self, hello_world: ANSIString, italic_code: str):
        s = hello_world.style(SGR.ITALIC, Words(("world",), ignore_case=True))
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

    def test_unstyle_words(self, hello_world: ANSIString):
        s = hello_world.style(SGR.BOLD, Words(("Hello",))).unstyle(Words(("Hello",)))
        assert str(s) == "Hello, World!"


class TestUnifiedColorMethods:
    """Range, word, and whole-string based color methods via fg, bg, ul."""

    @pytest.mark.parametrize(
        "method_name, color_val, expected_code",
        [
            ("fg", Foreground.BRIGHT_BLUE, style_ansi(Foreground.BRIGHT_BLUE)),
            ("fg", 135, style_ansi(Foreground.SET, 135)),
            ("fg", (0, 0, 255), style_ansi(Foreground.SET, 0, 0, 255)),
            ("bg", Background.BRIGHT_BLUE, style_ansi(Background.BRIGHT_BLUE)),
            ("bg", 135, style_ansi(Background.SET, 135)),
            ("bg", (0, 0, 255), style_ansi(Background.SET, 0, 0, 255)),
            ("ul", 135, style_ansi(Underline.SET, 135)),
            ("ul", (0, 0, 255), style_ansi(Underline.SET, 0, 0, 255)),
        ],
    )
    def test_unified_colors(self, method_name: str, color_val: Any, expected_code: str):
        s_range = getattr(ANSIString("Hello, World!"), method_name)(color_val, (0, 5))
        assert str(s_range) == ansi_wrap("Hello", expected_code) + ", World!", (
            f"{method_name} range mismatch"
        )

        s_word = getattr(ANSIString("Hello, World!"), method_name)(
            color_val, Words(("Hello",))
        )
        assert str(s_word) == ansi_wrap("Hello", expected_code) + ", World!", (
            f"{method_name} word mismatch"
        )

        s_whole = getattr(ANSIString("Hello, World!"), method_name)(color_val)
        assert str(s_whole) == ansi_wrap("Hello, World!", expected_code), (
            f"{method_name} whole mismatch"
        )

    def test_multiple_color_targets(self):
        s = (
            ANSIString("Hello, World!")
            .fg((0, 0, 255), (0, 5))
            .fg(Foreground.YELLOW, Words(("World",)))
        )
        blue = style_ansi(Foreground.SET, 0, 0, 255)
        yellow = style_ansi(Foreground.YELLOW)
        expected = ansi_wrap("Hello", blue) + ", " + ansi_wrap("World", yellow) + "!"
        assert str(s) == expected


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
        s = ANSIString("Hello, World!").ul((0, 128, 255)).style(mode)
        expected = f"{ul_ansi}Hello, World!{RESET}"
        assert str(s) == expected, f"Mode {mode.name} with color mismatch"

    def test_word_targeted_mode(self):
        mode = UnderlineMode.DOUBLE
        ul_ansi = Style().with_style(Underline.SET, 135).with_style(mode).to_ansi()
        s = (
            ANSIString("Hello, World!")
            .ul(135, Words(("World",)))
            .style(mode, Words(("World",)))
        )
        expected = "Hello, " + f"{ul_ansi}World{RESET}" + "!"
        assert str(s) == expected, "Word-targeted underline mode mismatch"


class TestGradient:
    def test_defaults_to_foreground(self):
        s = ANSIString("abc").gradient(
            [(255, 0, 0), (0, 0, 255)],
            (0, 1),
            (1, 2),
            (2, 3),
            space="rgb",
        )

        assert len(s.style_manager) == 3
        assert s.style_manager[0].foreground.to_rgb() == (255, 0, 0)
        assert s.style_manager[1].foreground.to_rgb() == (128, 0, 128)
        assert s.style_manager[2].foreground.to_rgb() == (0, 0, 255)
        assert not s.style_manager[0].background
        assert not s.style_manager[0].underline[0]

    def test_skips_whitespace_when_no_slices(self):
        s = ANSIString("a b").gradient(
            [(255, 0, 0), (0, 0, 255)],
            Chars(skip_whitespace=True),
            space="rgb",
        )

        assert 1 not in s.style_manager
        assert s.style_manager[0].foreground.to_rgb() == (255, 0, 0)
        assert s.style_manager[2].foreground.to_rgb() == (0, 0, 255)

    def test_hsl_space_interpolates_in_hsl(self):
        s = ANSIString("abc").gradient(
            [(255, 0, 0), (0, 255, 0)],
            (0, 1),
            (1, 2),
            (2, 3),
            space="hsl",
        )

        assert s.style_manager[0].foreground.to_rgb() == (255, 0, 0)
        assert s.style_manager[1].foreground.to_rgb() == (255, 255, 0)
        assert s.style_manager[2].foreground.to_rgb() == (0, 255, 0)

    def test_grouped_slices_share_same_color(self):
        s = ANSIString("abc").gradient(
            [(255, 0, 0), (0, 0, 255)],
            ((0, 1), (2, 3)),
            (1, 2),
            space="rgb",
        )

        assert s.style_manager[0].foreground.to_rgb() == (255, 0, 0)
        assert s.style_manager[2].foreground.to_rgb() == (255, 0, 0)
        assert s.style_manager[1].foreground.to_rgb() == (0, 0, 255)

    def test_emojis_colored_as_single_block(self):
        """
        Verify emojis are treated as a single styling block to protect ZWJ sequences.
        """
        s = ANSIString("a👩‍🚀b").gradient([(255, 0, 0), (0, 0, 255)], space="rgb")

        assert s.style_manager[0].foreground.to_rgb() == (255, 0, 0)
        assert s.style_manager[1].foreground.to_rgb() == (128, 0, 128)
        assert s.style_manager[2].foreground.to_rgb() == (128, 0, 128)
        assert s.style_manager[3].foreground.to_rgb() == (128, 0, 128)
        assert s.style_manager[4].foreground.to_rgb() == (0, 0, 255)

    def test_skip_emojis_flag(self):
        """Verify skip_emojis drops the emoji indices entirely."""
        s = ANSIString("a👩‍🚀b").gradient(
            [(255, 0, 0), (0, 0, 255)], Chars(skip_emojis=True), space="rgb"
        )

        assert 0 in s.style_manager
        assert s.style_manager[0].foreground.to_rgb() == (255, 0, 0)

        assert 1 not in s.style_manager
        assert 2 not in s.style_manager
        assert 3 not in s.style_manager

        assert 4 in s.style_manager
        assert s.style_manager[4].foreground.to_rgb() == (0, 0, 255)

    @pytest.mark.parametrize(
        "plain_text, words, colors, word_options, "
        "grad_options, expected_fg, expected_bg, absent",
        [
            pytest.param(
                "Red blue RED",
                ("red", "blue"),
                [(255, 0, 0), (0, 0, 255)],
                {"ignore_case": True},
                {"space": "rgb"},
                {0: (255, 0, 0), 4: (128, 0, 128), 9: (0, 0, 255)},
                {},
                {3, 8},
                id="rgb-case-insensitive",
            ),
            pytest.param(
                "aa bb cc",
                ("aa", "bb", "cc"),
                [(255, 0, 0), (0, 255, 0)],
                {},
                {"channel": Channel.BG, "space": "hsl"},
                {},
                {0: (255, 0, 0), 3: (255, 255, 0), 6: (0, 255, 0)},
                set[int](),
                id="hsl-targets-bg",
            ),
        ],
    )
    def test_words_cases(
        self,
        plain_text: str,
        words: tuple[str, ...],
        colors: tuple[tuple[int, int, int], ...],
        word_options: dict[str, Any],
        grad_options: dict[str, Any],
        expected_fg: dict[int, tuple[int, int, int]],
        expected_bg: dict[int, tuple[int, int, int]],
        absent: set[int],
    ):
        s = ANSIString(plain_text).gradient(
            list(colors), Words(words, **word_options), **grad_options
        )

        for index, rgb in expected_fg.items():
            assert s.style_manager[index].foreground.to_rgb() == rgb
        for index, rgb in expected_bg.items():
            assert s.style_manager[index].background.to_rgb() == rgb
        for index in absent:
            assert index not in s.style_manager

    @pytest.mark.parametrize(
        "plain_text, coordinates, options, expected_fg, expected_bg",
        [
            pytest.param(
                "ab\ncd",
                ((0, 0), (1, 1)),
                {"space": "rgb", "system": "terminal"},
                {0: (255, 0, 0), 4: (0, 0, 255)},
                {},
                id="terminal",
            ),
            pytest.param(
                "ab\ncd",
                (((0, 0), (1, 0)),),
                {"space": "rgb", "system": "cartesian"},
                {3: (255, 0, 0), 4: (255, 0, 0)},
                {},
                id="cartesian",
            ),
            pytest.param(
                "abc\ndef",
                ((1, 1),),
                {
                    "space": "rgb",
                    "system": "terminal",
                    "index_base": 1,
                    "origin": (1, 1),
                },
                {5: (255, 0, 0)},
                {},
                id="origin-terminal",
            ),
            pytest.param(
                "abc",
                ((0, 0), (1, 0), (2, 0)),
                {"channel": Channel.BG, "space": "hsl"},
                {},
                {0: (255, 0, 0), 1: (255, 255, 0), 2: (0, 255, 0)},
                id="hsl-targets-bg",
            ),
        ],
    )
    def test_coordinates_cases(
        self,
        plain_text: str,
        coordinates: tuple[tuple[int, int] | tuple[tuple[int, int], ...], ...],
        options: dict[str, Any],
        expected_fg: dict[int, tuple[int, int, int]],
        expected_bg: dict[int, tuple[int, int, int]],
    ):
        grad_colors = (
            [(255, 0, 0), (0, 0, 255)]
            if options.get("space") == "rgb"
            else [(255, 0, 0), (0, 255, 0)]
        )
        coord_kwargs = {
            k: v
            for k, v in options.items()
            if k in ("system", "index_base", "origin", "on_out_of_bounds")
        }
        grad_kwargs = {k: v for k, v in options.items() if k in ("space", "channel")}

        s = ANSIString(plain_text).gradient(
            grad_colors, Coords(coordinates, **coord_kwargs), **grad_kwargs
        )

        for index, rgb in expected_fg.items():
            assert s.style_manager[index].foreground.to_rgb() == rgb
        for index, rgb in expected_bg.items():
            assert s.style_manager[index].background.to_rgb() == rgb

    def test_coordinates_out_of_bounds_modes(self):
        ignored = ANSIString("ab").gradient(
            [(255, 0, 0), (0, 0, 255)],
            Coords(
                ((5, 0), (0, 0)),
                on_out_of_bounds="ignore",
            ),
            space="rgb",
        )
        assert len(ignored.style_manager) == 1
        assert ignored.style_manager[0].foreground.to_rgb() == (255, 0, 0)

        clamped = ANSIString("ab").gradient(
            [(255, 0, 0), (0, 0, 255)],
            Coords(
                ((5, 0),),
                on_out_of_bounds="clamp",
            ),
            space="rgb",
        )
        assert len(clamped.style_manager) == 1
        assert clamped.style_manager[1].foreground.to_rgb() == (255, 0, 0)

        with pytest.raises(IndexError, match="out of bounds"):
            ANSIString("ab").gradient(
                [(255, 0, 0), (0, 0, 255)],
                Coords(
                    ((5, 0),),
                    on_out_of_bounds="raise",
                ),
                space="rgb",
            )

    def test_coordinates_group_with_single_valid_coordinate_flattens(self):
        s = ANSIString("ab").gradient(
            [(255, 0, 0), (0, 0, 255)],
            Coords(
                (((0, 0), (99, 0)),),
                on_out_of_bounds="ignore",
            ),
            space="rgb",
        )
        assert len(s.style_manager) == 1
        assert s.style_manager[0].foreground.to_rgb() == (255, 0, 0)

    def test_coordinates_clamp_skips_empty_line(self):
        s = ANSIString("a\n\nb").gradient(
            [(255, 0, 0), (0, 0, 255)],
            Coords(
                ((5, 1),),
                on_out_of_bounds="clamp",
            ),
            space="rgb",
        )
        assert not s.style_manager

    def test_coordinates_emojis_colored_as_single_block(self):
        """Verify gradient does not slice emojis in half when targeting coordinates."""
        s = ANSIString("a👩‍🚀b").gradient(
            [(255, 0, 0), (0, 0, 255)], Coords(((1, 0),)), space="rgb"
        )

        msg = "'a' (index 0) was not targeted, should be unstyled"
        assert 0 not in s.style_manager, msg

        msg = "The engine must expand coordinate x=1 to the full grapheme span (1, 4)"
        assert 1 in s.style_manager, msg
        assert 2 in s.style_manager, msg
        assert 3 in s.style_manager, msg

        msg = "The whole emoji must share the exact same color to not break the ZWJ"
        color = s.style_manager[1].foreground.to_rgb()
        assert s.style_manager[2].foreground.to_rgb() == color, msg
        assert s.style_manager[3].foreground.to_rgb() == color, msg


class TestRainbow:
    def test_fg_rainbow_styles_all_chars(self):
        s = ANSIString("abcdefghij").rainbow()
        assert len(s.style_manager) == 10, "Rainbow should style every character"

    def test_bg_rainbow(self):
        s = ANSIString("abcdefghij").rainbow(channel=Channel.BG)
        assert len(s.style_manager) == 10
        assert s.style_manager[0].background, "Channel.BG should set background colors"

    @pytest.mark.parametrize(
        "ws_index",
        [pytest.param(1, id="space-at-1"), pytest.param(3, id="space-at-3")],
    )
    def test_skip_whitespace(self, ws_index: int):
        s = ANSIString("a b c").rainbow(Chars(skip_whitespace=True))
        assert ws_index not in s.style_manager, (
            f"Index {ws_index} (whitespace) should be skipped"
        )

    def test_skip_emojis(self):
        s = ANSIString("a👍🏽b").rainbow(Chars(skip_emojis=True))
        assert 0 in s.style_manager
        assert 1 not in s.style_manager  # 👍
        assert 2 not in s.style_manager  # 🏽
        assert 3 in s.style_manager

    def test_rainbow_matches_expected_palette(self):
        """Verify a known output for the builtin rainbow on the alphabet."""
        s = ANSIString("abcdefghijklmnopqrstuvwxyz").rainbow(
            Chars(skip_whitespace=True)
        )
        expected = ANSIString(
            "abcdefghijklmnopqrstuvwxyz",
            {
                0: "\x1b[38;2;255;0;0m",
                1: "\x1b[38;2;255;60;0m",
                2: "\x1b[38;2;255;123;0m",
                3: "\x1b[38;2;255;183;0m",
                4: "\x1b[38;2;255;247;0m",
                5: "\x1b[38;2;204;255;0m",
                6: "\x1b[38;2;144;255;0m",
                7: "\x1b[38;2;81;255;0m",
                8: "\x1b[38;2;21;255;0m",
                9: "\x1b[38;2;0;255;43m",
                10: "\x1b[38;2;0;255;102m",
                11: "\x1b[38;2;0;255;162m",
                12: "\x1b[38;2;0;255;225m",
                13: "\x1b[38;2;0;225;255m",
                14: "\x1b[38;2;0;161;255m",
                15: "\x1b[38;2;0;102;255m",
                16: "\x1b[38;2;0;43;255m",
                17: "\x1b[38;2;21;0;255m",
                18: "\x1b[38;2;81;0;255m",
                19: "\x1b[38;2;144;0;255m",
                20: "\x1b[38;2;204;0;255m",
                21: "\x1b[38;2;255;0;246m",
                22: "\x1b[38;2;255;0;183m",
                23: "\x1b[38;2;255;0;123m",
                24: "\x1b[38;2;255;0;59m",
                25: "\x1b[38;2;255;0;0m",
            },
        )
        assert str(s) == str(expected), "Rainbow palette must match known output"


class TestColorMap:
    @staticmethod
    def _cmap() -> ColorMap:
        return ColorMap(
            scale=ColorScale([(255, 0, 0), (0, 255, 0)], "rgb"),
            vmin=0,
            vmax=10,
            under_color=(128, 128, 128),
            over_color=(0, 0, 255),
        )

    def test_int_numbers_colored(self):
        s = ANSIString("0, 3, 9").colormap(self._cmap(), Pattern.numeric())
        expected = (
            ansi_wrap("0", "\x1b[38:2::255:0:0m")
            + ", "
            + ansi_wrap("3", "\x1b[38:2::178:76:0m")
            + ", "
            + ansi_wrap("9", "\x1b[38:2::26:230:0m")
        )
        assert str(s) == expected

    def test_float_numbers_colored(self):
        s = ANSIString("0.0, 3.14, 9.123").colormap(self._cmap(), Pattern.numeric())
        expected = (
            ansi_wrap("0.0", "\x1b[38:2::255:0:0m")
            + ", "
            + ansi_wrap("3.14", "\x1b[38:2::175:80:0m")
            + ", "
            + ansi_wrap("9.123", "\x1b[38:2::22:233:0m")
        )
        assert str(s) == expected

    def test_float_trailing_decimal_point(self):
        s = ANSIString("0., 3., 9.").colormap(self._cmap(), Pattern.numeric())
        expected = (
            ansi_wrap("0", "\x1b[38:2::255:0:0m")
            + "., "
            + ansi_wrap("3", "\x1b[38:2::178:76:0m")
            + "., "
            + ansi_wrap("9", "\x1b[38:2::26:230:0m")
            + "."
        )
        assert str(s) == expected

    def test_values_overflow(self):
        s = ANSIString("0, -3.14, 10.123").colormap(self._cmap(), Pattern.numeric())
        expected = (
            ansi_wrap("0", "\x1b[38:2::255:0:0m")
            + ", "
            + ansi_wrap("-3.14", "\x1b[38:2::128:128:128m")
            + ", "
            + ansi_wrap("10.123", "\x1b[38:2::0:0:255m")
            + ""
        )
        assert str(s) == expected

    def test_slices_colored(self):
        s = ANSIString("Ready | Go! | Steady? | Go! | Oh, wait...").colormap(
            self._cmap(),
            (0, 5),
            (8, 11),
            (14, 21),
            (24, 27),
            (30, 41),
            values=(0, 10, 5, 10, -999),
        )
        expected = (
            ansi_wrap("Ready", "\x1b[38:2::255:0:0m")
            + " | "
            + ansi_wrap("Go!", "\x1b[38:2::0:255:0m")
            + " | "
            + ansi_wrap("Steady?", "\x1b[38:2::128:128:0m")
            + " | "
            + ansi_wrap("Go!", "\x1b[38:2::0:255:0m")
            + " | "
            + ansi_wrap("Oh, wait...", "\x1b[38:2::128:128:128m")
        )
        assert str(s) == expected

    def test_custom_pattern(self):
        s = ANSIString("CPU: 4%, RAM: 8%").colormap(self._cmap(), Pattern(r"\d+(?=%)"))
        expected = (
            "CPU: "
            + ansi_wrap("4", "\x1b[38:2::153:102:0m")
            + "%, "
            + "RAM: "
            + ansi_wrap("8", "\x1b[38:2::51:204:0m")
            + "%"
        )
        assert str(s) == expected

    def test_bg_channel(self):
        s = ANSIString("5").colormap(
            self._cmap(), Pattern.numeric(), channel=Channel.BG
        )
        expected = ansi_wrap("5", "\x1b[48:2::128:128:0m")
        assert str(s) == expected

    def test_colormap_slices_with_emojis(self):
        """Verify automatic slice generation respects emojis."""
        s = ANSIString("1️⃣2️⃣").colormap(self._cmap(), Chars(), values=(0, 10))

        assert s.style_manager[0].foreground.to_rgb() == (255, 0, 0)
        assert s.style_manager[1].foreground.to_rgb() == (255, 0, 0)
        assert s.style_manager[2].foreground.to_rgb() == (255, 0, 0)

        assert s.style_manager[3].foreground.to_rgb() == (0, 255, 0)
        assert s.style_manager[4].foreground.to_rgb() == (0, 255, 0)
        assert s.style_manager[5].foreground.to_rgb() == (0, 255, 0)


class TestSegmentedColorMap:
    @staticmethod
    def _cmap() -> SegmentedColorMap:
        return SegmentedColorMap(
            segments={
                0: (0, 255, 0),
                50: (255, 255, 0),
                90: (255, 0, 0),
            },
            over_color=(255, 0, 255),
        )

    def test_segmented_exact_boundaries(self):
        s = ANSIString("0, 50, 90").colormap(self._cmap(), Pattern.numeric())
        expected = (
            ansi_wrap("0", "\x1b[38:2::0:255:0m")
            + ", "
            + ansi_wrap("50", "\x1b[38:2::255:255:0m")
            + ", "
            + ansi_wrap("90", "\x1b[38:2::255:0:0m")
        )
        assert str(s) == expected

    def test_segmented_between_boundaries(self):
        s = ANSIString("-10, 25, 75").colormap(self._cmap(), Pattern.numeric())
        expected = (
            ansi_wrap("-10", "\x1b[38:2::0:255:0m")
            + ", "
            + ansi_wrap("25", "\x1b[38:2::255:255:0m")
            + ", "
            + ansi_wrap("75", "\x1b[38:2::255:0:0m")
        )
        assert str(s) == expected

    def test_segmented_over_color(self):
        s = ANSIString("91, 999").colormap(self._cmap(), Pattern.numeric())
        expected = (
            ansi_wrap("91", "\x1b[38:2::255:0:255m")
            + ", "
            + ansi_wrap("999", "\x1b[38:2::255:0:255m")
        )
        assert str(s) == expected

    def test_segmented_slices_colored(self):
        """Verify colormap_slices integration with SegmentedColorMap."""
        s = ANSIString("OK | WARN | CRIT").colormap(
            self._cmap(), (0, 2), (5, 9), (12, 16), values=(0, 45, 85)
        )
        expected = (
            ansi_wrap("OK", "\x1b[38:2::0:255:0m")
            + " | "
            + ansi_wrap("WARN", "\x1b[38:2::255:255:0m")
            + " | "
            + ansi_wrap("CRIT", "\x1b[38:2::255:0:0m")
        )
        assert str(s) == expected
