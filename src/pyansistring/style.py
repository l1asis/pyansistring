import re
from functools import cached_property
from typing import Any, Literal

from .constants import (
    COLOR_THEMES,
    COLORS_8BIT,
    DEFAULT_THEME,
    SGR,
    Background,
    ColorMode,
    Foreground,
    Regex,
    ThemeName,
    Underline,
    UnderlineMode,
)
from .frozen import FrozenMeta


class Color(metaclass=FrozenMeta):
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

    def __eq__(self, other: Any) -> bool:
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
        prefix: Literal[Foreground.SET, Background.SET, Underline.SET] | str = "",
        format_mode: Literal["standard", "compatible"] = "standard",
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
            return (0, 0, 0)  # Default


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

    @cached_property
    def ansi(self) -> str:
        return self.to_ansi()

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
                ul = (Color.from_4bit(style), ul[1])
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
                        elif sgr_param in Underline:
                            underline = (
                                Color.from_4bit(Underline(sgr_param)),
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
    def ul_4bit(
        cls, color: Underline, mode: UnderlineMode = UnderlineMode.SINGLE
    ) -> "Style":
        return cls(underline=(Color.from_4bit(color), mode))

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


if __name__ == "__main__":
    cases = (
        ("24bit", None),
        (None, 1),
        ("24bit", (10, 20, 30)),
        ("8bit", 255),
        ("4bit", Foreground.BRIGHT_GREEN),
        ("4bit", 92),
    )

    for case in cases:
        color = Color(*case)
        print(color, f"{True if color else False}")
        print(color.to_sgr_param())
        print(color.to_sgr_param(format_mode="compatible"))
        print(color.to_sgr_param(Foreground.SET))
        print(color.to_sgr_param(Background.SET))
        print(color.to_sgr_param(Underline.SET))
        print(color.to_rgb())

    print("\n")

    cases = (
        ((Foreground.BRIGHT_CYAN,),),
        ((Background.BRIGHT_YELLOW,),),
        ((Underline.SET, 255, 0, 0),),
        ((Foreground.BRIGHT_CYAN,), (Background.BRIGHT_YELLOW,)),
        (
            (Foreground.BRIGHT_CYAN,),
            (Background.BRIGHT_YELLOW,),
            (Underline.SET, 255, 0, 0),
        ),
    )

    style = Style()
    for case in cases:
        style = Style()
        for to_apply in case:
            style = style.with_style(*to_apply)
        print(
            f"\t{style.foreground = }\n"
            f"\t{style.background = }\n"
            f"\t{style.underline = }\n"
            f"\t{style.attributes = }"
        )
        print(f"ANSI: {repr(ansi := style.to_ansi())}")
        print(f"{ansi}Hello, World!\x1b[0m")
        print(f"FROM ANSI: {Style.from_ansi(ansi) == style}")

    merged = style.merge(
        Style(
            foreground=Color.from_8bit(165),
            attributes=frozenset({SGR.BOLD, SGR.ITALIC}),
        )
    )
    print(
        f"\tMERGED {merged.foreground = }\n"
        f"\t{merged.background = }\n"
        f"\t{merged.underline = }\n"
        f"\t{merged.attributes = }"
    )
    print(f"ANSI: {repr(ansi := merged.to_ansi())}")
    print(f"{ansi}Hello, World!\x1b[0m")
