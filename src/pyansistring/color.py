__all__ = ["Color", "ColorScale", "ColorMap", "SegmentedColorMap"]

from bisect import bisect_left as _bisect_left
from collections.abc import Sequence as _Sequence
from colorsys import hls_to_rgb as _hls_to_rgb, rgb_to_hls as _rgb_to_hls
from math import trunc as _trunc
from typing import Any as _Any, Literal as _Literal, Mapping as _Mapping

from ._frozen import FrozenMeta as _FrozenMeta
from ._helpers import clamp as _clamp
from .config import config as _config
from .constants import (
    COLOR_THEMES,
    COLORS_256,
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
    depth : Literal["4bit", "8bit", "24bit"] | None, default None
        The color bit depth or ``None`` for unset.
    value : Foreground | Background | Underline | int \
            | tuple[int, int, int] | None, default None
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
        depth: _Literal["4bit", "8bit", "24bit"] | None = None,
        value: Foreground
        | Background
        | Underline
        | tuple[int, int, int]
        | int
        | None = None,
    ) -> None:
        if depth is None and value is None:
            self.depth = None
            self.value = None
            return

        if isinstance(value, (Foreground, Background, Underline)):
            value = value.value

        if depth == "24bit" and isinstance(value, tuple) and len(value) == 3:
            self.depth = depth
            self.value = value
        elif depth == "8bit" and isinstance(value, int):
            self.depth = depth
            self.value = value
        elif depth == "4bit" and isinstance(value, int):
            self.depth = depth
            self.value = value
        else:
            raise ValueError(
                f"Invalid Color state: depth '{depth}' "
                f"cannot be paired with value {value!r}. "
                "Please use Color.from_24bit(), Color.from_8bit(), etc."
            )

    def __iter__(self):
        for channel in self.to_rgb():
            yield channel

    def __getitem__(self, key: int) -> int:
        return self.to_rgb()[key]

    def __bool__(self) -> bool:
        return True if (self.depth and self.value) else False

    def __repr__(self) -> str:
        return f"Color(depth={self.depth!r}, value={self.value!r})"

    def __hash__(self) -> int:
        return hash((self.depth, self.value))

    def __eq__(self, other: _Any) -> bool:
        if not isinstance(other, Color):
            return NotImplemented
        return (self.depth, self.value) == (other.depth, other.value)

    @classmethod
    def unset(cls) -> "Color":
        """Create an unset Color instance."""
        return cls(None, None)

    @classmethod
    def from_4bit(cls, color: Foreground | Background | Underline) -> "Color":
        """Create a 4-bit Color."""
        return cls("4bit", color.value)

    @classmethod
    def from_8bit(cls, n: int) -> "Color":
        """Create an 8-bit Color from a 256-color palette index."""
        return cls("8bit", n)

    @classmethod
    def from_24bit(cls, r: int, g: int, b: int) -> "Color":
        """Create a 24-bit TrueColor."""
        return cls("24bit", (r, g, b))

    @classmethod
    def from_hex(cls, hex_str: str) -> "Color":
        """Create a 24-bit Color from a hex string (e.g., '#FF0000' or 'F00')."""
        hex_str = hex_str.lstrip("#").strip()

        # Elegant 3-character expansion
        if len(hex_str) == 3:
            hex_str = "".join(char * 2 for char in hex_str)

        if len(hex_str) != 6:
            raise ValueError(f"Invalid hex color format: '{hex_str}'")

        return cls(
            "24bit",
            (int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)),
        )

    def to_sgr_param(
        self,
        prefix: _Literal[Foreground.SET, Background.SET, Underline.SET] | str = "",
        format_mode: _Literal["standard", "compatible"] | None = None,
    ) -> str:
        """Generate an SGR parameter string for this color.

        Parameters
        ----------
        prefix : Foreground.SET | Background.SET | Underline.SET | str, default ""
            SGR prefix code that qualifies this color (e.g., 38 for foreground).
        format_mode : Literal["standard", "compatible"] | None, default None
            Separator style: ``"standard"`` uses colons, ``"compatible"``
            uses semicolons. Defaults to global config.

        Returns
        -------
        str
            SGR parameter string.
        """
        mode = format_mode or _config.format_mode

        if mode == "standard" or prefix == Underline.SET:
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
            return COLORS_256[self.value]
        elif self.depth == "4bit":
            assert isinstance(self.value, int)
            return COLOR_THEMES[theme][self.value]

        return (0, 0, 0)

    @staticmethod
    def rgb_to_hsl(r: int, g: int, b: int) -> tuple[float, float, float]:
        """Convert an RGB value to HSL."""
        h, l, s = _rgb_to_hls(r / 255, g / 255, b / 255)  # noqa: E741
        return h, s, l

    def to_hsl(
        self,
        theme: ThemeName = DEFAULT_THEME,
    ) -> tuple[float, float, float]:
        """Return the HSL tuple for this color based on the theme."""
        r, g, b = self.to_rgb(theme)
        h, l, s = _rgb_to_hls(r / 255, g / 255, b / 255)  # noqa: E741
        return h, s, l


class ColorScale:
    """Color interpolation scale for gradients.

    Parameters
    ----------
    colors : Sequence[Color | tuple[int, int, int]]
        The colors to interpolate between.
    space : Literal["rgb", "hsl"]
        The color space to use for interpolation.
    """

    __slots__ = ("colors", "space", "_rgb_stops", "_hsl_stops")

    def __init__(
        self,
        colors: _Sequence[Color | tuple[int, int, int]],
        space: _Literal["rgb", "hsl"],
    ) -> None:
        self.colors = list(colors)
        self.space = space
        self._rgb_stops = tuple(
            color.to_rgb() if isinstance(color, Color) else color
            for color in self.colors
        )
        self._hsl_stops: tuple[tuple[float, float, float], ...] = (
            tuple(Color.rgb_to_hsl(r, g, b) for r, g, b in self._rgb_stops)
            if space == "hsl"
            else ()
        )

    def __repr__(self) -> str:
        return f"ColorScale(colors={self.colors!r}, space={self.space!r})"

    def _ensure_hsl_stops(self) -> tuple[tuple[float, float, float], ...]:
        if not self._hsl_stops and self._rgb_stops:
            self._hsl_stops = tuple(
                Color.rgb_to_hsl(r, g, b) for r, g, b in self._rgb_stops
            )
        return self._hsl_stops

    def interpolate_rgb(self, t: float) -> tuple[int, int, int]:
        """Interpolate an RGB tuple at position t in [0.0, 1.0]."""

        if not self._rgb_stops:
            return (0, 0, 0)
        if self.space not in {"rgb", "hsl"}:
            raise ValueError(f"Unsupported color space: {self.space}")
        t = _clamp(t, 0.0, 1.0)

        n = len(self._rgb_stops)
        segments = n - 1
        t_scaled = t * segments
        left_index = _trunc(t_scaled)

        if left_index >= segments:
            return self._rgb_stops[-1]

        t_local = t_scaled - left_index

        if self.space == "rgb":
            r1, g1, b1 = self._rgb_stops[left_index]
            r2, g2, b2 = self._rgb_stops[left_index + 1]
            r = round(r1 + (r2 - r1) * t_local)
            g = round(g1 + (g2 - g1) * t_local)
            b = round(b1 + (b2 - b1) * t_local)
            return (r, g, b)

        hsl_stops = self._ensure_hsl_stops()
        h1, s1, l1 = hsl_stops[left_index]
        h2, s2, l2 = hsl_stops[left_index + 1]

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
        return (round(r * 255), round(g * 255), round(b * 255))

    def interpolate(self, t: float) -> Color:
        """Interpolate a color at position t in [0.0, 1.0]."""
        if not self._rgb_stops:
            return Color.unset()
        return Color.from_24bit(*self.interpolate_rgb(t))


class ColorMap:
    """Color mapping for continuous data values.

    Parameters
    ----------
    scale : ColorScale
        The color scale used for interpolation.
    vmin : int | float
        The minimum data value (maps to the start of the scale).
    vmax : int | float
        The maximum data value (maps to the end of the scale).
    under_color : Color | tuple[int, int, int] | None, default None
        Color to use for values strictly less than vmin.
    over_color : Color | tuple[int, int, int] | None, default None
        Color to use for values strictly greater than vmax.
    """

    __slots__ = ("scale", "vmin", "vmax", "under_color", "over_color")

    def __init__(
        self,
        scale: ColorScale,
        vmin: int | float,
        vmax: int | float,
        under_color: Color | tuple[int, int, int] | None = None,
        over_color: Color | tuple[int, int, int] | None = None,
    ) -> None:
        self.scale = scale
        self.vmin = vmin
        self.vmax = vmax
        self.under_color = (
            under_color
            if isinstance(under_color, Color)
            else Color.from_24bit(*under_color)
            if under_color
            else None
        )
        self.over_color = (
            over_color
            if isinstance(over_color, Color)
            else Color.from_24bit(*over_color)
            if over_color
            else None
        )

    def __repr__(self) -> str:
        return (
            f"ColorMap(scale={self.scale!r}, vmin={self.vmin!r}, vmax={self.vmax!r}, "
            f"under_color={self.under_color!r}, over_color={self.over_color!r})"
        )

    def __call__(self, value: int | float) -> Color:
        """Map a data value to a Color based on the scale and thresholds."""

        if value < self.vmin and self.under_color:
            return self.under_color
        elif value > self.vmax and self.over_color:
            return self.over_color
        else:
            if self.vmax == self.vmin:
                return self.scale.interpolate(0.5)

            t = _clamp((value - self.vmin) / (self.vmax - self.vmin), 0.0, 1.0)
            return self.scale.interpolate(t)


class SegmentedColorMap:
    """Discrete color mapping for data values based on thresholds.

    Parameters
    ----------
    segments : Mapping[int | float, Color | tuple[int, int, int]]
        A mapping of threshold boundary values to their assigned colors.
    over_color : Color | tuple[int, int, int] | None, default None
        Color to use for values greater than the maximum threshold boundary.
    """

    __slots__ = ("_boundaries", "_colors", "over_color")

    def __init__(
        self,
        segments: _Mapping[int | float, Color | tuple[int, int, int]],
        over_color: Color | tuple[int, int, int] | None = None,
    ) -> None:
        sorted_segments = sorted(segments.items())
        self._boundaries = [threshold for threshold, _ in sorted_segments]
        self._colors = [
            color if isinstance(color, Color) else Color.from_24bit(*color)
            for _, color in sorted_segments
        ]

        self.over_color = (
            over_color
            if isinstance(over_color, Color)
            else Color.from_24bit(*over_color)
            if over_color
            else None
        )

    def __repr__(self) -> str:
        segments = dict(zip(self._boundaries, self._colors))
        if self.over_color:
            return f"SegmentedColorMap({segments!r}, over_color={self.over_color!r})"
        return f"SegmentedColorMap({segments!r})"

    def __call__(self, value: int | float) -> Color:
        """Map a data value to a Color using binary search."""

        idx = _bisect_left(self._boundaries, value)

        if idx < len(self._boundaries):
            return self._colors[idx]

        if self.over_color:
            return self.over_color

        return self._colors[-1]
