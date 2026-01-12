import sys
import unittest

from pyansistring import ANSIString, StyleManager # type: ignore
from pyansistring.style import Style, Color  # type: ignore
from pyansistring.constants import *


output: list[tuple[str, str, str, str]] = []


class ExtendedAssertMixin:
    def get_function_name(self, depth: int = 0) -> str:
        return sys._getframe(depth).f_code.co_name  # type: ignore

    def extended_assert_equal(
        self,
        actual: str | ANSIString,
        expected: str | ANSIString,
        verbose: bool = True,
        function_name: str | None = None,
        comment: str = "",
    ):
        if not function_name:
            function_name = self.get_function_name(depth=2)
        actual = str(actual)
        expected = str(expected)
        if verbose:
            output.append((function_name, comment, actual, expected))
        self.assertEqual(actual, expected) # type: ignore
        self.assertEqual(str(eval(repr(actual))), expected) # type: ignore


class ANSIStringFeatureTest(ExtendedAssertMixin, unittest.TestCase):
    def test_plain(self):
        actual = ANSIString("Hello, World!")
        expected = "Hello, World!"
        self.extended_assert_equal(actual, expected)

    def test_fm(self):
        bold = Style().with_style(SGR.BOLD).to_ansi()
        italic = Style().with_style(SGR.ITALIC).to_ansi()
        res = f"\x1b[0m"
        actual = (
            ANSIString("Hello, World!").fm(SGR.BOLD),
            ANSIString("Hello, World!").fm(SGR.BOLD, (0, 5)),
            ANSIString("Hello, World!").fm(SGR.BOLD, (0, 5), slice(7, 12)),
            ANSIString("Hello, World!").fm(SGR.BOLD).fm(SGR.ITALIC),
        )
        expected = (
            "".join(f"{bold}{char}{res}" for char in "Hello, World!"),
            "".join(f"{bold}{char}{res}" for char in "Hello") + ", World!",
            "".join(f"{bold}{char}{res}" for char in "Hello")
            + ", "
            + "".join(f"{bold}{char}{res}" for char in "World")
            + "!",
            "".join(f"{bold}{italic}{char}{res}" for char in "Hello, World!"),
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_fm_w(self):
        bold = Style().with_style(SGR.BOLD).to_ansi()
        italic = Style().with_style(SGR.ITALIC).to_ansi()
        res = f"\x1b[0m"
        actual = (
            ANSIString("Hello, World!").fm_w(SGR.BOLD, "Hello"),
            ANSIString("Hello, World!").fm_w(SGR.ITALIC, "world", case_sensitive=False),
        )
        expected = (
            "".join(f"{bold}{char}{res}" for char in "Hello") + ", World!",
            "Hello, " + "".join(f"{italic}{char}{res}" for char in "World") + "!",
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_unfm(self):
        actual = (
            ANSIString("Hello, World!").fm(SGR.BOLD).unfm(),
            ANSIString("Hello, World!").fm(SGR.BOLD, (0, 5)).unfm((0, 5)),
            ANSIString("Hello, World!")
            .fm(SGR.BOLD, (0, 5), slice(7, 12))
            .unfm((0, 5), slice(7, 12)),
        )
        expected = (
            "Hello, World!",
            "Hello, World!",
            "Hello, World!",
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_unfm_w(self):
        actual = (
            ANSIString("Hello, World!").fm_w(SGR.BOLD, "Hello").unfm_w("Hello"),
            ANSIString("Hello, World!")
            .fm_w(SGR.ITALIC, "world", case_sensitive=False)
            .unfm_w("world", case_sensitive=False),
        )
        expected = (
            "Hello, World!",
            "Hello, World!",
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_fg_4b(self):
        bright_blue = Style().with_style(Foreground.BRIGHT_BLUE).to_ansi()
        bright_yellow = Style().with_style(Foreground.BRIGHT_YELLOW).to_ansi()
        res = f"\x1b[0m"
        actual = (
            ANSIString("Hello, World!")
            .fg_4b(Foreground.BRIGHT_BLUE, (0, 5))
            .fg_4b(Foreground.BRIGHT_YELLOW, (7, 12)),
        )
        expected = (
            "".join(f"{bright_blue}{char}{res}" for char in "Hello")
            + ", "
            + "".join(f"{bright_yellow}{char}{res}" for char in "World")
            + "!",
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_fg_4b_w(self):
        bright_blue = Style().with_style(Foreground.BRIGHT_BLUE).to_ansi()
        bright_yellow = Style().with_style(Foreground.BRIGHT_YELLOW).to_ansi()
        res = f"\x1b[0m"
        actual = (
            ANSIString("Hello, World!")
            .fg_4b_w(Foreground.BRIGHT_BLUE, "Hello")
            .fg_4b_w(Foreground.BRIGHT_YELLOW, "World"),
        )
        expected = (
            "".join(f"{bright_blue}{char}{res}" for char in "Hello")
            + ", "
            + "".join(f"{bright_yellow}{char}{res}" for char in "World")
            + "!",
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_fg_8b(self):
        color = Style().with_style(Foreground.SET, 135).to_ansi()
        res = f"\x1b[0m"
        actual = (ANSIString("Hello, World!").fg_8b(135),)
        expected = ("".join(f"{color}{char}{res}" for char in "Hello, World!"),)
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_fg_8b_w(self):
        color = Style().with_style(Foreground.SET, 135).to_ansi()
        res = f"\x1b[0m"
        actual = (ANSIString("Hello, World!").fg_8b_w(135, "Hello, ", "World!"),)
        expected = ("".join(f"{color}{char}{res}" for char in "Hello, World!"),)
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_fg_24b(self):
        blue = Style().with_style(Foreground.SET, 0, 0, 255).to_ansi()
        yellow = Style().with_style(Foreground.SET, 255, 255, 0).to_ansi()
        res = f"\x1b[0m"
        actual = (
            ANSIString("Hello, World!")
            .fg_24b(0, 0, 255, (0, 5))
            .fg_24b(255, 255, 0, (7, 12)),
        )
        expected = (
            "".join(f"{blue}{char}{res}" for char in "Hello")
            + ", "
            + "".join(f"{yellow}{char}{res}" for char in "World")
            + "!",
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_fg_24b_w(self):
        blue = Style().with_style(Foreground.SET, 0, 0, 255).to_ansi()
        yellow = Style().with_style(Foreground.SET, 255, 255, 0).to_ansi()
        res = f"\x1b[0m"
        actual = (
            ANSIString("Hello, World!")
            .fg_24b_w(0, 0, 255, "Hello")
            .fg_24b_w(255, 255, 0, "World"),
        )
        expected = (
            "".join(f"{blue}{char}{res}" for char in "Hello")
            + ", "
            + "".join(f"{yellow}{char}{res}" for char in "World")
            + "!",
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_bg_4b(self):
        bright_blue = Style().with_style(Background.BRIGHT_BLUE).to_ansi()
        bright_yellow = Style().with_style(Background.BRIGHT_YELLOW).to_ansi()
        res = f"\x1b[0m"
        actual = (
            ANSIString("Hello, World!")
            .bg_4b(Background.BRIGHT_BLUE, (0, 5))
            .bg_4b(Background.BRIGHT_YELLOW, (7, 12)),
        )
        expected = (
            "".join(f"{bright_blue}{char}{res}" for char in "Hello")
            + ", "
            + "".join(f"{bright_yellow}{char}{res}" for char in "World")
            + "!",
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_bg_4b_w(self):
        bright_blue = Style().with_style(Background.BRIGHT_BLUE).to_ansi()
        bright_yellow = Style().with_style(Background.BRIGHT_YELLOW).to_ansi()
        res = f"\x1b[0m"
        actual = (
            ANSIString("Hello, World!")
            .bg_4b_w(Background.BRIGHT_BLUE, "Hello")
            .bg_4b_w(Background.BRIGHT_YELLOW, "World"),
        )
        expected = (
            "".join(f"{bright_blue}{char}{res}" for char in "Hello")
            + ", "
            + "".join(f"{bright_yellow}{char}{res}" for char in "World")
            + "!",
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_bg_8b(self):
        color = Style().with_style(Background.SET, 135).to_ansi()
        res = f"\x1b[0m"
        actual = (ANSIString("Hello, World!").bg_8b(135),)
        expected = ("".join(f"{color}{char}{res}" for char in "Hello, World!"),)
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_bg_8b_w(self):
        color = Style().with_style(Background.SET, 135).to_ansi()
        res = f"\x1b[0m"
        actual = (ANSIString("Hello, World!").bg_8b_w(135, "Hello, ", "World!"),)
        expected = ("".join(f"{color}{char}{res}" for char in "Hello, World!"),)
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_bg_24b(self):
        blue = Style().with_style(Background.SET, 0, 0, 255).to_ansi()
        yellow = Style().with_style(Background.SET, 255, 255, 0).to_ansi()
        res = f"\x1b[0m"
        actual = (
            ANSIString("Hello, World!")
            .bg_24b(0, 0, 255, (0, 5))
            .bg_24b(255, 255, 0, (7, 12)),
        )
        expected = (
            "".join(f"{blue}{char}{res}" for char in "Hello")
            + ", "
            + "".join(f"{yellow}{char}{res}" for char in "World")
            + "!",
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_bg_24b_w(self):
        blue = Style().with_style(Background.SET, 0, 0, 255).to_ansi()
        yellow = Style().with_style(Background.SET, 255, 255, 0).to_ansi()
        res = f"\x1b[0m"
        actual = (
            ANSIString("Hello, World!")
            .bg_24b_w(0, 0, 255, "Hello")
            .bg_24b_w(255, 255, 0, "World"),
        )
        expected = (
            "".join(f"{blue}{char}{res}" for char in "Hello")
            + ", "
            + "".join(f"{yellow}{char}{res}" for char in "World")
            + "!",
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_from_ansi(self):
        blue = f"\x1b[38;2;0;0;255m"
        yellow = f"\x1b[38;2;255;255;0m"
        res = f"\x1b[0m"
        plain = (
            f"\x1b[10;10H{''.join(f'{blue}{char}{res}' for char in 'Hello')}, {yellow}World{res}!{res*3}",
            ANSIString("Hello, World!")
            .fg_24b_w(0, 0, 255, "Hello")
            .fg_24b_w(255, 255, 0, "World")
            .styled_text,
        )
        styles = {index: Style.from_ansi(blue) for index in range(0, 5)} | {
            index: Style.from_ansi(yellow) for index in range(7, 12)
        }
        actual = (ANSIString.from_ansi(p) for p in plain)
        expected = ANSIString("Hello, World!", styles)
        for a in actual:
            self.extended_assert_equal(a, expected)
            self.assertDictEqual(a.style_manager, expected.style_manager)

    def test_rainbow(self):
        actual = (
            ANSIString("abcdefghijklmnopqrstuvwxyz").rainbow(skip_whitespace=True),
            ANSIString("abcdefghijklmnopqrstuvwxyz").rainbow(bg=True),
        )
        expected = (
            ANSIString(
                "abcdefghijklmnopqrstuvwxyz",
                {
                    0: "\x1b[38;2;255;0;0m", 1: "\x1b[38;2;255;60;0m",
                    2: "\x1b[38;2;255;119;0m", 3: "\x1b[38;2;255;179;0m",
                    4: "\x1b[38;2;255;234;0m", 5: "\x1b[38;2;217;255;0m",
                    6: "\x1b[38;2;157;255;0m", 7: "\x1b[38;2;98;255;0m",
                    8: "\x1b[38;2;38;255;0m", 9: "\x1b[38;2;0;255;21m",
                    10: "\x1b[38;2;0;255;76m", 11: "\x1b[38;2;0;255;136m",
                    12: "\x1b[38;2;0;255;195m", 13: "\x1b[38;2;0;255;255m",
                    14: "\x1b[38;2;0;195;255m", 15: "\x1b[38;2;0;136;255m",
                    16: "\x1b[38;2;0;76;255m", 17: "\x1b[38;2;0;21;255m",
                    18: "\x1b[38;2;38;0;255m", 19: "\x1b[38;2;98;0;255m",
                    20: "\x1b[38;2;157;0;255m", 21: "\x1b[38;2;217;0;255m",
                    22: "\x1b[38;2;255;0;234m", 23: "\x1b[38;2;255;0;178m",
                    24: "\x1b[38;2;255;0;119m", 25: "\x1b[38;2;255;0;60m",
                }
            ),
            ANSIString(
                "abcdefghijklmnopqrstuvwxyz",
                {
                    0: "\x1b[48;2;255;0;0m", 1: "\x1b[48;2;255;60;0m",
                    2: "\x1b[48;2;255;119;0m", 3: "\x1b[48;2;255;179;0m",
                    4: "\x1b[48;2;255;234;0m", 5: "\x1b[48;2;217;255;0m",
                    6: "\x1b[48;2;157;255;0m", 7: "\x1b[48;2;98;255;0m",
                    8: "\x1b[48;2;38;255;0m", 9: "\x1b[48;2;0;255;21m",
                    10: "\x1b[48;2;0;255;76m", 11: "\x1b[48;2;0;255;136m",
                    12: "\x1b[48;2;0;255;195m", 13: "\x1b[48;2;0;255;255m",
                    14: "\x1b[48;2;0;195;255m", 15: "\x1b[48;2;0;136;255m",
                    16: "\x1b[48;2;0;76;255m", 17: "\x1b[48;2;0;21;255m",
                    18: "\x1b[48;2;38;0;255m", 19: "\x1b[48;2;98;0;255m",
                    20: "\x1b[48;2;157;0;255m", 21: "\x1b[48;2;217;0;255m",
                    22: "\x1b[48;2;255;0;234m", 23: "\x1b[48;2;255;0;178m",
                    24: "\x1b[48;2;255;0;119m", 25: "\x1b[48;2;255;0;60m",
                }
            ),
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_multicolor(self):
        string = "abcdefghijklmnopqrstuvwxyz"
        actual = (
            ANSIString(string).multicolor(MulticolorSequences.RAINBOW),
            ANSIString(string).multicolor(MulticolorSequences.REVERSED_RAINBOW),
            ANSIString(string).multicolor(
                "r=84:|g=161:|b=255: $ r+9:minmax(0,inf)|g+4:minmax(0,inf) &*"
            ),
            ANSIString(string).multicolor(
                "r=84:|g=161:|b=255: $ r+9:minmax(0,inf)|g+4:minmax(0,inf) @&*"
            ),
            ANSIString(string).multicolor(
                "r=84:|g=161:|b=255: $ r+50:minmax(0,inf)|g+25:minmax(0,inf) # b-70:minmax(0,inf) !&*"
            ),
        )
        expected = (
            ANSIString(
                "abcdefghijklmnopqrstuvwxyz",
                {
                    0: "\x1b[38;2;255;0;0m", 1: "\x1b[38;2;255;51;0m",
                    2: "\x1b[38;2;255;102;0m", 3: "\x1b[38;2;255;153;0m",
                    4: "\x1b[38;2;255;204;0m", 5: "\x1b[38;2;255;255;0m",
                    6: "\x1b[38;2;191;255;0m", 7: "\x1b[38;2;127;255;0m",
                    8: "\x1b[38;2;63;255;0m", 9: "\x1b[38;2;0;255;0m",
                    10: "\x1b[38;2;0;255;63m", 11: "\x1b[38;2;0;255;127m",
                    12: "\x1b[38;2;0;255;191m", 13: "\x1b[38;2;0;255;255m",
                    14: "\x1b[38;2;0;191;255m", 15: "\x1b[38;2;0;127;255m",
                    16: "\x1b[38;2;0;63;255m", 17: "\x1b[38;2;0;0;255m",
                    18: "\x1b[38;2;63;0;255m", 19: "\x1b[38;2;127;0;255m",
                    20: "\x1b[38;2;191;0;255m", 21: "\x1b[38;2;255;0;255m",
                    22: "\x1b[38;2;255;0;191m", 23: "\x1b[38;2;255;0;127m",
                    24: "\x1b[38;2;255;0;63m", 25: "\x1b[38;2;255;0;0m",
                },
            ),
            ANSIString(
                "abcdefghijklmnopqrstuvwxyz",
                {
                    0: "\x1b[38;2;255;0;0m", 1: "\x1b[38;2;255;0;63m",
                    2: "\x1b[38;2;255;0;127m", 3: "\x1b[38;2;255;0;191m",
                    4: "\x1b[38;2;255;0;255m", 5: "\x1b[38;2;191;0;255m",
                    6: "\x1b[38;2;127;0;255m", 7: "\x1b[38;2;63;0;255m",
                    8: "\x1b[38;2;0;0;255m", 9: "\x1b[38;2;0;63;255m",
                    10: "\x1b[38;2;0;127;255m", 11: "\x1b[38;2;0;191;255m",
                    12: "\x1b[38;2;0;255;255m", 13: "\x1b[38;2;0;255;191m",
                    14: "\x1b[38;2;0;255;127m", 15: "\x1b[38;2;0;255;63m",
                    16: "\x1b[38;2;0;255;0m", 17: "\x1b[38;2;63;255;0m",
                    18: "\x1b[38;2;127;255;0m", 19: "\x1b[38;2;191;255;0m",
                    20: "\x1b[38;2;255;255;0m", 21: "\x1b[38;2;255;204;0m",
                    22: "\x1b[38;2;255;153;0m", 23: "\x1b[38;2;255;102;0m",
                    24: "\x1b[38;2;255;51;0m", 25: "\x1b[38;2;255;0;0m",
                },
            ),
            ANSIString(
                "abcdefghijklmnopqrstuvwxyz",
                {
                    0: "\x1b[38;2;84;161;255m", 1: "\x1b[38;2;93;165;255m",
                    2: "\x1b[38;2;102;169;255m", 3: "\x1b[38;2;111;173;255m",
                    4: "\x1b[38;2;120;177;255m", 5: "\x1b[38;2;129;181;255m",
                    6: "\x1b[38;2;138;185;255m", 7: "\x1b[38;2;147;189;255m",
                    8: "\x1b[38;2;156;193;255m", 9: "\x1b[38;2;165;197;255m",
                    10: "\x1b[38;2;174;201;255m", 11: "\x1b[38;2;183;205;255m",
                    12: "\x1b[38;2;192;209;255m", 13: "\x1b[38;2;201;213;255m",
                    14: "\x1b[38;2;210;217;255m", 15: "\x1b[38;2;219;221;255m",
                    16: "\x1b[38;2;228;225;255m", 17: "\x1b[38;2;237;229;255m",
                    18: "\x1b[38;2;246;233;255m", 19: "\x1b[38;2;255;237;255m",
                    20: "\x1b[38;2;255;241;255m", 21: "\x1b[38;2;255;245;255m",
                    22: "\x1b[38;2;255;249;255m", 23: "\x1b[38;2;255;253;255m",
                    24: "\x1b[38;2;255;255;255m", 25: "\x1b[38;2;255;255;255m",
                },
            ),
            ANSIString(
                "abcdefghijklmnopqrstuvwxyz",
                {
                    0: "\x1b[38;2;255;255;255m", 1: "\x1b[38;2;255;255;255m",
                    2: "\x1b[38;2;255;253;255m", 3: "\x1b[38;2;255;249;255m",
                    4: "\x1b[38;2;255;245;255m", 5: "\x1b[38;2;255;241;255m",
                    6: "\x1b[38;2;255;237;255m", 7: "\x1b[38;2;246;233;255m",
                    8: "\x1b[38;2;237;229;255m", 9: "\x1b[38;2;228;225;255m",
                    10: "\x1b[38;2;219;221;255m", 11: "\x1b[38;2;210;217;255m",
                    12: "\x1b[38;2;201;213;255m", 13: "\x1b[38;2;192;209;255m",
                    14: "\x1b[38;2;183;205;255m", 15: "\x1b[38;2;174;201;255m",
                    16: "\x1b[38;2;165;197;255m", 17: "\x1b[38;2;156;193;255m",
                    18: "\x1b[38;2;147;189;255m", 19: "\x1b[38;2;138;185;255m",
                    20: "\x1b[38;2;129;181;255m", 21: "\x1b[38;2;120;177;255m",
                    22: "\x1b[38;2;111;173;255m", 23: "\x1b[38;2;102;169;255m",
                    24: "\x1b[38;2;93;165;255m", 25: "\x1b[38;2;84;161;255m",
                },
            ),
            ANSIString(
                "abcdefghijklmnopqrstuvwxyz",
                {
                    0: "\x1b[38;2;84;161;255m", 1: "\x1b[38;2;134;186;255m",
                    2: "\x1b[38;2;134;186;185m", 3: "\x1b[38;2;134;186;255m",
                    4: "\x1b[38;2;84;161;255m", 5: "\x1b[38;2;134;186;255m",
                    6: "\x1b[38;2;134;186;185m", 7: "\x1b[38;2;134;186;255m",
                    8: "\x1b[38;2;84;161;255m", 9: "\x1b[38;2;134;186;255m",
                    10: "\x1b[38;2;134;186;185m", 11: "\x1b[38;2;134;186;255m",
                    12: "\x1b[38;2;84;161;255m", 13: "\x1b[38;2;134;186;255m",
                    14: "\x1b[38;2;134;186;185m", 15: "\x1b[38;2;134;186;255m",
                    16: "\x1b[38;2;84;161;255m", 17: "\x1b[38;2;134;186;255m",
                    18: "\x1b[38;2;134;186;185m", 19: "\x1b[38;2;134;186;255m",
                    20: "\x1b[38;2;84;161;255m", 21: "\x1b[38;2;134;186;255m",
                    22: "\x1b[38;2;134;186;185m", 23: "\x1b[38;2;134;186;255m",
                    24: "\x1b[38;2;84;161;255m", 25: "\x1b[38;2;134;186;255m",
                },
            ),
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)
        self.assertDictEqual(
            actual[0].style_manager,
            {
                key: value
                for key, value in enumerate(reversed(tuple(actual[1].style_manager.values())))
            },
        )
        self.assertDictEqual(
            actual[2].style_manager,
            {
                key: value
                for key, value in enumerate(reversed(tuple(actual[3].style_manager.values())))
            },
        )

    def test_multicolor_c(self):
        actual = (
            ANSIString("Hello, \nWorld!\n It's pyansistring!")
            .multicolor_c(MulticolorSequences.RAINBOW)
            .style_manager.values()
        )
        expected = (
            ANSIString("Hello, World! It's pyansistring!")
            .multicolor(MulticolorSequences.RAINBOW)
            .style_manager.values()
        )
        for a, e in zip(actual, expected):
            self.assertEqual(a, e)

    def test_to_svg(self):
        # Build a minimal fake TTFont replacement
        class _Glyph:
            def __init__(self, width: int) -> None:
                self.width = width

        class _Head:
            unitsPerEm = 1000

        class _Hhea:
            ascent = 800
            descent = -200
            lineGap = 200

        class _Hmtx:
            def __getitem__(self, key: str):
                return (600, 0)  # width, lsb

        class _Name:
            def getDebugName(self, _):
                return "FakeFont"

        class FakeTTFont:
            def __getitem__(self, key: str):
                if key == "head":
                    return _Head()
                if key == "hhea":
                    return _Hhea()
                if key == "hmtx":
                    return _Hmtx()
                if key == "name":
                    return _Name()
                raise KeyError(key)

            def getBestCmap(self) -> dict[int, str]:
                # Force fallback to ".notdef" for all glyphs
                return {}  # type: ignore

            def getGlyphSet(self):
                return {".notdef": _Glyph(600)}

        # Ensure to_svg does not raise ImportError
        import pyansistring.pyansistring as pas
        pas.is_fonttools_available = True

        # Case 1: fully styled string
        s1 = ANSIString("Hello").fg_24b(255, 0, 0)
        svg1 = s1.to_svg(FakeTTFont(), font_size_px=16)  # type: ignore
        # self.assertTrue(svg1.startswith('<?xml'))
        self.assertIn('<svg ', svg1)
        self.assertIn('</svg>', svg1)
        self.assertIn('font-family="FakeFont"', svg1)
        self.assertEqual(svg1.count('fill="rgb(255, 0, 0)"'), len("Hello"))

        # Case 2: partially styled string
        s2 = ANSIString("Hello, World!").fg_24b(255, 0, 0, (0, 5))
        svg2 = s2.to_svg(FakeTTFont(), font_size_px=16)  # type: ignore
        self.assertEqual(svg2.count('fill="rgb(255, 0, 0)"'), 5)
        self.assertIn("<tspan>,</tspan>", svg2)

    def test_ul_attr(self):
        ul = Style().with_style(SGR.UNDERLINE).to_ansi()
        res = "\x1b[0m"
        actual = (
            ANSIString("Hello, World!").fm(SGR.UNDERLINE),
            ANSIString("Hello, World!").fm(SGR.UNDERLINE, (0, 5)),
            ANSIString("Hello, World!").fm(SGR.UNDERLINE, (0, 5), slice(7, 12)),
        )
        expected = (
            "".join(f"{ul}{c}{res}" for c in "Hello, World!"),
            "".join(f"{ul}{c}{res}" for c in "Hello") + ", World!",
            "".join(f"{ul}{c}{res}" for c in "Hello") + ", " + "".join(f"{ul}{c}{res}" for c in "World") + "!",
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_ul_8b(self):
        ulc = Style().with_style(Underline.SET, 135).to_ansi()
        res = "\x1b[0m"
        actual = (
            ANSIString("Hello, World!").ul_8b(135),
            ANSIString("Hello, World!").ul_8b(135, (0, 5)),
            ANSIString("Hello, World!").ul_8b(135, (0, 5), slice(7, 12)),
        )
        expected = (
            "".join(f"{ulc}{c}{res}" for c in "Hello, World!"),
            "".join(f"{ulc}{c}{res}" for c in "Hello") + ", World!",
            "".join(f"{ulc}{c}{res}" for c in "Hello") + ", " + "".join(f"{ulc}{c}{res}" for c in "World") + "!",
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_ul_8b_w(self):
        ulc = Style().with_style(Underline.SET, 135).to_ansi()
        res = "\x1b[0m"
        actual = (
            ANSIString("Hello, World!").ul_8b_w(135, "Hello"),
            ANSIString("Hello, World!").ul_8b_w(135, "World"),
        )
        expected = (
            "".join(f"{ulc}{c}{res}" for c in "Hello") + ", World!",
            "Hello, " + "".join(f"{ulc}{c}{res}" for c in "World") + "!",
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_ul_24b(self):
        blue_ul = Style().with_style(Underline.SET, 0, 0, 255).to_ansi()
        yellow_ul = Style().with_style(Underline.SET, 255, 255, 0).to_ansi()
        res = "\x1b[0m"
        actual = (
            ANSIString("Hello, World!").ul_24b(0, 0, 255, (0, 5)).ul_24b(255, 255, 0, (7, 12)),
        )
        expected = (
            "".join(f"{blue_ul}{c}{res}" for c in "Hello") + ", " + "".join(f"{yellow_ul}{c}{res}" for c in "World") + "!",
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_ul_24b_w(self):
        blue_ul = Style().with_style(Underline.SET, 0, 0, 255).to_ansi()
        yellow_ul = Style().with_style(Underline.SET, 255, 255, 0).to_ansi()
        res = "\x1b[0m"
        actual = (
            ANSIString("Hello, World!").ul_24b_w(0, 0, 255, "Hello").ul_24b_w(255, 255, 0, "World"),
        )
        expected = (
            "".join(f"{blue_ul}{c}{res}" for c in "Hello") + ", " + "".join(f"{yellow_ul}{c}{res}" for c in "World") + "!",
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_ul_modes(self):
        """Test underline modes with color."""
        modes = (
            UnderlineMode.SINGLE,
            UnderlineMode.DOUBLE,
            UnderlineMode.CURLY,
            UnderlineMode.DOTTED,
            UnderlineMode.DASHED,
        )
        for mode in modes:
            with self.subTest(mode=mode.name):
                actual = ANSIString("Hello, World!").ul_24b(0, 128, 255).fm(mode)
                ul_ansi = Style().with_style(Underline.SET, 0, 128, 255).with_style(mode).to_ansi()
                expected = "".join(f"{ul_ansi}{c}\x1b[0m" for c in "Hello, World!")
                self.extended_assert_equal(actual, expected)

    def test_ul_modes_w(self):
        """Test word-targeted underline mode with color."""
        mode = UnderlineMode.DOUBLE
        actual = (
            ANSIString("Hello, World!").ul_8b_w(135, "World").fm_w(mode, "World"),
        )
        ul_ansi = Style().with_style(Underline.SET, 135).with_style(mode).to_ansi()
        expected = (
            "Hello, " + "".join(f"{ul_ansi}{c}\x1b[0m" for c in "World") + "!",
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_fstring_basic(self):
        blue = Style().with_style(Foreground.BLUE).to_ansi()
        res = "\x1b[0m"
        actual = f"{ANSIString('Hello, World!').fg_4b(Foreground.BLUE)}"
        expected = "".join(f"{blue}{c}{res}" for c in "Hello, World!")
        self.extended_assert_equal(actual, expected)

    def test_fstring_with_literal_prefix(self):
        blue = Style().with_style(Foreground.BLUE).to_ansi()
        res = "\x1b[0m"
        actual = f"s{ANSIString('Hello, World!').fg_4b(Foreground.BLUE)}"
        expected = "s" + "".join(f"{blue}{c}{res}" for c in "Hello, World!")
        self.extended_assert_equal(actual, expected)

    def test_fstring_with_format_spec(self):
        red = Style().with_style(Foreground.RED).to_ansi()
        res = "\x1b[0m"
        actual = f"{ANSIString('Hi').fg_4b(Foreground.RED):>3}"
        expected = " " + "".join(f"{red}{c}{res}" for c in "Hi")
        self.extended_assert_equal(actual, expected)

if __name__ == "__main__":

    unittest.main(argv=["first-arg-is-ignored"], verbosity=2, exit=False)

    wall = "\x1b[100m \x1b[0m"
    if output:
        print(f"\n{'VERBOSE OUTPUT':-^70}")
    for function_name, comment, actual, expected in output:
        print(
            f"{function_name:<40}{'ACTUAL:':>10} "
            f"{wall}{actual}{wall}\n{comment:^35}{'EXPECTED:':>15} {wall}{expected}{wall}"
        )
