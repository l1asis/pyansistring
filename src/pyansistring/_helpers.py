__all__ = [
    "find_spans",
    "search_separators",
    "rsearch_separators",
    "clamp",
    "hsl_to_rgb",
]

from collections.abc import Generator as _Generator
from colorsys import hls_to_rgb as _hls_to_rgb

from emoji import analyze as _emoji_analyze

from pyansistring.constants import WHITESPACE


def find_spans(string: str, substring: str) -> _Generator[tuple[int, int], None, None]:
    """Find all non-overlapping occurrences of `substring` in `string`."""
    if substring == "":
        raise ValueError("substring must not be empty")
    start = 0
    size = len(substring)
    while True:
        i = string.find(substring, start)
        if i == -1:
            break
        yield (i, i + size)
        start = i + size


def search_separators(
    string: str, allowed: set[str] = WHITESPACE
) -> _Generator[str, None, None]:
    """Search for allowed separators in a string."""
    separator = ""
    for char in string:
        if char in allowed:
            separator += char
        elif separator:
            yield separator
            separator = ""
    if separator:
        yield separator


def rsearch_separators(
    string: str, allowed: set[str] = WHITESPACE
) -> _Generator[str, None, None]:
    """Search for allowed separators in a string, starting from the end."""
    return search_separators(string[::-1], allowed)


def clamp(
    value: int | float,
    min_: int | float = float("-inf"),
    max_: int | float = float("inf"),
) -> int | float:
    """Restrict a number between two bounds.

    Parameters
    ----------
    value : int | float
        The number to clamp.
    min_ : int | float, default -inf
        The minimum allowable value.
    max_ : int | float, default inf
        The maximum allowable value.

    Returns
    -------
    int | float
        The clamped value.
    """
    return min_ if value < min_ else max_ if value > max_ else value


def hsl_to_rgb(
    hue: int | float, saturation: int | float = 100, lightness: int | float = 50
) -> tuple[int, int, int]:
    """Convert HSL color values to RGB.

    Parameters
    ----------
    hue : int | float
        The hue angle in degrees (0-360).
    saturation : int | float, default 100
        The saturation percentage (0-100).
    lightness : int | float, default 50
        The lightness percentage (0-100).

    Returns
    -------
    tuple[int, int, int]
        The resolved RGB values (0-255).
    """
    r, g, b = _hls_to_rgb(hue / 360, lightness / 100, saturation / 100)
    return round(r * 255), round(g * 255), round(b * 255)


def get_grapheme_spans(
    text: str, skip_emojis: bool, skip_whitespace: bool
) -> tuple[tuple[int, int], ...]:
    """Build slices that respect Unicode grapheme clusters (emojis).

    Parameters
    ----------
    text : str
        The text to analyze.
    skip_emojis : bool
        When True, emoji clusters are ignored and excluded from the returned spans.
    skip_whitespace : bool
        When True, whitespace characters are ignored and excluded.

    Returns
    -------
    tuple[tuple[int, int], ...]
        A tuple of (start, end) index bounds representing safe grapheme spans.
    """
    spans: list[tuple[int, int]] = []
    current_idx = 0

    for token in _emoji_analyze(text, non_emoji=True):
        chars = token.chars
        token_len = len(chars)

        start = current_idx
        end = current_idx + token_len

        current_idx = end

        if skip_emojis and not isinstance(token.value, str):
            continue
        if skip_whitespace and chars.isspace():
            continue

        spans.append((start, end))

    return tuple(spans)
