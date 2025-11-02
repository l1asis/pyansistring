__all__ = [
    "StyleManager",
    "ANSIString",
]

import re
from collections.abc import Generator, Hashable, Sequence, Iterable
from copy import copy, deepcopy
from itertools import cycle
from pathlib import Path
from random import randint
from typing import Annotated, Any, Callable, Literal, Self, overload, Union, SupportsIndex, TYPE_CHECKING

if not TYPE_CHECKING:
    try:
        from fontTools.ttLib import TTFont
        from fontTools.pens.svgPathPen import SVGPathPen
        from fontTools.pens.transformPen import TransformPen
        is_fonttools_available = True
    except Exception:
        is_fonttools_available = False
else:
    from fontTools.ttLib import TTFont
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    is_fonttools_available = True

from .constants import *
from .helpers import *
from .style import Style
from .style_manager import StyleManager

class MulticolorInstruction:
    """Class representing a single instruction in a multicolor command."""
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
            raise TypeError(
                f"{self.__class__}.__init__() missing {len(missing_keys)}"
                f" required keyword argument{'s' if len(missing_keys)>1 else ''}:"
                ", ".join(missing_keys)
            )

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
    """Class representing a multicolor command with multiple instructions."""
    def __init__(
        self,
        instructions: list[MulticolorInstruction] | None = None,
        reset: str | None = None,
        repeat: int | str | None = None,
    ) -> None:
        self.instructions = instructions if instructions else []
        self.reset = reset
        if isinstance(repeat, str):
            self.repeat = int(repeat[7:-1])
        else:
            self.repeat = 1 if repeat is None else repeat


class ANSIString(str):
    r"""
    String class that allows you to extend your vanilla str with ANSI escape sequences for coloring/styling.

    Instance Attributes:
        _styles: dictionary containing pairs of char indices with ANSI escape sequences.
        _styled: plain string to which ANSI e.s. from `_styles` has been applied.

    Properties:
        styles: a getter for `_styles`.
        styled: a getter for `_styled` (checks if `styles` has been modified and renders it if so).
        plain: unformatted, normal string.
        actual_length: returns the length of `styled`.

    Note:
        *The `ANSIString` class is unhashable for consistency, because `styles` is an unhashable dict
        that we can change.
    """
    _style_manager: StyleManager
    _styled_text: str

    def __new__(
        cls,
        plain_text: str = "",
        style_manager: StyleManager | dict[int, Style] | dict[int, str] | None = None
    ) -> Self:
        instance = super().__new__(cls, plain_text)
        if isinstance(style_manager, StyleManager):
            instance._style_manager = style_manager
        elif isinstance(style_manager, dict):
            instance._style_manager = StyleManager(
                {
                    key: Style.from_ansi(value) 
                    if isinstance(value, str) else value 
                    for key, value in style_manager.items()
                }
            )
        else:
            instance._style_manager = StyleManager()
        instance._styled_text = cls._render(instance)
        return instance

    @property
    def style_manager(self) -> StyleManager:
        """Returns the StyleManager instance associated with this ANSIString."""
        return self._style_manager

    @property
    def styled_text(self) -> str:
        """Returns the styled text, applying styles if they have been modified."""
        if self._style_manager.has_been_modified:
            self._styled_text = self._render()
        return self._styled_text

    @property
    def plain_text(self) -> str:
        """Returns the plain text without any styles."""
        return str.__str__(self)

    @property
    def actual_length(self) -> int:
        """Returns the length of the styled text."""
        return len(self.styled_text)

    def __str__(self) -> str:
        """Returns the styled text."""
        return self.styled_text

    def __repr__(self) -> str:
        """Returns a string representation of the ANSIString."""
        return f"ANSIString({str.__repr__(self.plain_text)}, {self.style_manager if self.style_manager else None})"

    def __eq__(self, other: object) -> bool:
        """Checks if the styled text is equal to another string or ANSIString."""
        return self.styled_text == other

    def __add__(self, other: Union[str, "ANSIString"]) -> "ANSIString":
        """Concatenates another string or ANSIString to this ANSIString."""
        style_manager = self.style_manager.copy()
        if isinstance(other, ANSIString):
            style_manager.update({len(self) + index: value for index, value in other.style_manager.items()})
            other = other.plain_text
        return type(self)(self.plain_text + other, style_manager)

    def __radd__(self, other: Union[str, "ANSIString"]) -> "ANSIString":
        """Concatenates this ANSIString to another string or ANSIString."""
        styles = {index + len(other): value for index, value in self.style_manager.items()}
        if isinstance(other, ANSIString):
            styles.update(other.style_manager)
            other = other.plain_text
        return type(self)(other + self.plain_text, styles)

    def __getitem__(self, key: SupportsIndex | slice) -> "ANSIString":
        """Returns a new ANSIString with the specified slice or index."""
        indices = range(len(self))
        selected_indices = indices[key] if isinstance(key, slice) else [indices[key]]
        styles = {
            new_index: self.style_manager[old_index]
            for new_index, old_index in enumerate(selected_indices)
            if old_index in self.style_manager
        }
        return type(self)(super().__getitem__(key), styles)

    def __getattribute__(self, name: str) -> Any:
        """Handles attribute access, allowing for string methods to return ANSIString."""
        # TODO: Replace it with a more elegant solution like explicit overrides or dynamic class decorator.
        allowed_passthrough = {
            "ljust",
            "rjust",
            "center",
            "split",
            "rsplit",
            "join",
            "splitlines",
        }
        if name in dir(str) and name not in allowed_passthrough:
            def method(self: Self, *args: Any, **kwargs: Any) -> Any:
                result = getattr(str, name)(self.plain_text, *args, **kwargs)

                if isinstance(result, str):
                    return type(self)(result, self.style_manager)
                elif isinstance(result, list):
                    return [type(self)(item, self.style_manager) for item in result]  # type: ignore
                elif isinstance(result, tuple):
                    return tuple(type(self)(item, self.style_manager) for item in result)  # type: ignore
                return result

            return method.__get__(self)
        else:
            return super().__getattribute__(name)

    def __format__(self, format_spec: str) -> str:
        """Formats the ANSIString according to the given format specification and returns rendered text."""
        if not format_spec:
            return self.styled_text
        formatted = format(self.plain_text, format_spec)
        styles = self.style_manager.remap_styles(self.plain_text, formatted)
        return str(type(self)(formatted, StyleManager(styles)))

    def _render(self) -> str:
        """Renders the ANSIString to its final output form."""
        return "".join(
            f"{self.style_manager[index].ansi}{char}\x1b[0m" if index in self.style_manager else char
            for index, char in enumerate(self.plain_text)
        )

    def _coord_to_slice(self, coord: tuple[int, int]) -> slice:
        """Converts a (x, y) coordinate pair to a slice object."""
        index = 0
        lengths = tuple(len(line) for line in self.plain_text.splitlines())
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
        return slice(index, index + 1)

    def _get_all_coords(self) -> tuple[tuple[int, int], ...]:
        """Returns all (x, y) coordinates of the characters in the plain text."""
        def transform(lengths: Iterable[int]) -> Generator[tuple[int, int], None, None]:
            for y, length in enumerate(lengths):
                for x in range(length):
                    yield (x, y)
        return tuple(transform(len(line) for line in self.plain_text.splitlines()))

    def _get_indices(
        self, slice_: Annotated[Sequence[int], Length(3)] | slice
    ) -> tuple[int, int, int]:
        """Converts a slice or a sequence of three integers to start, stop, step indices."""
        if isinstance(slice_, slice):
            start, stop, step = slice_.indices(len(self))
        else:
            start, stop, step = slice(*slice_).indices(len(self))
        return start, stop, step

    def _search_spans(
        self, *words: str, case_sensitive: bool = True
    ) -> tuple[tuple[int, int], ...]:
        """Searches for words in the plain text and returns their spans as tuples of (start, end)."""
        flags = 0 if case_sensitive else re.IGNORECASE
        joined_words = "|".join(re.escape(word) for word in words)
        spans = (match.span(0) for match in re.finditer(joined_words, self.plain_text, flags=flags))
        return tuple(spans)

    def _process_multicolor_command(
        self,
        command: MulticolorCommand,
        rgb: dict[str, dict[str, dict[str, int]]],
        *slices: Annotated[Sequence[int], Length(3)] | slice,
    ):
        """Processes a multicolor command and applies it to the ANSIString."""
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

    def _apply_multicolor_command(
        self,
        rgb: dict[str, dict[str, int]],
        modes: dict[str, bool],
        *slices: Annotated[Sequence[int], Length(3)] | slice,
    ) -> None:
        """Applies the current RGB values to the specified slices."""
        if modes["fg"]:
            self.fg_24b(*(int(clamp(rgb["fg"][key], 0, 255)) for key in "rgb"), *slices)
        if modes["bg"]:
            self.bg_24b(*(int(clamp(rgb["bg"][key], 0, 255)) for key in "rgb"), *slices)
        if modes["ul"]:
            self.ul_24b(*(int(clamp(rgb["ul"][key], 0, 255)) for key in "rgb"), *slices)

    @staticmethod
    def from_ansi(plain: str) -> "ANSIString":
        """Creates an ANSIString from a plain string containing ANSI escape sequences."""
        start: int = 0
        decrement: int = 0
        style: str = ""
        styles: dict[int, str] = {}
        sequences: dict[int, str] = {}

        def smart_replacement(match_: re.Match[str]) -> str:
            nonlocal decrement
            sequence, span = match_.group(0), match_.span(0)
            if sequence.endswith("m"):
                if span[0] - decrement in sequences:
                    sequences[span[0] - decrement] += sequence
                else:
                    sequences[span[0] - decrement] = sequence
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

    def fm(
        self, parameter: int | str, *slices: Annotated[Sequence[int], Length(3)] | slice
    ) -> Self:
        """Formats (applies styling to) the string in a specified range."""
        # TODO: forbid formatting above the length of the string
        if parameter == SGR.RESET:
            return self.unfm(*slices)
        style = Style().with_style(parameter)
        if slices:
            for slice_ in slices:
                for index in range(*self._get_indices(slice_)):
                    if index not in self.style_manager:
                        self.style_manager[index] = style
                    else:
                        self.style_manager[index] = self.style_manager[index].merge(style)
        else:
            for index in range(0, len(self), 1):
                if index not in self.style_manager:
                    self.style_manager[index] = style
                else:
                    self.style_manager[index] = self.style_manager[index].merge(style)
        return self

    def fm_w(
        self, parameter: int | str, *words: str, case_sensitive: bool = True
    ) -> Self:
        """Formats (applies styling to) the word of the string."""
        return self.fm(
            parameter, *self._search_spans(*words, case_sensitive=case_sensitive)
        )

    def unfm(self, *slices: Annotated[Sequence[int], Length(3)] | slice) -> Self:
        """Unformats (removes styling) the string in a specified range."""
        if slices:
            for slice_ in slices:
                for index in range(*self._get_indices(slice_)):
                    if index in self.style_manager:
                        del self.style_manager[index]
        else:
            for index in range(0, len(self), 1):
                if index in self.style_manager:
                    del self.style_manager[index]
        return self

    def unfm_w(self, *words: str, case_sensitive: bool = True) -> Self:
        """Unformats (removes styling) the string per word index."""
        return self.unfm(*self._search_spans(*words, case_sensitive=case_sensitive))

    def fg_4b(
        self,
        parameter: Foreground,
        *slices: Annotated[Sequence[int], Length(3)] | slice,
    ) -> Self:
        """Applies the foreground given by the 4-bit color to the string in a specified range."""
        return self.fm(parameter, *slices)

    def fg_4b_w(
        self,
        parameter: Foreground,
        *words: str,
        case_sensitive: bool = True,
    ) -> Self:
        """Applies the foreground given by the 4-bit color to the word of the string."""
        return self.fg_4b(
            parameter, *self._search_spans(*words, case_sensitive=case_sensitive)
        )

    def fg_8b(
        self,
        parameter: Annotated[int, ValueRange(0, 255)],
        *slices: Annotated[Sequence[int], Length(3)] | slice,
    ) -> Self:
        """Applies the foreground given by the 8-bit color number (0-255) to the string in a specified range."""
        style = f"\x1b[{Foreground.SET};5;{parameter}m"
        return self.fm(style, *slices)

    def fg_8b_w(
        self,
        parameter: Annotated[int, ValueRange(0, 255)],
        *words: str,
        case_sensitive: bool = True,
    ) -> Self:
        """Applies the foreground given by the 8-bit color number (0-255) to the word of the string."""
        return self.fg_8b(
            parameter, *self._search_spans(*words, case_sensitive=case_sensitive)
        )

    def fg_24b(
        self,
        r: Annotated[int, ValueRange(0, 255)],
        g: Annotated[int, ValueRange(0, 255)],
        b: Annotated[int, ValueRange(0, 255)],
        *slices: Annotated[Sequence[int], Length(3)] | slice,
    ) -> Self:
        """Applies the foreground given by RGB to the string in a specified range."""
        style = f"\x1b[{Foreground.SET};2;{r};{g};{b}m"
        return self.fm(style, *slices)

    def fg_24b_w(
        self,
        r: Annotated[int, ValueRange(0, 255)],
        g: Annotated[int, ValueRange(0, 255)],
        b: Annotated[int, ValueRange(0, 255)],
        *words: str,
        case_sensitive: bool = True,
    ) -> Self:
        """Applies the foreground given by RGB to the word of the string."""
        return self.fg_24b(
            r, g, b, *self._search_spans(*words, case_sensitive=case_sensitive)
        )

    def bg_4b(
        self,
        parameter: Background,
        *slices: Annotated[Sequence[int], Length(3)] | slice,
    ) -> Self:
        """Applies the background given by the 4-bit color to the string in a specified range."""
        return self.fm(parameter, *slices)

    def bg_4b_w(
        self,
        parameter: Background,
        *words: str,
        case_sensitive: bool = True,
    ) -> Self:
        """Applies the background given by the 4-bit color to the word of the string."""
        return self.bg_4b(
            parameter, *self._search_spans(*words, case_sensitive=case_sensitive)
        )

    def bg_8b(
        self,
        parameter: Annotated[int, ValueRange(0, 255)],
        *slices: Annotated[Sequence[int], Length(3)] | slice,
    ) -> Self:
        """Applies the background given by the 8-bit color number (0-255) to the string in a specified range."""
        style = f"\x1b[{Background.SET};5;{parameter}m"
        return self.fm(style, *slices)

    def bg_8b_w(
        self,
        parameter: Annotated[int, ValueRange(0, 255)],
        *words: str,
        case_sensitive: bool = True,
    ) -> Self:
        """Applies the background given by the 8-bit color number (0-255) to the word of the string."""
        return self.bg_8b(
            parameter, *self._search_spans(*words, case_sensitive=case_sensitive)
        )

    def bg_24b(
        self,
        r: Annotated[int, ValueRange(0, 255)],
        g: Annotated[int, ValueRange(0, 255)],
        b: Annotated[int, ValueRange(0, 255)],
        *slices: Annotated[Sequence[int], Length(3)] | slice,
    ) -> Self:
        """Applies the background given by RGB to the string in a specified range."""
        style = f"\x1b[{Background.SET};2;{r};{g};{b}m"
        return self.fm(style, *slices)

    def bg_24b_w(
        self,
        r: Annotated[int, ValueRange(0, 255)],
        g: Annotated[int, ValueRange(0, 255)],
        b: Annotated[int, ValueRange(0, 255)],
        *words: str,
        case_sensitive: bool = True,
    ) -> Self:
        """Applies the background given by RGB to the word of the string."""
        return self.bg_24b(
            r, g, b, *self._search_spans(*words, case_sensitive=case_sensitive)
        )
    
    def ul_4b(
        self,
        parameter: Underline,
        *slices: Annotated[Sequence[int], Length(3)] | slice,
    ) -> Self:
        """Applies the underline given by the 4-bit color to the string in a specified range."""
        return self.fm(parameter, *slices)

    def ul_4b_w(
        self,
        parameter: Underline,
        *words: str,
        case_sensitive: bool = True,
    ) -> Self:
        """Applies the underline given by the 4-bit color to the word of the string."""
        return self.ul_4b(
            parameter, *self._search_spans(*words, case_sensitive=case_sensitive)
        )

    def ul_8b(
        self,
        parameter: Annotated[int, ValueRange(0, 255)],
        *slices: Annotated[Sequence[int], Length(3)] | slice,
    ) -> Self:
        """Applies the underline given by the 8-bit color number (0-255) to the string in a specified range."""
        style = f"\x1b[{Underline.SET}:5:{parameter}m"
        return self.fm(style, *slices)

    def ul_8b_w(
        self,
        parameter: Annotated[int, ValueRange(0, 255)],
        *words: str,
        case_sensitive: bool = True,
    ) -> Self:
        """Applies the underline given by the 8-bit color number (0-255) to the word of the string."""
        return self.ul_8b(
            parameter, *self._search_spans(*words, case_sensitive=case_sensitive)
        )

    def ul_24b(
        self,
        r: Annotated[int, ValueRange(0, 255)],
        g: Annotated[int, ValueRange(0, 255)],
        b: Annotated[int, ValueRange(0, 255)],
        *slices: Annotated[Sequence[int], Length(3)] | slice,
    ) -> Self:
        """Applies the underline given by RGB to the string in a specified range."""
        style = f"\x1b[{Underline.SET}:2::{r}:{g}:{b}m"
        return self.fm(style, *slices)

    def ul_24b_w(
        self,
        r: Annotated[int, ValueRange(0, 255)],
        g: Annotated[int, ValueRange(0, 255)],
        b: Annotated[int, ValueRange(0, 255)],
        *words: str,
        case_sensitive: bool = True,
    ) -> Self:
        """Applies the underline given by RGB to the word of the string."""
        return self.ul_24b(
            r, g, b, *self._search_spans(*words, case_sensitive=case_sensitive)
        )

    def rainbow(
        self,
        *slices: Annotated[Sequence[int], Length(3)] | slice,
        skip_whitespace: bool = False,
        fg: bool = False,
        bg: bool = False,
        ul: bool = False,
    ) -> Self:
        """Applies a rainbow effect to the string in a specified range."""
        if not slices:
            slices = tuple(
                (index, index + 1)
                for index, char in enumerate(self.plain_text)
                if not (skip_whitespace and char in WHITESPACE)
            )
        if not (fg or bg or ul):
            fg = True
        length = len(slices)
        for index, slice_ in enumerate(slices):
            hue = round(index / length * 360)
            if fg:
                self.fg_24b(*hsl_to_rgb(hue), slice_)
            if bg:
                self.bg_24b(*hsl_to_rgb(hue), slice_)
            if ul:
                self.ul_24b(*hsl_to_rgb(hue), slice_)
        return self

    def multicolor(
        self, sequence: str, *slices: Annotated[Sequence[int], Length(3)] | slice
    ) -> Self:
        """Applies a multicolor sequence to the string in a specified range."""
        if not slices:
            slices = tuple((index, index + 1) for index in range(0, len(self)))

        flags = {flag: 0 for flag in ("skipfirst", "cycle", "reverse", "mirror")}
        char_to_flag = {
            "*": "skipfirst",
            "&": "cycle",
            "@": "reverse",
            "!": "mirror",
        }
        offset = 0
        for char in reversed(sequence):
            if char in char_to_flag:
                flags[char_to_flag[char]] = 1
                offset -= 1
            elif char == " ":
                offset -= 1
            else:
                break
        if offset:
            sequence = sequence[:offset]

        rgb = {
            key: {
                key: {key: 0 for key in ("r", "g", "b")} for key in ("fg", "bg", "ul")
            }
            for key in ("actual", "start")
        }

        if "$" in sequence:
            start_command, sequence = map(str.strip, sequence.split("$"))
            object_start_command = MulticolorCommand()
            for start_instruction in map(str.strip, start_command.split("|")):
                match_start_instruction = re.match(
                    Regex.MULTICOLOR_INSTRUCTION, start_instruction
                )
                object_start_instruction = MulticolorInstruction(
                    rgb["actual"],
                    **match_start_instruction.groupdict(),
                    repeat=object_start_command.repeat,
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
            if object_command.repeat == 0:
                continue
            for instruction in map(str.strip, command.split("|")):
                match_instruction = re.match(Regex.MULTICOLOR_INSTRUCTION, instruction)
                if match_instruction:
                    object_instruction = MulticolorInstruction(
                        rgb["actual"],
                        **match_instruction.groupdict(),
                        repeat=object_command.repeat,
                    )
                    object_command.instructions.append(object_instruction)
            for no in range(object_command.repeat):
                commands.append(deepcopy(object_command))
                self._process_multicolor_command(object_command, rgb)

        rgb["actual"] = deepcopy(rgb["start"])

        if flags["mirror"] and len(commands) > 1:
            mirrored_commands: list[MulticolorCommand] = []
            for command in reversed(commands):
                mirrored_commands.append(
                    MulticolorCommand(None, command.reset, command.repeat)
                )
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
            if (
                slices[0]
                and isinstance(slices[0], Sequence)
                and isinstance(slices[0][0], (Sequence, slice))
            ):
                self._apply_multicolor_command(rgb["actual"], start_modes, *slices[0])
            else:
                self._apply_multicolor_command(rgb["actual"], start_modes, slices[0])
            slices = slices[1:]

        for obj, command in zip(slices, commands):
            if (
                obj
                and isinstance(obj, Sequence)
                and isinstance(obj[0], (Sequence, slice))
            ):
                self._process_multicolor_command(command, rgb, *obj)
            else:
                self._process_multicolor_command(command, rgb, obj)

        return self

    def multicolor_c(self, sequence: str, *coordinates: tuple[int, int]) -> Self:
        """Applies a multicolor sequence to the string at specified (x, y) coordinates."""
        def transform(coordinates):
            for obj in coordinates:
                if isinstance(obj, tuple) and isinstance(obj[0], tuple):
                    yield tuple(self._coord_to_slice(coord) for coord in obj)
                else:
                    yield self._coord_to_slice(obj)

        if not coordinates:
            coordinates = self._get_all_coords()
        return self.multicolor(sequence, *transform(coordinates))

    def to_svg(
        self,
        font: TTFont | Path | str,
        font_size_px: int | float,
        line_height_offset: int | float = 0,
        letter_spacing_offset: int | float = 0,
        padx: tuple[int | float, int | float] = (0, 0),
        pady: tuple[int | float, int | float] = (0, 0),
        transparent_background: bool = True,
        background_color: tuple[int, int, int] = (255, 255, 255),
        convert_text_to_path: bool = False,
        output_file: str | None = None,
    ) -> str:
        """Generates an SVG representation of the ANSIString using the specified font."""
        if not is_fonttools_available:
            raise ImportError(
                "The 'fontTools' package is required to use the 'to_svg' method. "
                "Please install it using 'pip install fonttools'."
            )
        if isinstance(font, (Path, str)):
            font = TTFont(font)

        escape_table = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;",
        }
        underline_style_map = {
            UnderlineMode.SINGLE: "solid",
            UnderlineMode.DOUBLE: "double",
            UnderlineMode.DOTTED: "dotted",
            UnderlineMode.DASHED: "dashed",
            UnderlineMode.CURLY: "wavy",
        }
        lines = self.plain_text.splitlines(keepends=False)
        svg_parts: list[str] = []
        texts: list[str] = []
        paths: list[str] = []
        rects: list[str] = []
        chars: list[str] = []

        font_family = font['name'].getDebugName(1) or "sans-serif"

        cmap = font.getBestCmap()
        glyph_set = font.getGlyphSet()

        units_per_em = font['head'].unitsPerEm
        ascent = font['hhea'].ascent
        descent = font['hhea'].descent
        line_gap = font['hhea'].lineGap

        hmtx = font["hmtx"]

        scale = font_size_px / units_per_em
        
        cell_height = ascent - descent  # or em_height
        line_height = cell_height + line_gap
        line_height_px = (ascent - descent + line_gap) * scale

        total_width = 0
        total_height = (ascent - descent + line_gap) * len(lines) * scale

        charno = 0
        y_cursor = ascent + line_gap / 2
        for lineno, line in enumerate(lines):
            x_cursor = 0
            for char in line:
                escaped_char: str = escape_table.get(char, char)

                glyph_name = cmap.get(ord(char), ".notdef")
                glyph = glyph_set.get(glyph_name, glyph_set[".notdef"])
                advance_width, _ = hmtx[glyph_name]

                if charno in self.style_manager:
                    svg_element_attributes: list[str] = []

                    if self.style_manager[charno].background:
                        rects.append(
                            " "*2
                            + f"<rect "
                            + f"x=\"{x_cursor * scale}\" "
                            + f"y=\"{(y_cursor - ascent - line_gap / 2) * scale}\" "
                            + f"width=\"{advance_width * scale}\" "
                            + f"height=\"{(cell_height + line_gap) * scale}\" "
                            + f"fill=\"rgb{self.style_manager[charno].background.to_rgb()}\""
                            + "/>"
                        )
                    if self.style_manager[charno].foreground:
                        svg_element_attributes.append(
                            f"fill=\"rgb{self.style_manager[charno].foreground.to_rgb()}\""
                        )

                    if not convert_text_to_path:
                        if SGR.BOLD in self.style_manager[charno].attributes:
                            svg_element_attributes.append(
                                "font-weight=\"bold\""
                            )
                        if SGR.ITALIC in self.style_manager[charno].attributes:
                            svg_element_attributes.append(
                                "font-style=\"italic\""
                            )
                        if not self.style_manager[charno].underline[0]:
                            if SGR.UNDERLINE in self.style_manager[charno].attributes:
                                svg_element_attributes.append(
                                    "text-decoration=\"underline auto solid\""
                                )
                            elif SGR.DOUBLE_UNDERLINE in self.style_manager[charno].attributes:
                                svg_element_attributes.append(
                                    "text-decoration=\"underline auto double\""
                                )
                            chars.append(
                                f"<tspan {" ".join(svg_element_attributes)}>"
                                + escaped_char
                                + "</tspan>"
                            )
                        else:
                            chars.append(
                                f"<tspan "
                                + f"fill=\"rgb{self.style_manager[charno].underline[0].to_rgb()}\" "
                                + f"text-decoration=\"underline auto {underline_style_map.get(self.style_manager[charno].underline[1], "solid")}\""
                                + ">"
                                + f"<tspan {" ".join(svg_element_attributes)}>"
                                + escaped_char
                                + ("</tspan>"*2)
                            )
                    else:
                        pen = SVGPathPen(glyph_set)
                        t_pen = TransformPen(pen, (scale, 0, 0, -scale, x_cursor * scale, y_cursor * scale))
                        
                        glyph_set[glyph_name].draw(t_pen)
                        svg_element_attributes.append(
                            f"d=\"{pen.getCommands()}\""
                        ) # FIXME: check for whitespace

                        ... # TODO: bold, italic, underline solution for path

                        paths.append(
                            f"{" "*2}<path {" ".join(svg_element_attributes)}/>"
                        )
                else:
                    if not convert_text_to_path:
                        chars.append(f"<tspan>{escape_table.get(char, char)}</tspan>")
                    else:
                        pen = SVGPathPen(glyph_set)
                        t_pen = TransformPen(pen, (scale, 0, 0, -scale, x_cursor * scale, y_cursor * scale))
                        
                        glyph_set[glyph_name].draw(t_pen)
                        
                        paths.append(
                            f"{" "*2}<path d=\"{pen.getCommands()}\"/>"
                        )

                x_cursor += advance_width
                charno += 1  # string char
            
            if not convert_text_to_path:
                texts.append(
                    f"{" "*4}<tspan x=\"0\" dy=\"{0 if lineno == 0 else line_height_px}\">\n{" "*6}{"".join(chars)}\n{" "*4}</tspan>"
                )
                chars.clear()

            # Move to next line
            if x_cursor * scale > total_width:
                total_width = x_cursor * scale
            y_cursor += line_height
            charno += 1  # newline

        print(total_width, total_height)
        print(paths)

        # Example: building SVG
        svg_parts = [
            # "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>",
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="{total_height}" viewBox="0 0 {total_width} {total_height}">',
            (f'{" "*2}<rect width="100%" height="100%" fill="rgb{background_color}"/>' if not transparent_background else ""),
        ]
        for svg_rect in rects:
            svg_parts.append(svg_rect)
        if not convert_text_to_path:
            svg_parts.append(f'{" "*2}<text x=\"{padx[0]}\" y=\"{pady[0] + (ascent + line_gap / 2) * scale}\" font-family=\"{font_family}\" font-size=\"{font_size_px}\" fill=\"black\" letter-spacing=\"{letter_spacing_offset}\">')
            for svg_text in texts:
                svg_parts.append(svg_text)
            svg_parts.append(f"{" "*2}</text>")
        for svg_path in paths:
            svg_parts.append(svg_path)
        svg_parts.append("</svg>")

        svg_content ="\n".join(svg_parts)

        if output_file:
            with open(output_file, "wt", encoding="utf-8") as file:
                file.write(svg_content)

        return svg_content

    def join(self, iterable: Iterable[str], /) -> "ANSIString":
        styles: dict[int, Style] = {}
        increment = 0
        for i, string in enumerate(iterable):
            increment += len(string)
            if i:
                increment += len(self)
            styles.update(
                {increment + index: style for index, style in self.style_manager.items()}
            )
            if type(string) == ANSIString:
                styles.update(
                    {
                        increment + index - len(string): style
                        for index, style in string.style_manager.items()
                    }
                )
        return type(self)(super().join(iterable), StyleManager(styles))

    def ljust(self, width: SupportsIndex, fillchar: str = " ") -> "ANSIString":
        return self + fillchar * (int(width) - len(self))

    def rjust(self, width: SupportsIndex, fillchar: str = " ") -> "ANSIString":
        return fillchar * (int(width) - len(self)) + self  # type: ignore

    def center(self, width: SupportsIndex, fillchar: str = " ") -> "ANSIString":
        margin = int(width) - len(self)
        left = (margin // 2) + (margin & int(width) & 1)
        return fillchar * left + self + fillchar * (margin - left)  # type: ignore

    def rsplit(self, sep: str | None = None, maxsplit: SupportsIndex = -1) -> list["ANSIString"]:  # type: ignore
        actual = super().rsplit(sep, maxsplit)
        max_index = len(self)
        if not sep:
            whitespace = rsearch_separators(self.plain_text)
            if self.plain_text[-1] in WHITESPACE:
                max_index -= len(next(whitespace, ""))
        for no, string in enumerate(actual[::-1]):
            min_index = max_index - len(string)
            styles = {
                index - min_index: self.style_manager[index]
                for index in range(min_index, max_index)
                if index in self.style_manager
            }
            actual[len(actual) - 1 - no] = type(self)(string, StyleManager(styles))
            max_index -= len(string) + (len(sep) if sep else len(next(whitespace, "")))  # type: ignore
        return actual  # type: ignore

    def split(self, sep: str | None = None, maxsplit: SupportsIndex = -1) -> list["ANSIString"]:  # type: ignore
        actual = super().split(sep, maxsplit)
        min_index = 0
        if not sep:
            whitespace = search_separators(self.plain_text)
            if self.plain_text[0] in WHITESPACE:
                min_index += len(next(whitespace, ""))
        for no, string in enumerate(actual):
            max_index = min_index + len(string)
            styles = {
                index - min_index: self.style_manager[index]
                for index in range(min_index, max_index)
                if index in self.style_manager
            }
            actual[no] = type(self)(string, StyleManager(styles))
            min_index += len(string) + (len(sep) if sep else len(next(whitespace, "")))  # type: ignore
        return actual  # type: ignore

    def splitlines(self, keepends: bool = False) -> list["ANSIString"]:  # type: ignore
        actual = super().splitlines(keepends)
        min_index = 0
        for no, string in enumerate(actual):
            max_index = min_index + len(string)
            styles = {
                index - min_index: self.style_manager[index]
                for index in range(min_index, max_index)
                if index in self.style_manager
            }
            actual[no] = type(self)(string, StyleManager(styles))
            min_index += len(string) + (0 if keepends else 1)
        return actual  # type: ignore
