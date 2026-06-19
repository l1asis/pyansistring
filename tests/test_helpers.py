"""Tests for pyansistring.helpers utility functions."""

from unittest.mock import patch

import pytest

from pyansistring._helpers import (
    clamp,
    find_spans,
    get_grapheme_spans,
    hsl_to_rgb,
    rsearch_separators,
    search_separators,
)
from pyansistring.constants import PUNCTUATION, WHITESPACE


class TestFindSpans:
    @pytest.mark.parametrize(
        "text, sub, expected",
        [
            pytest.param(
                "Hello, World! Hello, World! He",
                "He",
                ((0, 2), (14, 16), (28, 30)),
                id="multiple-occurrences",
            ),
            pytest.param("abcdef", "xyz", (), id="no-match"),
            pytest.param("aaa", "a", ((0, 1), (1, 2), (2, 3)), id="single-char"),
            pytest.param("", "x", (), id="empty-string"),
            pytest.param("aaa", "aa", ((0, 2),), id="non-overlapping"),
        ],
    )
    def test_find_spans(
        self, text: str, sub: str, expected: tuple[tuple[int, int], ...]
    ):
        result = tuple(find_spans(text, sub))
        assert result == expected, (
            f"find_spans({text!r}, {sub!r}) = {result}, expected {expected}"
        )


class TestSearchSeparators:
    @pytest.mark.parametrize(
        "text, seps, expected",
        [
            pytest.param(
                "Hello, World!",
                WHITESPACE | PUNCTUATION,
                (", ", "!"),
                id="ws-and-punct",
            ),
            pytest.param("a b  c", None, (" ", "  "), id="only-whitespace"),
            pytest.param("abc", None, (), id="no-separators"),
            pytest.param("   ", None, ("   ",), id="all-separators"),
        ],
    )
    def test_search_forward(
        self, text: str, seps: set[str] | None, expected: tuple[str, ...]
    ):
        if seps is None:
            result = tuple(search_separators(text))
        else:
            result = tuple(search_separators(text, seps))
        assert result == expected, (
            f"search_separators({text!r}) = {result}, expected {expected}"
        )


class TestRsearchSeparators:
    @pytest.mark.parametrize(
        "text, seps, expected",
        [
            pytest.param(
                "Hello, World!",
                WHITESPACE | PUNCTUATION,
                ("!", " ,"),
                id="ws-and-punct-reversed",
            ),
            pytest.param("abc", None, (), id="no-separators"),
        ],
    )
    def test_search_reversed(
        self, text: str, seps: set[str] | None, expected: tuple[str, ...]
    ):
        if seps is None:
            result = tuple(rsearch_separators(text))
        else:
            result = tuple(rsearch_separators(text, seps))
        assert result == expected, (
            f"rsearch_separators({text!r}) = {result}, expected {expected}"
        )


class TestClamp:
    @pytest.mark.parametrize(
        "value, min_val, max_val, expected",
        [
            pytest.param(5, 0, 10, 5, id="within-range"),
            pytest.param(-5, 0, 10, 0, id="below-min"),
            pytest.param(15, 0, 10, 10, id="above-max"),
            pytest.param(999, None, None, 999, id="no-upper-bound"),
            pytest.param(-999, None, None, -999, id="no-lower-bound"),
        ],
    )
    def test_clamp(
        self, value: int, min_val: int | None, max_val: int | None, expected: int
    ):
        kwargs: dict[str, int] = {}
        if min_val is not None:
            kwargs["min_"] = min_val
        if max_val is not None:
            kwargs["max_"] = max_val
        result = clamp(value, **kwargs) if kwargs else clamp(value)
        assert result == expected, (
            f"clamp({value}, {min_val}, {max_val}) = {result}, expected {expected}"
        )


class TestHslToRgb:
    @pytest.mark.parametrize(
        "hue, saturation, lightness, expected",
        [
            pytest.param(0, 100, 50, (255, 0, 0), id="pure-red"),
            pytest.param(0, 0, 0, (0, 0, 0), id="black"),
        ],
    )
    def test_known_colors(
        self, hue: int, saturation: int, lightness: int, expected: tuple[int, int, int]
    ):
        assert hsl_to_rgb(hue, saturation, lightness) == expected, (
            f"hsl_to_rgb({hue},{saturation},{lightness}) should be {expected}"
        )

    def test_returns_ints(self):
        r, g, b = hsl_to_rgb(120)
        assert all(isinstance(value, int) for value in (r, g, b)), (
            "hsl_to_rgb must return ints"
        )


class TestGetGraphemeSpans:
    def test_standard_text(self):
        """Standard 1-to-1 character iteration."""
        text = "abc"
        spans = get_grapheme_spans(text, skip_emojis=False, skip_whitespace=False)
        assert spans == ((0, 1), (1, 2), (2, 3))

    def test_simple_emoji(self):
        """Simple emojis count as exactly 1 Python string index."""
        text = "a😀b"
        spans = get_grapheme_spans(text, skip_emojis=False, skip_whitespace=False)
        assert spans == ((0, 1), (1, 2), (2, 3))

    def test_zwj_sequence(self):
        """ZWJ sequences (like female astronaut) are 3 code points glued together."""
        text = "👩‍🚀!"
        # 👩(1) + ZWJ(1) + 🚀(1) = length 3 -> span(0, 3)
        spans = get_grapheme_spans(text, skip_emojis=False, skip_whitespace=False)
        assert spans == ((0, 3), (3, 4))

    def test_modifier_sequence(self):
        """Skin tone modifiers are 2 code points glued together."""
        text = "👍🏽"
        # 👍(1) + 🏽(1) = length 2 -> span(0, 2)
        spans = get_grapheme_spans(text, skip_emojis=False, skip_whitespace=False)
        assert spans == ((0, 2),)

    def test_variation_selector(self):
        """
        Standard text characters forced into emoji rendering via Variation Selector-16.
        """
        text = "☁️"
        # ☁ (U+2601) + VS16 (U+FE0F) = length 2
        spans = get_grapheme_spans(text, skip_emojis=False, skip_whitespace=False)
        assert spans == ((0, 2),)

    def test_regional_indicator_flag(self):
        """Flags are made of two Regional Indicator characters."""
        text = "🇩🇪"
        # 🇩(1) + 🇪(1) = length 2
        spans = get_grapheme_spans(text, skip_emojis=False, skip_whitespace=False)
        assert spans == ((0, 2),)

    def test_multiple_simple_emojis(self):
        """Consecutive emojis without joiners should be split."""
        text = "😀😁"
        spans = get_grapheme_spans(text, skip_emojis=False, skip_whitespace=False)
        assert spans == ((0, 1), (1, 2))

    def test_consecutive_complex_emojis(self):
        """Mixed complex emojis and text should maintain perfect index tracking."""
        text = "a👩‍🚀👍🏽b"
        spans = get_grapheme_spans(text, skip_emojis=False, skip_whitespace=False)
        assert spans == ((0, 1), (1, 4), (4, 6), (6, 7))

    def test_empty(self):
        """An empty string should return an empty tuple."""
        spans = get_grapheme_spans("", skip_emojis=False, skip_whitespace=False)
        assert spans == ()

    def test_skip_whitespace(self):
        """Verify spaces, tabs, and newlines are skipped correctly."""
        text = "a \t\n b"
        spans = get_grapheme_spans(text, skip_emojis=False, skip_whitespace=True)
        assert spans == ((0, 1), (5, 6))

    def test_skip_emojis(self):
        """Verify all types of emojis are skipped."""
        text = "a👩‍🚀b👍🏽c"
        spans = get_grapheme_spans(text, skip_emojis=True, skip_whitespace=False)
        assert spans == ((0, 1), (4, 5), (7, 8))

    def test_skip_emojis_and_whitespace(self):
        """Verify dual filtering works concurrently."""
        text = "a 👩‍🚀 b"
        spans = get_grapheme_spans(text, skip_emojis=True, skip_whitespace=True)
        assert spans == ((0, 1), (6, 7))

    @patch("pyansistring._helpers._IS_EMOJI_AVAILABLE", False)
    def test_fallback_no_emoji_package(self):
        """
        If emoji package is missing and skip_emojis is False, fallback to enumerate.
        """
        text = "a b"
        spans = get_grapheme_spans(text, skip_emojis=False, skip_whitespace=True)
        assert spans == ((0, 1), (2, 3))

    @patch("pyansistring._helpers._IS_EMOJI_AVAILABLE", False)
    def test_raise_on_skip_emojis_without_package(self):
        """
        If user wants to skip emojis but the package is missing, raise ImportError.
        """
        text = "abc"
        with pytest.raises(ImportError, match="The 'emoji' package is required"):
            get_grapheme_spans(text, skip_emojis=True, skip_whitespace=False)
