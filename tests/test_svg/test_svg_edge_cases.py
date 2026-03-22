"""Edge-case tests for SVG export (both text and path modes)."""

import pytest

import pyansistring.pyansistring as pas
from pyansistring import ANSIString
from pyansistring.constants import SGR
from tests.test_svg.conftest import FakeTTFont


@pytest.fixture
def fake_font():
    pas.is_fonttools_available = True
    return FakeTTFont()


class TestEmptyStrings:
    def test_empty_string_text_mode(self, fake_font: FakeTTFont):
        s = ANSIString("")
        svg = s.to_svg(fake_font, font_size_px=16)
        assert "<svg " in svg
        assert "</svg>" in svg

    def test_empty_string_path_mode(self, fake_font: FakeTTFont):
        s = ANSIString("")
        svg = s.to_svg(fake_font, font_size_px=16, convert_text_to_path=True)
        assert "<svg " in svg
        assert "</svg>" in svg

    def test_whitespace_only(self, fake_font: FakeTTFont):
        s = ANSIString("   ")
        svg = s.to_svg(fake_font, font_size_px=16)
        assert "<svg " in svg


class TestSpecialChars:
    @pytest.mark.parametrize(
        "char,entity",
        [
            ("&", "&amp;"),
            ("<", "&lt;"),
            (">", "&gt;"),
        ],
    )
    def test_html_entity_escaping_text_mode(
        self, fake_font: FakeTTFont, char: str, entity: str
    ):
        s = ANSIString(char)
        svg = s.to_svg(fake_font, font_size_px=16)
        assert entity in svg

    def test_mixed_special_chars(self, fake_font: FakeTTFont):
        s = ANSIString("a<b&c>d").fg_24b(255, 0, 0)
        svg = s.to_svg(fake_font, font_size_px=16)
        assert "&amp;" in svg
        assert "&lt;" in svg
        assert "&gt;" in svg


class TestMultiLine:
    def test_multiline_text_mode(self, fake_font: FakeTTFont):
        s = ANSIString("Hello\nWorld").fg_24b(255, 0, 0)
        svg = s.to_svg(fake_font, font_size_px=16)
        assert "<svg " in svg
        # Two lines are rendered as <tspan> rows inside a single <text>
        assert svg.count("<tspan x=") == 2

    def test_multiline_path_mode(self, fake_font: FakeTTFont):
        s = ANSIString("AB\nCD").fg_24b(0, 255, 0)
        svg = s.to_svg(fake_font, font_size_px=16, convert_text_to_path=True)
        assert "<svg " in svg
        assert "<path " in svg

    def test_multiline_height_grows(self, fake_font: FakeTTFont):
        s1 = ANSIString("Line1").fg_24b(0, 0, 0)
        s2 = ANSIString("Line1\nLine2").fg_24b(0, 0, 0)
        svg1 = s1.to_svg(fake_font, font_size_px=16)
        svg2 = s2.to_svg(fake_font, font_size_px=16)
        h1 = float(svg1.split('height="')[1].split('"')[0])
        h2 = float(svg2.split('height="')[1].split('"')[0])
        assert h2 > h1


class TestNestedStyles:
    def test_bold_and_fg_text_mode(self, fake_font: FakeTTFont):
        s = ANSIString("Hello").style(SGR.BOLD).fg_24b(255, 0, 0)
        svg = s.to_svg(fake_font, font_size_px=16)
        assert 'fill="rgb(255, 0, 0)"' in svg
        assert "font-weight" in svg

    def test_bold_and_fg_path_mode(self, fake_font: FakeTTFont):
        s = ANSIString("Hello").style(SGR.BOLD).fg_24b(255, 0, 0)
        svg = s.to_svg(fake_font, font_size_px=16, convert_text_to_path=True)
        assert 'fill="rgb(255, 0, 0)"' in svg
        assert "stroke-width=" in svg

    def test_fg_bg_underline_combined(self, fake_font: FakeTTFont):
        s = ANSIString("X").fg_24b(255, 0, 0).bg_24b(0, 255, 0).ul_24b(0, 0, 255)
        svg = s.to_svg(fake_font, font_size_px=16, convert_text_to_path=True)
        assert 'fill="rgb(255, 0, 0)"' in svg  # foreground
        assert 'fill="rgb(0, 255, 0)"' in svg  # background rect
        assert 'fill="rgb(0, 0, 255)"' in svg  # underline

    def test_partial_styles_adjacent(self, fake_font: FakeTTFont):
        """Adjacent chars with different styles."""
        s = ANSIString("ABCD").fg_24b(255, 0, 0, (0, 2)).fg_24b(0, 0, 255, (2, 4))
        svg = s.to_svg(fake_font, font_size_px=16)
        assert svg.count('fill="rgb(255, 0, 0)"') == 2
        assert svg.count('fill="rgb(0, 0, 255)"') == 2


class TestFonttoolsGuard:
    def test_raises_when_fonttools_disabled(self):
        pas.is_fonttools_available = False
        s = ANSIString("Hi")
        with pytest.raises(ImportError):
            s.to_svg(None, font_size_px=16)  # type: ignore[arg-type]


class TestModeParity:
    def test_both_modes_contain_svg_tags(self, fake_font: FakeTTFont):
        s = ANSIString("Hello").fg_24b(255, 0, 0).style(SGR.BOLD)
        for mode in (False, True):
            svg = s.to_svg(fake_font, font_size_px=16, convert_text_to_path=mode)
            assert "<svg " in svg
            assert "</svg>" in svg
            assert 'fill="rgb(255, 0, 0)"' in svg
