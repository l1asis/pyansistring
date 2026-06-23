"""Tests for ANSIString str-method overrides (__getitem__, __add__, split, etc.)."""

from collections.abc import Callable
from pickle import dumps, loads

import pytest

from pyansistring import ANSIString
from pyansistring.constants import SGR, Foreground
from tests.conftest import RESET, ansi_wrap, style_ansi


class TestGetItem:
    def test_slice_preserves_styles(self, bold_code: str, italic_code: str):
        s = (
            ANSIString("Hello, World!")
            .style(SGR.BOLD, (0, 5))
            .style(SGR.ITALIC, (7, 12))
        )[2:-2]
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
        s = ANSIString("Hello").style(SGR.BOLD)
        assert str(s[index]) == f"{bold_code}{expected_char}{RESET}", (
            f"s[{index}] should be styled '{expected_char}'"
        )

    def test_step_slice(self):
        s = ANSIString("abcdef").style(SGR.BOLD)[::2]
        assert s.plain_text == "ace", "Step slice should select every 2nd char"


class TestConcatenation:
    @pytest.mark.parametrize(
        "lhs, rhs, expected_fn",
        [
            pytest.param(
                lambda _: ANSIString("Hello").style(SGR.BOLD),  # type: ignore[reportUnknownLambdaType]
                lambda _: ANSIString(", World!").style(SGR.ITALIC),  # type: ignore[reportUnknownLambdaType]
                lambda bc, ic: ansi_wrap("Hello", bc) + ansi_wrap(", World!", ic),  # type: ignore[reportUnknownLambdaType]
                id="ansi+ansi",
            ),
            pytest.param(
                lambda _: ANSIString("Hello").style(SGR.BOLD),  # type: ignore[reportUnknownLambdaType]
                lambda _: ", World!",  # type: ignore[reportUnknownLambdaType]
                lambda bc, _: ansi_wrap("Hello", bc) + ", World!",  # type: ignore[reportUnknownLambdaType]
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
        result = "Hello" + ANSIString(", World!").style(SGR.BOLD)
        expected = "Hello" + ansi_wrap(", World!", bold_code)
        assert str(result) == expected, "str + ANSIString should work via __radd__"


class TestFString:
    def test_basic(self):
        blue = style_ansi(Foreground.BLUE)
        s = ANSIString("Hello, World!").fg(Foreground.BLUE)
        assert f"{s}" == ansi_wrap("Hello, World!", blue)

    def test_with_literal_prefix(self):
        blue = style_ansi(Foreground.BLUE)
        s = ANSIString("Hello, World!").fg(Foreground.BLUE)
        assert f"s{s}" == "s" + ansi_wrap("Hello, World!", blue)

    def test_with_format_spec(self):
        red = style_ansi(Foreground.RED)
        s = ANSIString("Hi").fg(Foreground.RED)
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
        s = getattr(ANSIString(input_text).style(SGR.BOLD), method)()
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
        s = ANSIString(text).style(SGR.BOLD)
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
                lambda bc: ansi_wrap("Hello, World!", bc) + "<<<<",  # type: ignore[reportUnknownLambdaType]
                id="ljust-pad",
            ),
            pytest.param(
                "ljust",
                13,
                "<",
                lambda bc: ansi_wrap("Hello, World!", bc),  # type: ignore[reportUnknownLambdaType]
                id="ljust-no-pad",
            ),
            pytest.param(
                "rjust",
                17,
                ">",
                lambda bc: ">>>>" + ansi_wrap("Hello, World!", bc),  # type: ignore[reportUnknownLambdaType]
                id="rjust-pad",
            ),
            pytest.param(
                "center",
                17,
                "^",
                lambda bc: "^^" + ansi_wrap("Hello, World!", bc) + "^^",  # type: ignore[reportUnknownLambdaType]
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
        s = getattr(ANSIString("Hello, World!").style(SGR.BOLD), method)(width, fill)
        expected = expected_fn(bold_code)
        assert str(s) == expected, f"{method}({width}, {fill!r}) mismatch"


class TestSplit:
    """ANSIString.split() preserves per-character styles across pieces."""

    def test_default_split(self):
        s = (
            ANSIString(" Hello,   World!    ")
            .fg((0, 0, 255), (1, 2), (5, 6))
            .fg((255, 255, 0), (10, 11), (14, 15))
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
        s = ANSIString(text).style(SGR.BOLD)
        parts = s.split(sep, maxsplit) if maxsplit != -1 else s.split(sep)
        assert len(parts) == expected_count, (
            f"split({sep!r}) should produce {expected_count} parts"
        )
        assert parts[-1].plain_text == last_plain


class TestRsplit:
    def test_default_rsplit(self):
        s = (
            ANSIString(" Hello,   World!    ")
            .fg((0, 0, 255), (1, 2), (5, 6))
            .fg((255, 255, 0), (10, 11), (14, 15))
        )
        parts = s.rsplit()
        assert len(parts) == 2

    def test_rsplit_with_maxsplit(self):
        s = ANSIString("a b c d").style(SGR.BOLD)
        parts = s.rsplit(None, 2)
        assert len(parts) == 3
        assert parts[0].plain_text == "a b", (
            "rsplit maxsplit=2 first part should be 'a b'"
        )


class TestSplitlines:
    def test_splitlines(self):
        s = ANSIString("Hello\nWorld").style(SGR.BOLD)
        parts = s.splitlines()
        assert len(parts) == 2
        assert parts[0].plain_text == "Hello"
        assert parts[1].plain_text == "World"

    def test_splitlines_keepends(self):
        s = ANSIString("Hello\nWorld\n").style(SGR.BOLD)
        parts = s.splitlines(True)
        assert parts[0].plain_text == "Hello\n", "keepends should preserve newline"

    def test_splitlines_styles_preserved(self):
        blue_code = "\x1b[38:2::0:0:255m"
        yellow_code = "\x1b[38:2::255:255:0m"
        s = (
            ANSIString("\n\nHello, \nWorld!\n\n\n")
            .fg((0, 0, 255), (2, 3), (6, 7))
            .fg((255, 255, 0), (10, 11), (15, 16))
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
        sep = ANSIString(", ").style(SGR.BOLD)
        result = sep.join(
            (
                "Anyway",
                ANSIString("Hello").fg((0, 0, 255)),
                ANSIString("World!").fg((255, 255, 0)),
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


class TestContains:
    def test_contains_plain(self):
        s = ANSIString("Hello, World!").style(SGR.BOLD)
        assert "World" in s
        assert "world" not in s

    def test_contains_empty(self):
        s = ANSIString("abc")
        assert "" in s


class TestMul:
    def test_mul_repeats_text_and_styles(self, bold_code: str):
        s = ANSIString("ab").style(SGR.BOLD)
        result = s * 3
        assert result.plain_text == "ababab"
        assert str(result) == ansi_wrap("ababab", bold_code)

    def test_mul_zero(self):
        s = ANSIString("abc").style(SGR.BOLD)
        assert (s * 0).plain_text == ""

    def test_mul_negative(self):
        s = ANSIString("abc").style(SGR.BOLD)
        assert (s * -1).plain_text == ""

    def test_mul_one(self, bold_code: str):
        s = ANSIString("Hi").style(SGR.BOLD)
        result = s * 1
        assert str(result) == ansi_wrap("Hi", bold_code)

    def test_rmul(self, bold_code: str):
        s = ANSIString("ab").style(SGR.BOLD)
        result = 2 * s
        assert result.plain_text == "abab"
        assert str(result) == ansi_wrap("abab", bold_code)

    def test_mul_mixed_styles(self, bold_code: str, italic_code: str):
        s = ANSIString("ab").style(SGR.BOLD, (0, 1)).style(SGR.ITALIC, (1, 2))
        result = s * 2
        assert result.plain_text == "abab"
        expected = (
            ansi_wrap("a", bold_code)
            + ansi_wrap("b", italic_code)
            + ansi_wrap("a", bold_code)
            + ansi_wrap("b", italic_code)
        )
        assert str(result) == expected


class TestMod:
    def test_mod_basic(self, bold_code: str):
        s = ANSIString("Hello %s!").style(SGR.BOLD)
        result = s % "World"
        assert result.plain_text == "Hello World!"
        expected = ansi_wrap("Hello ", bold_code) + "World" + ansi_wrap("!", bold_code)
        assert str(result) == expected

    def test_mod_returns_ansistring(self):
        s = ANSIString("x=%d") % 42
        assert isinstance(s, ANSIString)
        assert s.plain_text == "x=42"

    def test_mod_tuple_args(self, bold_code: str):
        s = ANSIString("(%s, %d)").style(SGR.BOLD)
        result = s % ("hello", 42)
        assert result.plain_text == "(hello, 42)"
        expected = (
            ansi_wrap("(", bold_code)
            + "hello"
            + ansi_wrap(", ", bold_code)
            + "42"
            + ansi_wrap(")", bold_code)
        )
        assert str(result) == expected

    def test_mod_percent_escape(self, bold_code: str):
        s = ANSIString("100%%").style(SGR.BOLD)
        result = s % ()
        assert result.plain_text == "100%"
        assert str(result) == ansi_wrap("100%", bold_code)

    def test_mod_mapping_args(self, bold_code: str):
        s = ANSIString("Hi %(name)s!").style(SGR.BOLD)
        result = s % {"name": "Alice"}
        assert result.plain_text == "Hi Alice!"
        expected = ansi_wrap("Hi ", bold_code) + "Alice" + ansi_wrap("!", bold_code)
        assert str(result) == expected

    def test_mod_no_specifiers(self, bold_code: str):
        s = ANSIString("Hello").style(SGR.BOLD)
        result = s % ()
        assert result.plain_text == "Hello"
        assert str(result) == ansi_wrap("Hello", bold_code)


class TestNe:
    def test_ne_different(self, bold_code: str):
        a = ANSIString("Hello").style(SGR.BOLD)
        b = ANSIString("Hello").style(SGR.ITALIC)
        assert a != b

    def test_ne_same(self, bold_code: str):
        a = ANSIString("Hello").style(SGR.BOLD)
        b = ANSIString("Hello").style(SGR.BOLD)
        assert not (a != b)

    def test_ne_consistent_with_eq(self, bold_code: str):
        a = ANSIString("Hello").style(SGR.BOLD)
        b = ANSIString("Hello").style(SGR.BOLD)
        assert (a == b) == (not (a != b))


class TestIter:
    def test_iter_yields_ansistring(self, bold_code: str):
        s = ANSIString("abc").style(SGR.BOLD)
        chars: list[ANSIString] = list(s)  # type: ignore
        assert len(chars) == 3
        for c in chars:
            assert isinstance(c, ANSIString)
        assert chars[0].plain_text == "a"

    def test_iter_preserves_styles(self, bold_code: str, italic_code: str):
        s = ANSIString("ab").style(SGR.BOLD, (0, 1)).style(SGR.ITALIC, (1, 2))
        chars: list[ANSIString] = list(s)  # type: ignore
        assert str(chars[0]) == ansi_wrap("a", bold_code)
        assert str(chars[1]) == ansi_wrap("b", italic_code)

    def test_iter_unstyled_char(self, bold_code: str):
        s = ANSIString("ab").style(SGR.BOLD, (0, 1))
        chars: list[ANSIString] = list(s)  # type: ignore
        assert str(chars[0]) == ansi_wrap("a", bold_code)
        assert str(chars[1]) == "b"


class TestStrip:
    def test_strip_basic(self, bold_code: str):
        s = ANSIString("  Hello  ").style(SGR.BOLD, (2, 7))
        result = s.strip()
        assert result.plain_text == "Hello"
        assert str(result) == ansi_wrap("Hello", bold_code)

    def test_lstrip(self, bold_code: str):
        s = ANSIString("  Hello").style(SGR.BOLD, (2, 7))
        result = s.lstrip()
        assert result.plain_text == "Hello"
        assert str(result) == ansi_wrap("Hello", bold_code)

    def test_rstrip(self, bold_code: str):
        s = ANSIString("Hello  ").style(SGR.BOLD, (0, 5))
        result = s.rstrip()
        assert result.plain_text == "Hello"
        assert str(result) == ansi_wrap("Hello", bold_code)

    def test_strip_chars(self, bold_code: str):
        s = ANSIString("xxHelloxx").style(SGR.BOLD, (2, 7))
        result = s.strip("x")
        assert result.plain_text == "Hello"
        assert str(result) == ansi_wrap("Hello", bold_code)

    def test_strip_no_change(self, bold_code: str):
        s = ANSIString("Hello").style(SGR.BOLD)
        assert s.strip().plain_text == "Hello"


class TestReplace:
    def test_replace_basic(self, bold_code: str):
        s = ANSIString("Hello, World!").style(SGR.BOLD, (0, 5))
        result = s.replace("World", "Python")
        assert result.plain_text == "Hello, Python!"
        assert str(result) == ansi_wrap("Hello", bold_code) + ", Python!"

    def test_replace_with_count(self):
        s = ANSIString("aaa").style(SGR.BOLD)
        result = s.replace("a", "bb", 2)
        assert result.plain_text == "bbbba"

    def test_replace_shorter(self, bold_code: str):
        s = ANSIString("Hello World").style(SGR.BOLD, (6, 11))
        result = s.replace("Hello", "Hi")
        assert result.plain_text == "Hi World"
        assert str(result) == "Hi " + ansi_wrap("World", bold_code)

    def test_replace_no_match(self, bold_code: str):
        s = ANSIString("Hello").style(SGR.BOLD)
        result = s.replace("xyz", "abc")
        assert str(result) == ansi_wrap("Hello", bold_code)

    def test_replace_empty_old(self):
        s = ANSIString("ab").style(SGR.BOLD)
        result = s.replace("", "-")
        assert result.plain_text == "-a-b-"


class TestRemovefix:
    def test_removeprefix(self, bold_code: str):
        s = ANSIString("Hello, World!").style(SGR.BOLD, (7, 12))
        result = s.removeprefix("Hello, ")
        assert result.plain_text == "World!"
        assert str(result) == ansi_wrap("World", bold_code) + "!"

    def test_removeprefix_no_match(self, bold_code: str):
        s = ANSIString("Hello").style(SGR.BOLD)
        result = s.removeprefix("xyz")
        assert str(result) == ansi_wrap("Hello", bold_code)

    def test_removesuffix(self, bold_code: str):
        s = ANSIString("Hello, World!").style(SGR.BOLD, (0, 5))
        result = s.removesuffix(", World!")
        assert result.plain_text == "Hello"
        assert str(result) == ansi_wrap("Hello", bold_code)

    def test_removesuffix_no_match(self, bold_code: str):
        s = ANSIString("Hello").style(SGR.BOLD)
        result = s.removesuffix("xyz")
        assert str(result) == ansi_wrap("Hello", bold_code)

    def test_removeprefix_empty(self, bold_code: str):
        s = ANSIString("Hello").style(SGR.BOLD)
        result = s.removeprefix("")
        assert str(result) == ansi_wrap("Hello", bold_code)


class TestPartition:
    def test_partition_found(self, bold_code: str, italic_code: str):
        s = (
            ANSIString("Hello, World!")
            .style(SGR.BOLD, (0, 5))
            .style(SGR.ITALIC, (7, 12))
        )
        before, sep, after = s.partition(", ")
        assert before.plain_text == "Hello"
        assert sep.plain_text == ", "
        assert after.plain_text == "World!"
        assert str(before) == ansi_wrap("Hello", bold_code)
        assert str(after) == ansi_wrap("World", italic_code) + "!"

    def test_partition_not_found(self, bold_code: str):
        s = ANSIString("Hello").style(SGR.BOLD)
        before, sep, after = s.partition("xyz")
        assert str(before) == ansi_wrap("Hello", bold_code)
        assert sep.plain_text == ""
        assert after.plain_text == ""

    def test_rpartition_found(self, bold_code: str):
        s = ANSIString("a.b.c").style(SGR.BOLD, (4, 5))
        before, sep, after = s.rpartition(".")
        assert before.plain_text == "a.b"
        assert sep.plain_text == "."
        assert after.plain_text == "c"
        assert str(after) == ansi_wrap("c", bold_code)

    def test_rpartition_not_found(self, bold_code: str):
        s = ANSIString("Hello").style(SGR.BOLD)
        before, sep, after = s.rpartition("xyz")
        assert before.plain_text == ""
        assert sep.plain_text == ""
        assert str(after) == ansi_wrap("Hello", bold_code)


class TestZfill:
    def test_zfill_basic(self, bold_code: str):
        s = ANSIString("42").style(SGR.BOLD)
        result = s.zfill(5)
        assert result.plain_text == "00042"
        assert str(result) == "000" + ansi_wrap("42", bold_code)

    def test_zfill_with_sign(self, bold_code: str):
        s = ANSIString("-42").style(SGR.BOLD, (1, 3))
        result = s.zfill(6)
        assert result.plain_text == "-00042"
        assert str(result) == "-000" + ansi_wrap("42", bold_code)

    def test_zfill_no_pad(self, bold_code: str):
        s = ANSIString("12345").style(SGR.BOLD)
        result = s.zfill(3)
        assert str(result) == ansi_wrap("12345", bold_code)

    def test_zfill_sign_styled(self, bold_code: str):
        s = ANSIString("+5").style(SGR.BOLD)
        result = s.zfill(4)
        assert result.plain_text == "+005"
        expected = ansi_wrap("+", bold_code) + "00" + ansi_wrap("5", bold_code)
        assert str(result) == expected


class TestExpandtabs:
    def test_expandtabs_basic(self, bold_code: str):
        s = ANSIString("a\tb").style(SGR.BOLD)
        result = s.expandtabs(4)
        assert result.plain_text == "a   b"
        expected = ansi_wrap("a", bold_code) + "   " + ansi_wrap("b", bold_code)
        assert str(result) == expected

    def test_expandtabs_default(self):
        s = ANSIString("\tx")
        result = s.expandtabs()
        assert result.plain_text == "        x"

    def test_expandtabs_no_tabs(self, bold_code: str):
        s = ANSIString("Hello").style(SGR.BOLD)
        assert str(s.expandtabs()) == ansi_wrap("Hello", bold_code)


class TestEncode:
    def test_encode(self, bold_code: str):
        s = ANSIString("Hello").style(SGR.BOLD)
        encoded = s.encode("utf-8")
        assert isinstance(encoded, bytes)
        assert encoded == ansi_wrap("Hello", bold_code).encode("utf-8")


class TestReduce:
    def test_reduce(self, bold_code: str):
        s = ANSIString("Hello").style(SGR.BOLD)
        pickled = dumps(s)
        unpickled = loads(pickled)
        assert isinstance(unpickled, ANSIString)
        assert unpickled.plain_text == "Hello"
        assert str(unpickled) == ansi_wrap("Hello", bold_code)


class TestCasefold:
    def test_casefold_expands(self, bold_code: str):
        s = ANSIString("Straße").style(SGR.BOLD)
        folded = s.casefold()
        assert folded.plain_text == "strasse"
        assert str(folded) == ansi_wrap("strasse", bold_code)
        assert len(folded.style_manager) == len(s.style_manager) + 1

    def test_casefold_no_expansion(self, bold_code: str):
        s = ANSIString("Hello").style(SGR.BOLD)
        folded = s.casefold()
        assert folded.plain_text == "hello"
        assert str(folded) == ansi_wrap("hello", bold_code)
        assert len(folded.style_manager) == len(s.style_manager)

    def test_casefold_multiple_expansions(self, bold_code: str, italic_code: str):
        s = (
            ANSIString("Hello, ﬃ and ß!!!")
            .style(SGR.BOLD, (7, 8), (13, 14))
            .style(SGR.ITALIC, (9, 12), (14, 17))
        )
        folded = s.casefold()
        assert folded.plain_text == "hello, ffi and ss!!!"
        expected = (
            "hello, "
            + ansi_wrap("ffi", bold_code)
            + " "
            + ansi_wrap("and", italic_code)
            + " "
            + ansi_wrap("ss", bold_code)
            + ansi_wrap("!!!", italic_code)
        )
        assert str(folded) == expected
        assert len(folded.style_manager) == len(s.style_manager) + 3


class TestTranslate:
    def test_translate_one_to_one(self, bold_code: str):
        """Int mapping: replace char with another, style preserved."""
        s = ANSIString("abc").style(SGR.BOLD)
        result = s.translate({ord("a"): ord("x")})
        assert result.plain_text == "xbc"
        assert str(result) == ansi_wrap("xbc", bold_code)

    def test_translate_deletion(self, bold_code: str):
        """None mapping: delete char, styles shift correctly."""
        s = ANSIString("abc").style(SGR.BOLD)
        result = s.translate({ord("b"): None})
        assert result.plain_text == "ac"
        assert str(result) == ansi_wrap("ac", bold_code)

    def test_translate_expansion(self, bold_code: str):
        """Str mapping: expand char, source style replicated."""
        s = ANSIString("abc").style(SGR.BOLD)
        result = s.translate({ord("b"): "XYZ"})
        assert result.plain_text == "aXYZc"
        assert str(result) == ansi_wrap("aXYZc", bold_code)

    def test_translate_no_change(self, bold_code: str):
        """Table has no matching keys: styles copied as-is."""
        s = ANSIString("abc").style(SGR.BOLD)
        result = s.translate({ord("z"): ord("x")})
        assert result.plain_text == "abc"
        assert str(result) == ansi_wrap("abc", bold_code)

    def test_translate_mixed(self, bold_code: str, italic_code: str):
        """Mix of deletion, expansion, and 1:1 in one call."""
        s = ANSIString("abcd").style(SGR.BOLD, (0, 2)).style(SGR.ITALIC, (2, 4))
        table: dict[int, int | str | None] = {
            ord("a"): ord("X"),
            ord("b"): None,
            ord("c"): "MN",
        }
        result = s.translate(table)
        assert result.plain_text == "XMNd"
        expected = ansi_wrap("X", bold_code) + ansi_wrap("MNd", italic_code)
        assert str(result) == expected

    def test_translate_empty_string_mapping(self, bold_code: str):
        """Str mapping to empty string acts as deletion."""
        s = ANSIString("abc").style(SGR.BOLD)
        result = s.translate({ord("b"): ""})
        assert result.plain_text == "ac"
        assert str(result) == ansi_wrap("ac", bold_code)


class TestFormat:
    def test_format_keyword(self, bold_code: str):
        """Keyword arg: literal template styles preserved."""
        s = ANSIString("Hello, {name}!").style(SGR.BOLD)
        result = s.format(name="Alice")
        assert result.plain_text == "Hello, Alice!"
        expected = ansi_wrap("Hello, ", bold_code) + "Alice" + ansi_wrap("!", bold_code)
        assert str(result) == expected

    def test_format_positional(self, bold_code: str):
        """Positional arg with partial styling."""
        s = ANSIString("{0} + {1} = {2}").style(SGR.BOLD, (3, 6))
        result = s.format(1, 2, 3)
        assert result.plain_text == "1 + 2 = 3"
        expected = "1" + ansi_wrap(" + ", bold_code) + "2 = 3"
        assert str(result) == expected

    def test_format_auto_numbered(self, bold_code: str):
        """Auto-numbered {}: styles on surrounding literal text kept."""
        s = ANSIString("({})").style(SGR.BOLD)
        result = s.format("hi")
        assert result.plain_text == "(hi)"
        expected = ansi_wrap("(", bold_code) + "hi" + ansi_wrap(")", bold_code)
        assert str(result) == expected

    def test_format_escaped_braces(self, bold_code: str):
        """{{ and }} produce literal braces with styles."""
        s = ANSIString("a{{b}}c").style(SGR.BOLD)
        result = s.format()
        assert result.plain_text == "a{b}c"
        assert str(result) == ansi_wrap("a{b}c", bold_code)

    def test_format_with_spec(self, bold_code: str):
        """Format spec on field: literal styles kept, field output unstyled."""
        s = ANSIString("=[{:>5}]=").style(SGR.BOLD)
        result = s.format("hi")
        assert result.plain_text == "=[   hi]="
        expected = ansi_wrap("=[", bold_code) + "   hi" + ansi_wrap("]=", bold_code)
        assert str(result) == expected

    def test_format_no_styles(self):
        """No styles: plain ANSIString returned."""
        s = ANSIString("Hello, {name}!")
        result = s.format(name="World")
        assert result.plain_text == "Hello, World!"
        assert not result.style_manager

    def test_format_nested_spec(self, bold_code: str):
        """Nested format spec {:{}} resolves correctly."""
        s = ANSIString("[{:{}}]").style(SGR.BOLD)
        result = s.format("hi", ">6")
        assert result.plain_text == "[    hi]"
        expected = ansi_wrap("[", bold_code) + "    hi" + ansi_wrap("]", bold_code)
        assert str(result) == expected


class TestFormatMap:
    def test_format_map_keyword(self, bold_code: str):
        """Mapping lookup: literal template styles preserved."""
        s = ANSIString("Hello, {name}!").style(SGR.BOLD)
        result = s.format_map({"name": "Bob"})
        assert result.plain_text == "Hello, Bob!"
        expected = ansi_wrap("Hello, ", bold_code) + "Bob" + ansi_wrap("!", bold_code)
        assert str(result) == expected

    def test_format_map_escaped_braces(self, bold_code: str):
        """{{ and }} with format_map."""
        s = ANSIString("{{x}}={val}").style(SGR.BOLD)
        result = s.format_map({"val": 42})
        assert result.plain_text == "{x}=42"
        expected = ansi_wrap("{x}=", bold_code) + "42"
        assert str(result) == expected

    def test_format_map_no_styles(self):
        """No styles: plain ANSIString returned."""
        s = ANSIString("{a}+{b}")
        result = s.format_map({"a": 1, "b": 2})
        assert result.plain_text == "1+2"
        assert not result.style_manager

    def test_format_map_with_spec(self, bold_code: str):
        """Format spec with mapping."""
        s = ANSIString("[{val:>5}]").style(SGR.BOLD)
        result = s.format_map({"val": "hi"})
        assert result.plain_text == "[   hi]"
        expected = ansi_wrap("[", bold_code) + "   hi" + ansi_wrap("]", bold_code)
        assert str(result) == expected
