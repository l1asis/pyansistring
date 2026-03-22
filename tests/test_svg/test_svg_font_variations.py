"""Tests for font variation support in SVG export.

Covers:
- Dedicated font files (font_bold, font_italic, font_bold_italic, font_thin)
- Variable font detection and axis-based rendering
- Faux bold/italic as last-resort per-character fallbacks
- Resolution priority cascade
- Path data verification (correct variant's glyph set is used)
"""

import re

import pytest

import pyansistring.core as pas
from pyansistring import ANSIString
from pyansistring._helpers import get_style_key, prepare_font_variants, resolve_skew
from pyansistring.color import Color
from pyansistring.constants import SGR, UnderlineMode
from pyansistring.style import Style
from tests.test_svg.conftest import (
    FakeHead,
    FakeHhea,
    FakeHmtx,
    FakeName,
    FakePost,
    FakeTTFont,
)


def make_font(
    glyph_width: int = 600,
    *,
    glyph_marker: int = 0,
    fvar_axes: list["FakeAxis"] | None = None,
) -> FakeTTFont:
    """Create a FakeTTFont, optionally with fvar axes and a glyph marker."""
    tables: dict[str, object] = {
        "head": FakeHead(),
        "hhea": FakeHhea(),
        "hmtx": FakeHmtx(),
        "name": FakeName(),
        "post": FakePost(),
    }
    if fvar_axes is not None:
        tables["fvar"] = FakeFvar(fvar_axes)
    return FakeTTFont(tables=tables, glyph_width=glyph_width, glyph_marker=glyph_marker)


class FakeAxis:
    """Minimal stand-in for fontTools fvar Axis."""

    def __init__(self, tag: str, min_val: int, default_val: int, max_val: int) -> None:
        self.axTag = tag
        self.minValue = min_val
        self.defaultValue = default_val
        self.maxValue = max_val


class FakeFvar:
    """Minimal stand-in for an fvar table."""

    def __init__(self, axes: list[FakeAxis]) -> None:
        self.axes = axes


@pytest.fixture(autouse=True)
def _enable_fonttools() -> None:  # pyright: ignore[reportUnusedFunction]
    """Ensure fonttools guard is enabled for every test in this module."""
    pas.is_fonttools_available = True


@pytest.fixture
def regular_font() -> FakeTTFont:
    return make_font(600, glyph_marker=10)


@pytest.fixture
def bold_font() -> FakeTTFont:
    """Bold font variant with wider glyphs and distinct marker."""
    return make_font(650, glyph_marker=20)


@pytest.fixture
def italic_font() -> FakeTTFont:
    """Italic font variant with narrower glyphs and distinct marker."""
    return make_font(580, glyph_marker=30)


@pytest.fixture
def bold_italic_font() -> FakeTTFont:
    """Bold-italic font variant."""
    return make_font(640, glyph_marker=40)


@pytest.fixture
def thin_font() -> FakeTTFont:
    """Thin font variant with narrower glyphs."""
    return make_font(550, glyph_marker=50)


@pytest.fixture
def variable_font() -> FakeTTFont:
    """Variable font with wght + ital axes."""
    return make_font(
        600,
        fvar_axes=[
            FakeAxis("wght", 100, 400, 900),
            FakeAxis("ital", 0, 0, 1),
        ],
    )


@pytest.fixture
def variable_font_wght_only() -> FakeTTFont:
    """Variable font with only wght axis."""
    return make_font(
        600,
        fvar_axes=[
            FakeAxis("wght", 100, 400, 900),
        ],
    )


@pytest.fixture
def variable_font_slnt_only() -> FakeTTFont:
    """Variable font with only slnt axis."""
    return make_font(
        600,
        fvar_axes=[
            FakeAxis("slnt", -12, 0, 0),
        ],
    )


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------


class TestGetStyleKey:
    def test_regular_for_none(self):
        assert get_style_key(None) == "regular"

    def test_regular_for_fg_only(self):
        style = Style(
            foreground=Color.from_24bit(255, 0, 0),
            background=Color.unset(),
            underline=(Color.unset(), UnderlineMode.SINGLE),
            attributes=frozenset(),
        )
        assert get_style_key(style) == "regular"

    def test_bold(self):
        style = Style(
            foreground=Color.unset(),
            background=Color.unset(),
            underline=(Color.unset(), UnderlineMode.SINGLE),
            attributes=frozenset({SGR.BOLD}),
        )
        assert get_style_key(style) == "bold"

    def test_italic(self):
        style = Style(
            foreground=Color.unset(),
            background=Color.unset(),
            underline=(Color.unset(), UnderlineMode.SINGLE),
            attributes=frozenset({SGR.ITALIC}),
        )
        assert get_style_key(style) == "italic"

    def test_bold_italic(self):
        style = Style(
            foreground=Color.unset(),
            background=Color.unset(),
            underline=(Color.unset(), UnderlineMode.SINGLE),
            attributes=frozenset({SGR.BOLD, SGR.ITALIC}),
        )
        assert get_style_key(style) == "bold_italic"

    def test_dim(self):
        style = Style(
            foreground=Color.unset(),
            background=Color.unset(),
            underline=(Color.unset(), UnderlineMode.SINGLE),
            attributes=frozenset({SGR.DIM}),
        )
        assert get_style_key(style) == "thin"


class TestResolveSkew:
    def test_no_faux_returns_none(self):
        assert resolve_skew(False, None) is None

    def test_no_faux_with_override_returns_none(self):
        assert resolve_skew(False, -20) is None

    def test_faux_default(self):
        assert resolve_skew(True, None) == -12.0

    def test_faux_with_override(self):
        assert resolve_skew(True, -20) == -20.0


# ---------------------------------------------------------------------------
# Font variant preparation
# ---------------------------------------------------------------------------


class TestPrepareVariants:
    def test_no_fvar_no_variation_fonts(self, regular_font: FakeTTFont):
        variants = prepare_font_variants(regular_font, None, None, None, None)
        assert not variants["regular"].needs_faux_bold
        assert not variants["regular"].needs_faux_italic
        assert variants["bold"].needs_faux_bold
        assert not variants["bold"].needs_faux_italic
        assert not variants["italic"].needs_faux_bold
        assert variants["italic"].needs_faux_italic
        assert variants["bold_italic"].needs_faux_bold
        assert variants["bold_italic"].needs_faux_italic
        assert not variants["thin"].needs_faux_bold

    def test_with_bold_font(self, regular_font: FakeTTFont, bold_font: FakeTTFont):
        variants = prepare_font_variants(regular_font, bold_font, None, None, None)
        assert not variants["bold"].needs_faux_bold
        # Bold-italic should use bold font + faux italic
        assert not variants["bold_italic"].needs_faux_bold
        assert variants["bold_italic"].needs_faux_italic

    def test_with_italic_font(self, regular_font: FakeTTFont, italic_font: FakeTTFont):
        variants = prepare_font_variants(regular_font, None, italic_font, None, None)
        assert not variants["italic"].needs_faux_italic
        # Bold-italic should use italic font + faux bold
        assert variants["bold_italic"].needs_faux_bold
        assert not variants["bold_italic"].needs_faux_italic

    def test_with_all_fonts(
        self,
        regular_font: FakeTTFont,
        bold_font: FakeTTFont,
        italic_font: FakeTTFont,
        bold_italic_font: FakeTTFont,
        thin_font: FakeTTFont,
    ):
        variants = prepare_font_variants(
            regular_font,
            bold_font,
            italic_font,
            bold_italic_font,
            thin_font,
        )
        for key in ("regular", "bold", "italic", "bold_italic", "thin"):
            assert not variants[key].needs_faux_bold, f"{key} should not need faux bold"
            assert not variants[key].needs_faux_italic, (
                f"{key} should not need faux italic"
            )

    def test_variable_font_both_axes(self, variable_font: FakeTTFont):
        variants = prepare_font_variants(variable_font, None, None, None, None)
        assert not variants["bold"].needs_faux_bold
        assert not variants["italic"].needs_faux_italic
        assert not variants["bold_italic"].needs_faux_bold
        assert not variants["bold_italic"].needs_faux_italic

    def test_variable_font_wght_only(self, variable_font_wght_only: FakeTTFont):
        variants = prepare_font_variants(
            variable_font_wght_only, None, None, None, None
        )
        assert not variants["bold"].needs_faux_bold
        assert variants["italic"].needs_faux_italic
        # Bold-italic: variable bold + faux italic
        assert not variants["bold_italic"].needs_faux_bold
        assert variants["bold_italic"].needs_faux_italic

    def test_variable_font_slnt(self, variable_font_slnt_only: FakeTTFont):
        variants = prepare_font_variants(
            variable_font_slnt_only, None, None, None, None
        )
        assert variants["bold"].needs_faux_bold
        assert not variants["italic"].needs_faux_italic
        # Bold-italic: variable italic + faux bold
        assert variants["bold_italic"].needs_faux_bold
        assert not variants["bold_italic"].needs_faux_italic

    def test_dedicated_font_overrides_variable(
        self, variable_font: FakeTTFont, bold_font: FakeTTFont
    ):
        """
        When both a variable axis and a dedicated font
        exist, the dedicated font wins.
        """
        variants = prepare_font_variants(variable_font, bold_font, None, None, None)
        # Bold variant should use bold_font's glyph set, not the variable axis
        assert not variants["bold"].needs_faux_bold


class TestFontBoldParam:
    def test_bold_char_no_faux_stroke_with_font_bold(
        self, regular_font: FakeTTFont, bold_font: FakeTTFont
    ):
        """When font_bold is provided, bold chars should NOT get faux stroke."""
        s = ANSIString("AB").style(SGR.BOLD)
        svg = s.to_svg(
            regular_font,
            font_size_px=16,
            font_bold=bold_font,
            convert_text_to_path=True,
        )
        assert "stroke-width=" not in svg

    def test_bold_with_font_bold_text_mode(
        self, regular_font: FakeTTFont, bold_font: FakeTTFont
    ):
        """Text mode still emits font-weight='bold' CSS attribute."""
        s = ANSIString("AB").style(SGR.BOLD).fg_24b(0, 0, 0)
        svg = s.to_svg(regular_font, font_size_px=16, font_bold=bold_font)
        assert 'font-weight="bold"' in svg

    def test_non_bold_char_unaffected_by_font_bold(
        self, regular_font: FakeTTFont, bold_font: FakeTTFont
    ):
        """Regular chars use the regular font even when font_bold is present."""
        s = ANSIString("AB")
        svg = s.to_svg(
            regular_font,
            font_size_px=16,
            font_bold=bold_font,
            convert_text_to_path=True,
        )
        assert "stroke-width=" not in svg


class TestFontItalicParam:
    def test_italic_char_no_faux_skew_with_font_italic(
        self, regular_font: FakeTTFont, italic_font: FakeTTFont
    ):
        """When font_italic is provided, italic chars should NOT get faux skew."""
        s = ANSIString("AB").style(SGR.ITALIC)
        svg_with = s.to_svg(
            regular_font,
            font_size_px=16,
            font_italic=italic_font,
            convert_text_to_path=True,
        )
        svg_without = s.to_svg(
            regular_font,
            font_size_px=16,
            convert_text_to_path=True,
        )
        # Without font_italic, faux skew creates wider SVG
        w_with = float(svg_with.split('width="')[1].split('"')[0])
        w_without = float(svg_without.split('width="')[1].split('"')[0])
        # With font_italic: no extra italic overhang → narrower or equal width
        assert w_with <= w_without


class TestFontBoldItalicParam:
    def test_no_faux_effects_with_dedicated_font(
        self, regular_font: FakeTTFont, bold_italic_font: FakeTTFont
    ):
        """Dedicated bold-italic font removes all faux effects."""
        s = ANSIString("AB").style(SGR.BOLD).style(SGR.ITALIC)
        svg = s.to_svg(
            regular_font,
            font_size_px=16,
            font_bold_italic=bold_italic_font,
            convert_text_to_path=True,
        )
        assert "stroke-width=" not in svg

    def test_bold_italic_falls_back_to_bold_plus_faux_italic(
        self, regular_font: FakeTTFont, bold_font: FakeTTFont
    ):
        """Without font_bold_italic, bold font + faux italic is used."""
        s = ANSIString("AB").style(SGR.BOLD).style(SGR.ITALIC)
        svg = s.to_svg(
            regular_font,
            font_size_px=16,
            font_bold=bold_font,
            convert_text_to_path=True,
        )
        # No faux bold stroke (bold font handles it)
        assert "stroke-width=" not in svg


class TestFontThinParam:
    def test_dim_text_mode_emits_lighter(self, regular_font: FakeTTFont):
        """SGR.DIM chars get font-weight='lighter' in text mode."""
        s = ANSIString("AB").style(SGR.DIM).fg_24b(0, 0, 0)
        svg = s.to_svg(regular_font, font_size_px=16)
        assert 'font-weight="lighter"' in svg

    def test_dim_path_mode_with_font_thin(
        self, regular_font: FakeTTFont, thin_font: FakeTTFont
    ):
        """When font_thin is provided, SGR.DIM chars use it (no faux stroke)."""
        s = ANSIString("AB").style(SGR.DIM)
        svg = s.to_svg(
            regular_font,
            font_size_px=16,
            font_thin=thin_font,
            convert_text_to_path=True,
        )
        assert "stroke-width=" not in svg


class TestVariableFont:
    def test_variable_font_bold_no_faux(self, variable_font: FakeTTFont):
        s = ANSIString("AB").style(SGR.BOLD)
        svg = s.to_svg(variable_font, font_size_px=16, convert_text_to_path=True)
        assert "stroke-width=" not in svg

    def test_variable_font_italic_no_faux(self, variable_font: FakeTTFont):
        s = ANSIString("AB").style(SGR.ITALIC)
        svg_var = s.to_svg(variable_font, font_size_px=16, convert_text_to_path=True)
        svg_reg = s.to_svg(make_font(600), font_size_px=16, convert_text_to_path=True)
        # Both should work; variable font has native italic so no faux skew
        w_var = float(svg_var.split('width="')[1].split('"')[0])
        w_reg = float(svg_reg.split('width="')[1].split('"')[0])
        # Variable font: no faux italic → no extra overhang → narrower or equal
        assert w_var <= w_reg

    def test_variable_bold_italic_no_faux(self, variable_font: FakeTTFont):
        s = ANSIString("AB").style(SGR.BOLD).style(SGR.ITALIC)
        svg = s.to_svg(variable_font, font_size_px=16, convert_text_to_path=True)
        assert "stroke-width=" not in svg

    def test_variable_wght_only_italic_gets_faux(
        self, variable_font_wght_only: FakeTTFont
    ):
        """Variable font with only wght: italic still needs faux skew."""
        s = ANSIString("AB").style(SGR.ITALIC)
        svg_var = s.to_svg(
            variable_font_wght_only,
            font_size_px=16,
            convert_text_to_path=True,
        )
        svg_reg = s.to_svg(
            make_font(600),
            font_size_px=16,
            convert_text_to_path=True,
        )
        # Both should produce the same width (both faux italic)
        w_var = float(svg_var.split('width="')[1].split('"')[0])
        w_reg = float(svg_reg.split('width="')[1].split('"')[0])
        assert w_var == w_reg

    def test_variable_thin_uses_min_weight(self, variable_font: FakeTTFont):
        """SGR.DIM chars on a variable font use the wght axis minimum."""
        s = ANSIString("AB").style(SGR.DIM)
        svg = s.to_svg(variable_font, font_size_px=16, convert_text_to_path=True)
        assert "stroke-width=" not in svg


class TestFauxFallback:
    def test_faux_bold_default_700(self, regular_font: FakeTTFont):
        """Default faux weight is 700 when weight= is not specified."""
        s = ANSIString("AB").style(SGR.BOLD)
        svg = s.to_svg(regular_font, font_size_px=16, convert_text_to_path=True)
        expected_sw = (700 - 400) / 300 * 16 * 0.03
        assert f'stroke-width="{expected_sw}"' in svg

    def test_faux_bold_custom_weight(self, regular_font: FakeTTFont):
        """User can override the faux weight value."""
        s = ANSIString("AB").style(SGR.BOLD)
        svg = s.to_svg(
            regular_font,
            font_size_px=16,
            weight=900,
            convert_text_to_path=True,
        )
        expected_sw = (900 - 400) / 300 * 16 * 0.03
        assert f'stroke-width="{expected_sw}"' in svg

    def test_faux_italic_default_skew(self, regular_font: FakeTTFont):
        """Default faux skew is -12 when skew= is not specified."""
        s = ANSIString("AB").style(SGR.ITALIC)
        svg = s.to_svg(regular_font, font_size_px=16, convert_text_to_path=True)
        # Should produce wider SVG due to italic overflow
        svg_plain = ANSIString("AB").to_svg(
            regular_font,
            font_size_px=16,
            convert_text_to_path=True,
        )
        w_italic = float(svg.split('width="')[1].split('"')[0])
        w_plain = float(svg_plain.split('width="')[1].split('"')[0])
        assert w_italic > w_plain

    def test_faux_italic_custom_skew(self, regular_font: FakeTTFont):
        """User can override the faux skew angle."""
        s = ANSIString("AB").style(SGR.ITALIC)
        svg_default = s.to_svg(
            regular_font,
            font_size_px=16,
            convert_text_to_path=True,
        )
        svg_custom = s.to_svg(
            regular_font,
            font_size_px=16,
            skew=-20,
            convert_text_to_path=True,
        )
        # -20 degree skew should create more overhang than -12
        w_default = float(svg_default.split('width="')[1].split('"')[0])
        w_custom = float(svg_custom.split('width="')[1].split('"')[0])
        assert w_custom > w_default

    def test_faux_only_on_styled_chars(self, regular_font: FakeTTFont):
        """Faux effects apply only to bold/italic chars, not all chars."""
        s = ANSIString("ABCD").style(SGR.BOLD, (0, 2))  # Only AB is bold
        svg = s.to_svg(
            regular_font,
            font_size_px=16,
            convert_text_to_path=True,
        )
        paths = [line.strip() for line in svg.splitlines() if "<path " in line]
        bold_paths = [p for p in paths if "stroke-width=" in p]
        plain_paths = [p for p in paths if "stroke-width=" not in p]
        assert len(bold_paths) == 2  # A, B
        assert len(plain_paths) == 2  # C, D

    def test_weight_400_suppresses_faux_bold(self, regular_font: FakeTTFont):
        """weight=400 means no faux bold even for SGR.BOLD chars."""
        s = ANSIString("AB").style(SGR.BOLD)
        svg = s.to_svg(
            regular_font,
            font_size_px=16,
            weight=400,
            convert_text_to_path=True,
        )
        assert "stroke-width=" not in svg

    def test_skew_zero_suppresses_faux_italic(self, regular_font: FakeTTFont):
        """skew=0 means no faux italic even for SGR.ITALIC chars."""
        s = ANSIString("AB").style(SGR.ITALIC)
        svg = s.to_svg(
            regular_font,
            font_size_px=16,
            skew=0,
            convert_text_to_path=True,
        )
        svg_plain = ANSIString("AB").to_svg(
            regular_font,
            font_size_px=16,
            convert_text_to_path=True,
        )
        w_skew0 = float(svg.split('width="')[1].split('"')[0])
        w_plain = float(svg_plain.split('width="')[1].split('"')[0])
        assert w_skew0 == w_plain


class TestMixedStyles:
    def test_partial_bold_mixed_fonts(
        self, regular_font: FakeTTFont, bold_font: FakeTTFont
    ):
        """Bold chars use font_bold; regular chars use regular font."""
        s = ANSIString("ABCD").style(SGR.BOLD, (0, 2))
        svg = s.to_svg(
            regular_font,
            font_size_px=16,
            font_bold=bold_font,
            convert_text_to_path=True,
        )
        # No faux stroke anywhere since bold chars have font_bold
        assert "stroke-width=" not in svg

    def test_bold_and_italic_different_chars(
        self, regular_font: FakeTTFont, bold_font: FakeTTFont, italic_font: FakeTTFont
    ):
        """AB=bold, CD=italic — each uses its variant font."""
        s = ANSIString("ABCD").style(SGR.BOLD, (0, 2)).style(SGR.ITALIC, (2, 4))
        svg = s.to_svg(
            regular_font,
            font_size_px=16,
            font_bold=bold_font,
            font_italic=italic_font,
            convert_text_to_path=True,
        )
        # No faux bold (handled by font_bold) and
        # no faux italic (handled by font_italic)
        assert "stroke-width=" not in svg


def _extract_path_d(svg: str) -> list[str]:
    """Extract all ``d="..."`` values from ``<path>`` elements."""
    return re.findall(r'd="([^"]*)"', svg)


class TestPathDataDistinction:
    """Verify that each variant's glyph set is *actually drawn*, not just
    selected. Uses the marker-based ``_Glyph.draw()`` so different fonts
    produce recognisably different SVG path data.
    """

    def test_bold_chars_use_bold_font_paths(
        self, regular_font: FakeTTFont, bold_font: FakeTTFont
    ):
        s = ANSIString("AB").style(SGR.BOLD)
        svg_variant = s.to_svg(
            regular_font,
            font_size_px=16,
            font_bold=bold_font,
            convert_text_to_path=True,
        )
        svg_regular = ANSIString("AB").to_svg(
            regular_font,
            font_size_px=16,
            convert_text_to_path=True,
        )
        paths_variant = _extract_path_d(svg_variant)
        paths_regular = _extract_path_d(svg_regular)
        # Bold font has marker=20, regular has marker=10 → different paths
        assert paths_variant != paths_regular

    def test_italic_chars_use_italic_font_paths(
        self, regular_font: FakeTTFont, italic_font: FakeTTFont
    ):
        s = ANSIString("AB").style(SGR.ITALIC)
        svg_variant = s.to_svg(
            regular_font,
            font_size_px=16,
            font_italic=italic_font,
            convert_text_to_path=True,
        )
        svg_regular = ANSIString("AB").to_svg(
            regular_font,
            font_size_px=16,
            convert_text_to_path=True,
        )
        paths_variant = _extract_path_d(svg_variant)
        paths_regular = _extract_path_d(svg_regular)
        assert paths_variant != paths_regular

    def test_bold_italic_chars_use_bold_italic_font_paths(
        self, regular_font: FakeTTFont, bold_italic_font: FakeTTFont
    ):
        s = ANSIString("AB").style(SGR.BOLD).style(SGR.ITALIC)
        svg_variant = s.to_svg(
            regular_font,
            font_size_px=16,
            font_bold_italic=bold_italic_font,
            convert_text_to_path=True,
        )
        svg_regular = ANSIString("AB").to_svg(
            regular_font,
            font_size_px=16,
            convert_text_to_path=True,
        )
        paths_variant = _extract_path_d(svg_variant)
        paths_regular = _extract_path_d(svg_regular)
        assert paths_variant != paths_regular

    def test_mixed_string_each_variant_gets_own_paths(
        self, regular_font: FakeTTFont, bold_font: FakeTTFont, italic_font: FakeTTFont
    ):
        """AB=bold, CD=italic — bold paths differ from italic paths."""
        s = ANSIString("ABCD").style(SGR.BOLD, (0, 2)).style(SGR.ITALIC, (2, 4))
        svg = s.to_svg(
            regular_font,
            font_size_px=16,
            font_bold=bold_font,
            font_italic=italic_font,
            convert_text_to_path=True,
        )
        paths = _extract_path_d(svg)
        assert len(paths) == 4
        # The V (vertical) coordinate is position-independent (same line).
        # ascender=900, scale=16/1000=0.016 → baseline y=14.4
        # Bold marker=20: V = 14.4 - 20*0.016 = 14.08
        # Italic marker=30: V = 14.4 - 30*0.016 = 13.92
        assert "V14.08" in paths[0]  # A (bold)
        assert "V14.08" in paths[1]  # B (bold)
        assert "V13.92" in paths[2]  # C (italic)
        assert "V13.92" in paths[3]  # D (italic)

    def test_regular_chars_unaffected(
        self, regular_font: FakeTTFont, bold_font: FakeTTFont
    ):
        """Non-bold chars still use the regular font's glyph set."""
        s = ANSIString("ABCD").style(SGR.BOLD, (0, 2))  # AB bold, CD regular
        svg = s.to_svg(
            regular_font,
            font_size_px=16,
            font_bold=bold_font,
            convert_text_to_path=True,
        )
        paths = _extract_path_d(svg)
        assert len(paths) == 4
        # V coordinate is position-independent.
        # Bold marker=20: V = 14.4 - 20*0.016 = 14.08
        # Regular marker=10: V = 14.4 - 10*0.016 = 14.24
        assert "V14.08" in paths[0]  # A (bold)
        assert "V14.08" in paths[1]  # B (bold)
        assert "V14.24" in paths[2]  # C (regular)
        assert "V14.24" in paths[3]  # D (regular)
