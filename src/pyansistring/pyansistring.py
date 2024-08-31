
import re
from collections.abc import Generator, Hashable, Sequence
from copy import copy, deepcopy
from dataclasses import dataclass
from functools import wraps
from itertools import cycle
from random import randint
from types import MethodType
from typing import Annotated, Any, Callable, Dict, Literal, Self, Tuple

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

def clamp(value: int|float, min = -float("inf"), max = float("inf")) -> int|float:
    return min if value < min else max if value > max else value

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

class MulticolorInstruction:
    color: str
    operator: str
    value: str
    processed_value: int | float
    mode: str
    minmax: tuple[float, float]
    repeat: int
    def __init__(self, rgb: dict[str, dict[str, int]], **kwargs) -> None:
        allowed_keys = {"color", "operator", "value", "mode", "minmax", "repeat"}
        missing_keys = tuple(k for k in allowed_keys if k not in kwargs)
        if not kwargs or len(missing_keys):
            raise TypeError(f"{self.__class__}.__init__() missing {len(missing_keys)}"
                            f" required keyword argument{'s' if len(missing_keys)>1 else ''}:"
                            ", ".join(missing_keys))

        self.rgb = rgb
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.processed_value = self.process_value(self.value)

        if isinstance(self.minmax, str):
            self.minmax = tuple(map(float, self.minmax[7:-1].split(",")))
        elif self.minmax is None:
            self.minmax = (0, 255)

        if not self.mode:
            self.mode = "fg"

        if self.operator == ">":
            base_value = rgb[self.mode][self.color]
            if base_value <= self.processed_value:
                self.operator = "+"
                self.processed_value = (self.processed_value - base_value) / self.repeat
            elif base_value > self.processed_value:
                self.operator = "-"
                self.processed_value = (base_value - self.processed_value) / self.repeat

    def process_value(self, value: str, save: bool = False) -> int | float:
        if value.startswith("random"):
            from_value, to_value = map(int, value[7:-1].split(","))
            value = randint(from_value, to_value)
        elif value.endswith(("r", "g", "b")):
            mode, color = value.split("_")
            value = self.rgb[mode][color]
        else:
            value = float(value)
        if save:
            self.processed_value = value
        return value

class MulticolorCommand:
    def __init__(self,
                 instructions: list[MulticolorInstruction] | None = None,
                 reset: str | None = None,
                 repeat: int | str | None = None) -> None:
        self.instructions = instructions if instructions else []
        self.reset = reset
        if isinstance(repeat, str):
            self.repeat = int(repeat[7:-1])
        else:
            self.repeat = 1 if repeat is None else repeat

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

    def _coord_to_slice(self, coord: tuple[int, int]) -> slice:
        index = 0
        lengths = tuple(len(line) for line in self.plain.splitlines())
        if not lengths:
            raise IndexError(f"wrong y coordinate (empty string)")
        elif not (0 <= coord[1] < len(lengths)):
            raise IndexError(f"wrong y coordinate (0<=y<{len(lengths)})")
        for y, length in enumerate(lengths):
            if y == coord[1]:
                if not length:
                    raise IndexError(f"wrong x coordinate ({y=}: empty line)")
                elif not (0 <= coord[0] < length):
                    raise IndexError(f"wrong x coordinate ({y=}: 0<=x<{length})")
                index += coord[0] + y
                break
            index += length
        return slice(index, index+1)

    def _get_all_coords(self) -> tuple[tuple[int, int]]:
        def transform(lengths):
            for y, length in enumerate(lengths):
                for x in range(length):
                    yield (x, y)
        return tuple(transform(len(line) for line in self.plain.splitlines()))

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
    
    def _process_multicolor_command(self,
                                    command: MulticolorCommand,
                                    rgb: dict[str, dict[str, dict[str, int]]],
                                    *slices: Annotated[Sequence[int], Length(3)] | slice):
        if command.reset:
            if command.reset == "?":
                reset_rgb = deepcopy(rgb["actual"])
            elif command.reset == "??":
                reset_rgb = deepcopy(rgb["start"])
        else:
            reset_rgb = None

        modes = {"fg": False, "bg": False, "ul": False}
        for instruction in command.instructions:
            if not modes[instruction.mode]:
                modes[instruction.mode] = True
            if instruction.operator == "=":
                rgb["actual"][instruction.mode][instruction.color] = instruction.processed_value
            elif instruction.operator == "+":
                rgb["actual"][instruction.mode][instruction.color] += instruction.processed_value
            elif instruction.operator == "-":
                rgb["actual"][instruction.mode][instruction.color] -= instruction.processed_value

            rgb["actual"][instruction.mode][instruction.color] = clamp(
                rgb["actual"][instruction.mode][instruction.color], *instruction.minmax
            )
        
        if slices:
            self._apply_multicolor_command(rgb["actual"], modes, *slices)
        
        if reset_rgb:
            rgb["actual"] = reset_rgb

        return modes
    
    def _apply_multicolor_command(self,
                                rgb: dict[str, dict[str, int]],
                                modes: dict[str, bool],
                                *slices: Sequence[int, int, int] | slice) -> None:
        if modes["fg"]:
            self.fg_24b(*(int(clamp(rgb["fg"][key], 0, 255)) for key in "rgb"), *slices)
        if modes["bg"]:
            self.bg_24b(*(int(clamp(rgb["bg"][key], 0, 255)) for key in "rgb"), *slices)
        if modes["ul"]:
            NotImplemented

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
    
    def multicolor(self,
                   sequence: str,
                   *slices: Annotated[Sequence[int], Length(3)] | slice) -> Self:
        if not slices:
            slices = tuple((index, index+1) for index in range(0, len(self)))
        
        flags = {flag: 0 for flag in ("skipfirst", "cycle", "reverse", "mirror")}
        offset = 0
        for char in reversed(sequence):
            if char == "*":
                flags["skipfirst"] = 1; offset -= 1
            elif char == "&":
                flags["cycle"] = 1; offset -= 1
            elif char == "@":
                flags["reverse"] = 1; offset -= 1
            elif char == "!":
                flags["mirror"] = 1; offset -= 1
            elif char == " ":
                offset -= 1
            else:
                break
        if offset:
            sequence = sequence[:offset]
        
        rgb = {
            key: {
                key: {
                    key: 0 for key in ("r", "g", "b")
                } for key in ("fg", "bg", "ul")
            } for key in ("actual", "start")
        }

        if "$" in sequence:
            start_command, sequence = map(str.strip, sequence.split("$"))
            object_start_command = MulticolorCommand()
            for start_instruction in map(str.strip, start_command.split("|")):
                match_start_instruction = re.match(Regex.MULTICOLOR_INSTRUCTION, start_instruction)
                object_start_instruction = MulticolorInstruction(
                    rgb["actual"], **match_start_instruction.groupdict(), repeat=object_start_command.repeat
                )
                if match_start_instruction:
                    object_start_command.instructions.append(object_start_instruction)
            start_modes = self._process_multicolor_command(object_start_command, rgb)
            rgb["start"] = deepcopy(rgb["actual"])

        slices_length = len(slices) - (1 if flags["skipfirst"] else 0)
        auto_length = slices_length
        auto_count = 0
        span_decrement = 0
        list_repeats = []
        for match_repeat in re.finditer(r"repeat\((?P<value>\d+|auto)\)", sequence):
            start, stop = match_repeat.span()
            if match_repeat["value"] == "auto":
                auto_count += 1
                list_repeats.append("auto")
            else:
                value = int(repeat["value"])
                if value < auto_length:
                    value = auto_length
                auto_length -= value
                list_repeats.append(value)
            start -= span_decrement
            stop -= span_decrement
            sequence = f"{sequence[:start]}{'{}'}{sequence[stop:]}"
            span_decrement += len(match_repeat.group()) - len(r"{}")
        for index, repeat in enumerate(list_repeats):
            if repeat == "auto":
                value = -(auto_length // -auto_count)
                auto_length -= value
                auto_count -= 1
                list_repeats[index] = value
        sequence = sequence.format(*(f"repeat({value})" for value in list_repeats))

        commands: list[MulticolorCommand] = []
        for command in map(str.strip, sequence.split("#")):
            match_command = re.search(Regex.MULTICOLOR_COMMAND, command)
            object_command = MulticolorCommand(None, **match_command.groupdict())
            for instruction in map(str.strip, command.split("|")):
                match_instruction = re.match(Regex.MULTICOLOR_INSTRUCTION, instruction)
                if match_instruction:
                    object_instruction = MulticolorInstruction(
                        rgb["actual"], **match_instruction.groupdict(), repeat=object_command.repeat
                    )
                    object_command.instructions.append(object_instruction)
            for no in range(object_command.repeat):
                commands.append(deepcopy(object_command))
                self._process_multicolor_command(object_command, rgb)

        rgb["actual"] = deepcopy(rgb["start"])

        if flags["mirror"] and len(commands) > 1:
            mirrored_commands: list[MulticolorCommand] = []
            for command in reversed(commands):
                mirrored_commands.append(MulticolorCommand(None, command.reset, command.repeat))
                for instruction in command.instructions:
                    copied_instruction = copy(instruction)
                    if copied_instruction.operator == "+":
                        copied_instruction.operator = "-"
                    elif copied_instruction.operator == "-":
                        copied_instruction.operator = "+"
                    mirrored_commands[-1].instructions.append(copied_instruction)
            commands.extend(mirrored_commands)
        elif flags["reverse"]:
            if flags["cycle"] and len(commands) < slices_length:
                for command in cycle(commands):
                    if len(commands) == slices_length:
                        break
                    copied_command = deepcopy(command)
                    for instruction in copied_command.instructions:
                        instruction.process_value(instruction.value, save=True)
                    commands.append(copied_command)
            for command in commands:
                self._process_multicolor_command(command, rgb)
                for instruction in command.instructions:
                    if instruction.operator == "+":
                        instruction.operator = "-"
                    elif instruction.operator == "-":
                        instruction.operator = "+"
            commands.reverse()
        if flags["cycle"] and not flags["reverse"]:
            if len(commands) < slices_length:
                for command in cycle(commands):
                    if len(commands) == slices_length:
                        break
                    copied_command = deepcopy(command)
                    for instruction in copied_command.instructions:
                        instruction.process_value(instruction.value, save=True)
                    commands.append(copied_command)

        if flags["skipfirst"]:
            if slices[0] and isinstance(slices[0], Sequence) and isinstance(slices[0][0], (Sequence, slice)):
                self._apply_multicolor_command(rgb["actual"], start_modes, *slices[0])
            else:
                self._apply_multicolor_command(rgb["actual"], start_modes, slices[0])
            slices = slices[1:]
        
        for obj, command in zip(slices, commands):
            if obj and isinstance(obj, Sequence) and isinstance(obj[0], (Sequence, slice)):
                self._process_multicolor_command(command, rgb, *obj)
            else:
                self._process_multicolor_command(command, rgb, obj)

        return self
    
    def multicolor_c(self,
                     sequence: str,
                     *coordinates: tuple[int, int]) -> Self:
        def transform(coordinates):
            for obj in coordinates:
                if isinstance(obj, tuple) and isinstance(obj[0], tuple):
                    yield tuple(self._coord_to_slice(coord) for coord in obj)
                else:
                    yield self._coord_to_slice(obj)
        if not coordinates:
            coordinates = self._get_all_coords()
        return self.multicolor(sequence, *transform(coordinates))

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
