from __future__ import annotations

__all__ = [
    "StyleManager",
    "ANSIString",
]

import re
from collections.abc import Generator, Iterable, Sequence
from copy import copy, deepcopy
from itertools import cycle
from pathlib import Path
from random import randint
from typing import TYPE_CHECKING, Annotated, Any, Self, SupportsIndex, Union

if not TYPE_CHECKING:
    try:
        from fontTools.pens.svgPathPen import SVGPathPen
        from fontTools.pens.transformPen import TransformPen
        from fontTools.ttLib import TTFont

        is_fonttools_available = True
    except Exception:
        is_fonttools_available = False
else:
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.ttLib import TTFont

    is_fonttools_available = True

from ._helpers import *
from .constants import *
from .style import Style
from .style_manager import StyleManager


class MulticolorInstruction:
    """
    Represents a single instruction in a multicolor command, which defines how
    to modify a specific color channel (foreground, background, or underline)
    based on an operator and value.

    Parameters
    ----------
    color: str
        The color channel to modify ("r", "g", or "b").
    operator: str
        The operator to apply ("=", "+", or "-").
    value: str
        The value to use for the operation, which can be a number, a random range, or a reference to another color channel.
    processed_value: int | float
        The processed numeric value after evaluating the `value` string, which is used for calculations in
        the multicolor command.
    mode: str
        The mode of the color channel ("fg" for foreground, "bg" for background, or "ul" for underline).
    minmax: tuple[float, float] | str | None
        The minimum and maximum values for the color channel, which can be a tuple, a string in the format "minmax(min, max)", or None for default (0, 255).
    repeat: int
        The number of times to repeat this instruction, which is used for distributing changes across multiple slices in a multicolor command.
    """

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
    """
    Represents a multicolor command consisting of multiple instructions and optional reset and repeat parameters.

    Parameters
    ----------
    instructions: list[MulticolorInstruction] | None
        List of instructions to be applied in this command.
    reset: str | None
        Reset mode for the command. Can be "?" to reset to the current RGB values at
        the time of command execution, "??" to reset to the RGB values at the time of command creation, or None for no reset.
    repeat: int | str | None
        Number of times to repeat the command. Can be an integer or "auto" for automatic distribution across slices.
    """

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
    """Subclass of `str` that supports ANSI styling through an associated :class:`StyleManager`."""

    _style_manager: StyleManager
    _styled_text: str

    def __new__(
        cls,
        plain_text: str = "",
        style_manager: StyleManager | dict[int, Style] | dict[int, str] | None = None,
    ) -> Self:
        instance = super().__new__(cls, plain_text)
        if isinstance(style_manager, StyleManager):
            instance._style_manager = style_manager
        elif isinstance(style_manager, dict):
            instance._style_manager = StyleManager(
                {
                    key: Style.from_ansi(value) if isinstance(value, str) else value
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
            style_manager.update(
                {
                    len(self) + index: value
                    for index, value in other.style_manager.items()
                }
            )
            other = other.plain_text
        return type(self)(self.plain_text + other, style_manager)

    def __radd__(self, other: Union[str, "ANSIString"]) -> "ANSIString":
        """Concatenates this ANSIString to another string or ANSIString."""
        styles = {
            index + len(other): value for index, value in self.style_manager.items()
        }
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
            (
                f"{self.style_manager[index].ansi}{char}\x1b[0m"
                if index in self.style_manager
                else char
            )
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
        spans = (
            match.span(0)
            for match in re.finditer(joined_words, self.plain_text, flags=flags)
        )
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
                rgb["actual"][instruction.mode][
                    instruction.color
                ] = instruction.processed_value
            elif instruction.operator == "+":
                rgb["actual"][instruction.mode][
                    instruction.color
                ] += instruction.processed_value
            elif instruction.operator == "-":
                rgb["actual"][instruction.mode][
                    instruction.color
                ] -= instruction.processed_value

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
        font_bold: TTFont | Path | str | None = None,
        font_italic: TTFont | Path | str | None = None,
        font_bold_italic: TTFont | Path | str | None = None,
        font_thin: TTFont | Path | str | None = None,
        line_height_offset: int | float = 0,
        letter_spacing_offset: int | float = 0,
        weight: int | None = None,
        skew: int | None = None,
        transparent_background: bool = True,
        background_color: tuple[int, int, int] = (255, 255, 255),
        convert_text_to_path: bool = False,
        output_file: str | None = None,
    ) -> str:
        """
        Generates an SVG representation of the ANSIString using the specified font.

        Parameters
        ----------
        font: TTFont | Path | str
            Base font. Variable fonts are also supported.
        font_size_px: int | float
            Font size in pixels.
        line_height_offset: int | float
            Extra vertical spacing between lines (in font units).
        letter_spacing_offset: int | float
            Extra horizontal spacing between characters (in font units).
        weight: int | None
            Faux-bold stroke weight (100-900), used only as a last-resort fallback
            when no dedicated bold font or variable `wght` axis is available.
        skew: int | None
            Faux-italic skew angle in degrees, used only as a last-resort fallback
            when no dedicated italic font or variable `ital`/`slnt` axis is available.
        font_bold: TTFont | Path | str | None
            Font used for :pyattr:`SGR.BOLD` characters.
            (For when `font` is not a variable font).
        font_italic: TTFont | Path | str | None
            Font used for :pyattr:`SGR.ITALIC` characters.
            (For when `font` is not a variable font).
        font_bold_italic: TTFont | Path | str | None
            Font used for characters that are both bold and italic.
            (For when `font` is not a variable font).
        font_thin: TTFont | Path | str | None
            Font used for :pyattr:`SGR.DIM` characters.
            (For when `font` is not a variable font).
        transparent_background: bool
            When `True`, no background rectangle is drawn.
        background_color: tuple[int, int, int]
            RGB tuple used when *transparent_background* is `False`.
        convert_text_to_path: bool
            When `True`, glyphs render as `<path>` instead of `<text>`.
        output_file: str | None
            Optional file path to write the SVG output.

        Returns
        -------
        svg_content: str
            The generated SVG content as a string.
        """
        if not is_fonttools_available:
            raise ImportError(
                "The 'fontTools' package is required to use the 'to_svg' method. "
                "Please install it using 'pip install fonttools'."
            )
        font = load_font(font)

        # Load variation fonts
        loaded_bold = load_font(font_bold) if font_bold is not None else None
        loaded_italic = load_font(font_italic) if font_italic is not None else None
        loaded_bold_italic = (
            load_font(font_bold_italic) if font_bold_italic is not None else None
        )
        loaded_thin = load_font(font_thin) if font_thin is not None else None

        variants = prepare_font_variants(
            font,
            loaded_bold,
            loaded_italic,
            loaded_bold_italic,
            loaded_thin,
        )

        # Font metrics (from the base font)
        font_family = font["name"].getDebugName(1) or "sans-serif"
        units_per_em = font["head"].unitsPerEm
        ascent = font["hhea"].ascent
        descent = font["hhea"].descent
        line_gap = font["hhea"].lineGap
        underline_pos = font["post"].underlinePosition
        underline_thickness = font["post"].underlineThickness
        scale = font_size_px / units_per_em
        line_height = (ascent - descent) + line_gap + line_height_offset
        line_height_px = line_height * scale

        # Faux fallback values (used only when no real variation exists)
        faux_weight = weight if weight is not None else 700

        # Render state
        lines = self.plain_text.splitlines(keepends=False)
        rects: list[str] = []
        paths: list[str] = []
        underlines: list[str] = []
        texts: list[str] = []
        chars: list[str] = []

        total_width = 0.0
        total_height = line_height * len(lines) * scale
        italic_extra_width = 0.0
        italic_left_overflow = 0.0
        underline_max_bottom = 0.0

        # Character loop
        charno = 0
        y_cursor = ascent + line_gap / 2 + line_height_offset / 2

        for lineno, line in enumerate(lines):
            x_cursor = 0
            for char in line:
                escaped = SVG_ESCAPE.get(char, char)
                style = self.style_manager.get(charno)

                # Resolve font variant for this character
                style_key = get_style_key(style)
                variant = variants.get(style_key, variants["regular"])

                glyph_name = variant.cmap.get(ord(char), ".notdef")
                advance_width = variant.glyph_set[glyph_name].width
                x_px = x_cursor * scale
                y_px = y_cursor * scale

                # Background rect
                if style is not None and style.background:
                    bg_y = (
                        y_cursor - ascent - line_gap / 2 - line_height_offset / 2
                    ) * scale
                    rects.append(
                        f'  <rect x="{x_px}" y="{bg_y}" '
                        f'width="{(advance_width + letter_spacing_offset) * scale}" '
                        f'height="{line_height_px}" '
                        f'fill="rgb{style.background.to_rgb()}"/>'
                    )

                # Foreground fill attribute
                fill_attrs: list[str] = []
                if style is not None and style.foreground:
                    fill_attrs.append(f'fill="rgb{style.foreground.to_rgb()}"')

                # Text mode (using <text> and <tspan>)
                if not convert_text_to_path:
                    if style is not None:
                        if SGR.BOLD in style.attributes:
                            fill_attrs.append('font-weight="bold"')
                        if SGR.ITALIC in style.attributes:
                            fill_attrs.append('font-style="italic"')
                        if SGR.DIM in style.attributes:
                            fill_attrs.append('font-weight="lighter"')

                        if style.underline[0]:
                            # Coloured underline: outer tspan carries the decoration
                            if not style.foreground:
                                fill_attrs.append('fill="currentColor"')
                            ul_css = UNDERLINE_CSS.get(style.underline[1], "solid")
                            inner = tspan(escaped, fill_attrs)
                            chars.append(
                                f'<tspan fill="rgb{style.underline[0].to_rgb()}" '
                                f'text-decoration="underline auto {ul_css}">'
                                f"{inner}</tspan>"
                            )
                        else:
                            if SGR.UNDERLINE in style.attributes:
                                fill_attrs.append('text-decoration="underline auto solid"')
                            elif SGR.DOUBLE_UNDERLINE in style.attributes:
                                fill_attrs.append('text-decoration="underline auto double"')
                            chars.append(tspan(escaped, fill_attrs))
                    else:
                        chars.append(f"<tspan>{escaped}</tspan>")

                # Path mode (using <path> and other shapes)
                else:
                    effective_skew = resolve_skew(variant.needs_faux_italic, skew)
                    t_pen, pen, left_ov, right_ov = svg_create_transform_pen(
                        variant.glyph_set,
                        scale,
                        x_px,
                        y_px,
                        ascent,
                        descent,
                        effective_skew,
                    )
                    italic_left_overflow = max(italic_left_overflow, left_ov)
                    italic_extra_width = max(italic_extra_width, right_ov)

                    variant.glyph_set[glyph_name].draw(t_pen)
                    path_attrs = list(fill_attrs)
                    path_attrs.append(f'd="{pen.getCommands()}"')
                    path_attrs.extend(
                        svg_weight_stroke_attrs(
                            style,
                            variant.needs_faux_bold,
                            faux_weight,
                            font_size_px,
                            transparent_background,
                            background_color,
                        )
                    )
                    paths.append(f'  <path {" ".join(path_attrs)}/>')

                    # Underline (path mode only)
                    if style is not None:
                        ul_color, ul_mode = svg_resolve_underline(style)
                        if ul_color and ul_mode is not None:
                            ul_y = (y_cursor - underline_pos) * scale
                            ul_h = max(underline_thickness * scale, 1)
                            ul_w = (advance_width + letter_spacing_offset) * scale
                            new_elems, max_bot = svg_build_underline_elements(
                                ul_color,
                                ul_mode,
                                x_px,
                                ul_y,
                                ul_w,
                                ul_h,
                            )
                            underlines.extend(new_elems)
                            underline_max_bottom = max(underline_max_bottom, max_bot)

                x_cursor += advance_width + letter_spacing_offset
                charno += 1

            # End of line
            if not convert_text_to_path:
                dy = (
                    str(line_height_offset / 2 * scale)
                    if lineno == 0
                    else str(line_height_px)
                )
                texts.append(f'<tspan x="0" dy="{dy}">{"".join(chars)}</tspan>')
                chars.clear()

            total_width = max(total_width, x_cursor * scale)
            total_height = max(total_height, underline_max_bottom)
            y_cursor += line_height
            charno += 1  # newline

        # Assemble SVG
        total_width_with_italic = (
            total_width + italic_extra_width + italic_left_overflow
        )
        svg_parts: list[str] = [
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{total_width_with_italic}" height="{total_height}" '
            f'viewBox="{-italic_left_overflow} 0 {total_width_with_italic} {total_height}">'
            + (
                f'\n  <rect x="{-italic_left_overflow}" width="100%" height="100%" '
                f'fill="rgb{background_color}"/>'
                if not transparent_background
                else ""
            )
        ]
        svg_parts.extend(rects)
        if not convert_text_to_path:
            svg_parts.append(
                f'  <text x="0" y="{(ascent + line_gap / 2) * scale}" '
                f'font-family="{font_family}" font-size="{font_size_px}" '
                f'fill="black" letter-spacing="{letter_spacing_offset * scale}">'
                + "".join(texts)
                + "</text>"
            )
        svg_parts.extend(paths)
        svg_parts.extend(underlines)
        svg_parts.append("</svg>")

        svg_content = "\n".join(svg_parts)

        if output_file:
            with open(output_file, "wt", encoding="utf-8") as f:
                f.write(svg_content)

        return svg_content

    def join(self, iterable: Iterable[str], /) -> "ANSIString":
        styles: dict[int, Style] = {}
        increment = 0
        for i, string in enumerate(iterable):
            increment += len(string)
            if i:
                increment += len(self)
            styles.update(
                {
                    increment + index: style
                    for index, style in self.style_manager.items()
                }
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
