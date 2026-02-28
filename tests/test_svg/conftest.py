"""Shared fixtures and helpers for SVG export tests."""

from typing import TYPE_CHECKING

import pytest
from fontTools.pens.svgPathPen import SVGPathPen  # type: ignore[import-untyped]

import pyansistring.pyansistring as pas
from pyansistring import ANSIString

if TYPE_CHECKING:
    from fontTools.ttLib import TTFont as _TTFontBase  # type: ignore[import-untyped]
else:
    _TTFontBase = object

__all__ = [
    "FakeTTFont",
    "FakeGlyph",
    "FakeGlyphSet",
    "FakeHead",
    "FakeHhea",
    "FakeHmtx",
    "FakeName",
    "FakePost",
]


class FakeGlyph:
    def __init__(self, width: int = 600, *, marker: int = 0) -> None:
        self.width = width
        self._marker = marker

    def draw(self, pen: SVGPathPen) -> None:
        """Draw a small rectangle whose coordinates encode *marker*.

        This lets tests distinguish which glyph set (font variant) was
        actually used: each variant gets a different marker value, and
        the resulting SVG path data will differ accordingly.
        A marker of `0` produces no path commands (backward compat).
        """
        if self._marker == 0:
            return
        m = self._marker
        pen.moveTo((m, 0))
        pen.lineTo((m, m))
        pen.lineTo((0, m))
        pen.lineTo((0, 0))
        pen.closePath()


class FakeGlyphSet(dict[str, FakeGlyph]):
    """dict subclass so `glyph_set[name]` and `glyph_set.get()` work."""

    pass


class FakeHead:
    unitsPerEm = 1000


class FakeHhea:
    ascent = 800
    descent = -200
    lineGap = 200


class FakeHmtx:
    def __getitem__(self, key: str):
        return (600, 0)  # (advance_width, lsb)


class FakeName:
    def getDebugName(self, _):
        return "FakeFont"


class FakePost:
    underlinePosition = -100
    underlineThickness = 50


class FakeTTFont(_TTFontBase):
    """Lightweight stand-in for `fontTools.ttLib.TTFont`.

    Supports the `"fvar" in font` check (always `False` since
    this fake font is not variable).

    Pass *glyph_marker* to make every glyph draw a small rectangle
    whose coordinates encode the marker – useful for verifying which
    font variant was actually selected.
    """

    def __init__(
        self,
        *,
        tables: dict[str, object] | None = None,
        glyph_marker: int = 0,
        glyph_width: int = 600,
    ) -> None:
        self._tables = tables or {
            "head": FakeHead(),
            "hhea": FakeHhea(),
            "hmtx": FakeHmtx(),
            "name": FakeName(),
            "post": FakePost(),
        }
        self._glyph_marker = glyph_marker
        self._glyph_width = glyph_width

    def __getitem__(self, key: str):
        return self._tables[key]

    def __contains__(self, key: str) -> bool:
        return key in self._tables

    def getBestCmap(self, cmapPreferences: object = None) -> dict[int, str]:  # type: ignore[override]
        return {}  # all chars fall back to .notdef

    def getGlyphSet(  # type: ignore[override]
        self, *, location: dict[str, float] | None = None, **_kw: object
    ) -> FakeGlyphSet:
        return FakeGlyphSet(
            {
                ".notdef": FakeGlyph(self._glyph_width, marker=self._glyph_marker),
            }
        )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_font() -> FakeTTFont:
    """Return a *FakeTTFont* instance and enable the fonttools guard."""
    pas.is_fonttools_available = True
    return FakeTTFont()


@pytest.fixture
def styled_hello(fake_font: FakeTTFont) -> tuple[ANSIString, FakeTTFont]:
    """A five-character red string paired with the fake font."""
    return ANSIString("Hello").fg_24b(255, 0, 0), fake_font


@pytest.fixture
def partially_styled(fake_font: FakeTTFont) -> tuple[ANSIString, FakeTTFont]:
    """`Hello, World!` with only 'Hello' coloured red."""
    return ANSIString("Hello, World!").fg_24b(255, 0, 0, (0, 5)), fake_font
