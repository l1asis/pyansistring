"""Tests for ANSIString str-method overrides (__getitem__, __add__, split, etc.)."""

from collections.abc import Callable

import pytest

from pyansistring import ANSIString
from pyansistring.constants import SGR, Foreground
from tests.conftest import RESET, ansi_wrap, style_ansi


class TestGetItem:
    def test_slice_preserves_styles(self, bold_code: str, italic_code: str):
        s = (ANSIString("Hello, World!").fm(SGR.BOLD, (0, 5)).fm(SGR.ITALIC, (7, 12)))[
            2:-2
        ]
        # "llo, Worl" → bold on "llo", italic on "Worl"
        expected = ansi_wrap("llo", bold_code) + ", " + ansi_wrap("Worl", italic_code)
        assert str(s) == expected, "Slicing should preserve per-char styles"

    @pytest.mark.parametrize(
        "index, expected_char",
        [
            pytest.param(0, "H", id="first"),
            pytest.param(-1, "o", id="last"),
        ],
    )
    def test_single_index(self, index: int, expected_char: str, bold_code: str):
        s = ANSIString("Hello").fm(SGR.BOLD)
        assert str(s[index]) == f"{bold_code}{expected_char}{RESET}", (
            f"s[{index}] should be styled '{expected_char}'"
        )

    def test_step_slice(self):
        s = ANSIString("abcdef").fm(SGR.BOLD)[::2]
        assert s.plain_text == "ace", "Step slice should select every 2nd char"


class TestConcatenation:
    @pytest.mark.parametrize(
        "lhs, rhs, expected_fn",
        [
            pytest.param(
                lambda _: ANSIString("Hello").fm(SGR.BOLD),  # type: ignore
                lambda _: ANSIString(", World!").fm(SGR.ITALIC),  # type: ignore
                lambda bc, ic: ansi_wrap("Hello", bc) + ansi_wrap(", World!", ic),  # type: ignore
                id="ansi+ansi",
            ),
            pytest.param(
                lambda _: ANSIString("Hello").fm(SGR.BOLD),  # type: ignore
                lambda _: ", World!",  # type: ignore
                lambda bc, _: ansi_wrap("Hello", bc) + ", World!",  # type: ignore
                id="ansi+plain",
            ),
        ],
    )
    def test_add(
        self,
        lhs: Callable[[str], ANSIString],
        rhs: Callable[[str], ANSIString],
        expected_fn: Callable[[str, str], str],
        bold_code: str,
        italic_code: str,
    ):
        result = lhs(bold_code) + rhs(italic_code)
        expected = expected_fn(bold_code, italic_code)
        assert str(result) == expected

    def test_radd_plain_and_ansi(self, bold_code: str):
        result = "Hello" + ANSIString(", World!").fm(SGR.BOLD)
        expected = "Hello" + ansi_wrap(", World!", bold_code)
        assert str(result) == expected, "str + ANSIString should work via __radd__"


class TestFString:
    def test_basic(self):
        blue = style_ansi(Foreground.BLUE)
        s = ANSIString("Hello, World!").fg_4b(Foreground.BLUE)
        assert f"{s}" == ansi_wrap("Hello, World!", blue)

    def test_with_literal_prefix(self):
        blue = style_ansi(Foreground.BLUE)
        s = ANSIString("Hello, World!").fg_4b(Foreground.BLUE)
        assert f"s{s}" == "s" + ansi_wrap("Hello, World!", blue)

    def test_with_format_spec(self):
        red = style_ansi(Foreground.RED)
        s = ANSIString("Hi").fg_4b(Foreground.RED)
        result = f"{s:>3}"
        expected = " " + ansi_wrap("Hi", red)
        assert result == expected, "Format spec should pad then render ANSI"


class TestCaseMethods:
    @pytest.mark.parametrize(
        "method, input_text, expected_text",
        [
            pytest.param(
                "capitalize", "hello, world!", "Hello, world!", id="capitalize"
            ),
            pytest.param("lower", "Hello, World!", "hello, world!", id="lower"),
            pytest.param("upper", "Hello, World!", "HELLO, WORLD!", id="upper"),
            pytest.param("swapcase", "Hello, World!", "hELLO, wORLD!", id="swapcase"),
            pytest.param("title", "HELLO, WoRlD!", "Hello, World!", id="title"),
        ],
    )
    def test_case_method(
        self, method: str, input_text: str, expected_text: str, bold_code: str
    ):
        s = getattr(ANSIString(input_text).fm(SGR.BOLD), method)()
        assert str(s) == ansi_wrap(expected_text, bold_code), (
            f"{method}() on {input_text!r} should produce {expected_text!r}"
        )


_IS_METHODS = (
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


class TestIsMethods:
    @pytest.mark.parametrize("method_name", _IS_METHODS)
    def test_delegates_to_plain_text(
        self, method_name: str, bold_hello_world: ANSIString
    ):
        expected = getattr(bold_hello_world.plain_text, method_name)()
        actual = getattr(bold_hello_world, method_name)()
        assert actual == expected, f"{method_name}() should delegate to plain_text"


class TestSearchMethods:
    @pytest.mark.parametrize(
        "method, text, args, expected",
        [
            pytest.param("find", " Hello, World!", (" ",), 0, id="find-first"),
            pytest.param("find", " Hello, World!", (" ", 1), 7, id="find-from-1"),
            pytest.param("rfind", "Hello, World! ", (" ",), 13, id="rfind-last"),
            pytest.param("rfind", "Hello, World! ", (" ", 0, 13), 6, id="rfind-range"),
            pytest.param("index", " Hello, World!", (" ",), 0, id="index-first"),
            pytest.param("index", " Hello, World!", (" ", 1), 7, id="index-from-1"),
            pytest.param("rindex", "Hello, World! ", (" ",), 13, id="rindex-last"),
            pytest.param(
                "rindex", "Hello, World! ", (" ", 0, 13), 6, id="rindex-range"
            ),
        ],
    )
    def test_search(
        self,
        method: str,
        text: str,
        args: tuple[str] | tuple[str, int] | tuple[str, int, int],
        expected: int,
    ):
        s = ANSIString(text).fm(SGR.BOLD)
        result = getattr(s, method)(*args)
        assert result == expected, (
            f"{method}{args} on {text!r} = {result}, expected {expected}"
        )

    @pytest.mark.parametrize(
        "method, sub, expected",
        [
            pytest.param("startswith", "H", True, id="startswith-H"),
            pytest.param("startswith", "\x1b", False, id="startswith-esc"),
            pytest.param("endswith", "!", True, id="endswith-bang"),
            pytest.param("endswith", "[0m", False, id="endswith-reset"),
        ],
    )
    def test_starts_ends(
        self, method: str, sub: str, expected: bool, bold_hello_world: ANSIString
    ):
        result = getattr(bold_hello_world, method)(sub)
        assert result is expected, f"{method}({sub!r}) should be {expected}"


class TestAlignment:
    @pytest.mark.parametrize(
        "method, width, fill, expected_fn",
        [
            pytest.param(
                "ljust",
                17,
                "<",
                lambda bc: ansi_wrap("Hello, World!", bc) + "<<<<",  # type: ignore
                id="ljust-pad",
            ),
            pytest.param(
                "ljust",
                13,
                "<",
                lambda bc: ansi_wrap("Hello, World!", bc),  # type: ignore
                id="ljust-no-pad",
            ),
            pytest.param(
                "rjust",
                17,
                ">",
                lambda bc: ">>>>" + ansi_wrap("Hello, World!", bc),  # type: ignore
                id="rjust-pad",
            ),
            pytest.param(
                "center",
                17,
                "^",
                lambda bc: "^^" + ansi_wrap("Hello, World!", bc) + "^^",  # type: ignore
                id="center-pad",
            ),
        ],
    )
    def test_alignment(
        self,
        method: str,
        width: int,
        fill: str,
        expected_fn: Callable[[str], str],
        bold_code: str,
    ):
        s = getattr(ANSIString("Hello, World!").fm(SGR.BOLD), method)(width, fill)
        expected = expected_fn(bold_code)
        assert str(s) == expected, f"{method}({width}, {fill!r}) mismatch"


class TestSplit:
    """ANSIString.split() preserves per-character styles across pieces."""

    def test_default_split(self):
        s = (
            ANSIString(" Hello,   World!    ")
            .fg_24b(0, 0, 255, (1, 2), (5, 6))
            .fg_24b(255, 255, 0, (10, 11), (14, 15))
        )
        parts = s.split()
        assert len(parts) == 2, "Default split should produce 2 words"
        assert parts[0].plain_text == "Hello,"
        assert parts[1].plain_text == "World!"

    @pytest.mark.parametrize(
        "sep, maxsplit, expected_count, last_plain",
        [
            pytest.param(".", -1, 3, "c", id="sep-dot"),
            pytest.param(None, 2, 3, "c d", id="maxsplit-2"),
        ],
    )
    def test_split_variants(
        self, sep: str | None, maxsplit: int, expected_count: int, last_plain: str
    ):
        text = "a.b.c" if sep == "." else "a b c d"
        s = ANSIString(text).fm(SGR.BOLD)
        parts = s.split(sep, maxsplit) if maxsplit != -1 else s.split(sep)
        assert len(parts) == expected_count, (
            f"split({sep!r}) should produce {expected_count} parts"
        )
        assert parts[-1].plain_text == last_plain


class TestRsplit:
    def test_default_rsplit(self):
        s = (
            ANSIString(" Hello,   World!    ")
            .fg_24b(0, 0, 255, (1, 2), (5, 6))
            .fg_24b(255, 255, 0, (10, 11), (14, 15))
        )
        parts = s.rsplit()
        assert len(parts) == 2

    def test_rsplit_with_maxsplit(self):
        s = ANSIString("a b c d").fm(SGR.BOLD)
        parts = s.rsplit(None, 2)
        assert len(parts) == 3
        assert parts[0].plain_text == "a b", (
            "rsplit maxsplit=2 first part should be 'a b'"
        )


class TestSplitlines:
    def test_splitlines(self):
        s = ANSIString("Hello\nWorld").fm(SGR.BOLD)
        parts = s.splitlines()
        assert len(parts) == 2
        assert parts[0].plain_text == "Hello"
        assert parts[1].plain_text == "World"

    def test_splitlines_keepends(self):
        s = ANSIString("Hello\nWorld\n").fm(SGR.BOLD)
        parts = s.splitlines(True)
        assert parts[0].plain_text == "Hello\n", "keepends should preserve newline"

    def test_splitlines_styles_preserved(self):
        blue_code = "\x1b[38:2::0:0:255m"
        yellow_code = "\x1b[38:2::255:255:0m"
        s = (
            ANSIString("\n\nHello, \nWorld!\n\n\n")
            .fg_24b(0, 0, 255, (2, 3), (6, 7))
            .fg_24b(255, 255, 0, (10, 11), (15, 16))
        )
        parts = s.splitlines()
        hello = f"{blue_code}H{RESET}ell{blue_code}o{RESET}"
        world = f"{yellow_code}W{RESET}orld{yellow_code}!{RESET}"
        assert str(parts[2]) == f"{hello}, ", "splitlines should preserve blue on Hello"
        assert str(parts[3]) == world, "splitlines should preserve yellow on World"


class TestJoin:
    def test_join_with_styled_separator(self, bold_code: str):
        blue_code = "\x1b[38:2::0:0:255m"
        yellow_code = "\x1b[38:2::255:255:0m"
        sep = ANSIString(", ").fm(SGR.BOLD)
        result = sep.join(
            (
                "Anyway",
                ANSIString("Hello").fg_24b(0, 0, 255),
                ANSIString("World!").fg_24b(255, 255, 0),
            )
        )
        expected = (
            "Anyway"
            + ansi_wrap(", ", bold_code)
            + ansi_wrap("Hello", blue_code)
            + ansi_wrap(", ", bold_code)
            + ansi_wrap("World!", yellow_code)
        )
        assert str(result) == expected, "join should interleave styled separator"
