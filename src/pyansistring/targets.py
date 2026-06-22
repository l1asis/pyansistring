__all__ = [
    "Words",
    "Chars",
    "Coords",
    "Pattern",
]

import re as _re
from collections.abc import Callable as _Callable, Iterable as _Iterable
from dataclasses import dataclass as _dataclass
from typing import Any as _Any, Literal as _Literal

from ._types import CoordinateGroup as _CoordinateGroup


@_dataclass(slots=True, frozen=True)
class Words:
    """Target specific words or substrings within the text.

    Parameters
    ----------
    words : tuple[str, ...]
        A tuple of literal string words/phrases to search for.
    ignore_case : bool, default False
        Whether to perform a case-insensitive search.
    """

    words: tuple[str, ...]
    ignore_case: bool = False


@_dataclass(slots=True, frozen=True)
class Chars:
    """Target individual characters/graphemes.

    Parameters
    ----------
    skip_whitespace : bool, default False
        If ``True``, whitespace characters will not be targeted.
    skip_emojis : bool, default False
        If ``True``, emoji grapheme clusters will not be targeted.
    """

    skip_whitespace: bool = False
    skip_emojis: bool = False


@_dataclass(slots=True, frozen=True)
class Coords:
    """Target specific 2D coordinates in the terminal space.

    Parameters
    ----------
    points : tuple[CoordinateGroup, ...]
        The coordinates to target, represented as (x, y) tuples.
    index_base : int, default 0
        The base index for coordinates (e.g., 0-indexed or 1-indexed).
    origin : tuple[int, int], default (0, 0)
        The origin offset added to all coordinates.
    system : Literal["cartesian", "terminal"], default "terminal"
        The coordinate system. "terminal" originates at the top-left (y goes down),
        while "cartesian" originates at the bottom-left (y goes up).
    on_out_of_bounds : Literal["ignore", "clamp", "raise"], default "raise"
        Behavior when a coordinate falls outside the string's dimensions.
    """

    points: tuple[_CoordinateGroup, ...]
    index_base: int = 0
    origin: tuple[int, int] = (0, 0)
    system: _Literal["cartesian", "terminal"] = "terminal"
    on_out_of_bounds: _Literal["ignore", "clamp", "raise"] = "raise"


@_dataclass(slots=True, frozen=True)
class Pattern:
    """Target text matching a regular expression.

    Parameters
    ----------
    regex : str | re.Pattern[str]
        The regular expression pattern to search for.
    flags : int | re.RegexFlag, default 0
        Regex flags (e.g., re.IGNORECASE) applied if regex is a string.
    group : int | str, default 0
        The capture group to target. Defaults to 0 (the entire match).
    span_parser : Callable[[re.Match[str]], Iterable[Any]] | None, default None
        A custom callback to extract custom spans from a Match object.
        Overrides the `group` parameter if provided.
    """

    regex: str | _re.Pattern[str]
    flags: int | _re.RegexFlag = 0
    group: int | str = 0
    span_parser: _Callable[[_re.Match[str]], _Iterable[_Any]] | None = None

    def __post_init__(self):
        if isinstance(self.regex, str):
            compiled = _re.compile(self.regex, self.flags)
            object.__setattr__(self, "regex", compiled)

    @classmethod
    def numeric(
        cls,
        flags: int | _re.RegexFlag = 0,
        group: int | str = 0,
        span_parser: _Callable[[_re.Match[str]], _Iterable[_Any]] | None = None,
    ) -> "Pattern":
        """Factory method to instantly generate a standardized Numeric pattern."""
        return cls(
            regex=r"[-+]?(?:\d*\.\d+|\d+)",
            flags=flags,
            group=group,
            span_parser=span_parser,
        )
