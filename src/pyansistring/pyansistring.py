
import re
from collections.abc import Generator, Hashable, Sequence
from dataclasses import dataclass
from functools import wraps
from types import MethodType
from typing import Annotated, Any, Callable, Dict, Literal, Self

from pyansistring.constants import *

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
        yield (start, index+1)

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

@dataclass
class ValueRange:
    lo: int
    hi: int

def wrapper_has_been_modified(method: Callable, bound: bool = False):
    @wraps(method)
    def wrapped(self: "StyleDict", *args, **kwargs):
        previous_length = len(self)
        if not bound:
            result = method(self, *args, **kwargs)
        else:
            result = method(*args, **kwargs)
        if not self._has_been_modified and previous_length != len(self):
            self._has_been_modified = True
        return result
    return wrapped

class StyleDict(dict):
    """
    A dictionary subclass for storing and tracking changes to styles.

    Attributes:
        _has_been_modified: A boolean indicating whether the styles have 
        been modified since the last check.

    Parameters:
        has_been_modified: A getter for `_has_been_modified`

    Usage:
        >>> style_dict = StyleDict()
        >>> style_dict[key] = value
        >>> style_dict.has_been_modified  # returns True
        >>> style_dict.has_been_modified  # returns False
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._has_been_modified = False
        for name in {"clear", "pop", "popitem", "setdefault", "update"}:
            setattr(self, name, 
                    MethodType(wrapper_has_been_modified(getattr(self, name), bound=True), self))

    @property
    def has_been_modified(self) -> bool:
        result = self._has_been_modified
        if self._has_been_modified:
            self._has_been_modified = False
        return result

    def __repr__(self) -> str:
        return f"StyleDict({dict.__repr__(self)})"

    def __setitem__(self, key: Hashable, value: Any) -> None:
        if isinstance(key, Hashable):
            self._has_been_modified = True
        return super().__setitem__(key, value)
        
    @wrapper_has_been_modified
    def __delitem__(self, key: Any) -> None:
        return super().__delitem__(key)
    
    def copy(self) -> "StyleDict":
        copied = StyleDict(dict.copy(self))
        copied._has_been_modified = self._has_been_modified
        return copied

class ANSIString(str):
    r"""
    String class that allows you to extend your vanilla str with ANSI escape sequences for coloring/styling.
    
    Attributes:
        _styles: dictionary containing pairs of char indices with ANSI escape sequences.
        _styled: plain string to which ANSI e.s. from `_styles` has been applied.
    
    Parameters:
        styles: a getter for `_styles`.
        styled: a getter for `_styled` (checks if `styles` has been modified and renders it if so).
        plain: unformatted, normal string.
        actual_length: returns the length of `styled`.
    
    Note:
        *The `ANSIString` class is unhashable for consistency, because `styles` is an unhashable dict 
        that we can change.
    """
    
    def __new__(cls,
                string: str = "",
                styles: StyleDict | dict[int, str] | None = None):
        obj = super().__new__(cls, string)
        if not styles:
            obj._styles = StyleDict()
        elif type(styles) == dict:
            obj._styles = StyleDict(styles)
        else:
            obj._styles = styles
        obj._styled = cls._render(obj)
        return obj
    
    @property
    def styles(self) -> StyleDict:
        return self._styles
    
    @property
    def styled(self) -> str:
        if self._styles.has_been_modified:
            self._styled = self._render()
        return self._styled
    
    @property
    def plain(self) -> str:
        return str.__str__(self)
    
    @property
    def actual_length(self) -> int:
        return len(self.styled)

    def __str__(self) -> str:
        return self.styled
    
    def __repr__(self) -> str:
        return f"ANSIString({str.__repr__(self.plain)}, {self.styles if self.styles else None})"
    
    def __eq__(self, value: object) -> bool:
        return self.styled == value

    def __add__(self, string) -> "ANSIString":
        styles = self.styles.copy()
        if type(string) == ANSIString:
            styles.update({len(self)+index: value for index, value in string.styles.items()})
            string = string.plain
        return type(self)(self.plain + string, styles)
    
    def __radd__(self, string) -> "ANSIString":
        styles = {index+len(string): value for index, value in self.styles.items()}
        if type(string) == ANSIString:
            styles.update(string.styles)
            string = string.plain
        return type(self)(string + self.plain, styles)

    def __getitem__(self, key: slice) -> "ANSIString":
        styles = {new_index: self.styles[old_index] 
                  for new_index, old_index in enumerate(range(len(self))[key])
                  if old_index in self.styles}
        return type(self)(super().__getitem__(key), styles)

    def __getattribute__(self, name: str):
        if name in dir(str) and name not in {"ljust", "rjust", "center", "split", "rsplit", "join"}:
            def method(self, *args, **kwargs):
                value = getattr(super(), name)(*args, **kwargs)
                if isinstance(value, str):
                    return type(self)(value, self.styles)
                elif isinstance(value, list):
                    return [type(self)(i, self.styles) for i in value]
                elif isinstance(value, tuple):
                    return tuple(type(self)(i, self.styles) for i in value)
                else:
                    return value
            return method.__get__(self)
        else:
            return super().__getattribute__(name)

    def __format__(self, format_spec: str):
        if len(format_spec) > 1 and (align := format_spec[1]) in ("<", ">", "^"):
            fill = format_spec[0]
            minimum_width = int(format_spec[2:])
            if align == "<":
                return self.ljust(minimum_width, fill)
            elif align == ">":
                return self.rjust(minimum_width, fill)
            elif align == "^":
                return self.center(minimum_width, fill)
        return super().__format__(format_spec)

    def _render(self) -> str:
        return "".join(
            f"{self.styles[index]}{char}\x1b[0m" if index in self.styles else char
            for index, char in enumerate(self.plain)
        )

    def _get_indices(self, slice_: Sequence[int, int, int] | slice) -> tuple[int, int, int]:
        if isinstance(slice_, slice):
            start, stop, step = slice_.indices(len(self))
        else:
            start, stop, step = slice(*slice_).indices(len(self))
        return start, stop, step
    
    def _search_spans(self, *words: str, case_sensitive: bool = True) -> tuple[tuple[int, int], ...]:
        flags = (0 if case_sensitive else re.IGNORECASE)
        words = "|".join(re.escape(word) for word in words)
        spans = (match.span(0) for match in re.finditer(words, self.plain, flags=flags))
        return tuple(spans)

    def fm(self,
           parameter: int | str,
           *slices: Sequence[int, int, int] | slice) -> Self:
        """Formats (applies styling to) the string in a specified range."""
        if parameter == SGR.RESET: return self.unfm(*slices)
        style = f"\x1b[{parameter}m"
        if slices:
            for slice_ in slices:
                for index in range(*self._get_indices(slice_)):
                    if index in self.styles:
                        self.styles[index] += style
                    else:
                        self.styles[index] = style
        else:
            for index in range(0, len(self), 1):
                if index in self.styles:
                    self.styles[index] += style
                else:
                    self.styles[index] = style
        return self

    def fm_w(self,
             parameter: int | str,
             *words: str,
             case_sensitive: bool = True) -> Self:
        """Formats (applies styling to) the word of the string."""
        return self.fm(parameter, *self._search_spans(*words, case_sensitive=case_sensitive))

    def unfm(self,
             *slices: Sequence[int, int, int] | slice) -> Self:
        """Unformats (removes styling) the string in a specified range."""
        if slices:
            for slice_ in slices:
                for index in range(*self._get_indices(slice_)):
                    if index in self.styles:
                        del self.styles[index]
        else:
            for index in range(0, len(self), 1):
                if index in self.styles:
                    del self.styles[index]
        return self

    def unfm_w(self,
               *words: str,
               case_sensitive: bool = True) -> Self:
        """Unformats (removes styling) the string per word index."""
        return self.unfm(*self._search_spans(*words, case_sensitive=case_sensitive))

    def fg_4b(self,
              parameter: Foreground,
              *slices: Sequence[int, int, int] | slice) -> Self:
        return self.fm(parameter, *slices)

    def fg_4b_w(self,
                parameter: Foreground,
                *words: str,
                case_sensitive: bool = True) -> Self:
        return self.fg_4b(parameter, *self._search_spans(*words, case_sensitive=case_sensitive))

    def fg_8b(self,
              parameter: Annotated[int, ValueRange(0, 255)],
              *slices: Sequence[int, int, int] | slice) -> Self:
        """Applies the foreground given by the 8-bit color number (0-255) to the string in a specified range."""
        parameter = f"{Foreground.SET};5;{parameter}"
        return self.fm(parameter, *slices)

    def fg_8b_w(self,
                parameter: Annotated[int, ValueRange(0, 255)],
                *words: str,
                case_sensitive: bool = True) -> Self:
        return self.fg_8b(parameter, *self._search_spans(*words, case_sensitive=case_sensitive))

    def fg_24b(self,
               r: Annotated[int, ValueRange(0, 255)],
               g: Annotated[int, ValueRange(0, 255)],
               b: Annotated[int, ValueRange(0, 255)],
               *slices: Sequence[int, int, int] | slice) -> Self:
        """Applies the foreground given by RGB to the string in a specified range."""
        parameter = f"{Foreground.SET};2;{r};{g};{b}"
        return self.fm(parameter, *slices)

    def fg_24b_w(self,
                 r: Annotated[int, ValueRange(0, 255)],
                 g: Annotated[int, ValueRange(0, 255)],
                 b: Annotated[int, ValueRange(0, 255)],
                 *words: str,
                 case_sensitive: bool = True) -> Self:
        return self.fg_24b(r, g, b, *self._search_spans(*words, case_sensitive=case_sensitive))

    def bg_4b(self,
              parameter: Foreground,
              *slices: Sequence[int, int, int] | slice) -> Self:
        return self.fm(parameter, *slices)

    def bg_4b_w(self,
                parameter: Foreground,
                *words: str,
                case_sensitive: bool = True) -> Self:
        return self.bg_4b(parameter, *self._search_spans(*words, case_sensitive=case_sensitive))

    def bg_8b(self,
              parameter: Annotated[int, ValueRange(0, 255)],
              *slices: Sequence[int, int, int] | slice) -> Self:
        """Applies the background given by the 8-bit color number (0-255) to the string in a specified range."""
        parameter = f"{Background.SET};5;{parameter}"
        return self.fm(parameter, *slices)
    
    def bg_8b_w(self,
                parameter: Annotated[int, ValueRange(0, 255)],
                *words: str,
                case_sensitive: bool = True) -> Self:
        return self.bg_8b(parameter, *self._search_spans(*words, case_sensitive=case_sensitive))

    def bg_24b(self,
               r: Annotated[int, ValueRange(0, 255)],
               g: Annotated[int, ValueRange(0, 255)],
               b: Annotated[int, ValueRange(0, 255)],
               *slices: Sequence[int, int, int] | slice) -> Self:
        """Applies the background given by RGB to the string in a specified range."""
        parameter = f"{Background.SET};2;{r};{g};{b}"
        return self.fm(parameter, *slices)
    
    def bg_24b_w(self,
                 r: Annotated[int, ValueRange(0, 255)],
                 g: Annotated[int, ValueRange(0, 255)],
                 b: Annotated[int, ValueRange(0, 255)],
                 *words: str,
                 case_sensitive: bool = True) -> Self:
        return self.bg_24b(r, g, b, *self._search_spans(*words, case_sensitive=case_sensitive))

    def ljust(self, width: int, fillchar: str = " ") -> "ANSIString":
        return self + fillchar*(width - len(self))

    def rjust(self, width: int, fillchar: str = " ") -> "ANSIString":
        return fillchar*(width - len(self)) + self

    def center(self, width: int, fillchar: str = " ") -> "ANSIString":
        margin = width - len(self)
        left = (margin // 2) + (margin & width & 1)
        return fillchar*left + self + fillchar*(margin-left)

    def split(self, sep: str|None = None, maxsplit: int = -1) -> list['ANSIString']:
        actual = super().split(sep, maxsplit)
        min_index = 0
        if not sep:
            whitespace = search_separators(self.plain)
            if self.plain[0] in WHITESPACE:
                min_index += len(next(whitespace, ""))
        for no, string in enumerate(actual):
            max_index = min_index+len(string)
            styles = {index-min_index: self.styles[index] for index in range(min_index, max_index) if index in self.styles}
            actual[no] = type(self)(string, StyleDict(styles))
            min_index += len(string) + (len(sep) if sep else len(next(whitespace, "")))
        return actual
    
    def rsplit(self, sep: str|None = None, maxsplit: int = -1) -> list['ANSIString']:
        actual = super().rsplit(sep, maxsplit)
        max_index = len(self)
        if not sep:
            whitespace = rsearch_separators(self.plain)
            if self.plain[-1] in WHITESPACE:
                max_index -= len(next(whitespace, ""))
        for no, string in enumerate(actual[::-1]):
            min_index = max_index-len(string)
            styles = {index-min_index: self.styles[index] for index in range(min_index, max_index) if index in self.styles}
            actual[len(actual)-1-no] = type(self)(string, StyleDict(styles))
            max_index -= len(string) + (len(sep) if sep else len(next(whitespace, "")))
        return actual
    
    def join(self, iterable: list[str], /) -> "ANSIString":
        styles, increment = {}, 0
        for i, string in enumerate(iterable):
            increment += len(string)
            if i: increment += len(self)
            styles.update({increment+index: style for index, style in self.styles.items()})
            if type(string) == ANSIString:
                styles.update({increment+index-len(string): style for index, style in string.styles.items()})
        return type(self)(super().join(iterable), StyleDict(styles))

    @staticmethod
    def from_ansi(plain: str) -> "ANSIString":
        start, style, styles = 0, "", {}
        decrement, sequences = 0, {}
        def smart_replacement(match_: re.Match[str]) -> str:
            nonlocal decrement
            sequence, span = match_.group(0), match_.span(0)
            if sequence.endswith("m"):
                if span[0]-decrement in sequences:
                    sequences[span[0]-decrement] += sequence
                else:
                    sequences[span[0]-decrement] = sequence
            decrement += len(sequence)
            return ""
        plain = re.sub(Regex.ANSI_SEQ, smart_replacement, plain)
        for index, sequence in sequences.items():
            for match_ in re.finditer(Regex.SGR_PARAM, sequence):
                parameter = match_.group(0)
                if parameter == "0":
                    if style:
                        for sub_index in range(start, index):
                            styles[sub_index] = style
                        style = ""
                else:
                    style += f"\x1b[{parameter}m"
                    start = index
        return ANSIString(plain, styles)
