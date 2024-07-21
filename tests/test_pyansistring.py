import sys
import unittest

from pyansistring.constants import *
from pyansistring import (ANSIString, StyleDict, rsearch_separators, search_separators, search_word_spans)


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
        actual = ANSIString("Hello, World!").fm(SGR.BOLD).endswith("!")
        self.assertEqual(actual, True)

    def test_find(self):
        actual = (
            ANSIString("Hello, World!").fm(SGR.BOLD).find("Hello"),
            ANSIString("Hello, World!").fm(SGR.BOLD).find("World"),
            ANSIString("Hello, World!").fm(SGR.BOLD).find("Hello", 5),
        )
        expected = (0, 7, -1)
        for a, e in zip(actual, expected):
            self.assertEqual(a, e)

    def test_index(self):
        actual = (
            ANSIString("Hello, World!").fm(SGR.BOLD).index("Hello"),
            ANSIString("Hello, World!").fm(SGR.BOLD).index("World"),
        )
        expected = (0, 7)
        for a, e in zip(actual, expected):
            self.assertEqual(a, e)

    @unittest.skip
    def test_split(self):
        steps = 0
        seps = (None, ".", "..", "...")
        maxsplits = (-1, 0, 1, 2, 3)
        spaces = ANSIString(" hello,   world    ")
        dots = ANSIString(".hello,...world....")
        actual = {
            sep: {
                maxsplit: (spaces if not sep else dots).split(sep, maxsplit) for maxsplit in maxsplits
            } for sep in seps
        }
        expected = {
            None: {
                ...
            },
            ".": {
                ...
            },
            "..": {
                ...
            },
            "...": {
                ...
            }
        }
        for sep in seps:
            for maxsplit in maxsplits:
                a_list, e_list = actual[sep][maxsplit], expected[sep][maxsplit]
                self.assertEqual(len(a), len(e))
                a_list, e_list = tuple(filter(None, a_list), filter(None, e_list))
                for a, e in zip(a_list, e_list):
                    self.extended_assert_equal(
                        a, e,
                        verbose=False,
                        comment=f"({repr(sep)} {maxsplit})",
                        function_name=(None if not steps else "")
                    )
                    steps += 1

    @unittest.skip
    def test_rsplit(self):
        steps = 0
        seps = (None, ".", "..", "...")
        maxsplits = (-1, 0, 1, 2, 3)
        spaces = ANSIString(" hello,   world    ")
        dots = ANSIString(".hello,...world....")
        actual = {
            sep: {
                maxsplit: (spaces if not sep else dots).split(sep, maxsplit) for maxsplit in maxsplits
            } for sep in seps
        }
        expected = {
            None: {
                ...
            },
            ".": {
                ...
            },
            "..": {
                ...
            },
            "...": {
                ...
            }
        }
        for sep in seps:
            for maxsplit in maxsplits:
                a_list, e_list = actual[sep][maxsplit], expected[sep][maxsplit]
                self.assertEqual(len(a), len(e))
                a_list, e_list = tuple(filter(None, a_list), filter(None, e_list))
                for a, e in zip(a_list, e_list):
                    self.extended_assert_equal(
                        a, e,
                        verbose=False,
                        comment=f"({repr(sep)} {maxsplit})",
                        function_name=(None if not steps else "")
                    )
                    steps += 1

    @unittest.skip
    def test_join(self):
        ...

if __name__ == "__main__":

    unittest.main(argv=['first-arg-is-ignored'], verbosity=2, exit=False)

    wall = "\x1b[100m \x1b[0m"
    if output: print(f"\n{'VERBOSE OUTPUT':-^70}")
    for function_name, comment, actual, expected in output:
        print(f"{function_name:<40}{'ACTUAL:':>10} "
                f"{wall}{actual}{wall}\n{comment:^35}{'EXPECTED:':>15} {wall}{expected}{wall}")