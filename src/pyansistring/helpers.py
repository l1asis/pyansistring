__all__ = [
    "search_word_spans",
    "search_separators",
    "rsearch_separators",
    "clamp",
    "hsl_to_rgb",
    "ValueRange",
    "Length",
]

from collections.abc import Generator
from dataclasses import dataclass

from pyansistring.constants import WHITESPACE


def search_word_spans(string: str, word: str) -> Generator[tuple[int, int]]:
    """Searches for a word spans in a string."""
    temp, start = "", None
    for index, char in enumerate(string):
        if len(temp) < len(word):
            if char in word[len(temp)]:
                temp += char
                if start is None:
                    start = index
            else:
                start, temp = None, ""
        else:
            yield start, index
            start, temp = None, ""
    if temp and len(temp) == len(word):
        yield (start, index + 1)


def search_separators(string: str, allowed: set = WHITESPACE):
    r"""Searches for allowed separators in a string."""
    separator = ""
    for char in string:
        if char in allowed:
            separator += char
        elif separator:
            yield separator
            separator = ""
    if separator:
        yield separator


def rsearch_separators(string: str, allowed: set = WHITESPACE):
    r"""Searches for allowed separators in a reversed string."""
    return search_separators(string[::-1], allowed)


def clamp(value: int | float, min=-float("inf"), max=float("inf")) -> int | float:
    return min if value < min else max if value > max else value


def hsl_to_rgb(hue: int | float, saturation: int = 100, lightness: int = 50) -> tuple[int, int, int]:
    hue = hue / 100
    saturation = saturation / 100
    lightness = lightness / 100

    def f(n: int | float):
        k = (n + hue * (10 / 3)) % 12
        a = saturation * min(lightness, 1 - lightness)
        return round((lightness - a * max(-1, min(k - 3, 9 - k, 1))) * 255)

    return f(0), f(8), f(4)


@dataclass
class ValueRange:
    lo: int
    hi: int

    def __hash__(self) -> int:
        return hash((self.lo, self.hi))


@dataclass
class Length:
    value: int

    def __hash__(self) -> int:
        return hash(self.value)
