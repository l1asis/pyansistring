import unittest

from tests.test_pyansistring_features import ExtendedAssertMixin
from pyansistring import ANSIString, StyleManager # type: ignore
from pyansistring.style import Style, Color  # type: ignore
from pyansistring.constants import *


output: list[tuple[str, str, ANSIString, str]] = []


class ANSIStringDefaultTest(ExtendedAssertMixin, unittest.TestCase):
    def test___getitem__(self):
        bold, italic, res = f"\x1b[1m", f"\x1b[3m", f"\x1b[0m"
        actual = (
            ANSIString("Hello, World!")
            .fm(SGR.BOLD, (0, 5))
            .fm(SGR.ITALIC, (7, 12))[2:-2]
        )
        expected = (
            "".join(f"{bold}{char}{res}" for char in "llo")
            + ", "
            + "".join(f"{italic}{char}{res}" for char in "Worl")
        )
        self.extended_assert_equal(actual, expected)

    def test___add__(self):
        bold, italic, res = f"\x1b[1m", f"\x1b[3m", f"\x1b[0m"
        actual = (
            ANSIString("Hello").fm(SGR.BOLD) + ANSIString(", World!").fm(SGR.ITALIC),
            ANSIString("Hello").fm(SGR.BOLD) + ", World!",
        )
        expected = (
            "".join(f"{bold}{char}{res}" for char in "Hello")
            + "".join(f"{italic}{char}{res}" for char in ", World!"),
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
            self.extended_assert_equal(
                a,
                e,
                verbose=(False if no != 4 else True),
                function_name=("" if no != 4 else None),
            )

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
        methods = (
            "isalnum",
            "isalpha",
            "isascii",
            "isdecimal",
            "isdigit",
            "isidentifier",
            "islower",
            "isnumeric",
            "isprintable",
            "isspace",
            "istitle",
            "isupper",
        )
        string = ANSIString("Hello, World!").fm(SGR.BOLD)
        actual = (getattr(string, method)() for method in methods)
        expected = (getattr(string.plain_text, method)() for method in methods)
        for a, e in zip(actual, expected):
            self.assertEqual(a, e)

    def test_join(self):
        blue, yellow = f"\x1b[38:2::0:0:255m", f"\x1b[38:2::255:255:0m"
        bold, res = f"\x1b[1m", f"\x1b[0m"
        actual = (
            ANSIString(", ")
            .fm(SGR.BOLD)
            .join(
                (
                    "Anyway",
                    ANSIString("Hello").fg_24b(0, 0, 255),
                    ANSIString("World!").fg_24b(255, 255, 0),
                )
            )
        )
        expected = (
            "Anyway"
            + "".join(f"{bold}{char}{res}" for char in ", ")
            + "".join(f"{blue}{char}{res}" for char in "Hello")
            + "".join(f"{bold}{char}{res}" for char in ", ")
            + "".join(f"{yellow}{char}{res}" for char in "World!")
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
            self.extended_assert_equal(
                a,
                e,
                verbose=(False if no != 4 else True),
                function_name=("" if no != 4 else None),
            )

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
            self.extended_assert_equal(
                a,
                e,
                verbose=(False if no != 4 else True),
                function_name=("" if no != 4 else None),
            )

    def test_rsplit(self):
        blue, yellow, res = f"\x1b[38:2::0:0:255m", f"\x1b[38:2::255:255:0m", "\x1b[0m"
        steps = 0
        seps = (None, ".", "..", "...")
        maxsplits = (-1, 0, 1, 2, 3)
        spaces = (
            ANSIString(" hello,   world!    ")
            .fg_24b(0, 0, 255, (1, 2), (5, 6))
            .fg_24b(255, 255, 0, (10, 11), (14, 15))
        )
        dots = (
            ANSIString(".hello,...world!....")
            .fg_24b(0, 0, 255, (1, 2), (5, 6))
            .fg_24b(255, 255, 0, (10, 11), (14, 15))
        )
        hello = f"{blue}h{res}ell{blue}o{res}"
        world = f"{yellow}w{res}orl{yellow}d{res}"
        actual = {
            sep: {
                maxsplit: (spaces if not sep else dots).rsplit(sep, maxsplit)
                for maxsplit in maxsplits
            }
            for sep in seps
        }
        expected: dict[None | str, dict[int, list[str]]] = {
            None: {
                -1: [f"{hello},", f"{world}!"],
                0: [f" {hello},   {world}!"],
                1: [f" {hello},", f"{world}!"],
                2: [f"{hello},", f"{world}!"],
                3: [f"{hello},", f"{world}!"],
            },
            ".": {
                -1: ["", f"{hello},", "", "", f"{world}!", "", "", "", ""],
                0: [f".{hello},...{world}!...."],
                1: [f".{hello},...{world}!...", ""],
                2: [f".{hello},...{world}!..", "", ""],
                3: [f".{hello},...{world}!.", "", "", ""],
            },
            "..": {
                -1: [f".{hello},.", f"{world}!", "", ""],
                0: [f".{hello},...{world}!...."],
                1: [f".{hello},...{world}!..", ""],
                2: [f".{hello},...{world}!", "", ""],
                3: [f".{hello},.", f"{world}!", "", ""],
            },
            "...": {
                -1: [f".{hello},", f"{world}!.", ""],
                0: [f".{hello},...{world}!...."],
                1: [f".{hello},...{world}!.", ""],
                2: [f".{hello},", f"{world}!.", ""],
                3: [f".{hello},", f"{world}!.", ""],
            },
        }
        for sep in seps:
            for maxsplit in maxsplits:
                a_list, e_list = actual[sep][maxsplit], expected[sep][maxsplit]
                self.assertEqual(len(a_list), len(e_list))
                a_list, e_list = filter(None, a_list), filter(None, e_list)
                for a, e in zip(a_list, e_list, strict=True):
                    self.extended_assert_equal(
                        a,
                        e,
                        verbose=False,
                        comment=f"({repr(sep)} {maxsplit})",
                        function_name=(None if not steps else ""),
                    )
                    steps += 1

    def test_split(self):
        blue, yellow, res = f"\x1b[38:2::0:0:255m", f"\x1b[38:2::255:255:0m", "\x1b[0m"
        steps = 0
        seps = (None, ".", "..", "...")
        maxsplits = (-1, 0, 1, 2, 3)
        spaces = (
            ANSIString(" Hello,   World!    ")
            .fg_24b(0, 0, 255, (1, 2), (5, 6))
            .fg_24b(255, 255, 0, (10, 11), (14, 15))
        )
        dots = (
            ANSIString(".Hello,...World!....")
            .fg_24b(0, 0, 255, (1, 2), (5, 6))
            .fg_24b(255, 255, 0, (10, 11), (14, 15))
        )
        hello = f"{blue}H{res}ell{blue}o{res}"
        world = f"{yellow}W{res}orl{yellow}d{res}"
        actual = {
            sep: {
                maxsplit: (spaces if not sep else dots).split(sep, maxsplit)
                for maxsplit in maxsplits
            }
            for sep in seps
        }
        expected: dict[None | str, dict[int, list[str]]] = {
            None: {
                -1: [f"{hello},", f"{world}!"],
                0: [f"{hello},   {world}!    "],
                1: [f"{hello},", f"{world}!    "],
                2: [f"{hello},", f"{world}!"],
                3: [f"{hello},", f"{world}!"],
            },
            ".": {
                -1: ["", f"{hello},", "", "", f"{world}!", "", "", "", ""],
                0: [f".{hello},...{world}!...."],
                1: ["", f"{hello},...{world}!...."],
                2: ["", f"{hello},", f"..{world}!...."],
                3: ["", f"{hello},", "", f".{world}!...."],
            },
            "..": {
                -1: [f".{hello},", f".{world}!", "", ""],
                0: [f".{hello},...{world}!...."],
                1: [f".{hello},", f".{world}!...."],
                2: [f".{hello},", f".{world}!", ".."],
                3: [f".{hello},", f".{world}!", "", ""],
            },
            "...": {
                -1: [f".{hello},", f"{world}!", "."],
                0: [f".{hello},...{world}!...."],
                1: [f".{hello},", f"{world}!...."],
                2: [f".{hello},", f"{world}!", "."],
                3: [f".{hello},", f"{world}!", "."],
            },
        }
        for sep in seps:
            for maxsplit in maxsplits:
                a_list, e_list = actual[sep][maxsplit], expected[sep][maxsplit]
                self.assertEqual(len(a_list), len(e_list))
                a_list, e_list = filter(None, a_list), filter(None, e_list)
                for a, e in zip(a_list, e_list, strict=True):
                    self.extended_assert_equal(
                        a,
                        e,
                        verbose=False,
                        comment=f"({repr(sep)} {maxsplit})",
                        function_name=(None if not steps else ""),
                    )
                    steps += 1

    def test_splitlines(self):
        blue, yellow, res = f"\x1b[38:2::0:0:255m", f"\x1b[38:2::255:255:0m", "\x1b[0m"
        hello = f"{blue}H{res}ell{blue}o{res}"
        world = f"{yellow}W{res}orld{yellow}!{res}"
        string = (
            ANSIString("\n\nHello, \nWorld!\n\n\n")
            .fg_24b(0, 0, 255, (2, 3), (6, 7))
            .fg_24b(255, 255, 0, (10, 11), (15, 16))
        )
        actual = (
            string.splitlines(),
            string.splitlines(True),
        )
        expected = (
            ["", "", f"{hello}, ", f"{world}", "", ""],
            ["\n", "\n", f"{hello}, \n", f"{world}\n", "\n", "\n"],
        )
        for step, (a_list, e_list) in enumerate(zip(actual, expected)):
            self.assertEqual(len(a_list), len(e_list))
            a_list, e_list = filter(None, a_list), filter(None, e_list)
            for a, e in zip(a_list, e_list, strict=True):
                self.extended_assert_equal(
                    a,
                    e,
                    verbose=False,
                    comment=f"(keeptrue={False if not step else True})",
                )

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