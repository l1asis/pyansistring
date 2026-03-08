from __future__ import annotations

__all__ = [
    "StyleManager",
    "ANSIString",
]

import re
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, Self, SupportsIndex, Union, cast

if not TYPE_CHECKING:
    try:
        from fontTools.ttLib import TTFont

        is_fonttools_available = True
    except Exception:
        is_fonttools_available = False
else:
    from fontTools.ttLib import TTFont  # type: ignore[import]

    is_fonttools_available = True

from ._helpers import (
    SVG_ESCAPE,
    UNDERLINE_CSS,
    Length,
    ValueRange,
    get_style_key,
    hsl_to_rgb,
    load_font,
    prepare_font_variants,
    resolve_skew,
    rsearch_separators,
    search_separators,
    svg_build_underline_elements,
    svg_create_transform_pen,
    svg_resolve_underline,
    svg_weight_stroke_attrs,
    tspan,
)
from .constants import (
    SGR,
    WHITESPACE,
    Background,
    Foreground,
    Regex,
    Underline,
)
from .style import Style
from .style_manager import StyleManager


class ANSIString(str):
    """Subclass of ``str`` that supports ANSI styling via a :class:`StyleManager`."""

    _style_manager: StyleManager
    _styled_text: str

    # str method names to delegate (computed once at class definition time)
    _STR_DELEGATED: frozenset[str] = frozenset(dir(str)) - {
        "ljust",
        "rjust",
        "center",
        "split",
        "rsplit",
        "join",
        "splitlines",
    }

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
        """The :class:`StyleManager` instance associated with this ANSIString."""
        return self._style_manager

    @property
    def styled_text(self) -> str:
        """The styled text, recomputed if styles have been modified."""
        if self._style_manager.has_been_modified:
            self._styled_text = self._render()
        return self._styled_text

    @property
    def plain_text(self) -> str:
        """The plain text without any styles."""
        return str.__str__(self)

    @property
    def actual_length(self) -> int:
        """The length of the styled text."""
        return len(self.styled_text)

    def __str__(self) -> str:
        """Return the styled text."""
        return self.styled_text

    def __repr__(self) -> str:
        """Return a string representation of the ANSIString."""
        return (
            f"ANSIString({str.__repr__(self.plain_text)}, "
            f"{self.style_manager if self.style_manager else None})"
        )

    def __eq__(self, other: object) -> bool:
        """Check if the styled text is equal to another string or ANSIString."""
        return self.styled_text == other

    def __add__(self, other: Union[str, "ANSIString"]) -> "ANSIString":
        """Concatenate another string or ANSIString to this ANSIString."""
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
        """Concatenate this ANSIString to another string or ANSIString."""
        styles = {
            index + len(other): value for index, value in self.style_manager.items()
        }
        if isinstance(other, ANSIString):
            styles.update(other.style_manager)
            other = other.plain_text
        return type(self)(other + self.plain_text, styles)

    def __getitem__(self, key: SupportsIndex | slice) -> "ANSIString":
        """Return a new ANSIString with the specified slice or index."""
        indices = range(len(self))
        selected_indices = indices[key] if isinstance(key, slice) else [indices[key]]
        styles = {
            new_index: self.style_manager[old_index]
            for new_index, old_index in enumerate(selected_indices)
            if old_index in self.style_manager
        }
        return type(self)(super().__getitem__(key), styles)

    def __getattribute__(self, name: str) -> Any:
        """Handle attribute access, delegating str methods to return ANSIString."""
        if name in type(self)._STR_DELEGATED:

            def method(self: Self, *args: Any, **kwargs: Any) -> Any:
                result = getattr(str, name)(self.plain_text, *args, **kwargs)

                if isinstance(result, str):
                    return type(self)(result, self.style_manager)
                elif isinstance(result, list):
                    items = cast(list[str], result)
                    return [type(self)(item, self.style_manager) for item in items]
                elif isinstance(result, tuple):
                    items_t = cast(tuple[str, ...], result)
                    return tuple(
                        type(self)(item, self.style_manager) for item in items_t
                    )
                return result

            return method.__get__(self)
        else:
            return super().__getattribute__(name)

    def __format__(self, format_spec: str) -> str:
        """Format the ANSIString with the given format spec and return rendered text."""
        if not format_spec:
            return self.styled_text
        formatted = format(self.plain_text, format_spec)
        styles = self.style_manager.remap_styles(self.plain_text, formatted)
        return str(type(self)(formatted, StyleManager(styles)))

    def _render(self) -> str:
        """Render the ANSIString to its final output form."""
        sm = self._style_manager
        if not sm:
            return self.plain_text

        plain = self.plain_text
        n = len(plain)
        sorted_keys = sorted(sm)
        parts: list[str] = []

        # Unstyled prefix before first styled index
        run_start = sorted_keys[0]
        if run_start > 0:
            parts.append(plain[:run_start])
        run_ansi = sm[run_start].ansi

        for k in range(1, len(sorted_keys)):
            idx = sorted_keys[k]
            prev_idx = sorted_keys[k - 1]
            if idx == prev_idx + 1 and sm[idx].ansi == run_ansi:
                continue

            # Flush current styled run
            run_end = prev_idx + 1
            parts.append(f"{run_ansi}{plain[run_start:run_end]}\x1b[0m")

            # Unstyled gap
            if idx > run_end:
                parts.append(plain[run_end:idx])

            run_start = idx
            run_ansi = sm[idx].ansi

        # Flush last styled run
        last_end = sorted_keys[-1] + 1
        parts.append(f"{run_ansi}{plain[run_start:last_end]}\x1b[0m")

        # Unstyled suffix
        if last_end < n:
            parts.append(plain[last_end:])

        return "".join(parts)

    def _get_indices(
        self, slice_: Annotated[Sequence[int], Length(3)] | slice
    ) -> tuple[int, int, int]:
        """Convert a slice or sequence of three integers to (start, stop, step)."""
        if isinstance(slice_, slice):
            start, stop, step = slice_.indices(len(self))
        else:
            start, stop, step = slice(*slice_).indices(len(self))
        return start, stop, step

    def _search_spans(
        self, *words: str, case_sensitive: bool = True
    ) -> tuple[tuple[int, int], ...]:
        """Search for words in the plain text and return their (start, end) spans."""
        flags = 0 if case_sensitive else re.IGNORECASE
        joined_words = "|".join(re.escape(word) for word in words)
        spans = (
            match.span(0)
            for match in re.finditer(joined_words, self.plain_text, flags=flags)
        )
        return tuple(spans)

    @staticmethod
    def from_ansi(plain: str) -> "ANSIString":
        """Create an ANSIString from a plain string containing ANSI escape sequences."""
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
        """Format (apply styling to) the string in a specified range."""
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
                        self.style_manager[index] = self.style_manager[index].merge(
                            style
                        )
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
        """Format (apply styling to) matched words of the string."""
        return self.fm(
            parameter, *self._search_spans(*words, case_sensitive=case_sensitive)
        )

    def unfm(self, *slices: Annotated[Sequence[int], Length(3)] | slice) -> Self:
        """Remove styling from the string in a specified range."""
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
        """Remove styling from matched words of the string."""
        return self.unfm(*self._search_spans(*words, case_sensitive=case_sensitive))

    def fg_4b(
        self,
        parameter: Foreground,
        *slices: Annotated[Sequence[int], Length(3)] | slice,
    ) -> Self:
        """Apply a 4-bit foreground color to the string in a specified range."""
        return self.fm(parameter, *slices)

    def fg_4b_w(
        self,
        parameter: Foreground,
        *words: str,
        case_sensitive: bool = True,
    ) -> Self:
        """Apply a 4-bit foreground color to matched words of the string."""
        return self.fg_4b(
            parameter, *self._search_spans(*words, case_sensitive=case_sensitive)
        )

    def fg_8b(
        self,
        parameter: Annotated[int, ValueRange(0, 255)],
        *slices: Annotated[Sequence[int], Length(3)] | slice,
    ) -> Self:
        """Apply an 8-bit foreground color to the string in a specified range."""
        style = f"\x1b[{Foreground.SET};5;{parameter}m"
        return self.fm(style, *slices)

    def fg_8b_w(
        self,
        parameter: Annotated[int, ValueRange(0, 255)],
        *words: str,
        case_sensitive: bool = True,
    ) -> Self:
        """Apply an 8-bit foreground color to matched words of the string."""
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
        """Apply a 24-bit foreground color to the string in a specified range."""
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
        """Apply a 24-bit foreground color to matched words of the string."""
        return self.fg_24b(
            r, g, b, *self._search_spans(*words, case_sensitive=case_sensitive)
        )

    def bg_4b(
        self,
        parameter: Background,
        *slices: Annotated[Sequence[int], Length(3)] | slice,
    ) -> Self:
        """Apply a 4-bit background color to the string in a specified range."""
        return self.fm(parameter, *slices)

    def bg_4b_w(
        self,
        parameter: Background,
        *words: str,
        case_sensitive: bool = True,
    ) -> Self:
        """Apply a 4-bit background color to matched words of the string."""
        return self.bg_4b(
            parameter, *self._search_spans(*words, case_sensitive=case_sensitive)
        )

    def bg_8b(
        self,
        parameter: Annotated[int, ValueRange(0, 255)],
        *slices: Annotated[Sequence[int], Length(3)] | slice,
    ) -> Self:
        """Apply an 8-bit background color to the string in a specified range."""
        style = f"\x1b[{Background.SET};5;{parameter}m"
        return self.fm(style, *slices)

    def bg_8b_w(
        self,
        parameter: Annotated[int, ValueRange(0, 255)],
        *words: str,
        case_sensitive: bool = True,
    ) -> Self:
        """Apply an 8-bit background color to matched words of the string."""
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
        """Apply a 24-bit background color to the string in a specified range."""
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
        """Apply a 24-bit background color to matched words of the string."""
        return self.bg_24b(
            r, g, b, *self._search_spans(*words, case_sensitive=case_sensitive)
        )

    def ul_4b(
        self,
        parameter: Underline,
        *slices: Annotated[Sequence[int], Length(3)] | slice,
    ) -> Self:
        """Apply a 4-bit underline color to the string in a specified range."""
        return self.fm(parameter, *slices)

    def ul_4b_w(
        self,
        parameter: Underline,
        *words: str,
        case_sensitive: bool = True,
    ) -> Self:
        """Apply a 4-bit underline color to matched words of the string."""
        return self.ul_4b(
            parameter, *self._search_spans(*words, case_sensitive=case_sensitive)
        )

    def ul_8b(
        self,
        parameter: Annotated[int, ValueRange(0, 255)],
        *slices: Annotated[Sequence[int], Length(3)] | slice,
    ) -> Self:
        """Apply an 8-bit underline color to the string in a specified range."""
        style = f"\x1b[{Underline.SET}:5:{parameter}m"
        return self.fm(style, *slices)

    def ul_8b_w(
        self,
        parameter: Annotated[int, ValueRange(0, 255)],
        *words: str,
        case_sensitive: bool = True,
    ) -> Self:
        """Apply an 8-bit underline color to matched words of the string."""
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
        """Apply a 24-bit underline color to the string in a specified range."""
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
        """Apply a 24-bit underline color to matched words of the string."""
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
        """Apply a rainbow effect to the string in a specified range."""
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
        """Generate an SVG representation of the ANSIString using the specified font.

        Parameters
        ----------
        font : TTFont | Path | str
            Base font. Variable fonts are also supported.
        font_size_px : int | float
            Font size in pixels.
        line_height_offset : int | float
            Extra vertical spacing between lines (in font units).
        letter_spacing_offset : int | float
            Extra horizontal spacing between characters (in font units).
        weight : int | None
            Faux-bold stroke weight (100-900), used only as a last-resort fallback
            when no dedicated bold font or variable ``wght`` axis is available.
        skew : int | None
            Faux-italic skew angle in degrees, used only as a last-resort fallback
            when no dedicated italic font or variable ``ital``/``slnt`` axis is
            available.
        font_bold : TTFont | Path | str | None
            Font used for :pyattr:`SGR.BOLD` characters (for when *font* is not
            a variable font).
        font_italic : TTFont | Path | str | None
            Font used for :pyattr:`SGR.ITALIC` characters (for when *font* is
            not a variable font).
        font_bold_italic : TTFont | Path | str | None
            Font used for characters that are both bold and italic (for when
            *font* is not a variable font).
        font_thin : TTFont | Path | str | None
            Font used for :pyattr:`SGR.DIM` characters (for when *font* is not
            a variable font).
        transparent_background : bool
            When ``True``, no background rectangle is drawn.
        background_color : tuple[int, int, int]
            RGB tuple used when *transparent_background* is ``False``.
        convert_text_to_path : bool
            When ``True``, glyphs render as ``<path>`` instead of ``<text>``.
        output_file : str | None
            Optional file path to write the SVG output.

        Returns
        -------
        svg_content : str
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
        font_family = cast(str, font["name"].getDebugName(1)) or "sans-serif"  # type: ignore[union-attr]
        units_per_em = cast(int, font["head"].unitsPerEm)  # type: ignore[union-attr]
        ascent = cast(int, font["hhea"].ascent)  # type: ignore[union-attr]
        descent = cast(int, font["hhea"].descent)  # type: ignore[union-attr]
        line_gap = cast(int, font["hhea"].lineGap)  # type: ignore[union-attr]
        underline_pos = cast(int, font["post"].underlinePosition)  # type: ignore[union-attr]
        underline_thickness = cast(int, font["post"].underlineThickness)  # type: ignore[union-attr]
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
                                fill_attrs.append(
                                    'text-decoration="underline auto solid"'
                                )
                            elif SGR.DOUBLE_UNDERLINE in style.attributes:
                                fill_attrs.append(
                                    'text-decoration="underline auto double"'
                                )
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
                    paths.append(f"  <path {' '.join(path_attrs)}/>")

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
            f'viewBox="{-italic_left_overflow} 0 '
            f'{total_width_with_italic} {total_height}">'
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
        strings = list(iterable)
        styles: dict[int, Style] = {}
        pos = 0
        for i, string in enumerate(strings):
            if i:
                styles.update(
                    {pos + index: style for index, style in self.style_manager.items()}
                )
                pos += len(self)
            if type(string) is ANSIString:
                styles.update(
                    {
                        pos + index: style
                        for index, style in string.style_manager.items()
                    }
                )
            pos += len(string)
        return type(self)(super().join(strings), StyleManager(styles))

    def ljust(self, width: SupportsIndex, fillchar: str = " ") -> "ANSIString":
        return self + fillchar * (int(width) - len(self))

    def rjust(self, width: SupportsIndex, fillchar: str = " ") -> "ANSIString":
        return self.__radd__(fillchar * (int(width) - len(self)))

    def center(self, width: SupportsIndex, fillchar: str = " ") -> "ANSIString":
        margin = int(width) - len(self)
        left = (margin // 2) + (margin & int(width) & 1)
        return self.__radd__(fillchar * left) + fillchar * (margin - left)

    def rsplit(  # type: ignore[override]
        self, sep: str | None = None, maxsplit: SupportsIndex = -1
    ) -> list["ANSIString"]:
        actual: list[Any] = list(super().rsplit(sep, maxsplit))
        max_index = len(self)
        whitespace = rsearch_separators(self.plain_text) if not sep else iter(())
        if not sep:
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
            max_index -= len(string) + (len(sep) if sep else len(next(whitespace, "")))
        return actual

    def split(  # type: ignore[override]
        self, sep: str | None = None, maxsplit: SupportsIndex = -1
    ) -> list["ANSIString"]:
        actual: list[Any] = list(super().split(sep, maxsplit))
        min_index = 0
        whitespace = search_separators(self.plain_text) if not sep else iter(())
        if not sep:
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
            min_index += len(string) + (len(sep) if sep else len(next(whitespace, "")))
        return actual

    def splitlines(self, keepends: bool = False) -> list["ANSIString"]:  # type: ignore[override]
        actual: list[Any] = list(super().splitlines(keepends))
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
        return actual
