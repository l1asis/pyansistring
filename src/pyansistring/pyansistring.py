from __future__ import annotations

__all__ = [
    "StyleManager",
    "ANSIString",
]

import re
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Mapping,
    Self,
    SupportsIndex,
    Union,
    cast,
)

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
    FMT,
    MAP_FMT,
    SVG_ESCAPE,
    UNDERLINE_CSS,
    Length,
    ValueRange,
    get_style_key,
    hsl_to_rgb,
    load_font,
    prepare_font_variants,
    remap_format,
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
    get_casefold_expansions,
)
from .style import Style
from .style_manager import StyleManager


class ANSIString(str):
    """Subclass of ``str`` that supports ANSI styling via a :class:`StyleManager`."""

    _style_manager: StyleManager
    _styled_text: str

    # str method names that have explicit overrides and must NOT be
    # auto-delegated by __getattribute__.
    _STR_OVERRIDDEN: frozenset[str] = frozenset(
        {
            # Dunder methods with custom implementations
            "__contains__",
            "__eq__",
            "__format__",
            "__getitem__",
            "__iter__",
            "__mod__",
            "__mul__",
            "__ne__",
            "__reduce__",
            "__reduce_ex__",
            "__getnewargs__",
            "__rmul__",
            # Public methods with custom implementations
            "center",
            "expandtabs",
            "join",
            "ljust",
            "lstrip",
            "partition",
            "removeprefix",
            "removesuffix",
            "replace",
            "rjust",
            "rpartition",
            "rsplit",
            "rstrip",
            "split",
            "splitlines",
            "strip",
            "zfill",
            "encode",
            "casefold",
            "translate",
            "format",
            "format_map",
        }
    )
    _STR_DELEGATED: frozenset[str] = frozenset(dir(str)) - _STR_OVERRIDDEN

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

    def __iter__(self) -> Iterable[Self]:  # type: ignore[override]
        """Iterate over characters, yielding styled ANSIStrings."""
        for index, char in enumerate(self.plain_text):
            style = self.style_manager.get(index)
            yield type(self)(char, {0: style} if style is not None else None)

    def __ne__(self, other: object) -> bool:
        """Check if the styled text is not equal to another string or ANSIString."""
        return self.styled_text != other

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

    def __contains__(self, sub: object) -> bool:  # type: ignore[override]
        """Check if a substring exists in the plain text."""
        return str.__contains__(self, sub)  # type: ignore[arg-type]

    def __mul__(self, value: SupportsIndex) -> "ANSIString":
        """Repeat the ANSIString a specified number of times."""
        n = int(value)
        if n <= 0:
            return type(self)("")
        if n == 1:
            return type(self)(self.plain_text, self.style_manager.copy())
        length = len(self)
        styles: dict[int, Style] = dict(self.style_manager)
        for i in range(1, n):
            offset = length * i
            for index, style in self.style_manager.items():
                styles[index + offset] = style
        return type(self)(self.plain_text * n, StyleManager(styles))

    def __rmul__(self, value: SupportsIndex) -> "ANSIString":
        """Repeat the ANSIString a specified number of times (reflected operand)."""
        return self.__mul__(value)

    def __mod__(self, args: Any) -> "ANSIString":
        """Perform ``%``-formatting, remapping styles to match the output."""
        formatted = str.__mod__(self.plain_text, args)
        plain = self.plain_text
        if not self.style_manager:
            return type(self)(formatted)

        specs = list(Regex.MOD_SPEC.finditer(plain))
        if not specs:
            return type(self)(formatted, self.style_manager.copy())

        result_styles: dict[int, Style] = {}
        is_mapping = isinstance(args, dict)
        args_tuple = cast(tuple[Any, ...], args if isinstance(args, tuple) else (args,))
        arg_idx = 0
        src = 0
        dest = 0

        for spec in specs:
            spec_start, spec_end = spec.span()

            # Copy styles for literal segment before this specifier
            if spec_start > src:
                result_styles.update(
                    self.style_manager.copy_range(src, spec_start, dest)
                )
                dest += spec_start - src

            conv = spec.group(4)
            if conv == "%":
                # %% → single '%'; preserve style from first '%'
                if spec_start in self.style_manager:
                    result_styles[dest] = self.style_manager[spec_start]
                dest += 1
            else:
                # Real specifier: format individually to get output length
                if is_mapping:
                    spec_output = str.__mod__(spec.group(), args)
                else:
                    n_args = 1
                    if spec.group(2) == "*":
                        n_args += 1
                    if spec.group(3) == "*":
                        n_args += 1
                    spec_args = args_tuple[arg_idx : arg_idx + n_args]
                    arg_idx += n_args
                    spec_output = str.__mod__(spec.group(), spec_args)
                dest += len(spec_output)

            src = spec_end

        # Trailing literal segment
        if src < len(plain):
            result_styles.update(self.style_manager.copy_range(src, len(plain), dest))

        return type(self)(formatted, StyleManager(result_styles))

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
        styles = self.style_manager.remap(self.plain_text, formatted)
        return str(type(self)(formatted, StyleManager(styles)))

    def __sizeof__(self) -> int:
        """Return the size of the ANSIString in bytes."""
        return (
            str.__sizeof__(self)
            + self.styled_text.__sizeof__()
            + self.style_manager.__sizeof__()
        )

    def __reduce__(self) -> tuple[Any, tuple[str, dict[int, Style]]]:
        """Return a tuple for pickling the ANSIString."""
        return (ANSIString, (self.plain_text, dict(self.style_manager)))

    def __getnewargs__(self) -> tuple[str, dict[int, Style]]:  # type: ignore[override]
        """Return arguments for creating a new ANSIString during unpickling."""
        return (self.plain_text, dict(self.style_manager))

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
            styles = self.style_manager.copy_range(min_index, max_index, 0)
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
            styles = self.style_manager.copy_range(min_index, max_index, 0)
            actual[no] = type(self)(string, StyleManager(styles))
            min_index += len(string) + (len(sep) if sep else len(next(whitespace, "")))
        return actual

    def splitlines(self, keepends: bool = False) -> list["ANSIString"]:  # type: ignore[override]
        actual: list[Any] = list(super().splitlines(keepends))
        min_index = 0
        for no, string in enumerate(actual):
            max_index = min_index + len(string)
            styles = self.style_manager.copy_range(min_index, max_index, 0)
            actual[no] = type(self)(string, StyleManager(styles))
            min_index += len(string) + (0 if keepends else 1)
        return actual

    def strip(self, chars: str | None = None) -> "ANSIString":
        actual = super().strip(chars)
        if len(actual) == len(self):
            return type(self)(actual, self.style_manager.copy())
        index = len(self.plain_text) - len(super().lstrip(chars))
        styles = self.style_manager.copy_range(index, index + len(actual), 0)
        return type(self)(actual, StyleManager(styles))

    def lstrip(self, chars: str | None = None) -> "ANSIString":
        actual = super().lstrip(chars)
        if len(actual) == len(self):
            return type(self)(actual, self.style_manager.copy())
        index = len(self.plain_text) - len(actual)
        styles = self.style_manager.copy_range(index, index + len(actual), 0)
        return type(self)(actual, StyleManager(styles))

    def rstrip(self, chars: str | None = None) -> "ANSIString":
        actual = super().rstrip(chars)
        if len(actual) == len(self):
            return type(self)(actual, self.style_manager.copy())
        styles = self.style_manager.copy_range(0, len(actual), 0)
        return type(self)(actual, StyleManager(styles))

    def replace(
        self,
        old: str,
        new: str,
        count: SupportsIndex = -1,
    ) -> "ANSIString":
        max_count = int(count)
        plain = self.plain_text
        old_len = len(old)
        new_len = len(new)

        # Special case: empty separator inserts *new* between every char
        if not old_len:
            parts: list[str] = []
            result_styles: dict[int, Style] = {}
            dest = 0
            replacements = 0
            for i, ch in enumerate(plain):
                if max_count < 0 or replacements < max_count:
                    parts.append(new)
                    dest += new_len
                    replacements += 1
                if i in self.style_manager:
                    result_styles[dest] = self.style_manager[i]
                parts.append(ch)
                dest += 1
            if max_count < 0 or replacements < max_count:
                parts.append(new)
            return type(self)("".join(parts), StyleManager(result_styles))

        parts = []
        result_styles: dict[int, Style] = {}
        src = 0
        dest = 0
        replacements = 0
        while src <= len(plain):
            if max_count < 0 or replacements < max_count:
                pos = plain.find(old, src)
            else:
                pos = -1
            if pos == -1:
                result_styles.update(
                    self.style_manager.copy_range(src, len(plain), dest)
                )
                parts.append(plain[src:])
                break
            result_styles.update(self.style_manager.copy_range(src, pos, dest))
            parts.append(plain[src:pos])
            dest += pos - src
            parts.append(new)
            dest += new_len
            src = pos + old_len
            replacements += 1
        return type(self)("".join(parts), StyleManager(result_styles))

    def removeprefix(self, prefix: str, /) -> "ANSIString":
        if self.plain_text.startswith(prefix) and prefix:
            offset = len(prefix)
            return self[offset:]
        return type(self)(self.plain_text, self.style_manager.copy())

    def removesuffix(self, suffix: str, /) -> "ANSIString":
        if self.plain_text.endswith(suffix) and suffix:
            return self[: len(self) - len(suffix)]
        return type(self)(self.plain_text, self.style_manager.copy())

    def partition(self, sep: str, /) -> tuple["ANSIString", "ANSIString", "ANSIString"]:  # type: ignore[override]
        idx = self.plain_text.find(sep)
        if idx == -1:
            return (
                type(self)(self.plain_text, self.style_manager.copy()),
                type(self)(""),
                type(self)(""),
            )
        return (self[:idx], self[idx : idx + len(sep)], self[idx + len(sep) :])

    def rpartition(  # type: ignore[override]
        self,
        sep: str,
        /,
    ) -> tuple["ANSIString", "ANSIString", "ANSIString"]:
        idx = self.plain_text.rfind(sep)
        if idx == -1:
            return (
                type(self)(""),
                type(self)(""),
                type(self)(self.plain_text, self.style_manager.copy()),
            )
        return (self[:idx], self[idx : idx + len(sep)], self[idx + len(sep) :])

    def zfill(self, width: SupportsIndex, /) -> "ANSIString":
        w = int(width)
        plain = self.plain_text
        if len(plain) >= w:
            return type(self)(plain, self.style_manager.copy())
        pad = w - len(plain)
        if plain and plain[0] in ("+", "-"):
            # Sign char stays at position 0 (unstyled in the padding zone)
            sign_style = self.style_manager.get(0)
            new_styles: dict[int, Style] = {}
            if sign_style is not None:
                new_styles[0] = sign_style
            for index, style in self.style_manager.items():
                if index > 0:
                    new_styles[index + pad] = style
            return type(self)(
                plain[0] + "0" * pad + plain[1:], StyleManager(new_styles)
            )
        shifted = {index + pad: style for index, style in self.style_manager.items()}
        return type(self)("0" * pad + plain, StyleManager(shifted))

    def expandtabs(self, tabsize: SupportsIndex = 8) -> "ANSIString":  # type: ignore[override]
        ts = int(tabsize)
        plain = self.plain_text
        parts: list[str] = []
        result_styles: dict[int, Style] = {}
        src = 0
        dest = 0
        col = 0
        while src < len(plain):
            tab_pos = plain.find("\t", src)
            if tab_pos == -1:
                result_styles.update(
                    self.style_manager.copy_range(src, len(plain), dest)
                )
                parts.append(plain[src:])
                break
            # Segment before tab
            if tab_pos > src:
                segment = plain[src:tab_pos]
                result_styles.update(self.style_manager.copy_range(src, tab_pos, dest))
                parts.append(segment)
                last_nl = segment.rfind("\n")
                if last_nl != -1:
                    col = len(segment) - last_nl - 1
                else:
                    col += len(segment)
                dest += len(segment)
            # Expand tab
            spaces = ts - (col % ts) if ts > 0 else 0
            parts.append(" " * spaces)
            dest += spaces
            col += spaces
            src = tab_pos + 1
        return type(self)("".join(parts), StyleManager(result_styles))

    def encode(self, encoding: str = "utf-8", errors: str = "strict") -> bytes:
        return self.styled_text.encode(encoding, errors)

    def casefold(self) -> "ANSIString":
        actual = super().casefold()
        if actual == self.plain_text:
            return type(self)(actual, self.style_manager.copy())
        expansions = get_casefold_expansions()
        styles: dict[int, Style] = {}
        dest = 0
        for src, char in enumerate(self.plain_text):
            folded = expansions.get(char)
            if folded is not None:
                # Expanding char: replicate source style across all output chars
                if src in self.style_manager:
                    style = self.style_manager[src]
                    for j in range(len(folded)):
                        styles[dest + j] = style
                dest += len(folded)
            else:
                if src in self.style_manager:
                    styles[dest] = self.style_manager[src]
                dest += 1
        return type(self)(actual, StyleManager(styles))

    def translate(self, table: Mapping[int, int | str | None]) -> "ANSIString":  # type: ignore[override]
        actual = super().translate(table)
        if actual == self.plain_text:
            return type(self)(actual, self.style_manager.copy())
        styles: dict[int, Style] = {}
        dest = 0
        for src, char in enumerate(self.plain_text):
            mapped = table.get(ord(char))
            if mapped is None and ord(char) in table:
                # Deletion: skip this character entirely
                continue
            if src in self.style_manager:
                style = self.style_manager[src]
                if isinstance(mapped, str):
                    for j in range(len(mapped)):
                        styles[dest + j] = style
                    dest += len(mapped)
                else:
                    styles[dest] = style
                    dest += 1
            else:
                if isinstance(mapped, str):
                    dest += len(mapped)
                else:
                    dest += 1
        return type(self)(actual, StyleManager(styles))

    def format(self, /, *args: Any, **kwargs: Any) -> "ANSIString":
        formatted = str.format(self.plain_text, *args, **kwargs)
        if not self.style_manager:
            return type(self)(formatted)
        styles = remap_format(self.plain_text, self.style_manager, FMT, args, kwargs)
        return type(self)(formatted, StyleManager(styles))

    def format_map(self, mapping: Mapping[str, Any], /) -> "ANSIString":  # type: ignore[override]
        formatted = str.format_map(self.plain_text, mapping)
        if not self.style_manager:
            return type(self)(formatted)
        styles = remap_format(self.plain_text, self.style_manager, MAP_FMT, (), mapping)
        return type(self)(formatted, StyleManager(styles))
