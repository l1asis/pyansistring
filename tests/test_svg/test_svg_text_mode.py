"""Tests for SVG export in text mode (default: convert_text_to_path=False)."""

import pathlib

from pyansistring import ANSIString
from pyansistring.constants import SGR
from tests.test_svg.conftest import FakeTTFont


class TestSvgTextModeStructure:
    """Basic SVG structure checks in text mode."""

    def test_svg_wrapper(self, styled_hello: tuple[ANSIString, FakeTTFont]):
        s, font = styled_hello
        svg = s.to_svg(font, font_size_px=16)
        assert "<svg " in svg
        assert "</svg>" in svg

    def test_font_family_attribute(self, styled_hello: tuple[ANSIString, FakeTTFont]):
        s, font = styled_hello
        svg = s.to_svg(font, font_size_px=16)
        assert 'font-family="FakeFont"' in svg

    def test_viewbox_present(self, styled_hello: tuple[ANSIString, FakeTTFont]):
        s, font = styled_hello
        svg = s.to_svg(font, font_size_px=16)
        assert "viewBox=" in svg

    def test_width_height_present(self, styled_hello: tuple[ANSIString, FakeTTFont]):
        s, font = styled_hello
        svg = s.to_svg(font, font_size_px=16)
        assert 'width="' in svg
        assert 'height="' in svg


class TestSvgTextModeForeground:
    def test_full_fg_fill_count(self, styled_hello: tuple[ANSIString, FakeTTFont]):
        s, font = styled_hello
        svg = s.to_svg(font, font_size_px=16)
        assert svg.count('fill="rgb(255, 0, 0)"') == len("Hello")

    def test_partial_fg_fill_count(
        self, partially_styled: tuple[ANSIString, FakeTTFont]
    ):
        s, font = partially_styled
        svg = s.to_svg(font, font_size_px=16)
        assert svg.count('fill="rgb(255, 0, 0)"') == 5

    def test_unstyled_chars_have_tspan(
        self, partially_styled: tuple[ANSIString, FakeTTFont]
    ):
        s, font = partially_styled
        svg = s.to_svg(font, font_size_px=16)
        # Unstyled characters still produce <tspan>
        assert "<tspan>,</tspan>" in svg


class TestSvgTextModeBackground:
    def test_bg_rect_present(self, fake_font: FakeTTFont):
        s = ANSIString("Hi").bg((0, 255, 0))
        svg = s.to_svg(fake_font, font_size_px=16)
        assert "<rect " in svg
        assert 'fill="rgb(0, 255, 0)"' in svg

    def test_transparent_background(self, fake_font: FakeTTFont):
        s = ANSIString("Hi").fg((255, 0, 0))
        svg = s.to_svg(fake_font, font_size_px=16, transparent_background=True)
        # Should not have a full-width background rect
        # But may have per-char bg rects if per-char bg is set
        assert "<svg " in svg

    def test_opaque_background_color(self, fake_font: FakeTTFont):
        s = ANSIString("Hi").fg((255, 0, 0))
        svg = s.to_svg(
            fake_font,
            font_size_px=16,
            transparent_background=False,
            background_color=(30, 30, 30),
        )
        assert 'fill="rgb(30, 30, 30)"' in svg


class TestSvgTextModeAttributes:
    def test_bold_font_weight(self, fake_font: FakeTTFont):
        s = ANSIString("Hi").style(SGR.BOLD).fg((0, 0, 0))
        svg = s.to_svg(fake_font, font_size_px=16)
        assert "font-weight" in svg

    def test_italic_font_style(self, fake_font: FakeTTFont):
        s = ANSIString("Hi").style(SGR.ITALIC).fg((0, 0, 0))
        svg = s.to_svg(fake_font, font_size_px=16)
        assert "font-style" in svg


class TestSvgTextModeOutputFile:
    def test_output_file_written(self, fake_font: FakeTTFont, tmp_path: pathlib.Path):
        s = ANSIString("Hi").fg((255, 0, 0))
        out = tmp_path / "test.svg"
        svg = s.to_svg(fake_font, font_size_px=16, output_file=str(out))
        assert out.exists()
        assert out.read_text(encoding="utf-8") == svg
