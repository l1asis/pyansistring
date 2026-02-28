"""Tests for pyansistring.helpers utility functions."""

import pytest

from pyansistring._helpers import (
    clamp,
    find_spans,
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
