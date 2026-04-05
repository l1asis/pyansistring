__all__ = [
    "find_spans",
    "search_separators",
    "rsearch_separators",
    "clamp",
    "hsl_to_rgb",
]

from collections.abc import Generator as _Generator
from colorsys import hls_to_rgb as _hls_to_rgb

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
    """Restrict a number between two other numbers."""
    return min_ if value < min_ else max_ if value > max_ else value


def hsl_to_rgb(
    hue: int | float, saturation: int | float = 100, lightness: int | float = 50
) -> tuple[int, int, int]:
    """Convert HSL color values to RGB."""
    r, g, b = _hls_to_rgb(hue / 360, lightness / 100, saturation / 100)
    return round(r * 255), round(g * 255), round(b * 255)
