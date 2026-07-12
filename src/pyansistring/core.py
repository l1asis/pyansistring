from __future__ import annotations

__all__ = [
    "StyleManager",
    "ANSIString",
    "SliceSpec",
    "SliceGroup",
    "Coordinate",
    "CoordinateGroup",
]

import re as _re
from collections.abc import (
    Callable as _Callable,
    Iterable as _Iterable,
    Iterator as _Iterator,
    Sequence as _Sequence,
)
from pathlib import Path as _Path
from typing import (
    TYPE_CHECKING,
    Any as _Any,
    Literal as _Literal,
    Mapping as _Mapping,
    Self as _Self,
    SupportsIndex as _SupportsIndex,
    Union as _Union,
    cast as _cast,
)

if not TYPE_CHECKING:
    try:
        from fontTools.ttLib import TTFont as _TTFont

        _IS_FONTTOOLS_AVAILABLE = True
    except Exception:
        _IS_FONTTOOLS_AVAILABLE = False
else:
    from fontTools.ttLib import TTFont as _TTFont  # type: ignore[import]

    _IS_FONTTOOLS_AVAILABLE = True

from ._format import (
    FMT as _FMT,
    MAP_FMT as _MAP_FMT,
    remap_format as _remap_format,
)
from ._helpers import (
    get_grapheme_spans as _get_grapheme_spans,
    hsl_to_rgb as _hsl_to_rgb,
    rsearch_separators as _rsearch_separators,
    search_separators as _search_separators,
)
from ._types import (
    ColorStop,
    Coordinate,
    CoordinateGroup,
    SliceGroup,
    SliceSpec,
    ThemeName,
)
from .config import config
from .targets import Chars, Coords, Pattern, Words

if _IS_FONTTOOLS_AVAILABLE or TYPE_CHECKING:
    from ._svg import (
        SVG_ESCAPE as _SVG_ESCAPE,
        UNDERLINE_CSS as _UNDERLINE_CSS,
        get_style_key as _get_style_key,
        load_font as _load_font,
        prepare_font_variants as _prepare_font_variants,
        resolve_skew as _resolve_skew,
        svg_build_underline_elements as _svg_build_underline_elements,
        svg_create_transform_pen as _svg_create_transform_pen,
        svg_resolve_underline as _svg_resolve_underline,
        svg_weight_stroke_attrs as _svg_weight_stroke_attrs,
        tspan as _tspan,
    )

from .color import Color, ColorMap, ColorScale, SegmentedColorMap
from .constants import (
    CASEFOLD_EXPANSIONS,
    SGR,
    WHITESPACE,
    Background,
    Bit8Index,
    Channel,
    ColorSupportLevel,
    Foreground,
    Regex,
    Underline,
    UnderlineMode,
)
from .style import Style, StyleManager


def _resolve_color(color: _Any, enum_type: type) -> Color:
    """Intelligently infer the color depth based on the input type."""
    if isinstance(color, Color):
        return color
    if isinstance(color, enum_type):
        return Color.from_4bit(color)
    if isinstance(color, int):
        return Color.from_8bit(color)
    if isinstance(color, str):
        return Color.from_hex(color)
    if isinstance(color, tuple) and len(color) == 3:  # type: ignore
        return Color.from_24bit(*color)  # type: ignore

    raise TypeError(f"Invalid color format: {color!r}")


class ANSIString(str):
    """Subclass of ``str`` that supports ANSI styling via a :class:`StyleManager`."""

    __slots__ = (
        "_style_manager",
        "_rendered_cache",
        "_last_config_state",
        "_line_starts",
    )

    _style_manager: StyleManager
    _rendered_cache: dict[tuple[_Literal[":", ";"], ColorSupportLevel, bool], str]
    _last_config_state: (
        tuple[_Literal[":", ";"], ColorSupportLevel, bool, ThemeName] | None
    )
    _line_starts: tuple[int, ...] | None

    # str method names that have explicit overrides and must NOT be
    # auto-delegated by __getattribute__.
    _OVERRIDDEN_STR_METHODS: frozenset[str] = frozenset(
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
    _DELEGATED_STR_METHODS: frozenset[str] = (
        frozenset(dir(str)) - _OVERRIDDEN_STR_METHODS
    )

    def __new__(
        cls,
        plain_text: str = "",
        style_manager: StyleManager | dict[int, Style] | dict[int, str] | None = None,
    ) -> _Self:
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
        instance._rendered_cache = {}
        instance._last_config_state = None
        instance._line_starts = None
        return instance

    @property
    def style_manager(self) -> StyleManager:
        """The :class:`StyleManager` instance associated with this ANSIString."""
        return self._style_manager

    @property
    def styled_text(self) -> str:
        """The fully rendered TrueColor string that respects format mode."""
        return self._get_rendered(config.separator, ColorSupportLevel.BIT24, False)

    @property
    def plain_text(self) -> str:
        """The plain text without any styles."""
        return str.__str__(self)

    @property
    def styled_length(self) -> int:
        """The length including ANSI escape codes."""
        return len(self.styled_text)

    def __str__(self) -> str:
        """Return the styled text."""
        if config.color_support == ColorSupportLevel.NONE:
            return self.plain_text
        return self._get_rendered(
            config.separator, config.color_support, config.downsample
        )

    def __repr__(self) -> str:
        """Return a string representation of the ANSIString."""
        return (
            f"ANSIString({str.__repr__(self.plain_text)}, "
            f"{self.style_manager if self.style_manager else None})"
        )

    def __iter__(self) -> _Iterable[_Self]:  # type: ignore[override]
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

    def __add__(self, other: _Union[str, "ANSIString"]) -> "ANSIString":
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

    def __radd__(self, other: _Union[str, "ANSIString"]) -> "ANSIString":
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

    def __mul__(self, value: _SupportsIndex) -> "ANSIString":
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

    def __rmul__(self, value: _SupportsIndex) -> "ANSIString":
        """Repeat the ANSIString a specified number of times (reflected operand)."""
        return self.__mul__(value)

    def __mod__(self, args: _Any) -> "ANSIString":
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
        args_tuple = _cast(
            tuple[_Any, ...], args if isinstance(args, tuple) else (args,)
        )
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

    def __getitem__(self, key: _SupportsIndex | slice) -> "ANSIString":
        """Return a new ANSIString with the specified slice or index."""
        indices = range(len(self))
        selected_indices = indices[key] if isinstance(key, slice) else [indices[key]]
        styles = {
            new_index: self.style_manager[old_index]
            for new_index, old_index in enumerate(selected_indices)
            if old_index in self.style_manager
        }
        return type(self)(super().__getitem__(key), styles)

    def __getattribute__(self, name: str) -> _Any:
        """Handle attribute access, delegating str methods to return ANSIString."""
        if name in type(self)._DELEGATED_STR_METHODS:

            def method(self: _Self, *args: _Any, **kwargs: _Any) -> _Any:
                result = getattr(str, name)(self.plain_text, *args, **kwargs)

                if isinstance(result, str):
                    return type(self)(result, self.style_manager)
                elif isinstance(result, list):
                    items = _cast(list[str], result)
                    return [type(self)(item, self.style_manager) for item in items]
                elif isinstance(result, tuple):
                    items_t = _cast(tuple[str, ...], result)
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

    def __reduce__(self) -> tuple[_Any, tuple[str, dict[int, Style]]]:
        """Return a tuple for pickling the ANSIString."""
        return (ANSIString, (self.plain_text, dict(self.style_manager)))

    def __getnewargs__(self) -> tuple[str, dict[int, Style]]:  # type: ignore[override]
        """Return arguments for creating a new ANSIString during unpickling."""
        return (self.plain_text, dict(self.style_manager))

    def _get_rendered(
        self,
        separator: _Literal[":", ";"] | None = None,
        color_support: ColorSupportLevel | None = None,
        downsample: bool | None = None,
    ) -> str:
        """Retrieve or calculate the rendered string for a specific render profile."""
        separator = separator if separator is not None else config.separator
        color_support = (
            color_support if color_support is not None else config.color_support
        )
        downsample = downsample if downsample is not None else config.downsample

        current_state = (separator, color_support, downsample, config.theme)

        if (
            self._style_manager.pop_modified()
            or getattr(self, "_last_config_state", None) != current_state
        ):
            self._rendered_cache.clear()
            self._last_config_state = current_state

        cache_key = (separator, color_support, downsample)
        if cache_key not in self._rendered_cache:
            self._rendered_cache[cache_key] = self._render(
                separator, color_support, downsample
            )

        return self._rendered_cache[cache_key]

    def _render(
        self,
        separator: _Literal[":", ";"],
        level: ColorSupportLevel,
        downsample: bool,
    ) -> str:
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

        current_style = sm[run_start]
        run_ansi = current_style.to_ansi(
            separator=separator, color_support=level, downsample=downsample
        )

        for k in range(1, len(sorted_keys)):
            idx = sorted_keys[k]
            prev_idx = sorted_keys[k - 1]
            style = sm[idx]

            if idx == prev_idx + 1:
                # Object logical equality avoids rebuilding strings
                if style == current_style:
                    continue

                # Compute new string.
                # If they match after downsampling, keep the run going
                new_ansi = style.to_ansi(
                    separator=separator, color_support=level, downsample=downsample
                )
                if new_ansi == run_ansi:
                    current_style = style
                    continue
            else:
                new_ansi = style.to_ansi(
                    separator=separator, color_support=level, downsample=downsample
                )

            # Flush current styled run
            run_end = prev_idx + 1
            if run_ansi:
                parts.append(f"{run_ansi}{plain[run_start:run_end]}\x1b[0m")
            else:
                parts.append(plain[run_start:run_end])

            # Unstyled gap
            if idx > run_end:
                parts.append(plain[run_end:idx])

            run_start = idx
            run_ansi = new_ansi
            current_style = style

        # Flush last styled run
        last_end = sorted_keys[-1] + 1
        if run_ansi:
            parts.append(f"{run_ansi}{plain[run_start:last_end]}\x1b[0m")
        else:
            parts.append(plain[run_start:last_end])

        # Unstyled suffix
        if last_end < n:
            parts.append(plain[last_end:])

        return "".join(parts)

    def _get_indices(self, slice_: SliceGroup) -> tuple[int, int, int]:
        """Convert a slice or sequence of three integers to (start, stop, step)."""
        if isinstance(slice_, slice):
            start, stop, step = slice_.indices(len(self))
        else:
            start, stop, step = slice(*slice_).indices(len(self))
        return start, stop, step

    def _get_line_starts(self) -> tuple[int, ...]:
        """Return cached line start indices for plain text coordinates."""
        if self._line_starts is None:
            self._line_starts = (
                0,
                *(
                    index + 1
                    for index, char in enumerate(self.plain_text)
                    if char == "\n" and index + 1 < len(self)
                ),
            )
        return self._line_starts

    def _search_spans(
        self, *words: str, ignore_case: bool = False
    ) -> tuple[tuple[int, int], ...]:
        """Search for words in the plain text and return their (start, end) spans."""
        flags = _re.IGNORECASE if ignore_case else 0
        joined_words = "|".join(_re.escape(word) for word in words)
        spans = (
            match.span(0)
            for match in _re.finditer(joined_words, self.plain_text, flags=flags)
        )
        return tuple(spans)

    def _resolve_coordinates(
        self,
        coordinates: tuple[CoordinateGroup, ...],
        index_base: int,
        origin: tuple[int, int],
        system: _Literal["cartesian", "terminal"],
        on_out_of_bounds: _Literal["ignore", "clamp", "raise"],
    ) -> tuple[SliceGroup, ...]:
        """Convert a list of CoordinateGroups into a list of SliceGroups."""
        line_starts = self._get_line_starts()
        height = len(line_starts)
        slices: list[SliceGroup] = []

        index_to_span = {
            i: span
            for span in _get_grapheme_spans(
                self.plain_text, skip_emojis=False, skip_whitespace=False
            )
            if span[1] - span[0] > 1
            for i in range(*span)
        }

        def _resolve_coord(cx: int, cy: int) -> tuple[int, int] | None:
            cx = cx - index_base + origin[0]

            if system == "terminal":
                cy = cy - index_base + origin[1]
            elif system == "cartesian":
                cy = height - (cy - index_base + origin[1]) - 1

            if not (0 <= cy < height):
                if on_out_of_bounds == "raise":
                    raise IndexError(
                        f"Y coordinate {cy} is out of bounds for height {height}"
                    )
                elif on_out_of_bounds == "clamp":
                    cy = max(0, min(cy, height - 1))
                else:
                    return None

            line_start = line_starts[cy]
            line_end = line_starts[cy + 1] - 1 if cy + 1 < height else len(self)
            line_length = line_end - line_start

            if 0 <= cx < line_length:
                index = line_start + cx
                return index_to_span.get(index, (index, index + 1))
            else:
                if on_out_of_bounds == "raise":
                    raise IndexError(
                        f"X coordinate {cx} is out of bounds "
                        f"for line {cy} with length {line_length}"
                    )
                elif on_out_of_bounds == "clamp":
                    if line_length == 0:
                        return None
                    clamped_x = max(0, min(cx, line_length - 1))
                    index = line_start + clamped_x
                    return index_to_span.get(index, (index, index + 1))
            return None

        for item in coordinates:
            if len(item) == 2 and isinstance(item[0], int):
                span = _resolve_coord(*_cast(Coordinate, item))
                if span:
                    slices.append(span)
            else:
                group: list[SliceSpec] = []
                for sub_item in _cast(tuple[Coordinate, ...], item):
                    span = _resolve_coord(*sub_item)
                    if span:
                        group.append(span)

                if len(group) == 1:
                    slices.append(group[0])
                elif len(group) > 1:
                    slices.append(tuple(group))

        return tuple(slices)

    def _search_pattern(
        self,
        pattern: str | _re.Pattern[str],
        flags: int | _re.RegexFlag = 0,
    ) -> _Iterator[_re.Match[str]]:
        """Search for a regex pattern and return their (start, end) spans."""
        if isinstance(pattern, str):
            pattern = _re.compile(pattern, flags)

        for match in pattern.finditer(self.plain_text):
            yield match

    def _resolve_targets(self, targets: tuple[_Any, ...]) -> tuple[SliceGroup, ...]:
        """
        Convert diverse target selectors into concrete character slices.

        Evaluates abstract targeting objects (`Pattern`, `Words`, `Coords`, `Chars`)
        against the current plain text to determine the exact indices they span.

        Parameters
        ----------
        targets : tuple[Any, ...]
            A tuple of target selector objects or explicit slices/indices.

        Returns
        -------
        tuple[SliceGroup, ...]
            A flattened tuple of resolved slice boundaries indicating exactly
            where styles should be applied or removed.
        """
        resolved: list[SliceGroup] = []
        for target in targets:
            if isinstance(target, Pattern):
                for match in _cast(_re.Pattern[str], target.regex).finditer(
                    self.plain_text
                ):
                    if target.span_parser:
                        try:
                            result = target.span_parser(match)
                            if not result:
                                continue

                            if (
                                isinstance(result, tuple)
                                and len(result) >= 2
                                and isinstance(result[0], int)
                            ):
                                resolved.append(result)
                            else:
                                resolved.extend(result)
                        except Exception:
                            continue
                    else:
                        try:
                            span = match.span(target.group)
                            if span != (-1, -1):
                                resolved.append(span)
                        except IndexError:
                            continue
            elif isinstance(target, Words):
                spans = self._search_spans(
                    *target.words, ignore_case=target.ignore_case
                )
                resolved.extend(spans)
            elif isinstance(target, Coords):
                slices = self._resolve_coordinates(
                    target.points,
                    target.index_base,
                    target.origin,
                    target.system,
                    target.on_out_of_bounds,
                )
                resolved.extend(slices)
            elif isinstance(target, Chars):
                spans = _get_grapheme_spans(
                    self.plain_text, target.skip_emojis, target.skip_whitespace
                )
                resolved.extend(spans)
            else:
                resolved.append(target)
        return tuple(resolved)

    @staticmethod
    def from_ansi(plain: str) -> "ANSIString":
        """
        Create an ANSIString from a plain string containing ANSI escape sequences.

        Parses standard terminal escape codes (e.g., `\\x1b[31m`) embedded within
        the input string, strips them out of the plain text, and converts them
        into a managed `StyleManager` mapping.

        Parameters
        ----------
        plain : str
            The input string containing raw ANSI escape sequences.

        Returns
        -------
        ANSIString
            A new instance where the plain text is stripped of escape codes,
            and all parsed styles are applied to their corresponding indices.
        """
        start: int = 0
        decrement: int = 0
        style: str = ""
        styles: dict[int, str] = {}
        sequences: dict[int, str] = {}

        def flush(end: int) -> None:
            nonlocal style, start
            if style and start < end:
                for sub_index in range(start, end):
                    styles[sub_index] = style

        def smart_replacement(match_: _re.Match[str]) -> str:
            nonlocal decrement
            sequence, span = match_.group(0), match_.span(0)
            if sequence.endswith("m"):
                if span[0] - decrement in sequences:
                    sequences[span[0] - decrement] += sequence
                else:
                    sequences[span[0] - decrement] = sequence
            decrement += len(sequence)
            return ""

        plain = _re.sub(Regex.ANSI_SEQ, smart_replacement, plain)
        for index, sequence in sequences.items():
            for match_ in _re.finditer(Regex.SGR_PARAM, sequence):
                parameter = match_.group(0)
                if parameter == "0":
                    flush(index)
                    style = ""
                    start = index
                else:
                    if style and start < index:
                        flush(index)
                    style += f"\x1b[{parameter}m"
                    start = index
        flush(len(plain))
        return ANSIString(plain, styles)

    def style(
        self,
        style: Style
        | Foreground
        | Background
        | Underline
        | UnderlineMode
        | SGR
        | str
        | int
        | None,
        *targets: SliceGroup | Pattern | Words | Coords | Chars,
    ) -> _Self:
        """Apply a style to the string.
        
        Parameters
        ----------
        style : Style | Foreground | Background | Underline \
                | UnderlineMode | SGR | str | int | None
            The style to apply. Can be a pre-configured Style object \
            or an individual attribute.
        *targets : SliceGroup | Pattern | Words | Coords | Chars
            Target selectors defining where the style should be applied. If none are 
            provided, the style is applied to the entire string.
            
        Returns
        -------
        Self
            This ANSIString instance, modified in place.
        """
        if style == SGR.RESET:
            return self.unstyle(*targets)

        if not isinstance(style, Style):
            style = Style().with_style(style)

        # User passed no targets -> e.g., text.style(SGR.BOLD)
        if not targets:
            for index in range(len(self)):
                if index not in self.style_manager:
                    self.style_manager[index] = style
                else:
                    self.style_manager[index] = self.style_manager[index].merge(style)
            return self

        # User passed targets
        slices = self._resolve_targets(targets)

        # Targets were provided but matched nothing.
        if not slices:
            return self

        for slice_ in slices:
            for index in range(*self._get_indices(slice_)):
                if index not in self.style_manager:
                    self.style_manager[index] = style
                else:
                    self.style_manager[index] = self.style_manager[index].merge(style)

        return self

    def unstyle(self, *targets: SliceGroup | Pattern | Words | Coords | Chars) -> _Self:
        """Remove styling from the string.

        Parameters
        ----------
        *targets : SliceGroup | Pattern | Words | Coords | Chars
            Target selectors defining where the styling should be removed. If none are
            provided, all styling is removed from the entire string.

        Returns
        -------
        Self
            This ANSIString instance, modified in place.
        """

        if not targets:
            for index in range(len(self)):
                if index in self.style_manager:
                    del self.style_manager[index]
            return self

        slices = self._resolve_targets(targets)

        if not slices:
            return self

        for slice_ in slices:
            for index in range(*self._get_indices(slice_)):
                if index in self.style_manager:
                    del self.style_manager[index]

        return self

    def fg(
        self,
        color: Foreground | Bit8Index | Color | tuple[int, int, int] | str | int,
        *targets: SliceGroup | Pattern | Words | Coords | Chars,
    ) -> _Self:
        """Apply a foreground color.

        Parameters
        ----------
        color : Foreground | Palette256 | Color | tuple[int, int, int] | str | int
            The color to apply. Automatically infers 4-bit, 8-bit, or 24-bit depth.
        *targets : SliceGroup | Pattern | Words | Coords | Chars
            Target selectors defining where the color should be applied.

        Returns
        -------
        Self
            This ANSIString instance, modified in place.
        """
        resolved = _resolve_color(color, Foreground)
        return self.style(Style(foreground=resolved), *targets)

    def bg(
        self,
        color: Background | Bit8Index | Color | tuple[int, int, int] | str | int,
        *targets: SliceGroup | Pattern | Words | Coords | Chars,
    ) -> _Self:
        """Apply a background color.

        Parameters
        ----------
        color : Background | Palette256 | Color | tuple[int, int, int] | str | int
            The color to apply. Automatically infers 4-bit, 8-bit, or 24-bit depth.
        *targets : SliceGroup | Pattern | Words | Coords | Chars
            Target selectors defining where the color should be applied.

        Returns
        -------
        Self
            This ANSIString instance, modified in place.
        """
        resolved = _resolve_color(color, Background)
        return self.style(Style(background=resolved), *targets)

    def ul(
        self,
        color: Underline
        | Bit8Index
        | Color
        | tuple[int, int, int]
        | str
        | int = Underline.DEFAULT,
        *targets: SliceGroup | Pattern | Words | Coords | Chars,
    ) -> _Self:
        """Apply a underline color.

        Parameters
        ----------
        color : Underline | Palette256 | Color | tuple[int, int, int] | str | int, \
                default Underline.DEFAULT
            The color to apply. Automatically infers 4-bit, 8-bit, or 24-bit depth.
        *targets : SliceGroup | Pattern | Words | Coords | Chars
            Target selectors defining where the color should be applied.

        Returns
        -------
        Self
            This ANSIString instance, modified in place.
        """
        resolved = _resolve_color(color, Underline)
        return self.style(Style(underline=(resolved, UnderlineMode.SINGLE)), *targets)

    def rainbow(
        self,
        *targets: SliceGroup | Pattern | Words | Coords | Chars,
        channel: Channel = Channel.FG,
    ) -> _Self:
        """Apply a rainbow effect to the string.

        Parameters
        ----------
        *targets : SliceGroup | Pattern | Words | Coords | Chars
            Target selectors defining where the rainbow should be applied.
        channel : Channel, default Channel.FG
            The color channel(s) to apply the effect to (e.g., FG, BG, UL).

        Returns
        -------
        Self
            This ANSIString instance, modified in place.
        """

        if not targets:
            targets = (Chars(skip_whitespace=True),)

        slices = self._resolve_targets(targets)

        if not slices:
            return self

        length = len(slices)
        denom = length - 1 if length > 1 else 1

        for index, slice_ in enumerate(slices):
            hue = round(index / denom * 360)
            if Channel.FG in channel:
                self.fg(_hsl_to_rgb(hue), slice_)
            if Channel.BG in channel:
                self.bg(_hsl_to_rgb(hue), slice_)
            if Channel.UL in channel:
                self.ul(_hsl_to_rgb(hue), slice_)

        return self

    def to_svg(
        self,
        font: _TTFont | _Path | str,
        font_size_px: int | float,
        font_bold: _TTFont | _Path | str | None = None,
        font_italic: _TTFont | _Path | str | None = None,
        font_bold_italic: _TTFont | _Path | str | None = None,
        font_thin: _TTFont | _Path | str | None = None,
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
            Bold weight (100-900). If a variable ``wght`` axis is available,
            this value is used for bold variants (clamped to axis bounds).
            Otherwise, it is used as faux-bold stroke weight.
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
        if not _IS_FONTTOOLS_AVAILABLE:
            raise ImportError(
                "The 'fontTools' package is required to use the 'to_svg' method. "
                "Install it using 'pip install fonttools'."
            )
        font = _load_font(font)

        # Load variation fonts
        loaded_bold = _load_font(font_bold) if font_bold is not None else None
        loaded_italic = _load_font(font_italic) if font_italic is not None else None
        loaded_bold_italic = (
            _load_font(font_bold_italic) if font_bold_italic is not None else None
        )
        loaded_thin = _load_font(font_thin) if font_thin is not None else None

        variants = _prepare_font_variants(
            font,
            loaded_bold,
            loaded_italic,
            loaded_bold_italic,
            loaded_thin,
            weight if weight is not None else 700,
        )

        # Font metrics (from the base font)
        font_family = _cast(str, font["name"].getDebugName(1)) or "sans-serif"  # type: ignore[union-attr]
        units_per_em = _cast(int, font["head"].unitsPerEm)  # type: ignore[union-attr]
        ascent = _cast(int, font["hhea"].ascent)  # type: ignore[union-attr]
        descent = _cast(int, font["hhea"].descent)  # type: ignore[union-attr]
        line_gap = _cast(int, font["hhea"].lineGap)  # type: ignore[union-attr]
        underline_pos = _cast(int, font["post"].underlinePosition)  # type: ignore[union-attr]
        underline_thickness = _cast(int, font["post"].underlineThickness)  # type: ignore[union-attr]
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
                escaped = _SVG_ESCAPE.get(char, char)
                style = self.style_manager.get(charno)

                # Resolve font variant for this character
                style_key = _get_style_key(style)
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
                            ul_css = _UNDERLINE_CSS.get(style.underline[1], "solid")
                            inner = _tspan(escaped, fill_attrs)
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
                            chars.append(_tspan(escaped, fill_attrs))
                    else:
                        chars.append(f"<tspan>{escaped}</tspan>")

                # Path mode (using <path> and other shapes)
                else:
                    effective_skew = _resolve_skew(variant.needs_faux_italic, skew)
                    t_pen, pen, left_ov, right_ov = _svg_create_transform_pen(
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
                        _svg_weight_stroke_attrs(
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
                        ul_color, ul_mode = _svg_resolve_underline(style)
                        if ul_color and ul_mode is not None:
                            ul_y = (y_cursor - underline_pos) * scale
                            ul_h = max(underline_thickness * scale, 1)
                            ul_w = (advance_width + letter_spacing_offset) * scale
                            new_elems, max_bot = _svg_build_underline_elements(
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

    def gradient(
        self,
        colors: ColorScale | _Sequence[ColorStop],
        *targets: SliceGroup | Pattern | Words | Coords | Chars,
        space: _Literal["rgb", "hsl"] = "hsl",
        channel: Channel = Channel.FG,
    ) -> _Self:
        """Apply a gradient across targets of the string.

        Parameters
        ----------
        colors : ColorScale | Sequence[ColorStop]
            Gradient stops used for interpolation. When a list is provided, it is
            converted to a ColorScale using the `space` argument.
        *targets : SliceGroup | Pattern | Words | Coords | Chars
            Target selectors defining where the gradient should be applied. If no
            targets are provided, defaults to individual characters
            (skipping whitespace).
        space : Literal["rgb", "hsl"], default "hsl"
            Color interpolation space used when *colors* is a list.
        channel : Channel, default Channel.FG
            The color channel(s) to apply the gradient to (e.g., FG, BG, UL).

        Returns
        -------
        Self
            This ANSIString instance, modified in place.
        """

        if not isinstance(colors, ColorScale):
            colors = ColorScale(colors, space)

        if not targets:
            targets = (Chars(skip_whitespace=True),)

        slices = self._resolve_targets(targets)

        if not slices:
            return self

        length = len(slices)
        denom = length - 1 if length > 1 else 1

        for index, item in enumerate(slices):
            color = colors.interpolate_rgb(index / denom)
            if isinstance(item, slice) or isinstance(item[0], int):
                # Assume it's a slice or a tuple of (start, end, [step])
                item = _cast(SliceSpec, item)
                if Channel.FG in channel:
                    self.fg(color, item)
                if Channel.BG in channel:
                    self.bg(color, item)
                if Channel.UL in channel:
                    self.ul(color, item)
            else:
                # Assume it's a group of slice specs to be applied with the same color
                item = _cast(tuple[SliceSpec, ...], item)
                for sub_item in item:
                    if Channel.FG in channel:
                        self.fg(color, sub_item)
                    if Channel.BG in channel:
                        self.bg(color, sub_item)
                    if Channel.UL in channel:
                        self.ul(color, sub_item)

        return self

    def colormap(
        self,
        cmap: ColorMap | SegmentedColorMap,
        *targets: SliceGroup | Pattern | Words | Coords | Chars,
        values: _Sequence[int | float] | None = None,
        to_value: _Callable[[str], int | float] = float,
        channel: Channel = Channel.FG,
    ) -> "ANSIString":
        """Apply a colormap to targets based on a corresponding
        sequence of values or text extraction.

        Parameters
        ----------
        cmap : ColorMap | SegmentedColorMap
            The colormap used to resolve numerical values to Colors.
        *targets : SliceGroup | Pattern | Words | Coords | Chars
            Target selectors defining what substrings to evaluate. If no targets
            are provided, defaults to evaluating every non-whitespace character.
        values : Sequence[int | float] | None, default None
            Explicit numerical values corresponding to the matched targets.
            If not provided, the method extracts the text of each target
            and parses it using `to_value`.
        to_value : Callable[[str], int | float], default float
            A parser function that converts the extracted target text into a number.
            Only used if `values` is None.
        channel : Channel, default Channel.FG
            The color channel(s) to apply the colormap to (e.g., FG, BG, UL).

        Returns
        -------
        Self
            This ANSIString instance, modified in place.
        """

        if not targets:
            targets = (Chars(skip_whitespace=True),)

        slices = self._resolve_targets(targets)

        if not slices:
            return self

        if values is not None:
            iterator = zip(slices, values)

        else:
            plain = self.plain_text

            def _extract_and_parse():
                for slice_item in slices:
                    if isinstance(slice_item, tuple):
                        if isinstance(slice_item[0], int):
                            if len(slice_item) == 2:
                                substring = plain[slice_item[0] : slice_item[1]]
                            else:
                                substring = plain[slice(*slice_item)]
                        else:
                            first = slice_item[0]
                            if isinstance(first, slice):
                                substring = plain[first]
                            elif len(first) == 2:
                                substring = plain[first[0] : first[1]]
                            else:
                                substring = plain[slice(*first)]
                    else:
                        substring = plain[slice_item]

                    try:
                        yield slice_item, to_value(substring)
                    except (ValueError, TypeError):
                        continue

            iterator = _extract_and_parse()

        for slice_item, value in iterator:
            color = cmap(value).to_rgb()

            if isinstance(slice_item, slice) or isinstance(slice_item[0], int):
                slice_item = _cast(SliceSpec, slice_item)
                if Channel.FG in channel:
                    self.fg(color, slice_item)
                if Channel.BG in channel:
                    self.bg(color, slice_item)
                if Channel.UL in channel:
                    self.ul(color, slice_item)
            else:
                slice_item = _cast(tuple[SliceSpec, ...], slice_item)
                for sub_item in slice_item:
                    if Channel.FG in channel:
                        self.fg(color, sub_item)
                    if Channel.BG in channel:
                        self.bg(color, sub_item)
                    if Channel.UL in channel:
                        self.ul(color, sub_item)

        return self

    def join(self, iterable: _Iterable[str], /) -> "ANSIString":
        """
        Concatenate strings in an iterable,
        preserving ANSI styles from this string.
        """
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

    def ljust(self, width: _SupportsIndex, fillchar: str = " ") -> "ANSIString":
        """Left-justify the string within a given width, preserving ANSI styles."""
        return self + fillchar * (int(width) - len(self))

    def rjust(self, width: _SupportsIndex, fillchar: str = " ") -> "ANSIString":
        """Right-justify the string within a given width, preserving ANSI styles."""
        return self.__radd__(fillchar * (int(width) - len(self)))

    def center(self, width: _SupportsIndex, fillchar: str = " ") -> "ANSIString":
        """Center the string within a given width, preserving ANSI styles."""
        margin = int(width) - len(self)
        left = (margin // 2) + (margin & int(width) & 1)
        return self.__radd__(fillchar * left) + fillchar * (margin - left)

    def rsplit(  # type: ignore[override]
        self, sep: str | None = None, maxsplit: _SupportsIndex = -1
    ) -> list["ANSIString"]:
        """Split the string by a separator, preserving ANSI styles for each segment."""
        actual: list[_Any] = list(super().rsplit(sep, maxsplit))
        max_index = len(self)
        whitespace = _rsearch_separators(self.plain_text) if not sep else iter(())
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
        self, sep: str | None = None, maxsplit: _SupportsIndex = -1
    ) -> list["ANSIString"]:
        """Split the string by a separator, preserving ANSI styles for each segment."""
        actual: list[_Any] = list(super().split(sep, maxsplit))
        min_index = 0
        whitespace = _search_separators(self.plain_text) if not sep else iter(())
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
        """Split the string at line boundaries, preserving ANSI styles for each line."""
        actual: list[_Any] = list(super().splitlines(keepends))
        min_index = 0
        for no, string in enumerate(actual):
            max_index = min_index + len(string)
            styles = self.style_manager.copy_range(min_index, max_index, 0)
            actual[no] = type(self)(string, StyleManager(styles))
            min_index += len(string) + (0 if keepends else 1)
        return actual

    def strip(self, chars: str | None = None) -> "ANSIString":
        """
        Remove leading and trailing characters,
        preserving ANSI styles for the retained portion.
        """
        actual = super().strip(chars)
        if len(actual) == len(self):
            return type(self)(actual, self.style_manager.copy())
        index = len(self.plain_text) - len(super().lstrip(chars))
        styles = self.style_manager.copy_range(index, index + len(actual), 0)
        return type(self)(actual, StyleManager(styles))

    def lstrip(self, chars: str | None = None) -> "ANSIString":
        """
        Remove leading characters,
        preserving ANSI styles for the remaining string.
        """
        actual = super().lstrip(chars)
        if len(actual) == len(self):
            return type(self)(actual, self.style_manager.copy())
        index = len(self.plain_text) - len(actual)
        styles = self.style_manager.copy_range(index, index + len(actual), 0)
        return type(self)(actual, StyleManager(styles))

    def rstrip(self, chars: str | None = None) -> "ANSIString":
        """
        Remove trailing characters,
        preserving ANSI styles for the remaining string.
        """
        actual = super().rstrip(chars)
        if len(actual) == len(self):
            return type(self)(actual, self.style_manager.copy())
        styles = self.style_manager.copy_range(0, len(actual), 0)
        return type(self)(actual, StyleManager(styles))

    def replace(
        self,
        old: str,
        new: str,
        count: _SupportsIndex = -1,
    ) -> "ANSIString":
        """
        Replace occurrences of a substring,
        remapping existing ANSI styles to the new content.
        """
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
        """Remove a prefix, preserving ANSI styles for the remainder of the string."""
        if self.plain_text.startswith(prefix) and prefix:
            offset = len(prefix)
            return self[offset:]
        return type(self)(self.plain_text, self.style_manager.copy())

    def removesuffix(self, suffix: str, /) -> "ANSIString":
        """Remove a suffix, preserving ANSI styles for the remainder of the string."""
        if self.plain_text.endswith(suffix) and suffix:
            return self[: len(self) - len(suffix)]
        return type(self)(self.plain_text, self.style_manager.copy())

    def partition(self, sep: str, /) -> tuple["ANSIString", "ANSIString", "ANSIString"]:  # type: ignore[override]
        """
        Partition the string into three parts using the given separator,
        preserving ANSI styles.
        """
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
        """
        Partition the string into three parts using the given separator,
        starting at the end and preserving ANSI styles.
        """
        idx = self.plain_text.rfind(sep)
        if idx == -1:
            return (
                type(self)(""),
                type(self)(""),
                type(self)(self.plain_text, self.style_manager.copy()),
            )
        return (self[:idx], self[idx : idx + len(sep)], self[idx + len(sep) :])

    def zfill(self, width: _SupportsIndex, /) -> "ANSIString":
        """
        Pad a numeric string with zeros on the left preserving ANSI styles,
        to fill a field of the given width.
        """
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

    def expandtabs(self, tabsize: _SupportsIndex = 8) -> "ANSIString":  # type: ignore[override]
        """
        Return a copy where all tab characters are expanded using spaces,
        preserving ANSI styles for the resulting string.
        """
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
        """
        Encode the fully rendered styled string using the codec registered for encoding.
        """
        return self.styled_text.encode(encoding, errors)

    def casefold(self) -> "ANSIString":
        """
        Return a version of the string suitable for caseless comparisons,
        mapping styles to expanded characters.
        """
        actual = super().casefold()
        if actual == self.plain_text:
            return type(self)(actual, self.style_manager.copy())
        expansions = CASEFOLD_EXPANSIONS
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

    def translate(self, table: _Mapping[int, int | str | None]) -> "ANSIString":  # type: ignore[override]
        """
        Replace each character in the string using the given translation table,
        preserving ANSI styles for the mapped content.
        """
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

    def format(self, /, *args: _Any, **kwargs: _Any) -> "ANSIString":
        """
        Return a formatted version of the string,
        using substitutions from args and kwargs
        and remapping existing ANSI styles to the new content.
        """
        formatted = str.format(self.plain_text, *args, **kwargs)
        if not self.style_manager:
            return type(self)(formatted)
        styles = _remap_format(self.plain_text, self.style_manager, _FMT, args, kwargs)
        return type(self)(formatted, StyleManager(styles))

    def format_map(self, mapping: _Mapping[str, _Any], /) -> "ANSIString":  # type: ignore[override]
        """
        Return a formatted version of the string, using substitutions from mapping
        and remapping existing ANSI styles.
        """
        formatted = str.format_map(self.plain_text, mapping)
        if not self.style_manager:
            return type(self)(formatted)
        styles = _remap_format(
            self.plain_text, self.style_manager, _MAP_FMT, (), mapping
        )
        return type(self)(formatted, StyleManager(styles))
