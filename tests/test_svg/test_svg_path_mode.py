"""Tests for SVG export in path mode (convert_text_to_path=True)."""

from pyansistring import ANSIString
from pyansistring.constants import SGR, UnderlineMode
from tests.test_svg.conftest import FakeTTFont


class TestPathModeBold:
    def test_bold_produces_stroke(self, fake_font: FakeTTFont):
        s = ANSIString("AB").fm(SGR.BOLD)
        svg = s.to_svg(fake_font, font_size_px=16, convert_text_to_path=True)
        assert "stroke-width=" in svg
        assert "stroke-linejoin=" in svg
        assert "<path " in svg

    def test_explicit_weight_overrides(self, fake_font: FakeTTFont):
        s = ANSIString("AB").fm(SGR.BOLD)
        svg = s.to_svg(
            fake_font, font_size_px=16, convert_text_to_path=True, weight=900
        )
        bold_900_sw = (900 - 400) / 300 * 16 * 0.03
        assert f'stroke-width="{bold_900_sw}"' in svg

    def test_weight_below_400_thins_with_bg(self, fake_font: FakeTTFont):
        s = ANSIString("AB").fm(SGR.BOLD)
        svg = s.to_svg(
            fake_font,
            font_size_px=16,
            convert_text_to_path=True,
            weight=200,
            transparent_background=False,
            background_color=(255, 255, 255),
        )
        thin_sw = (400 - 200) / 300 * 16 * 0.03
        assert f'stroke-width="{thin_sw}"' in svg
        assert 'stroke="rgb(255, 255, 255)"' in svg

    def test_weight_below_400_skipped_transparent(self, fake_font: FakeTTFont):
        s = ANSIString("AB")
        svg = s.to_svg(
            fake_font,
            font_size_px=16,
            convert_text_to_path=True,
            weight=200,
            transparent_background=True,
        )
        assert "stroke-width=" not in svg

    def test_weight_400_no_stroke(self, fake_font: FakeTTFont):
        s = ANSIString("AB").fm(SGR.BOLD)
        svg = s.to_svg(
            fake_font, font_size_px=16, convert_text_to_path=True, weight=400
        )
        assert "stroke-width=" not in svg

    def test_weight_ignored_on_non_bold(self, fake_font: FakeTTFont):
        """weight= is a faux fallback; it does nothing on non-bold chars."""
        s = ANSIString("AB")
        svg = s.to_svg(
            fake_font, font_size_px=16, convert_text_to_path=True, weight=401
        )
        assert "stroke-width=" not in svg

    def test_weight_on_non_bold_no_stroke(self, fake_font: FakeTTFont):
        """weight= on non-bold text produces no stroke effect."""
        s = ANSIString("AB")
        svg = s.to_svg(
            fake_font, font_size_px=16, convert_text_to_path=True, weight=700
        )
        assert "stroke-width=" not in svg


class TestPathModeItalic:
    def test_italic_no_transform_attr(self, fake_font: FakeTTFont):
        s = ANSIString("AB").fm(SGR.ITALIC)
        svg = s.to_svg(fake_font, font_size_px=16, convert_text_to_path=True)
        assert "transform=" not in svg
        assert "<path " in svg

    def test_explicit_skew_baked_in(self, fake_font: FakeTTFont):
        s = ANSIString("AB").fm(SGR.ITALIC)
        svg = s.to_svg(fake_font, font_size_px=16, convert_text_to_path=True, skew=-20)
        assert "transform=" not in svg

    def test_no_italic_no_skew(self, fake_font: FakeTTFont):
        s = ANSIString("AB").fm(SGR.BOLD)
        svg = s.to_svg(fake_font, font_size_px=16, convert_text_to_path=True)
        assert "transform=" not in svg

    def test_skew_zero(self, fake_font: FakeTTFont):
        s = ANSIString("AB").fm(SGR.ITALIC)
        svg = s.to_svg(fake_font, font_size_px=16, convert_text_to_path=True, skew=0)
        assert "transform=" not in svg

    def test_skew_ignored_on_non_italic(self, fake_font: FakeTTFont):
        """skew= is a faux fallback; it has no effect on non-italic chars."""
        s = ANSIString("AB")
        svg_no = s.to_svg(fake_font, font_size_px=16, convert_text_to_path=True)
        svg_sk = s.to_svg(
            fake_font, font_size_px=16, convert_text_to_path=True, skew=-15
        )
        no_w = float(svg_no.split('width="')[1].split('"')[0])
        sk_w = float(svg_sk.split('width="')[1].split('"')[0])
        assert sk_w == no_w  # no effect on non-italic chars

    def test_positive_skew(self, fake_font: FakeTTFont):
        s = ANSIString("AB").fm(SGR.ITALIC)
        svg = s.to_svg(fake_font, font_size_px=16, convert_text_to_path=True, skew=12)
        assert "<path " in svg


class TestPathModeCombined:
    def test_bold_italic(self, fake_font: FakeTTFont):
        s = ANSIString("AB").fm(SGR.BOLD).fm(SGR.ITALIC)
        svg = s.to_svg(fake_font, font_size_px=16, convert_text_to_path=True)
        assert "stroke-width=" in svg
        assert "transform=" not in svg

    def test_bold_italic_underline(self, fake_font: FakeTTFont):
        s = ANSIString("Hi").fm(SGR.BOLD).fm(SGR.ITALIC).fm(SGR.UNDERLINE)
        svg = s.to_svg(fake_font, font_size_px=16, convert_text_to_path=True)
        assert "stroke-width=" in svg
        assert "transform=" not in svg
        rects = [line for line in svg.splitlines() if "<rect x=" in line]
        assert len(rects) >= 2

    def test_coloured_underline_with_bold_italic(self, fake_font: FakeTTFont):
        s = (
            ANSIString("Hi")
            .fm(SGR.BOLD)
            .fm(SGR.ITALIC)
            .ul_24b(255, 128, 0)
            .fm(UnderlineMode.CURLY)
        )
        svg = s.to_svg(fake_font, font_size_px=16, convert_text_to_path=True)
        assert "stroke-width=" in svg
        assert "transform=" not in svg
        wavy = [
            line
            for line in svg.splitlines()
            if 'stroke="rgb(255, 128, 0)"' in line and " Q " in line
        ]
        assert len(wavy) >= 2


class TestPathModeUnderline:
    def test_sgr_underline_rect(self, fake_font: FakeTTFont):
        s = ANSIString("AB").fm(SGR.UNDERLINE)
        svg = s.to_svg(fake_font, font_size_px=16, convert_text_to_path=True)
        assert svg.count("<rect x=") >= 2

    def test_sgr_underline_fg_colour(self, fake_font: FakeTTFont):
        s = ANSIString("A").fg_24b(255, 0, 0).fm(SGR.UNDERLINE)
        svg = s.to_svg(fake_font, font_size_px=16, convert_text_to_path=True)
        rects = [line for line in svg.splitlines() if "<rect x=" in line]
        coloured = [r for r in rects if 'fill="rgb(255, 0, 0)"' in r]
        assert len(coloured) >= 1

    def test_sgr_underline_fallback_black(self, fake_font: FakeTTFont):
        s = ANSIString("A").fm(SGR.UNDERLINE)
        svg = s.to_svg(fake_font, font_size_px=16, convert_text_to_path=True)
        rects = [line for line in svg.splitlines() if "<rect x=" in line]
        assert any('fill="black"' in r for r in rects)

    def test_double_underline(self, fake_font: FakeTTFont):
        s = ANSIString("A").fm(SGR.DOUBLE_UNDERLINE)
        svg = s.to_svg(fake_font, font_size_px=16, convert_text_to_path=True)
        rects = [line for line in svg.splitlines() if "<rect x=" in line]
        assert len(rects) >= 2

    def test_coloured_single(self, fake_font: FakeTTFont):
        s = ANSIString("AB").ul_24b(0, 128, 255)
        svg = s.to_svg(fake_font, font_size_px=16, convert_text_to_path=True)
        rects = [line for line in svg.splitlines() if "<rect x=" in line]
        assert sum(1 for r in rects if 'fill="rgb(0, 128, 255)"' in r) >= 2

    def test_coloured_double(self, fake_font: FakeTTFont):
        s = ANSIString("A").ul_24b(255, 0, 0).fm(UnderlineMode.DOUBLE)
        svg = s.to_svg(fake_font, font_size_px=16, convert_text_to_path=True)
        rects = [line for line in svg.splitlines() if "<rect x=" in line]
        assert sum(1 for r in rects if 'fill="rgb(255, 0, 0)"' in r) >= 2

    def test_curly(self, fake_font: FakeTTFont):
        s = ANSIString("AB").ul_24b(0, 200, 0).fm(UnderlineMode.CURLY)
        svg = s.to_svg(fake_font, font_size_px=16, convert_text_to_path=True)
        wavy = [
            line for line in svg.splitlines() if "stroke=" in line and " Q " in line
        ]
        assert len(wavy) >= 2

    def test_dotted(self, fake_font: FakeTTFont):
        s = ANSIString("AB").ul_24b(128, 0, 255).fm(UnderlineMode.DOTTED)
        svg = s.to_svg(fake_font, font_size_px=16, convert_text_to_path=True)
        dots = [
            line
            for line in svg.splitlines()
            if "<circle " in line and 'fill="rgb(128, 0, 255)"' in line
        ]
        assert len(dots) >= 2

    def test_dashed(self, fake_font: FakeTTFont):
        s = ANSIString("AB").ul_24b(200, 100, 0).fm(UnderlineMode.DASHED)
        svg = s.to_svg(fake_font, font_size_px=16, convert_text_to_path=True)
        dashed = [line for line in svg.splitlines() if "stroke-dasharray=" in line]
        assert len(dashed) >= 2

    def test_no_underline_on_unstyled(self, fake_font: FakeTTFont):
        s = ANSIString("ABCD").fm(SGR.UNDERLINE, (0, 2))
        svg = s.to_svg(fake_font, font_size_px=16, convert_text_to_path=True)
        rects = [line for line in svg.splitlines() if "<rect x=" in line]
        assert len(rects) == 2
