__all__ = [
    "Style",
    "StyleManager",
]

import re as _re
from enum import IntEnum as _IntEnum
from functools import wraps as _wraps
from typing import Any as _Any, Callable as _Callable, Literal as _Literal

from ._frozen import FrozenMeta as _FrozenMeta
from .color import Color as _Color
from .config import config as _config
from .constants import (
    SGR as _SGR,
    Background as _Background,
    ColorSupportLevel as _ColorSupportLevel,
    Foreground as _Foreground,
    Regex as _Regex,
    Underline as _Underline,
    UnderlineMode as _UnderlineMode,
)


class _ColorFormat(_IntEnum):
    BIT8 = 5
    BIT24 = 2


def _detect_style_change(
    method: _Callable[..., _Any],
) -> _Callable[..., _Any]:
    """Detect changes in the StyleManager and set the modified flag."""

    @_wraps(method)
    def wrapped(self: "StyleManager", *args: _Any, **kwargs: _Any) -> _Any:
        previous_length = len(self)
        result = method(self, *args, **kwargs)
        self._update_modified(previous_length)  # type: ignore
        return result

    return wrapped


class Style(metaclass=_FrozenMeta):
    """Composite style representation.

    Parameters
    ----------
    foreground : Color | tuple[Literal["4bit", "8bit", "24bit"], Any]
        The foreground color.
    background : Color | tuple[Literal["4bit", "8bit", "24bit"], Any]
        The background color.
    underline : tuple[Color | tuple[Literal["4bit", "8bit", "24bit"], Any], \
            UnderlineMode | int | None]
        The underline color and mode. Defaults to single underline with no color.
    attributes : frozenset[SGR | int]
        The set of SGR attributes (e.g., bold, italic).

    Attributes
    ----------
    foreground : Color
        The foreground color.
    background : Color
        The background color.
    underline : tuple[Color, UnderlineMode]
        The underline color and mode.
    attributes : frozenset[SGR]
        The set of SGR attributes.
    """

    __slots__ = (
        "foreground",
        "background",
        "underline",
        "attributes",
        "_is_frozen",
    )

    def __init__(
        self,
        foreground: _Color | tuple[_Literal["4bit", "8bit", "24bit"], _Any] = _Color(),
        background: _Color | tuple[_Literal["4bit", "8bit", "24bit"], _Any] = _Color(),
        underline: tuple[
            _Color | tuple[_Literal["4bit", "8bit", "24bit"], _Any],
            _UnderlineMode | int | None,
        ] = (
            _Color(),
            _UnderlineMode.SINGLE,
        ),
        attributes: frozenset[_SGR | int] = frozenset(),
    ) -> None:
        if isinstance(foreground, tuple):
            self.foreground = _Color(*foreground)
        else:
            self.foreground = foreground
        if isinstance(background, tuple):
            self.background = _Color(*background)
        else:
            self.background = background
        if type(underline[1]) is int and 1 <= underline[1] <= 5:
            underline_mode = _UnderlineMode(underline[1])
        elif isinstance(underline[1], _UnderlineMode):
            underline_mode = underline[1]
        else:
            underline_mode = _UnderlineMode.SINGLE
        if isinstance(underline[0], tuple):
            self.underline = (_Color(*underline[0]), underline_mode)
        else:
            self.underline = (underline[0], underline_mode)
        self.attributes = attributes

    def __bool__(self) -> bool:
        return (
            True
            if (
                self.foreground
                and self.background
                and self.underline
                and self.attributes
            )
            else False
        )

    def __repr__(self) -> str:
        attrs = ", ".join(f"_SGR.{_SGR(attr).name}" for attr in self.attributes)
        return (
            "Style("
            f"foreground={self.foreground!r}, "
            f"background={self.background!r}, "
            f"underline=({self.underline[0]!r}, "
            f"_UnderlineMode.{self.underline[1].name}), "
            f"attributes={{{attrs}}})"
        )

    def __hash__(self) -> int:
        return hash((self.foreground, self.background, self.underline, self.attributes))

    def __eq__(self, other: _Any) -> bool:
        if not isinstance(other, Style):
            return NotImplemented
        return (self.foreground, self.background, self.underline, self.attributes) == (
            other.foreground,
            other.background,
            other.underline,
            other.attributes,
        )

    def with_style(
        self,
        style: _Foreground
        | _Background
        | _Underline
        | _UnderlineMode
        | _SGR
        | str
        | int
        | None = None,
        *args: int,
    ) -> "Style":
        """Return a new Style with the given style data applied.

        Parameters
        ----------
        style : Foreground | Background | Underline | UnderlineMode \
                | SGR | str | int | None, default None
            Style code or SGR constant to apply. When ``None``, no changes are made.
        *args : int
            Additional color parameters 
            (e.g., palette index or RGB components for 24-bit color).

        Returns
        -------
        Style
            A new Style instance with the given style applied.
        """
        fg = self.foreground
        bg = self.background
        ul = self.underline
        attrs = set(self.attributes)

        if isinstance(style, _Foreground):
            if style == _Foreground.SET:
                if len(args) == 1:
                    fg = _Color.from_8bit(args[0])
                elif len(args) == 3:
                    fg = _Color.from_24bit(*args)
            else:
                fg = _Color.from_4bit(style)
        elif isinstance(style, _Background):
            if style == _Background.SET:
                if len(args) == 1:
                    bg = _Color.from_8bit(args[0])
                elif len(args) == 3:
                    bg = _Color.from_24bit(*args)
            else:
                bg = _Color.from_4bit(style)
        elif isinstance(style, _Underline):
            if style == _Underline.SET:
                if len(args) == 1:
                    ul = (_Color.from_8bit(args[0]), ul[1])
                elif len(args) == 3:
                    ul = (_Color.from_24bit(*args), ul[1])
            else:
                ul = (_Color.from_4bit(_Underline.DEFAULT), ul[1])
        elif isinstance(style, _UnderlineMode):
            ul = (ul[0], style)
        elif isinstance(style, _SGR):
            attrs.add(style)
        elif isinstance(style, int):
            if style in _SGR:
                attrs.add(_SGR(style))
        elif isinstance(style, str):
            return self.from_ansi(style)

        return Style(
            foreground=fg, background=bg, underline=ul, attributes=frozenset(attrs)
        )

    def to_ansi(
        self,
        separate_codes: bool = True,
        separator: _Literal[":", ";"] | None = None,
        color_support: _ColorSupportLevel | None = None,
        downsample: bool | None = None,
    ) -> str:
        """Generate an ANSI escape sequence from this Style.

        Parameters
        ----------
        separate_codes : bool, default True
            When ``True``, emit each ANSI code as a separate escape sequence.
            When ``False``, combine all codes into a single sequence.
        TODO

        Returns
        -------
        str
            An ANSI escape sequence string.
        """
        separator = separator if separator is not None else _config.separator
        color_support = (
            color_support if color_support is not None else _config.color_support
        )
        downsample = downsample if downsample is not None else _config.downsample

        parameters: list[str] = []

        if self.foreground:
            fg_param = self.foreground.to_sgr_param(
                _Foreground.SET, separator, color_support, downsample
            )
            if fg_param:
                parameters.append(fg_param)

        if self.background:
            bg_param = self.background.to_sgr_param(
                _Background.SET, separator, color_support, downsample
            )
            if bg_param:
                parameters.append(bg_param)

        if self.underline[0]:
            ul_param = self.underline[0].to_sgr_param(
                _Underline.SET, separator, color_support, downsample
            )
            if ul_param:
                parameters.extend((f"{_SGR.UNDERLINE}:{self.underline[1]}", ul_param))

        for attr in self.attributes:
            parameters.append(f"{attr}")

        if not parameters:
            return ""

        if separate_codes:
            return "".join(f"\x1b[{parameter}m" for parameter in parameters)
        return f"\x1b[{';'.join(parameters)}m"

    @classmethod
    def from_ansi(cls, ansi: str) -> "Style":
        """Parse a Style from an ANSI escape sequence string.

        Parameters
        ----------
        ansi : str
            An ANSI escape sequence (e.g., ``"\\x1b[1;32m"``).

        Returns
        -------
        Style
            A Style instance with colors and attributes parsed from the sequence.
        """
        foreground = _Color.unset()
        background = _Color.unset()
        underline = (_Color.unset(), _UnderlineMode.SINGLE)
        attributes: set[_SGR] = set()

        sequences: list[str] = _re.findall(_Regex.ANSI_SEQ, ansi)
        for sequence in sequences:
            sequence = (
                sequence.strip()
                .removeprefix("\x1b[")
                .removeprefix("\\e[")
                .removeprefix("\033[")
                .removesuffix("m")
                + ";"  # Add a delimiter to process the last parameter
            )

            parameter: str = ""
            style: (
                _Literal[
                    _Foreground.SET, _Background.SET, _Underline.SET, _SGR.UNDERLINE
                ]
                | None
            ) = None
            color_format: _Literal[_ColorFormat.BIT8, _ColorFormat.BIT24] | None = None
            rgb: list[int] = []

            for char in sequence:
                if char.isdigit():
                    parameter += char
                # Process the parameter when a delimiter is found
                elif parameter:
                    # Use a temporary variable for the check to satisfy Pylance
                    active_style = style
                    sgr_param = int(parameter)

                    if not active_style:
                        if sgr_param == _Foreground.SET:
                            style = _Foreground.SET
                        elif sgr_param == _Background.SET:
                            style = _Background.SET
                        elif sgr_param == _Underline.SET:
                            style = _Underline.SET
                        elif sgr_param == _SGR.UNDERLINE:
                            # Set state to expect an underline mode parameter next
                            style = _SGR.UNDERLINE
                        elif sgr_param in _Foreground:
                            foreground = _Color.from_4bit(_Foreground(sgr_param))
                        elif sgr_param in _Background:
                            background = _Color.from_4bit(_Background(sgr_param))
                        elif sgr_param == _Underline.DEFAULT:
                            underline = (
                                _Color.from_4bit(_Underline.DEFAULT),
                                underline[1],
                            )
                        elif sgr_param in _SGR:
                            attributes.add(_SGR(sgr_param))

                    # Check for underline mode or color format
                    elif not color_format:
                        if active_style == _SGR.UNDERLINE:
                            # This special case handles codes like "4:1"
                            if 1 <= sgr_param <= 5:
                                underline = (underline[0], _UnderlineMode(sgr_param))
                            else:  # Fallback for simple underline
                                attributes.add(_SGR.UNDERLINE)
                            style = None
                        elif sgr_param == _ColorFormat.BIT8:
                            color_format = _ColorFormat.BIT8
                        elif sgr_param == _ColorFormat.BIT24:
                            color_format = _ColorFormat.BIT24

                    # Process color data now that style and color format are set
                    else:
                        if color_format == _ColorFormat.BIT8:
                            if active_style == _Foreground.SET:
                                foreground = _Color.from_8bit(sgr_param)
                            elif active_style == _Background.SET:
                                background = _Color.from_8bit(sgr_param)
                            elif active_style == _Underline.SET:
                                underline = (_Color.from_8bit(sgr_param), underline[1])
                            style = color_format = None

                        elif color_format == _ColorFormat.BIT24:
                            if 0 <= sgr_param <= 255:
                                rgb.append(sgr_param)
                            else:
                                # TODO: Do replace, e.g. clamp(value, 0, 255)?
                                # NOTE: Invalid RGB value, reset
                                style = color_format = None
                                rgb.clear()
                                continue

                            if len(rgb) == 3:
                                if active_style == _Foreground.SET:
                                    foreground = _Color.from_24bit(*rgb)
                                elif active_style == _Background.SET:
                                    background = _Color.from_24bit(*rgb)
                                elif active_style == _Underline.SET:
                                    underline = (_Color.from_24bit(*rgb), underline[1])
                                style = color_format = None
                                rgb.clear()

                    parameter = ""  # Reset for the next parameter
                # If char is a delimiter but parameter is
                # empty (e.g., "::"), do nothing.

        return cls(
            foreground=foreground,
            background=background,
            underline=underline,
            attributes=frozenset(attributes),
        )

    def merge(self, other: "Style") -> "Style":
        """Merge another style into this one, with other taking precedence.

        Parameters
        ----------
        other : Style
            The style to merge in. Non-empty attributes of *other* override
            this style's equivalents.

        Returns
        -------
        Style
            A new Style combining both, with *other* having priority.
        """
        ul_color = other.underline[0] or self.underline[0]
        if other.underline[0] or other.underline[1] != _UnderlineMode.SINGLE:
            ul_mode = other.underline[1]
        else:
            ul_mode = self.underline[1]
        return Style(
            foreground=other.foreground or self.foreground,
            background=other.background or self.background,
            underline=(ul_color, ul_mode),
            attributes=other.attributes | self.attributes,
        )

    @classmethod
    def fg_4bit(cls, color: _Foreground) -> "Style":
        """Create a Style with a 4-bit foreground color."""
        return cls(foreground=_Color.from_4bit(color))

    @classmethod
    def bg_4bit(cls, color: _Background) -> "Style":
        """Create a Style with a 4-bit background color."""
        return cls(background=_Color.from_4bit(color))

    @classmethod
    def ul_default(cls, mode: _UnderlineMode = _UnderlineMode.SINGLE) -> "Style":
        """Create a Style with the default underline color and mode."""
        return cls(underline=(_Color.from_4bit(_Underline.DEFAULT), mode))

    @classmethod
    def fg_8bit(cls, n: int) -> "Style":
        """Create a Style with an 8-bit (256-color palette) foreground color."""
        return cls(foreground=_Color.from_8bit(n))

    @classmethod
    def bg_8bit(cls, n: int) -> "Style":
        """Create a Style with an 8-bit (256-color palette) background color."""
        return cls(background=_Color.from_8bit(n))

    @classmethod
    def ul_8bit(cls, n: int, mode: _UnderlineMode = _UnderlineMode.SINGLE) -> "Style":
        """Create a Style with an 8-bit (256-color palette) underline color."""
        return cls(underline=(_Color.from_8bit(n), mode))

    @classmethod
    def fg_24bit(cls, r: int, g: int, b: int) -> "Style":
        """Create a Style with a 24-bit (true color) foreground color."""
        return cls(foreground=_Color.from_24bit(r, g, b))

    @classmethod
    def bg_24bit(cls, r: int, g: int, b: int) -> "Style":
        """Create a Style with a 24-bit (true color) background color."""
        return cls(background=_Color.from_24bit(r, g, b))

    @classmethod
    def ul_24bit(
        cls, r: int, g: int, b: int, mode: _UnderlineMode = _UnderlineMode.SINGLE
    ) -> "Style":
        """Create a Style with a 24-bit (true color) underline color."""
        return cls(underline=(_Color.from_24bit(r, g, b), mode))


class StyleManager(dict[int, Style]):
    """A dict subclass for managing :class:`Style` instances with change tracking.

    Attributes
    ----------
    has_changes : bool
        Modification state of the StyleManager.
    """

    def __init__(self, *args: _Any, **kwargs: _Any) -> None:
        super().__init__(*args, **kwargs)
        self._has_changes = False

    @property
    def has_changes(self) -> bool:
        """Indicate if the manager has unrendered style modifications."""
        return self._has_changes

    def pop_modified(self) -> bool:
        """Consume the ``has_changes`` flag and reset it."""
        result = self._has_changes
        if self._has_changes:
            self._has_changes = False
        return result

    def _update_modified(self, previous_length: int) -> None:
        """Update the ``has_changes`` flag if the collection length changed."""
        if not self._has_changes and previous_length != len(self):
            self._has_changes = True

    def __repr__(self) -> str:
        """Return a string representation of the StyleManager."""
        return f"StyleManager({super().__repr__()})"

    def __setitem__(self, key: _Any, value: _Any) -> None:
        """Set a Style instance in the dictionary, with caching and change tracking."""
        if not isinstance(value, Style):
            raise TypeError("StyleManager values must be Style instances")
        self._has_changes = True
        return super().__setitem__(key, value)

    @_detect_style_change
    def __delitem__(self, key: _Any) -> None:
        """Delete a style from the dictionary and mark as modified."""
        return super().__delitem__(key)

    @_detect_style_change  # type: ignore[override]
    def clear(self) -> None:
        return super().clear()

    @_detect_style_change  # type: ignore[override]
    def pop(self, *args: _Any) -> _Any:
        return super().pop(*args)

    @_detect_style_change  # type: ignore[override]
    def popitem(self) -> tuple[int, Style]:
        return super().popitem()

    @_detect_style_change  # type: ignore[override]
    def setdefault(self, *args: _Any, **kwargs: _Any) -> _Any:
        return super().setdefault(*args, **kwargs)

    @_detect_style_change  # type: ignore[override]
    def update(self, *args: _Any, **kwargs: _Any) -> None:
        return super().update(*args, **kwargs)

    def copy(self) -> "StyleManager":
        """Create a shallow copy of the StyleManager."""
        copied = StyleManager(dict[_Any, _Any].copy(self))
        copied._has_changes = self._has_changes
        return copied

    def copy_range(
        self, src_start: int, src_end: int, dest_start: int
    ) -> dict[int, Style]:
        """Copy styles from [src_start, src_end) offset to dest_start."""
        offset = dest_start - src_start
        return {i + offset: self[i] for i in range(src_start, src_end) if i in self}

    def remap(
        self, original: str, formatted: str, visible_only: bool = True
    ) -> dict[int, Style]:
        """Remap styles from the original string to the formatted string."""
        if formatted == original:
            return dict(self)

        pad_left = formatted.find(original)
        if pad_left == -1:
            raise ValueError("Original string not found inside formatted string.")

        if visible_only:
            return self.copy_range(0, len(original), pad_left)
        else:
            return self.shift(pad_left)

    def shift(self, offset: int) -> dict[int, Style]:
        """Shift all style indexes by a given offset."""
        return {index + offset: style for index, style in self.items()}

    def shift_in_range(
        self, offset: int, start: int, end: int, step: int = 1
    ) -> dict[int, Style]:
        """Shift styles within a specific range by a given offset."""
        return {
            index + offset: self[index]
            for index in range(start, end, step)
            if index in self
        }

    def reverse(self, length: int) -> dict[int, Style]:
        """Reverse style indexes based on the given length."""
        return {length - index - 1: style for index, style in self.items()}
