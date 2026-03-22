__all__ = ["Color"]

from typing import Any as _Any, Literal as _Literal

from ._frozen import FrozenMeta as _FrozenMeta
from .constants import (
    COLOR_THEMES,
    COLORS_8BIT,
    DEFAULT_THEME,
    Background,
    Foreground,
    ThemeName,
    Underline,
)


class Color(metaclass=_FrozenMeta):
    """Unified color representation.

    Parameters
    ----------
    mode : Literal["4bit", "8bit", "24bit"] | None
        The color mode or ``None`` for unset.
    value : Foreground | Background | Underline | int | tuple[int, int, int] | None
        The color value.

    Attributes
    ----------
    mode : Literal["4bit", "8bit", "24bit"] | None
        The color mode or ``None`` for unset.
    value : int | tuple[int, int, int] | None
        The normalized color value.
    """

    __slots__ = ("mode", "value", "_is_frozen")

    def __init__(
        self,
        mode: str | None = None,
        value: Foreground
        | Background
        | Underline
        | tuple[int, int, int]
        | int
        | None = None,
    ) -> None:
        if mode in {"4bit", "8bit", "24bit"}:
            self.mode = mode
        else:
            self.mode = None
        if isinstance(value, (Foreground, Background, Underline)):
            self.value = value.value
        elif isinstance(value, (int, tuple)):
            self.value = value
        else:
            self.value = None

    def __bool__(self) -> bool:
        return True if (self.mode and self.value) else False

    def __repr__(self) -> str:
        return f"Color(mode={self.mode!r}, value={self.value!r})"

    def __hash__(self) -> int:
        return hash((self.mode, self.value))

    def __eq__(self, other: _Any) -> bool:
        if not isinstance(other, Color):
            return NotImplemented
        return (self.mode, self.value) == (other.mode, other.value)

    @classmethod
    def unset(cls) -> "Color":
        # TODO: Make it a constant?
        return cls(None, None)

    @classmethod
    def from_4bit(cls, color: Foreground | Background | Underline) -> "Color":
        return cls("4bit", color.value)

    @classmethod
    def from_8bit(cls, n: int) -> "Color":
        return cls("8bit", n)

    @classmethod
    def from_24bit(cls, r: int, g: int, b: int) -> "Color":
        return cls("24bit", (r, g, b))

    def to_sgr_param(
        self,
        prefix: _Literal[Foreground.SET, Background.SET, Underline.SET] | str = "",
        format_mode: _Literal["standard", "compatible"] = "standard",
    ) -> str:
        if format_mode == "standard" or prefix == Underline.SET:
            separator = ":"
        else:
            separator = ";"
        if prefix:
            prefix = str(prefix) + separator
        if self.mode == "24bit" and isinstance(self.value, tuple):
            r, g, b = self.value
            sep = separator * 2 if separator == ":" else ";"
            return f"{prefix}2{sep}{r}{separator}{g}{separator}{b}"
        elif self.mode == "8bit" and isinstance(self.value, int):
            return f"{prefix}5{separator}{self.value}"
        elif self.mode == "4bit" and isinstance(self.value, int):
            return f"{self.value}"
        return ""

    def to_rgb(
        self,
        theme: ThemeName = DEFAULT_THEME,
    ) -> tuple[int, int, int]:
        """Return the RGB tuple for this color based on the theme."""
        if self.mode == "24bit":
            assert isinstance(self.value, tuple)
            return self.value
        elif self.mode == "8bit":
            assert isinstance(self.value, int)
            return COLORS_8BIT[self.value]
        elif self.mode == "4bit":
            assert isinstance(self.value, int)
            return COLOR_THEMES[theme][self.value]
        else:
            return (0, 0, 0)
