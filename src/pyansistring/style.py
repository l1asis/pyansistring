__all__ = [
    "Style",
    "StyleManager",
]

import re
from functools import wraps
from typing import Any, Callable, Literal

from ._frozen import FrozenMeta
from .color import Color
from .constants import (
    SGR,
    Background,
    ColorMode,
    Foreground,
    Regex,
    Underline,
    UnderlineMode,
)


def _detect_style_change(
    method: Callable[..., Any],
) -> Callable[..., Any]:
    """Detect changes in the StyleManager and set the modified flag."""

    @wraps(method)
    def wrapped(self: "StyleManager", *args: Any, **kwargs: Any) -> Any:
        previous_length = len(self)
        result = method(self, *args, **kwargs)
        self._update_modified(previous_length)  # type: ignore
        return result

    return wrapped


class Style(metaclass=FrozenMeta):
    """Composite style representation.

    Parameters
    ----------
    foreground : Color | tuple[str, Any]
        The foreground color.
    background : Color | tuple[str, Any]
        The background color.
    underline : tuple[Color | tuple[str, Any], UnderlineMode | int]
        The underline color and mode.
    attributes : frozenset[SGR | int]
        The set of SGR attributes.

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
        "_ansi",
        "_is_frozen",
    )

    def __init__(
        self,
        foreground: Color | tuple[str, Any] = Color(),
        background: Color | tuple[str, Any] = Color(),
        underline: tuple[Color | tuple[str, Any], UnderlineMode | int | None] = (
            Color(),
            UnderlineMode.SINGLE,
        ),
        attributes: frozenset[SGR | int] = frozenset(),
    ) -> None:
        if isinstance(foreground, tuple):
            self.foreground = Color(*foreground)
        else:
            self.foreground = foreground
        if isinstance(background, tuple):
            self.background = Color(*background)
        else:
            self.background = background
        if type(underline[1]) is int and 1 <= underline[1] <= 5:
            underline_mode = UnderlineMode(underline[1])
        elif isinstance(underline[1], UnderlineMode):
            underline_mode = underline[1]
        else:
            underline_mode = UnderlineMode.SINGLE
        if isinstance(underline[0], tuple):
            self.underline = (Color(*underline[0]), underline_mode)
        else:
            self.underline = (underline[0], underline_mode)
        self.attributes = attributes
        self._ansi = self.to_ansi()

    @property
    def ansi(self) -> str:
        return self._ansi

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
        attrs = ", ".join(f"SGR.{SGR(attr).name}" for attr in self.attributes)
        return (
            "Style("
            f"foreground={self.foreground!r}, "
            f"background={self.background!r}, "
            f"underline=({self.underline[0]!r}, "
            f"UnderlineMode.{self.underline[1].name}), "
            f"attributes={{{attrs}}})"
        )

    def __hash__(self) -> int:
        return hash((self.foreground, self.background, self.underline, self.attributes))

    def __eq__(self, other: Any) -> bool:
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
        style: Foreground
        | Background
        | Underline
        | UnderlineMode
        | SGR
        | str
        | int
        | None = None,
        *args: int,
    ) -> "Style":
        """Return a new Style with the given style data applied."""
        fg = self.foreground
        bg = self.background
        ul = self.underline
        attrs = set(self.attributes)

        if isinstance(style, Foreground):
            if style == Foreground.SET:
                if len(args) == 1:
                    fg = Color.from_8bit(args[0])
                elif len(args) == 3:
                    fg = Color.from_24bit(*args)
            else:
                fg = Color.from_4bit(style)
        elif isinstance(style, Background):
            if style == Background.SET:
                if len(args) == 1:
                    bg = Color.from_8bit(args[0])
                elif len(args) == 3:
                    bg = Color.from_24bit(*args)
            else:
                bg = Color.from_4bit(style)
        elif isinstance(style, Underline):
            if style == Underline.SET:
                if len(args) == 1:
                    ul = (Color.from_8bit(args[0]), ul[1])
                elif len(args) == 3:
                    ul = (Color.from_24bit(*args), ul[1])
            else:
                ul = (Color.from_4bit(Underline.DEFAULT), ul[1])
        elif isinstance(style, UnderlineMode):
            ul = (ul[0], style)
        elif isinstance(style, SGR):
            attrs.add(style)
        elif isinstance(style, int):
            if style in SGR:
                attrs.add(SGR(style))
        elif isinstance(style, str):
            return self.from_ansi(style)

        return Style(
            foreground=fg, background=bg, underline=ul, attributes=frozenset(attrs)
        )

    def to_ansi(
        self,
        separate_codes: bool = True,
        format_mode: Literal["standard", "compatible"] = "standard",
    ) -> str:
        parameters: list[str] = []

        if self.foreground:
            parameters.append(self.foreground.to_sgr_param(Foreground.SET, format_mode))
        if self.background:
            parameters.append(self.background.to_sgr_param(Background.SET, format_mode))
        if self.underline[0]:
            underline_mode = f"{SGR.UNDERLINE}:{self.underline[1]}"
            underline_style = (
                f"{self.underline[0].to_sgr_param(Underline.SET, format_mode)}"
            )
            parameters.extend((underline_mode, underline_style))

        for attr in self.attributes:
            # TODO: Should all the SGRs be at the end of the array?
            # if (attr == SGR.UNDERLINE and not self.underline[0]) \
            #     or attr in {SGR.BOLD, SGR.ITALIC}:
            #     parameters.insert(0, f"{attr}")
            # else:
            parameters.append(f"{attr}")

        if separate_codes:
            return "".join(f"\x1b[{parameter}m" for parameter in parameters)
        return f"\x1b[{';'.join(parameters)}m"

    @classmethod
    def from_ansi(cls, ansi: str) -> "Style":
        foreground = Color.unset()
        background = Color.unset()
        underline = (Color.unset(), UnderlineMode.SINGLE)
        attributes: set[SGR] = set()

        sequences: list[str] = re.findall(Regex.ANSI_SEQ, ansi)
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
                Literal[Foreground.SET, Background.SET, Underline.SET, SGR.UNDERLINE]
                | None
            ) = None
            mode: Literal[ColorMode.PALETTE, ColorMode.TRUE_COLOR] | None = None
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
                        if sgr_param == Foreground.SET:
                            style = Foreground.SET
                        elif sgr_param == Background.SET:
                            style = Background.SET
                        elif sgr_param == Underline.SET:
                            style = Underline.SET
                        elif sgr_param == SGR.UNDERLINE:
                            # Set state to expect an underline mode parameter next
                            style = SGR.UNDERLINE
                        elif sgr_param in Foreground:
                            foreground = Color.from_4bit(Foreground(sgr_param))
                        elif sgr_param in Background:
                            background = Color.from_4bit(Background(sgr_param))
                        elif sgr_param == Underline.DEFAULT:
                            underline = (
                                Color.from_4bit(Underline.DEFAULT),
                                underline[1],
                            )
                        elif sgr_param in SGR:
                            attributes.add(SGR(sgr_param))

                    # Check for underline mode or color mode
                    elif not mode:
                        if active_style == SGR.UNDERLINE:
                            # This special case handles codes like "4:1"
                            if 1 <= sgr_param <= 5:
                                underline = (underline[0], UnderlineMode(sgr_param))
                            else:  # Fallback for simple underline
                                attributes.add(SGR.UNDERLINE)
                            style = None
                        elif sgr_param == ColorMode.PALETTE:
                            mode = ColorMode.PALETTE
                        elif sgr_param == ColorMode.TRUE_COLOR:
                            mode = ColorMode.TRUE_COLOR

                    # Process color data now that style and mode are set
                    else:
                        if mode == ColorMode.PALETTE:
                            if active_style == Foreground.SET:
                                foreground = Color.from_8bit(sgr_param)
                            elif active_style == Background.SET:
                                background = Color.from_8bit(sgr_param)
                            elif active_style == Underline.SET:
                                underline = (Color.from_8bit(sgr_param), underline[1])
                            style = mode = None

                        elif mode == ColorMode.TRUE_COLOR:
                            if 0 <= sgr_param <= 255:
                                rgb.append(sgr_param)
                            else:
                                # TODO: Do replace, e.g. clamp(value, 0, 255)?
                                # NOTE: Invalid RGB value, reset
                                style = mode = None
                                rgb.clear()
                                continue

                            if len(rgb) == 3:
                                if active_style == Foreground.SET:
                                    foreground = Color.from_24bit(*rgb)
                                elif active_style == Background.SET:
                                    background = Color.from_24bit(*rgb)
                                elif active_style == Underline.SET:
                                    underline = (Color.from_24bit(*rgb), underline[1])
                                style = mode = None
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
        ul_color = other.underline[0] or self.underline[0]
        if other.underline[0] or other.underline[1] != UnderlineMode.SINGLE:
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
    def fg_4bit(cls, color: Foreground) -> "Style":
        return cls(foreground=Color.from_4bit(color))

    @classmethod
    def bg_4bit(cls, color: Background) -> "Style":
        return cls(background=Color.from_4bit(color))

    @classmethod
    def ul_default(cls, mode: UnderlineMode = UnderlineMode.SINGLE) -> "Style":
        return cls(underline=(Color.from_4bit(Underline.DEFAULT), mode))

    @classmethod
    def fg_8bit(cls, n: int) -> "Style":
        return cls(foreground=Color.from_8bit(n))

    @classmethod
    def bg_8bit(cls, n: int) -> "Style":
        return cls(background=Color.from_8bit(n))

    @classmethod
    def ul_8bit(cls, n: int, mode: UnderlineMode = UnderlineMode.SINGLE) -> "Style":
        return cls(underline=(Color.from_8bit(n), mode))

    @classmethod
    def fg_24bit(cls, r: int, g: int, b: int) -> "Style":
        return cls(foreground=Color.from_24bit(r, g, b))

    @classmethod
    def bg_24bit(cls, r: int, g: int, b: int) -> "Style":
        return cls(background=Color.from_24bit(r, g, b))

    @classmethod
    def ul_24bit(
        cls, r: int, g: int, b: int, mode: UnderlineMode = UnderlineMode.SINGLE
    ) -> "Style":
        return cls(underline=(Color.from_24bit(r, g, b), mode))


class StyleManager(dict[int, Style]):
    """A dict subclass for managing :class:`Style` instances with change tracking.

    Attributes
    ----------
    has_changes : bool
        Modification state of the StyleManager.

    Methods
    -------
    pop_modified() -> bool
        Consume the ``has_changes`` flag and reset it.

    Examples
    --------
    >>> style_manager = StyleManager()
    >>> style_manager[key] = value
    >>> style_manager.pop_modified()
    True
    >>> style_manager.pop_modified()
    False
    """

    _style_cache: dict[int, Style] = {}

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._has_changes = False

    @property
    def has_changes(self) -> bool:
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
        # TODO: it is too verbose, but it is useful for debugging
        return f"StyleManager({super().__repr__()})"

    def __setitem__(self, key: Any, value: Any) -> None:
        """Set a `Style` instance in the dictionary."""
        if not isinstance(value, Style):
            raise TypeError("StyleManager values must be Style instances")
        # NOTE: Cache identical Style objects by their hash
        style_hash = hash(value)
        cached = self._style_cache.get(style_hash)
        if cached is not None and cached == value:
            value = cached
        else:
            self._style_cache[style_hash] = value
        self._has_changes = True
        return super().__setitem__(key, value)

    @_detect_style_change
    def __delitem__(self, key: Any) -> None:
        """Delete a style from the dictionary."""
        return super().__delitem__(key)

    @_detect_style_change  # type: ignore[override]
    def clear(self) -> None:
        return super().clear()

    @_detect_style_change  # type: ignore[override]
    def pop(self, *args: Any) -> Any:
        return super().pop(*args)

    @_detect_style_change  # type: ignore[override]
    def popitem(self) -> tuple[int, Style]:
        return super().popitem()

    @_detect_style_change  # type: ignore[override]
    def setdefault(self, *args: Any, **kwargs: Any) -> Any:
        return super().setdefault(*args, **kwargs)

    @_detect_style_change  # type: ignore[override]
    def update(self, *args: Any, **kwargs: Any) -> None:
        return super().update(*args, **kwargs)

    def copy(self) -> "StyleManager":
        """Create a shallow copy of the StyleManager."""
        copied = StyleManager(dict[Any, Any].copy(self))
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
