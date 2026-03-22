__all__ = [
    "SVG_ESCAPE",
    "UNDERLINE_CSS",
    "FontVariant",
    "find_spans",
    "search_separators",
    "rsearch_separators",
    "clamp",
    "hsl_to_rgb",
    "load_font",
    "get_style_key",
    "prepare_font_variants",
    "tspan",
    "resolve_skew",
    "svg_create_transform_pen",
    "svg_weight_stroke_attrs",
    "svg_resolve_underline",
    "svg_build_underline_elements",
    "FMT",
    "MAP_FMT",
    "remap_format",
]

import math
from collections.abc import Generator
from colorsys import hls_to_rgb
from pathlib import Path
from string import Formatter as _Formatter
from typing import Any, NamedTuple

from fontTools.pens.svgPathPen import SVGPathPen  # type: ignore[import-untyped]
from fontTools.pens.transformPen import TransformPen  # type: ignore[import-untyped]
from fontTools.ttLib import TTFont  # type: ignore[import-untyped]

from pyansistring.constants import SGR, WHITESPACE, UnderlineMode
from pyansistring.style import Style, StyleManager

SVG_ESCAPE: dict[str, str] = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
}

UNDERLINE_CSS: dict[int, str] = {
    UnderlineMode.SINGLE: "solid",
    UnderlineMode.DOUBLE: "double",
    UnderlineMode.DOTTED: "dotted",
    UnderlineMode.DASHED: "dashed",
    UnderlineMode.CURLY: "wavy",
}


class FontVariant(NamedTuple):
    """Pre-computed font data for a single style variant (bold, italic, …)."""

    glyph_set: Any
    cmap: dict[int, str]
    needs_faux_bold: bool
    needs_faux_italic: bool


def find_spans(string: str, substring: str) -> Generator[tuple[int, int], None, None]:
    """Find all non-overlapping occurrences of `substring` in `string`."""
    i = j = 0
    while i < len(string):
        i = string[i:].find(substring)
        if i == -1:
            break
        yield (i + j, i + j + len(substring))
        j = i = i + j + len(substring)


def search_separators(
    string: str, allowed: set[str] = WHITESPACE
) -> Generator[str, None, None]:
    """Search for allowed separators in a string."""
    separator = ""
    for char in string:
        if char in allowed:
            separator += char
        elif separator:
            yield separator
            separator = ""
    if separator:
        yield separator


def rsearch_separators(
    string: str, allowed: set[str] = WHITESPACE
) -> Generator[str, None, None]:
    """Search for allowed separators in a string, starting from the end."""
    return search_separators(string[::-1], allowed)


def clamp(
    value: int | float,
    min_: int | float = float("-inf"),
    max_: int | float = float("inf"),
) -> int | float:
    """Restrict a number between two other numbers."""
    return min_ if value < min_ else max_ if value > max_ else value


def hsl_to_rgb(
    hue: int | float, saturation: int | float = 100, lightness: int | float = 50
) -> tuple[int, int, int]:
    """Convert HSL color values to RGB."""
    r, g, b = hls_to_rgb(hue / 360, lightness / 100, saturation / 100)
    return int(round(r * 255)), int(round(g * 255)), int(round(b * 255))


def load_font(font: "TTFont | Path | str") -> "TTFont":
    """Normalize a font argument to a `TTFont` instance."""
    if isinstance(font, (Path, str)):
        return TTFont(font)
    return font


def get_style_key(style: "Style | None") -> str:
    """Map a per-character :class:`Style` to one of the variant keys.

    Parameters
    ----------
    style : Style | None
        The character's Style, or ``None`` for default.

    Returns
    -------
    key : Literal["regular", "bold", "italic", "bold_italic", "thin"]
        Type key for the font variant to use when rendering this character.
    """
    if style is None:
        return "regular"
    is_bold = SGR.BOLD in style.attributes
    is_italic = SGR.ITALIC in style.attributes
    is_dim = SGR.DIM in style.attributes
    if is_bold and is_italic:
        return "bold_italic"
    if is_bold:
        return "bold"
    if is_italic:
        return "italic"
    if is_dim:
        return "thin"
    return "regular"


def prepare_font_variants(
    font: "TTFont",
    font_bold: "TTFont | None",
    font_italic: "TTFont | None",
    font_bold_italic: "TTFont | None",
    font_thin: "TTFont | None",
) -> dict[str, FontVariant]:
    """Build a mapping from style keys to :class:`FontVariant` tuples.

    Parameters
    ----------
    font : TTFont
        The main font to use for regular text.
    font_bold : TTFont | None
        Optional font to use for bold text. If ``None``, bold will be emulated.
    font_italic : TTFont | None
        Optional font to use for italic text. If ``None``, italic will be emulated.
    font_bold_italic : TTFont | None
        Optional font to use for bold italic text. If ``None``, bold italic will
        be emulated.
    font_thin : TTFont | None
        Optional font to use for thin (SGR.DIM) text. If ``None``, thin will be
        emulated as regular.

    Returns
    -------
    variants : dict[str, FontVariant]
        Mapping from style keys ("regular", "bold", "italic", "bold_italic",
        "thin") to pre-computed FontVariant tuples.
    """

    # -- fontTools helper wrappers (no stubs available) --
    def _cmap(f: TTFont) -> dict[int, str]:
        return f.getBestCmap()  # type: ignore[no-any-return]

    def _gs(f: TTFont, **kw: Any) -> Any:
        return f.getGlyphSet(**kw)  # type: ignore[no-any-return]

    def _fvar_axes(f: TTFont) -> dict[str, Any]:
        return {a.axTag: a for a in f["fvar"].axes}  # type: ignore[union-attr]

    main_cmap = _cmap(font)
    main_gs = _gs(font)

    variants: dict[str, FontVariant] = {
        "regular": FontVariant(main_gs, main_cmap, False, False),
    }

    # Detect variable-font axes
    has_fvar = "fvar" in font
    var_axes: dict[str, Any] = {}
    if has_fvar:
        var_axes = _fvar_axes(font)

    has_wght = "wght" in var_axes
    has_ital = "ital" in var_axes
    has_slnt = "slnt" in var_axes

    # Bold
    if font_bold is not None:
        variants["bold"] = FontVariant(
            _gs(font_bold),
            _cmap(font_bold),
            False,
            False,
        )
    elif has_wght:
        variants["bold"] = FontVariant(
            _gs(font, location={"wght": 700}),
            main_cmap,
            False,
            False,
        )
    else:
        variants["bold"] = FontVariant(main_gs, main_cmap, True, False)

    # Italic
    if font_italic is not None:
        variants["italic"] = FontVariant(
            _gs(font_italic),
            _cmap(font_italic),
            False,
            False,
        )
    elif has_ital:
        variants["italic"] = FontVariant(
            _gs(font, location={"ital": 1}),
            main_cmap,
            False,
            False,
        )
    elif has_slnt:
        variants["italic"] = FontVariant(
            _gs(font, location={"slnt": var_axes["slnt"].minValue}),
            main_cmap,
            False,
            False,
        )
    else:
        variants["italic"] = FontVariant(main_gs, main_cmap, False, True)

    # Bold Italic
    if font_bold_italic is not None:
        variants["bold_italic"] = FontVariant(
            _gs(font_bold_italic),
            _cmap(font_bold_italic),
            False,
            False,
        )
    elif has_wght and (has_ital or has_slnt):
        loc: dict[str, int | float] = {"wght": 700}
        if has_ital:
            loc["ital"] = 1
        else:
            loc["slnt"] = var_axes["slnt"].minValue
        variants["bold_italic"] = FontVariant(
            _gs(font, location=loc),
            main_cmap,
            False,
            False,
        )
    elif font_bold is not None:
        # Bold font available, faux italic only
        variants["bold_italic"] = FontVariant(
            _gs(font_bold),
            _cmap(font_bold),
            False,
            True,
        )
    elif font_italic is not None:
        # Italic font available, faux bold only
        variants["bold_italic"] = FontVariant(
            _gs(font_italic),
            _cmap(font_italic),
            True,
            False,
        )
    elif has_wght:
        # Variable bold + faux italic
        variants["bold_italic"] = FontVariant(
            _gs(font, location={"wght": 700}),
            main_cmap,
            False,
            True,
        )
    elif has_ital or has_slnt:
        # Variable italic + faux bold
        loc = {"ital": 1} if has_ital else {"slnt": var_axes["slnt"].minValue}
        variants["bold_italic"] = FontVariant(
            _gs(font, location=loc),
            main_cmap,
            True,
            False,
        )
    else:
        # No real font support — faux both
        variants["bold_italic"] = FontVariant(main_gs, main_cmap, True, True)

    # Thin (SGR.DIM)
    if font_thin is not None:
        variants["thin"] = FontVariant(
            _gs(font_thin),
            _cmap(font_thin),
            False,
            False,
        )
    elif has_wght:
        variants["thin"] = FontVariant(
            _gs(font, location={"wght": var_axes["wght"].minValue}),
            main_cmap,
            False,
            False,
        )
    else:
        # No thin support — render as regular
        variants["thin"] = FontVariant(main_gs, main_cmap, False, False)

    return variants


def tspan(content: str, attrs: list[str]) -> str:
    """Build a `<tspan>` element with optional attributes."""
    attr_str = f" {' '.join(attrs)}" if attrs else ""
    return f"<tspan{attr_str}>{content}</tspan>"


def resolve_skew(
    needs_faux_italic: bool,
    skew_override: int | None,
) -> float | None:
    """Return the faux-italic skew angle, or ``None`` when no skew is needed.

    Parameters
    ----------
    needs_faux_italic : bool
        Whether the current font variant requires faux italic emulation.
    skew_override : int | None
        Optional user-provided skew angle in degrees. If ``None``, a default of
        -12° will be used when *needs_faux_italic* is ``True``.

    Returns
    -------
    effective_skew : float | None
        The skew angle to apply for faux italic emulation, or ``None`` if no
        skew is needed.
    """
    if not needs_faux_italic:
        return None
    if skew_override is not None:
        return float(skew_override)
    return -12.0


def svg_create_transform_pen(
    glyph_set: Any,
    scale: float,
    x_px: float,
    y_px: float,
    ascent: int,
    descent: int,
    effective_skew: float | None,
) -> tuple[Any, Any, float, float]:
    """Create an SVGPathPen + TransformPen with optional italic skew.

    Parameters
    ----------
    glyph_set : Any
        The fontTools glyph set to use for rendering.
    scale : float
        Font size in pixels divided by the font's units-per-em.
    x_px : float
        Horizontal position in pixels to render the glyph at.
    y_px : float
        Vertical position in pixels to render the glyph at.
    ascent : int
        Font ascent in font units.
    descent : int
        Font descent in font units (negative value).
    effective_skew : float | None
        Skew angle in degrees to apply for faux italic emulation,
        or ``None`` if no skew is needed.

    Returns
    -------
    transform_pen : TransformPen
        A fontTools pen that applies the necessary transformations for rendering
        the glyph with optional skew.
    svg_path_pen : SVGPathPen
        The SVGPathPen that was used to generate the path data.
    left_overflow : float
        The amount of overflow to the left of the glyph's bounding box.
    right_overflow : float
        The amount of overflow to the right of the glyph's bounding box.
    """
    pen = SVGPathPen(glyph_set)
    left_ov = 0.0
    right_ov = 0.0

    if effective_skew is not None and effective_skew != 0:
        tan = math.tan(math.radians(effective_skew))
        t_pen = TransformPen(
            pen,
            (scale, 0, -scale * tan, -scale, x_px, y_px),
        )
        if tan > 0:
            left_ov = tan * ascent * scale - x_px
            right_ov = tan * abs(descent) * scale
        else:
            right_ov = abs(tan) * ascent * scale
            left_ov = abs(tan) * abs(descent) * scale - x_px
    else:
        t_pen = TransformPen(pen, (scale, 0, 0, -scale, x_px, y_px))

    return t_pen, pen, left_ov, right_ov


def svg_weight_stroke_attrs(
    style: Style | None,
    needs_faux_bold: bool,
    faux_weight: int,
    font_size_px: int | float,
    transparent_background: bool,
    background_color: tuple[int, int, int],
) -> list[str]:
    """Build SVG stroke attributes for faux
    font-weight emulation on ``<path>`` elements.

    Parameters
    ----------
    style : Style | None
        The character's Style, or ``None`` for default.
    needs_faux_bold : bool
        Whether the current font variant requires faux bold emulation.
    faux_weight : int
        The user-provided faux weight (100-900) to emulate, or 400 for normal weight.
    font_size_px : int | float
        The font size in pixels, used to calculate stroke width.
    transparent_background : bool
        Whether the overall background is transparent. If ``True``, faux bold will
        not be emulated with a background-colored stroke, since that would not be
        visible.
    background_color : tuple[int, int, int]
        The background color as an RGB tuple, used for faux bold emulation when no
        background color is specified in the Style.

    Returns
    -------
    stroke_attrs : list[str]
        A list of SVG attributes to apply a stroke for faux bold emulation, or an
        empty list if no stroke is needed.
    """
    if not needs_faux_bold or faux_weight == 400:
        return []

    sw = abs(faux_weight - 400) / 300 * font_size_px * 0.03

    if faux_weight > 400:
        color = (
            f"rgb{style.foreground.to_rgb()}"
            if style is not None and style.foreground
            else "currentColor"
        )
        return [f'stroke="{color}"', f'stroke-width="{sw}"', 'stroke-linejoin="round"']

    # faux_weight < 400: thin the glyph with background-coloured stroke
    if style is not None and style.background:
        thin = f"rgb{style.background.to_rgb()}"
    elif not transparent_background:
        thin = f"rgb{background_color}"
    else:
        return []
    return [f'stroke="{thin}"', f'stroke-width="{sw}"', 'stroke-linejoin="round"']


def svg_resolve_underline(style: Style) -> tuple[str | None, UnderlineMode | None]:
    """Determine underline colour string and mode from a character's Style."""
    if style.underline[0]:
        return f"rgb{style.underline[0].to_rgb()}", style.underline[1]
    if SGR.UNDERLINE in style.attributes:
        color = f"rgb{style.foreground.to_rgb()}" if style.foreground else "black"
        return color, UnderlineMode.SINGLE
    if SGR.DOUBLE_UNDERLINE in style.attributes:
        color = f"rgb{style.foreground.to_rgb()}" if style.foreground else "black"
        return color, UnderlineMode.DOUBLE
    return None, None


def svg_build_underline_elements(
    ul_color: str,
    ul_mode: UnderlineMode,
    ul_x: float,
    ul_y: float,
    ul_w: float,
    ul_h: float,
) -> tuple[list[str], float]:
    """Build SVG elements for a single-character underline.

    Parameters
    ----------
    ul_color : str
        The underline color as an SVG color string (e.g. ``"rgb(255,0,0)"``).
    ul_mode : UnderlineMode
        The underline mode (single, double, curly, dotted, dashed).
    ul_x : float
        The x-coordinate of the left edge of the underline.
    ul_y : float
        The y-coordinate of the top edge of the underline.
    ul_w : float
        The width of the underline.
    ul_h : float
        The thickness of the underline.

    Returns
    -------
    element_strings : list[str]
        A list of SVG element strings (e.g. ``<rect>``, ``<path>``,
        ``<circle>``, ``<line>``) that together render the underline.
    max_bottom_y : float
        The maximum y-coordinate of the bottom edge of any element in the
        underline.
    """
    elems: list[str] = []
    max_bot = 0.0

    if ul_mode == UnderlineMode.SINGLE:
        elems.append(
            f'  <rect x="{ul_x}" y="{ul_y}" '
            f'width="{ul_w}" height="{ul_h}" fill="{ul_color}"/>'
        )
        max_bot = ul_y + ul_h

    elif ul_mode == UnderlineMode.DOUBLE:
        gap = ul_h * 1.5
        for y_off in (ul_y, ul_y + ul_h + gap):
            elems.append(
                f'  <rect x="{ul_x}" y="{y_off}" '
                f'width="{ul_w}" height="{ul_h}" fill="{ul_color}"/>'
            )
        max_bot = ul_y + 2 * ul_h + gap

    elif ul_mode == UnderlineMode.CURLY:
        cy = ul_y + ul_h / 2
        amp = ul_h * 2
        segs = max(2, int(ul_w / (ul_h * 4)))
        seg_w = ul_w / segs
        d = f"M {ul_x},{cy}"
        for i in range(segs):
            cp_x = ul_x + seg_w * (i + 0.5)
            end_x = ul_x + seg_w * (i + 1)
            cp_y = cy + (amp if i % 2 == 0 else -amp)
            d += f" Q {cp_x},{cp_y} {end_x},{cy}"
        elems.append(
            f'  <path d="{d}" stroke="{ul_color}" stroke-width="{ul_h}" fill="none"/>'
        )
        max_bot = cy + amp + ul_h / 2

    elif ul_mode == UnderlineMode.DOTTED:
        cy = ul_y + ul_h / 2
        r = ul_h / 2
        spacing = ul_h * 3
        pos = r + math.ceil((ul_x - r) / spacing) * spacing if ul_x > r else r
        while pos < ul_x + ul_w:
            elems.append(f'  <circle cx="{pos}" cy="{cy}" r="{r}" fill="{ul_color}"/>')
            pos += spacing
        max_bot = cy + r

    elif ul_mode == UnderlineMode.DASHED:
        dash = ul_h * 3
        cy = ul_y + ul_h / 2
        elems.append(
            f'  <line x1="{ul_x}" y1="{cy}" x2="{ul_x + ul_w}" y2="{cy}" '
            f'stroke="{ul_color}" stroke-width="{ul_h}" '
            f'stroke-dasharray="{dash},{dash}"/>'
        )
        max_bot = cy + ul_h / 2

    return elems, max_bot


FMT = _Formatter()


class _MapFmt(_Formatter):
    """Formatter that resolves all field names through *kwargs* (the mapping)."""

    def get_value(
        self, key: int | str, args: Any, kwargs: Any
    ) -> Any:  # pragma: no cover
        return kwargs[key]


MAP_FMT = _MapFmt()


def _resolve_format_spec(
    spec: str,
    fmt: _Formatter,
    args: tuple[Any, ...],
    kwargs: Any,
    auto_idx: int,
) -> tuple[str, int]:
    """Resolve nested replacement fields inside a format spec."""
    if "{" not in spec:
        return spec, auto_idx
    parts: list[str] = []
    for literal, field_name, sub_spec, conv in fmt.parse(spec):
        parts.append(literal)
        if field_name is not None:
            if field_name == "":
                field_name = str(auto_idx)
                auto_idx += 1
            obj, _ = fmt.get_field(field_name, args, kwargs)
            if conv:
                obj = fmt.convert_field(obj, conv)
            resolved_sub, auto_idx = _resolve_format_spec(
                sub_spec or "", fmt, args, kwargs, auto_idx
            )
            parts.append(format(obj, resolved_sub))
    return "".join(parts), auto_idx


def remap_format(
    template: str,
    sm: StyleManager,
    fmt: _Formatter,
    args: tuple[Any, ...],
    kwargs: Any,
) -> dict[int, Style]:
    """Map styles from a format template onto the formatted output positions."""
    styles: dict[int, Style] = {}
    src = 0
    dest = 0
    auto_idx = 0

    for literal, field_name, spec, conv in fmt.parse(template):
        # Literal chars, {{ and }}, each occupy 2 source chars
        for ch in literal:
            if src in sm:
                styles[dest] = sm[src]
            src += 2 if ch in "{}" else 1
            dest += 1

        if field_name is not None:
            # Resolve auto-numbering
            if field_name == "":
                resolved = str(auto_idx)
                auto_idx += 1
            else:
                resolved = field_name

            obj, _ = fmt.get_field(resolved, args, kwargs)
            if conv:
                obj = fmt.convert_field(obj, conv)

            resolved_spec, auto_idx = _resolve_format_spec(
                spec or "", fmt, args, kwargs, auto_idx
            )
            dest += len(format(obj, resolved_spec))

            # Advance src past the {…} replacement field
            depth = 1
            src += 1  # skip opening '{'
            while depth:
                if template[src] == "{":
                    depth += 1
                elif template[src] == "}":
                    depth -= 1
                src += 1

    return styles
