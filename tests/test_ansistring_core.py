"""Tests for ANSIString construction, properties, repr, equality, and from_ansi."""

from typing import Any

import pytest

from pyansistring import ANSIString, StyleManager
from pyansistring.color import Color
from pyansistring.constants import SGR, Foreground
from pyansistring.style import Style
from tests.conftest import ansi_wrap


class TestConstruction:
    def test_plain_text(self, hello_world: ANSIString):
        assert hello_world.plain_text == "Hello, World!", "plain_text mismatch"
        assert hello_world.styled_text == "Hello, World!", (
            "Unstyled styled_text should match plain"
        )
        assert str(hello_world) == "Hello, World!"
        assert len(hello_world.style_manager) == 0, "No styles should be present"

    @pytest.mark.parametrize(
        "styles_input, description",
        [
            pytest.param(
                StyleManager(),
                "StyleManager object",
                id="style-manager",
            ),
            pytest.param(
                {0: Style(foreground=Color.from_4bit(Foreground.RED))},
                "dict of Styles",
                id="dict-of-styles",
            ),
            pytest.param(
                {0: "\x1b[31m"},
                "dict of raw ANSI strings",
                id="dict-of-ansi-strings",
            ),
        ],
    )
    def test_construction_with_styles(self, styles_input: Any, description: str):
        if isinstance(styles_input, StyleManager):
            styles_input[0] = Style(foreground=Color.from_4bit(Foreground.RED))
        s = ANSIString("Hi", styles_input)
        assert len(s.style_manager) == 1, (
            f"Construction with {description} should have 1 style"
        )

    def test_empty_string(self):
        s = ANSIString("")
        assert s.plain_text == "", "Empty ANSIString plain_text should be ''"
        assert str(s) == ""

    def test_styled_text_renders_correctly(self, bold_code: str):
        s = ANSIString("Hello, World!").style(SGR.BOLD)
        assert str(s) == ansi_wrap("Hello, World!", bold_code)

    def test_actual_length(self):
        s = ANSIString("Hello, World!").style(SGR.BOLD)
        assert s.styled_length > len("Hello, World!"), (
            "actual_length should exceed plain length due to ANSI codes"
        )


class TestRepr:
    def test_repr_contains_class(self, hello_world: ANSIString):
        assert "ANSIString" in repr(hello_world), "repr must mention 'ANSIString'"

    def test_repr_plain_eval_roundtrip(self):
        s = ANSIString("Hello!")
        assert eval(repr(str(s))) == str(s), "eval(repr(styled_text)) should roundtrip"


class TestEquality:
    def test_compares_styled_text(self, bold_code: str):
        s = ANSIString("Hi").style(SGR.BOLD)
        assert s == ansi_wrap("Hi", bold_code), (
            "ANSIString should equal its rendered output"
        )

    def test_plain_equals_plain_str(self):
        assert ANSIString("Hi") == "Hi", "Plain ANSIString should equal plain str"


class TestFromAnsi:
    """Parse raw ANSI strings back into ANSIString."""

    def test_basic_parse(self):
        blue = "\x1b[38;2;0;0;255m"
        raw = (
            ansi_wrap("Hello", blue)
            + ", "
            + ansi_wrap("World", "\x1b[38;2;255;255;0m")
            + "!"
        )
        result = ANSIString.from_ansi(raw)
        assert result.plain_text == "Hello, World!", (
            "Parsed plain_text should strip ANSI"
        )

    def test_preserves_style(self):
        blue = "\x1b[38;2;0;0;255m"
        raw = ansi_wrap("Hello", blue) + ", World!"
        result = ANSIString.from_ansi(raw)
        expected = ANSIString("Hello, World!").fg_24b(0, 0, 255, (0, 5))
        assert result.style_manager == expected.style_manager, (
            "from_ansi should produce equivalent styles"
        )

    def test_roundtrip(self):
        s = (
            ANSIString("Hello, World!")
            .fg_24b(0, 0, 255, (0, 5))
            .fg_24b(255, 255, 0, (7, 12))
        )
        parsed = ANSIString.from_ansi(s.styled_text)
        assert parsed.style_manager == s.style_manager, (
            "Style roundtrip should be lossless"
        )

    def test_ignores_non_sgr_escapes(self):
        """Cursor-move sequences like \\x1b[10;10H should be stripped."""
        raw = "\x1b[10;10H\x1b[31mH\x1b[0mello"
        result = ANSIString.from_ansi(raw)
        assert result.plain_text == "Hello", "Non-SGR escapes should be dropped"

    def test_parses_4bit_foreground_red(self):
        raw = "\x1b[31mError\x1b[0m: file not found"
        parsed = ANSIString.from_ansi(raw)
        expected = ANSIString("Error: file not found").fg_4b(Foreground.RED, (0, 5))

        assert parsed.style_manager == expected.style_manager, (
            "SGR 31 should parse as red foreground, not split into style attrs"
        )

    def test_style_change_without_intermediate_reset(self):
        raw = "\x1b[31mA\x1b[32mB\x1b[0m"
        parsed = ANSIString.from_ansi(raw)
        expected = (
            ANSIString("AB")
            .fg_4b(Foreground.RED, (0, 1))
            .fg_4b(Foreground.GREEN, (1, 2))
        )

        assert parsed.style_manager == expected.style_manager, (
            "Changing colors mid-string should preserve the previous styled span"
        )

    def test_trailing_style_without_reset_is_applied(self):
        parsed = ANSIString.from_ansi("\x1b[31mX")
        expected = ANSIString("X").fg_4b(Foreground.RED, (0, 1))

        assert parsed.style_manager == expected.style_manager, (
            "Active styles at end-of-input should be applied even without reset"
        )
