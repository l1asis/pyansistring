__all__ = ["Color"]

from colorsys import hls_to_rgb as _hls_to_rgb, rgb_to_hls as _rgb_to_hls
from math import trunc as _trunc
from typing import Any as _Any, Literal as _Literal

from ._frozen import FrozenMeta as _FrozenMeta
from ._helpers import clamp as _clamp
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
    depth : Literal["4bit", "8bit", "24bit"] | None
        The color bit depth or ``None`` for unset.
    value : Foreground | Background | Underline | int | tuple[int, int, int] | None
        The color value.

    Attributes
    ----------
    depth : Literal["4bit", "8bit", "24bit"] | None
        The color bit depth or ``None`` for unset.
    value : int | tuple[int, int, int] | None
        The normalized color value.
    """

    __slots__ = ("depth", "value", "_is_frozen")

    def __init__(
        self,
        depth: str | None = None,
        value: Foreground
        | Background
        | Underline
        | tuple[int, int, int]
        | int
        | None = None,
    ) -> None:
        if depth in {"4bit", "8bit", "24bit"}:
            self.depth = depth
        else:
            self.depth = None
        if isinstance(value, (Foreground, Background, Underline)):
            self.value = value.value
        elif isinstance(value, (int, tuple)):
            self.value = value
        else:
            self.value = None

    def __iter__(self):
        for channel in self.to_rgb():
            yield channel

    def __getitem__(self, key: int) -> int:
        return self.to_rgb()[key]

    def __bool__(self) -> bool:
        return True if (self.depth and self.value) else False

    def __repr__(self) -> str:
        return f"Color(mode={self.depth!r}, value={self.value!r})"

    def __hash__(self) -> int:
        return hash((self.depth, self.value))

    def __eq__(self, other: _Any) -> bool:
        if not isinstance(other, Color):
            return NotImplemented
        return (self.depth, self.value) == (other.depth, other.value)

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
        if self.depth == "24bit" and isinstance(self.value, tuple):
            r, g, b = self.value
            sep = separator * 2 if separator == ":" else ";"
            return f"{prefix}2{sep}{r}{separator}{g}{separator}{b}"
        elif self.depth == "8bit" and isinstance(self.value, int):
            return f"{prefix}5{separator}{self.value}"
        elif self.depth == "4bit" and isinstance(self.value, int):
            return f"{self.value}"
        return ""

    def to_rgb(
        self,
        theme: ThemeName = DEFAULT_THEME,
    ) -> tuple[int, int, int]:
        """Return the RGB tuple for this color based on the theme."""
        if self.depth == "24bit":
            assert isinstance(self.value, tuple)
            return self.value
        elif self.depth == "8bit":
            assert isinstance(self.value, int)
            return COLORS_8BIT[self.value]
        elif self.depth == "4bit":
            assert isinstance(self.value, int)
            return COLOR_THEMES[theme][self.value]
        else:
            return (0, 0, 0)

    def to_hsl(
        self,
        theme: ThemeName = DEFAULT_THEME,
    ) -> tuple[float, float, float]:
        """Return the HSL tuple for this color based on the theme."""
        r, g, b = self.to_rgb(theme)
        h, l, s = _rgb_to_hls(r / 255, g / 255, b / 255)  # noqa: E741
        return h, s, l


class ColorScale:
    """Color interpolation scale for gradients."""

    __slots__ = ("colors", "space")

    def __init__(
        self, colors: list[Color | tuple[int, int, int]], space: _Literal["rgb", "hsl"]
    ) -> None:
        self.colors = colors
        self.space = space

    def __repr__(self) -> str:
        return f"ColorScale(colors={self.colors!r}, space={self.space!r})"

    def interpolate(self, t: float) -> Color:
        """Interpolate a color at position t in [0, 1]."""

        if not self.colors:
            return Color.unset()
        if self.space not in {"rgb", "hsl"}:
            raise ValueError(f"Unsupported color space: {self.space}")
        t = _clamp(t, 0.0, 1.0)

        n = len(self.colors)
        segments = n - 1
        t_scaled = t * segments
        left_index = _trunc(t_scaled)

        if left_index >= segments:
            return Color.from_24bit(
                *self.colors[-1].to_rgb()
                if isinstance(self.colors[-1], Color)
                else self.colors[-1]
            )

        t_local = t_scaled - left_index

        c1 = self.colors[left_index]
        c2 = self.colors[left_index + 1]

        if self.space == "rgb":
            r1, g1, b1 = c1.to_rgb() if isinstance(c1, Color) else c1
            r2, g2, b2 = c2.to_rgb() if isinstance(c2, Color) else c2
            r = round(r1 + (r2 - r1) * t_local)
            g = round(g1 + (g2 - g1) * t_local)
            b = round(b1 + (b2 - b1) * t_local)
            return Color.from_24bit(r, g, b)

        elif self.space == "hsl":
            if isinstance(c1, Color):
                h1, s1, l1 = c1.to_hsl()
            else:
                r1, g1, b1 = c1
                h1, l1, s1 = _rgb_to_hls(r1 / 255, g1 / 255, b1 / 255)
            if isinstance(c2, Color):
                h2, s2, l2 = c2.to_hsl()
            else:
                r2, g2, b2 = c2
                h2, l2, s2 = _rgb_to_hls(r2 / 255, g2 / 255, b2 / 255)

            # Interpolate Hue with Shortest-Path Math
            d = h2 - h1
            if d > 0.5:
                d -= 1.0
            elif d < -0.5:
                d += 1.0
            h_out = (h1 + d * t_local) % 1.0

            # Interpolate S and L normally
            s_out = s1 + (s2 - s1) * t_local
            l_out = l1 + (l2 - l1) * t_local

            r, g, b = _hls_to_rgb(h_out, l_out, s_out)
            return Color.from_24bit(round(r * 255), round(g * 255), round(b * 255))

        return Color.unset()
