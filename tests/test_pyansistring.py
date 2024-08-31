import sys
import unittest

from pyansistring import (ANSIString, StyleDict, rsearch_separators,
                          search_separators, search_word_spans)
from pyansistring.constants import *

output = []

class OtherFunctionsTest(unittest.TestCase):
    def test_search_word_spans(self):
        actual = tuple(search_word_spans("Hello, World! Hello, World! He", "Hello"))
        expected = ((0, 5), (14, 19))
        self.assertTupleEqual(actual, expected)

    def test_search_separators(self):
        actual = tuple(search_separators("Hello, World!", WHITESPACE.union(PUNCTUATION)))
        expected = (", ", "!")
        self.assertTupleEqual(actual, expected)

    def test_rsearch_separators(self):
        actual = tuple(rsearch_separators("Hello, World!", WHITESPACE.union(PUNCTUATION)))
        expected = ("!", " ,")
        self.assertTupleEqual(actual, expected)

class BaseTestCase:
    def get_function_name(self, depth: int = 0) -> str:
        return sys._getframe(depth).f_code.co_name

    def extended_assert_equal(
            self, actual: ANSIString, expected: str,
            verbose: bool = True, function_name: str | None = None,
            comment: str = ""):
        if not function_name:
            function_name = self.get_function_name(depth=2)
        if verbose: output.append((function_name, comment, actual, expected))
        self.assertEqual(actual, expected)
        self.assertEqual(str(actual), expected)
        self.assertEqual(eval(repr(actual)), eval(repr(expected)))

class ANSIStringFeatureTest(BaseTestCase, unittest.TestCase):
    def test_plain(self):
        actual = ANSIString("Hello, World!")
        expected = "Hello, World!"
        self.extended_assert_equal(actual, expected)

    def test_fm(self):
        bold, italic, res = f"\x1b[1m", f"\x1b[3m", f"\x1b[0m"
        actual = (
            ANSIString("Hello, World!").fm(SGR.BOLD),
            ANSIString("Hello, World!").fm(SGR.BOLD, (0, 5)),
            ANSIString("Hello, World!").fm(SGR.BOLD, (0, 5), slice(7, 12)),
            ANSIString("Hello, World!").fm(SGR.BOLD).fm(SGR.ITALIC),
        )
        expected = (
            "".join(f"{bold}{char}{res}" for char in "Hello, World!"),
            "".join(f"{bold}{char}{res}" for char in "Hello") + ", World!",
            "".join(f"{bold}{char}{res}" for char in "Hello") + ", " +
            "".join(f"{bold}{char}{res}" for char in "World") + "!",
            "".join(f"{bold}{italic}{char}{res}" for char in "Hello, World!"),
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_fm_w(self):
        bold, italic, res = f"\x1b[1m", f"\x1b[3m", f"\x1b[0m"
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
            ANSIString("Hello, World!").fm(SGR.BOLD, (0, 5), slice(7, 12)).unfm((0, 5), slice(7, 12)),
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
            ANSIString("Hello, World!").fm_w(SGR.ITALIC, "world",
                                                case_sensitive=False).unfm_w("world",
                                                                            case_sensitive=False),
        )
        expected = (
            "Hello, World!",
            "Hello, World!",
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_fg_4b(self):
        bright_blue, bright_yellow, res = f"\x1b[94m", f"\x1b[93m", f"\x1b[0m"
        actual = (
            ANSIString("Hello, World!").fg_4b(Foreground.BRIGHT_BLUE, (0, 5)) \
                                        .fg_4b(Foreground.BRIGHT_YELLOW, (7, 12)),
        )
        expected = (
            "".join(f"{bright_blue}{char}{res}" for char in "Hello") + ", " + 
            "".join(f"{bright_yellow}{char}{res}" for char in "World") + "!",
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_fg_4b_w(self):
        bright_blue, bright_yellow, res = f"\x1b[94m", f"\x1b[93m", f"\x1b[0m"
        actual = (
            ANSIString("Hello, World!").fg_4b_w(Foreground.BRIGHT_BLUE, "Hello") \
                                        .fg_4b_w(Foreground.BRIGHT_YELLOW, "World"),
        )
        expected = (
            "".join(f"{bright_blue}{char}{res}" for char in "Hello") + ", " +
            "".join(f"{bright_yellow}{char}{res}" for char in "World") + "!",
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_fg_8b(self):
        color, res = f"\x1b[38;5;135m", f"\x1b[0m"
        actual = (
            ANSIString("Hello, World!").fg_8b(135),
        )
        expected = (
            "".join(f"{color}{char}{res}" for char in "Hello, World!"),
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_fg_8b_w(self):
        color, res = f"\x1b[38;5;135m", f"\x1b[0m"
        actual = (
            ANSIString("Hello, World!").fg_8b_w(135, "Hello, ", "World!"),
        )
        expected = (
            "".join(f"{color}{char}{res}" for char in "Hello, World!"),
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_fg_24b(self):
        blue, yellow, res = f"\x1b[38;2;0;0;255m", f"\x1b[38;2;255;255;0m", f"\x1b[0m"
        actual = (
            ANSIString("Hello, World!").fg_24b(0, 0, 255, (0, 5)) \
                                        .fg_24b(255, 255, 0, (7, 12)),
        )
        expected = (
            "".join(f"{blue}{char}{res}" for char in "Hello") + ", " + 
            "".join(f"{yellow}{char}{res}" for char in "World") + "!",
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_fg_24b_w(self):
        blue, yellow, res = f"\x1b[38;2;0;0;255m", f"\x1b[38;2;255;255;0m", f"\x1b[0m"
        actual = (
            ANSIString("Hello, World!").fg_24b_w(0, 0, 255, "Hello") \
                                        .fg_24b_w(255, 255, 0, "World"),
        )
        expected = (
            "".join(f"{blue}{char}{res}" for char in "Hello") + ", " + 
            "".join(f"{yellow}{char}{res}" for char in "World") + "!",
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_bg_4b(self):
        bright_blue, bright_yellow, res = f"\x1b[104m", f"\x1b[103m", f"\x1b[0m"
        actual = (
            ANSIString("Hello, World!").bg_4b(Background.BRIGHT_BLUE, (0, 5)) \
                                        .bg_4b(Background.BRIGHT_YELLOW, (7, 12)),
        )
        expected = (
            "".join(f"{bright_blue}{char}{res}" for char in "Hello") + ", " + 
            "".join(f"{bright_yellow}{char}{res}" for char in "World") + "!",
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_bg_4b_w(self):
        bright_blue, bright_yellow, res = f"\x1b[104m", f"\x1b[103m", f"\x1b[0m"
        actual = (
            ANSIString("Hello, World!").bg_4b_w(Background.BRIGHT_BLUE, "Hello") \
                                        .bg_4b_w(Background.BRIGHT_YELLOW, "World"),
        )
        expected = (
            "".join(f"{bright_blue}{char}{res}" for char in "Hello") + ", " +
            "".join(f"{bright_yellow}{char}{res}" for char in "World") + "!",
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_bg_8b(self):
        color, res = f"\x1b[48;5;135m", f"\x1b[0m"
        actual = (
            ANSIString("Hello, World!").bg_8b(135),
        )
        expected = (
            "".join(f"{color}{char}{res}" for char in "Hello, World!"),
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_bg_8b_w(self):
        color, res = f"\x1b[48;5;135m", f"\x1b[0m"
        actual = (
            ANSIString("Hello, World!").bg_8b_w(135, "Hello, ", "World!"),
        )
        expected = (
            "".join(f"{color}{char}{res}" for char in "Hello, World!"),
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_bg_24b(self):
        blue, yellow, res = f"\x1b[48;2;0;0;255m", f"\x1b[48;2;255;255;0m", f"\x1b[0m"
        actual = (
            ANSIString("Hello, World!").bg_24b(0, 0, 255, (0, 5)) \
                                        .bg_24b(255, 255, 0, (7, 12)),
        )
        expected = (
            "".join(f"{blue}{char}{res}" for char in "Hello") + ", " + 
            "".join(f"{yellow}{char}{res}" for char in "World") + "!",
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_bg_24b_w(self):
        blue, yellow, res = f"\x1b[48;2;0;0;255m", f"\x1b[48;2;255;255;0m", f"\x1b[0m"
        actual = (
            ANSIString("Hello, World!").bg_24b_w(0, 0, 255, "Hello") \
                                        .bg_24b_w(255, 255, 0, "World"),
        )
        expected = (
            "".join(f"{blue}{char}{res}" for char in "Hello") + ", " + 
            "".join(f"{yellow}{char}{res}" for char in "World") + "!",
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test_from_ansi(self):
        blue, yellow, res = f"\x1b[38;2;0;0;255m", f"\x1b[38;2;255;255;0m", f"\x1b[0m"
        plain = (
            f"\x1b[10;10H{''.join(f'{blue}{char}{res}' for char in 'Hello')}, {yellow}World{res}!{res*3}",
            ANSIString("Hello, World!").fg_24b_w(0,0,255,"Hello").fg_24b_w(255,255,0,"World").styled
        )
        styles = {index: blue for index in range(0, 5)} | {index: yellow for index in range(7, 12)}
        actual = (ANSIString.from_ansi(p) for p in plain)
        expected = ANSIString("Hello, World!", styles)
        for a in actual:
            self.extended_assert_equal(a, expected)
            self.assertDictEqual(a.styles, styles)

    def test_multicolor(self):
        string = "abcdefghijklmnopqrstuvwxyz"
        actual = (
            ANSIString(string).multicolor(MulticolorSequences.RAINBOW),
            ANSIString(string).multicolor(MulticolorSequences.REVERSED_RAINBOW),
            ANSIString(string).multicolor("r=84:|g=161:|b=255: $ r+9:minmax(0,inf)|g+4:minmax(0,inf) &*"),
            ANSIString(string).multicolor("r=84:|g=161:|b=255: $ r+9:minmax(0,inf)|g+4:minmax(0,inf) @&*"),
            ANSIString(string).multicolor("r=84:|g=161:|b=255: $ r+50:minmax(0,inf)|g+25:minmax(0,inf) # b-70:minmax(0,inf) !&*"),
        )
        expected = (
            ANSIString('abcdefghijklmnopqrstuvwxyz',
                       StyleDict({0: '\x1b[38;2;255;0;0m', 1: '\x1b[38;2;255;51;0m',
                                  2: '\x1b[38;2;255;102;0m', 3: '\x1b[38;2;255;153;0m',
                                  4: '\x1b[38;2;255;204;0m', 5: '\x1b[38;2;255;255;0m',
                                  6: '\x1b[38;2;191;255;0m', 7: '\x1b[38;2;127;255;0m',
                                  8: '\x1b[38;2;63;255;0m', 9: '\x1b[38;2;0;255;0m',
                                  10: '\x1b[38;2;0;255;63m', 11: '\x1b[38;2;0;255;127m',
                                  12: '\x1b[38;2;0;255;191m', 13: '\x1b[38;2;0;255;255m',
                                  14: '\x1b[38;2;0;191;255m', 15: '\x1b[38;2;0;127;255m',
                                  16: '\x1b[38;2;0;63;255m', 17: '\x1b[38;2;0;0;255m',
                                  18: '\x1b[38;2;63;0;255m', 19: '\x1b[38;2;127;0;255m',
                                  20: '\x1b[38;2;191;0;255m', 21: '\x1b[38;2;255;0;255m',
                                  22: '\x1b[38;2;255;0;191m', 23: '\x1b[38;2;255;0;127m',
                                  24: '\x1b[38;2;255;0;63m', 25: '\x1b[38;2;255;0;0m'})),
            ANSIString('abcdefghijklmnopqrstuvwxyz',
                       StyleDict({0: '\x1b[38;2;255;0;0m', 1: '\x1b[38;2;255;0;63m',
                                  2: '\x1b[38;2;255;0;127m', 3: '\x1b[38;2;255;0;191m',
                                  4: '\x1b[38;2;255;0;255m', 5: '\x1b[38;2;191;0;255m',
                                  6: '\x1b[38;2;127;0;255m', 7: '\x1b[38;2;63;0;255m',
                                  8: '\x1b[38;2;0;0;255m', 9: '\x1b[38;2;0;63;255m',
                                  10: '\x1b[38;2;0;127;255m', 11: '\x1b[38;2;0;191;255m',
                                  12: '\x1b[38;2;0;255;255m', 13: '\x1b[38;2;0;255;191m',
                                  14: '\x1b[38;2;0;255;127m', 15: '\x1b[38;2;0;255;63m',
                                  16: '\x1b[38;2;0;255;0m', 17: '\x1b[38;2;63;255;0m',
                                  18: '\x1b[38;2;127;255;0m', 19: '\x1b[38;2;191;255;0m',
                                  20: '\x1b[38;2;255;255;0m', 21: '\x1b[38;2;255;204;0m',
                                  22: '\x1b[38;2;255;153;0m', 23: '\x1b[38;2;255;102;0m',
                                  24: '\x1b[38;2;255;51;0m', 25: '\x1b[38;2;255;0;0m'})),
            ANSIString('abcdefghijklmnopqrstuvwxyz',
                       StyleDict({0: '\x1b[38;2;84;161;255m', 1: '\x1b[38;2;93;165;255m',
                                  2: '\x1b[38;2;102;169;255m', 3: '\x1b[38;2;111;173;255m',
                                  4: '\x1b[38;2;120;177;255m', 5: '\x1b[38;2;129;181;255m',
                                  6: '\x1b[38;2;138;185;255m', 7: '\x1b[38;2;147;189;255m',
                                  8: '\x1b[38;2;156;193;255m', 9: '\x1b[38;2;165;197;255m',
                                  10: '\x1b[38;2;174;201;255m', 11: '\x1b[38;2;183;205;255m',
                                  12: '\x1b[38;2;192;209;255m', 13: '\x1b[38;2;201;213;255m',
                                  14: '\x1b[38;2;210;217;255m', 15: '\x1b[38;2;219;221;255m',
                                  16: '\x1b[38;2;228;225;255m', 17: '\x1b[38;2;237;229;255m',
                                  18: '\x1b[38;2;246;233;255m', 19: '\x1b[38;2;255;237;255m',
                                  20: '\x1b[38;2;255;241;255m', 21: '\x1b[38;2;255;245;255m',
                                  22: '\x1b[38;2;255;249;255m', 23: '\x1b[38;2;255;253;255m',
                                  24: '\x1b[38;2;255;255;255m', 25: '\x1b[38;2;255;255;255m'})),
            ANSIString('abcdefghijklmnopqrstuvwxyz',
                       StyleDict({0: '\x1b[38;2;255;255;255m', 1: '\x1b[38;2;255;255;255m',
                                  2: '\x1b[38;2;255;253;255m', 3: '\x1b[38;2;255;249;255m',
                                  4: '\x1b[38;2;255;245;255m', 5: '\x1b[38;2;255;241;255m',
                                  6: '\x1b[38;2;255;237;255m', 7: '\x1b[38;2;246;233;255m',
                                  8: '\x1b[38;2;237;229;255m', 9: '\x1b[38;2;228;225;255m',
                                  10: '\x1b[38;2;219;221;255m', 11: '\x1b[38;2;210;217;255m',
                                  12: '\x1b[38;2;201;213;255m', 13: '\x1b[38;2;192;209;255m',
                                  14: '\x1b[38;2;183;205;255m', 15: '\x1b[38;2;174;201;255m',
                                  16: '\x1b[38;2;165;197;255m', 17: '\x1b[38;2;156;193;255m',
                                  18: '\x1b[38;2;147;189;255m', 19: '\x1b[38;2;138;185;255m',
                                  20: '\x1b[38;2;129;181;255m', 21: '\x1b[38;2;120;177;255m',
                                  22: '\x1b[38;2;111;173;255m', 23: '\x1b[38;2;102;169;255m',
                                  24: '\x1b[38;2;93;165;255m', 25: '\x1b[38;2;84;161;255m'})),
            ANSIString('abcdefghijklmnopqrstuvwxyz',
                       StyleDict({0: '\x1b[38;2;84;161;255m', 1: '\x1b[38;2;134;186;255m',
                                  2: '\x1b[38;2;134;186;185m', 3: '\x1b[38;2;134;186;255m',
                                  4: '\x1b[38;2;84;161;255m', 5: '\x1b[38;2;134;186;255m',
                                  6: '\x1b[38;2;134;186;185m', 7: '\x1b[38;2;134;186;255m',
                                  8: '\x1b[38;2;84;161;255m', 9: '\x1b[38;2;134;186;255m',
                                  10: '\x1b[38;2;134;186;185m', 11: '\x1b[38;2;134;186;255m',
                                  12: '\x1b[38;2;84;161;255m', 13: '\x1b[38;2;134;186;255m',
                                  14: '\x1b[38;2;134;186;185m', 15: '\x1b[38;2;134;186;255m',
                                  16: '\x1b[38;2;84;161;255m', 17: '\x1b[38;2;134;186;255m',
                                  18: '\x1b[38;2;134;186;185m', 19: '\x1b[38;2;134;186;255m',
                                  20: '\x1b[38;2;84;161;255m', 21: '\x1b[38;2;134;186;255m',
                                  22: '\x1b[38;2;134;186;185m', 23: '\x1b[38;2;134;186;255m',
                                  24: '\x1b[38;2;84;161;255m', 25: '\x1b[38;2;134;186;255m'}))
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)
        self.assertDictEqual(
            actual[0].styles,
            {key: value for key, value in enumerate(reversed(actual[1].styles.values()))}
        )
        self.assertDictEqual(
            actual[2].styles,
            {key: value for key, value in enumerate(reversed(actual[3].styles.values()))}
        )
    
    def test_multicolor_c(self):
        actual = ANSIString("Hello, \nWorld!\n It's pyansistring!").multicolor_c(MulticolorSequences.RAINBOW).styles.values()
        expected = ANSIString("Hello, World! It's pyansistring!").multicolor(MulticolorSequences.RAINBOW).styles.values()
        for a, e in zip(actual, expected):
            self.assertEqual(a, e)
        

class ANSIStringDefaultTest(BaseTestCase, unittest.TestCase):
    def test___getitem__(self):
        bold, italic, res = f"\x1b[1m", f"\x1b[3m", f"\x1b[0m"
        actual = ANSIString("Hello, World!").fm(SGR.BOLD, (0, 5)) \
                                            .fm(SGR.ITALIC, (7, 12))[2:-2]
        expected = "".join(f"{bold}{char}{res}" for char in "llo") + ", " + \
                   "".join(f"{italic}{char}{res}" for char in "Worl")
        self.extended_assert_equal(actual, expected)

    def test___add__(self):
        bold, italic, res = f"\x1b[1m", f"\x1b[3m", f"\x1b[0m"
        actual = (
            ANSIString("Hello").fm(SGR.BOLD) + ANSIString(", World!").fm(SGR.ITALIC),
            ANSIString("Hello").fm(SGR.BOLD) + ", World!",
        )
        expected = (
            "".join(f"{bold}{char}{res}" for char in "Hello") + \
            "".join(f"{italic}{char}{res}" for char in ", World!"),
            "".join(f"{bold}{char}{res}" for char in "Hello") + ", World!",
        )
        for a, e in zip(actual, expected):
            self.extended_assert_equal(a, e)

    def test___radd__(self):
        bold, res = f"\x1b[1m", f"\x1b[0m"
        actual = "Hello" + ANSIString(", World!").fm(SGR.BOLD)
        expected = "Hello" + "".join(f"{bold}{char}{res}" for char in ", World!")
        self.extended_assert_equal(actual, expected)

    def test_capitalize(self):
        bold, res = f"\x1b[1m", f"\x1b[0m"
        actual = ANSIString("hello, world!").fm(SGR.BOLD).capitalize()
        expected = "".join(f"{bold}{char}{res}" for char in "Hello, world!")
        self.extended_assert_equal(actual, expected)

    def test_center(self):
        bold, res = f"\x1b[1m", f"\x1b[0m"
        actual = tuple(
            ANSIString("Hello, World!").fm(SGR.BOLD).center(width, "^")
            for width in range(13, 18)
        )
        expected = (
            "".join(f"{bold}{char}{res}" for char in "Hello, World!"),
            "".join(f"{bold}{char}{res}" for char in "Hello, World!") + "^",
            "^" + "".join(f"{bold}{char}{res}" for char in "Hello, World!") + "^",
            "^" + "".join(f"{bold}{char}{res}" for char in "Hello, World!") + "^^",
            "^^" + "".join(f"{bold}{char}{res}" for char in "Hello, World!") + "^^",
        ) 
        for no, (a, e) in enumerate(zip(actual, expected)):
            self.extended_assert_equal(a, e,
                                       verbose=(False if no != 4 else True),
                                       function_name=("" if no != 4 else None))
            
    def test_endswith(self):
        string = ANSIString("Hello, World!").fm(SGR.BOLD)
        self.assertEqual(string.endswith("!"), True)
        self.assertEqual(string.endswith("[0m"), False)

    def test_find(self):
        actual = (
            ANSIString(" Hello, World!").fm(SGR.BOLD).find(" "),
            ANSIString(" Hello, World!").fm(SGR.BOLD).find(" ", 1),
        )
        expected = (0, 7)
        for a, e in zip(actual, expected):
            self.assertEqual(a, e)

    def test_index(self):
        actual = (
            ANSIString(" Hello, World!").fm(SGR.BOLD).index(" "),
            ANSIString(" Hello, World!").fm(SGR.BOLD).index(" ", 1),
        )
        expected = (0, 7)
        for a, e in zip(actual, expected):
            self.assertEqual(a, e)

    def test_is_methods(self):
        methods = ("isalnum", "isalpha", "isascii", "isdecimal", "isdigit",
                   "isidentifier", "islower", "isnumeric", "isprintable",
                   "isspace", "istitle", "isupper")
        string = ANSIString("Hello, World!").fm(SGR.BOLD)
        actual = (getattr(string, method)() for method in methods)
        expected = (getattr(string.plain, method)() for method in methods)
        for a, e in zip(actual, expected):
            self.assertEqual(a, e)

    def test_join(self):
        blue, yellow = f"\x1b[38;2;0;0;255m", f"\x1b[38;2;255;255;0m"
        bold, res = f"\x1b[1m", f"\x1b[0m"
        actual = ANSIString(", ").fm(SGR.BOLD).join(
            (
                "Anyway",
                ANSIString("Hello").fg_24b(0,0,255),
                ANSIString("World!").fg_24b(255,255,0),
            )
        )
        expected = (
            "Anyway" +
            "".join(f"{bold}{char}{res}" for char in ", ") +
            "".join(f"{blue}{char}{res}" for char in "Hello") +
            "".join(f"{bold}{char}{res}" for char in ", ") +
            "".join(f"{yellow}{char}{res}" for char in "World!")
        )
        self.extended_assert_equal(actual, expected)

    def test_ljust(self):
        bold, res = f"\x1b[1m", f"\x1b[0m"
        actual = tuple(
            ANSIString("Hello, World!").fm(SGR.BOLD).ljust(width, "<")
            for width in range(13, 18)
        )
        expected = (
            "".join(f"{bold}{char}{res}" for char in "Hello, World!"),
            "".join(f"{bold}{char}{res}" for char in "Hello, World!") + "<",
            "".join(f"{bold}{char}{res}" for char in "Hello, World!") + "<<",
            "".join(f"{bold}{char}{res}" for char in "Hello, World!") + "<<<",
            "".join(f"{bold}{char}{res}" for char in "Hello, World!") + "<<<<",
        ) 
        for no, (a, e) in enumerate(zip(actual, expected)):
            self.extended_assert_equal(a, e,
                                       verbose=(False if no != 4 else True),
                                       function_name=("" if no != 4 else None))
            
    def test_lower(self):
        bold, res = f"\x1b[1m", f"\x1b[0m"
        actual = ANSIString("Hello, World!").fm(SGR.BOLD).lower()
        expected = "".join(f"{bold}{char}{res}" for char in "hello, world!")
        self.extended_assert_equal(actual, expected)

    def test_rfind(self):
        actual = (
            ANSIString("Hello, World! ").fm(SGR.BOLD).rfind(" "),
            ANSIString("Hello, World! ").fm(SGR.BOLD).rfind(" ", 0, 13),
        )
        expected = (13, 6)
        for a, e in zip(actual, expected):
            self.assertEqual(a, e)

    def test_rindex(self):
        actual = (
            ANSIString("Hello, World! ").fm(SGR.BOLD).rindex(" "),
            ANSIString("Hello, World! ").fm(SGR.BOLD).rindex(" ", 0, 13),
        )
        expected = (13, 6)
        for a, e in zip(actual, expected):
            self.assertEqual(a, e)

    def test_rjust(self):
        bold, res = f"\x1b[1m", f"\x1b[0m"
        actual = tuple(
            ANSIString("Hello, World!").fm(SGR.BOLD).rjust(width, ">")
            for width in range(13, 18)
        )
        expected = (
            "".join(f"{bold}{char}{res}" for char in "Hello, World!"),
            ">" + "".join(f"{bold}{char}{res}" for char in "Hello, World!"),
            ">>" + "".join(f"{bold}{char}{res}" for char in "Hello, World!"),
            ">>>" + "".join(f"{bold}{char}{res}" for char in "Hello, World!"),
            ">>>>" + "".join(f"{bold}{char}{res}" for char in "Hello, World!"),
        ) 
        for no, (a, e) in enumerate(zip(actual, expected)):
            self.extended_assert_equal(a, e,
                                       verbose=(False if no != 4 else True),
                                       function_name=("" if no != 4 else None))

    def test_rsplit(self):
        blue, yellow, res = f"\x1b[38;2;0;0;255m", f"\x1b[38;2;255;255;0m", "\x1b[0m"
        steps = 0
        seps = (None, ".", "..", "...")
        maxsplits = (-1, 0, 1, 2, 3)
        spaces = ANSIString(" hello,   world!    ").fg_24b(0,0,255,(1,2),(5,6)).fg_24b(255,255,0,(10,11),(14,15))
        dots = ANSIString(".hello,...world!....").fg_24b(0,0,255,(1,2),(5,6)).fg_24b(255,255,0,(10,11),(14,15))
        hello = f"{blue}h{res}ell{blue}o{res}"
        world = f"{yellow}w{res}orl{yellow}d{res}"
        actual = {
            sep: {
                maxsplit: (spaces if not sep else dots).rsplit(sep, maxsplit) for maxsplit in maxsplits
            } for sep in seps
        }
        expected = {
            None: {
                -1: [f'{hello},', f'{world}!'],
                0: [f' {hello},   {world}!'],
                1: [f' {hello},', f'{world}!'],
                2: [f'{hello},', f'{world}!'],
                3: [f'{hello},', f'{world}!'],
            },
            ".": {
                -1: ['', f'{hello},', '', '', f'{world}!', '', '', '', ''],
                0: [f'.{hello},...{world}!....'],
                1: [f'.{hello},...{world}!...', ''],
                2: [f'.{hello},...{world}!..', '', ''],
                3: [f'.{hello},...{world}!.', '', '', ''],
            },
            "..": {
                -1: [f'.{hello},.', f'{world}!', '', ''],
                0: [f'.{hello},...{world}!....'],
                1: [f'.{hello},...{world}!..', ''],
                2: [f'.{hello},...{world}!', '', ''],
                3: [f'.{hello},.', f'{world}!', '', ''],
            },
            "...": {
                -1: [f'.{hello},', f'{world}!.', ''],
                0: [f'.{hello},...{world}!....'],
                1: [f'.{hello},...{world}!.', ''],
                2: [f'.{hello},', f'{world}!.', ''],
                3: [f'.{hello},', f'{world}!.', ''],
            },
        }
        for sep in seps:
            for maxsplit in maxsplits:
                a_list, e_list = actual[sep][maxsplit], expected[sep][maxsplit]
                self.assertEqual(len(a_list), len(e_list))
                a_list, e_list = filter(None, a_list), filter(None, e_list)
                for a, e in zip(a_list, e_list, strict=True):
                    self.extended_assert_equal(
                        a, e,
                        verbose=False,
                        comment=f"({repr(sep)} {maxsplit})",
                        function_name=(None if not steps else "")
                    )
                    steps += 1

    def test_split(self):
        blue, yellow, res = f"\x1b[38;2;0;0;255m", f"\x1b[38;2;255;255;0m", "\x1b[0m"
        steps = 0
        seps = (None, ".", "..", "...")
        maxsplits = (-1, 0, 1, 2, 3)
        spaces = ANSIString(" hello,   world!    ").fg_24b(0,0,255,(1,2),(5,6)).fg_24b(255,255,0,(10,11),(14,15))
        dots = ANSIString(".hello,...world!....").fg_24b(0,0,255,(1,2),(5,6)).fg_24b(255,255,0,(10,11),(14,15))
        hello = f"{blue}h{res}ell{blue}o{res}"
        world = f"{yellow}w{res}orl{yellow}d{res}"
        actual = {
            sep: {
                maxsplit: (spaces if not sep else dots).split(sep, maxsplit) for maxsplit in maxsplits
            } for sep in seps
        }
        expected = {
            None: {
                -1: [f'{hello},', f'{world}!'],
                0: [f'{hello},   {world}!    '],
                1: [f'{hello},', f'{world}!    '],
                2: [f'{hello},', f'{world}!'],
                3: [f'{hello},', f'{world}!'],
            },
            ".": {
                -1: ['', f'{hello},', '', '', f'{world}!', '', '', '', ''],
                0: [f'.{hello},...{world}!....'],
                1: ['', f'{hello},...{world}!....'],
                2: ['', f'{hello},', f'..{world}!....'],
                3: ['', f'{hello},', '', f'.{world}!....'],
            },
            "..": {
                -1: [f'.{hello},', f'.{world}!', '', ''],
                0: [f'.{hello},...{world}!....'],
                1: [f'.{hello},', f'.{world}!....'],
                2: [f'.{hello},', f'.{world}!', '..'],
                3: [f'.{hello},', f'.{world}!', '', ''],
            },
            "...": {
                -1: [f'.{hello},', f'{world}!', '.'],
                0: [f'.{hello},...{world}!....'],
                1: [f'.{hello},', f'{world}!....'],
                2: [f'.{hello},', f'{world}!', '.'],
                3: [f'.{hello},', f'{world}!', '.'],
            },
        }
        for sep in seps:
            for maxsplit in maxsplits:
                a_list, e_list = actual[sep][maxsplit], expected[sep][maxsplit]
                self.assertEqual(len(a_list), len(e_list))
                a_list, e_list = filter(None, a_list), filter(None, e_list)
                for a, e in zip(a_list, e_list, strict=True):
                    self.extended_assert_equal(
                        a, e,
                        verbose=False,
                        comment=f"({repr(sep)} {maxsplit})",
                        function_name=(None if not steps else "")
                    )
                    steps += 1
    
    def test_startswith(self):
        string = ANSIString("Hello, World!").fm(SGR.BOLD)
        self.assertEqual(string.startswith("H"), True)
        self.assertEqual(string.startswith("\x1b"), False)

    def test_swapcase(self):
        bold, res = f"\x1b[1m", f"\x1b[0m"
        actual = ANSIString("Hello, World!").fm(SGR.BOLD).swapcase()
        expected = "".join(f"{bold}{char}{res}" for char in "hELLO, wORLD!")
        self.extended_assert_equal(actual, expected)

    def test_title(self):
        bold, res = f"\x1b[1m", f"\x1b[0m"
        actual = ANSIString("HELLO, WoRlD!").fm(SGR.BOLD).title()
        expected = "".join(f"{bold}{char}{res}" for char in "Hello, World!")
        self.extended_assert_equal(actual, expected)

    def test_upper(self):
        bold, res = f"\x1b[1m", f"\x1b[0m"
        actual = ANSIString("Hello, World!").fm(SGR.BOLD).upper()
        expected = "".join(f"{bold}{char}{res}" for char in "HELLO, WORLD!")
        self.extended_assert_equal(actual, expected)


if __name__ == "__main__":

    unittest.main(argv=['first-arg-is-ignored'], verbosity=2, exit=False)

    wall = "\x1b[100m \x1b[0m"
    if output: print(f"\n{'VERBOSE OUTPUT':-^70}")
    for function_name, comment, actual, expected in output:
        print(f"{function_name:<40}{'ACTUAL:':>10} "
                f"{wall}{actual}{wall}\n{comment:^35}{'EXPECTED:':>15} {wall}{expected}{wall}")