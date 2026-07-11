"""Tests for StyleManager."""

import pytest

from pyansistring import StyleManager
from pyansistring.color import Color
from pyansistring.constants import Foreground
from pyansistring.style import Style


@pytest.fixture
def red_style():
    """A Style with 4-bit red foreground."""
    return Style(foreground=Color.from_4bit(Foreground.RED))


@pytest.fixture
def populated_manager(red_style: Style):
    """A StyleManager with one entry at index 0, modification flag reset."""
    sm = StyleManager()
    sm[0] = red_style
    sm.pop_modified()  # consume the flag
    return sm


class TestStyleManagerBasics:
    """Construction, repr, type enforcement."""

    def test_empty_manager(self, empty_style_manager: StyleManager):
        assert len(empty_style_manager) == 0, "New StyleManager should be empty"
        assert not empty_style_manager, "Empty StyleManager should be falsy"

    def test_repr(self, empty_style_manager: StyleManager):
        assert "StyleManager" in repr(empty_style_manager), (
            "repr must mention StyleManager"
        )

    def test_rejects_non_style_values(self, empty_style_manager: StyleManager):
        with pytest.raises(TypeError):
            empty_style_manager[0] = "not a style"

    def test_accepts_style_values(
        self, empty_style_manager: StyleManager, red_style: Style
    ):
        empty_style_manager[0] = red_style
        assert empty_style_manager[0] == red_style, "Stored Style should match input"


class TestStyleManagerModificationTracking:
    """has_changes property."""

    def test_initially_unmodified(self, empty_style_manager: StyleManager):
        assert empty_style_manager.pop_modified() is False, (
            "New StyleManager should not be marked modified"
        )

    @pytest.mark.parametrize(
        "operation",
        [
            pytest.param("setitem", id="setitem"),
            pytest.param("delitem", id="delitem"),
            pytest.param("clear", id="clear"),
        ],
    )
    def test_mutating_operations_mark_modified(
        self, populated_manager: StyleManager, operation: str
    ):
        if operation == "setitem":
            populated_manager[1] = Style()
        elif operation == "delitem":
            del populated_manager[0]
        elif operation == "clear":
            populated_manager.clear()
        assert populated_manager.pop_modified() is True, (
            f"{operation} should mark StyleManager as modified"
        )

    def test_accessing_flag_resets_it(self, empty_style_manager: StyleManager):
        empty_style_manager[0] = Style()
        assert empty_style_manager.pop_modified() is True
        assert empty_style_manager.pop_modified() is False, (
            "Second access should return False (flag auto-resets)"
        )


class TestStyleManagerCopy:
    def test_copy_is_independent(
        self, populated_manager: StyleManager, red_style: Style
    ):
        sm2 = populated_manager.copy()
        assert sm2[0] == red_style, "Copy should contain same styles"
        del sm2[0]
        assert 0 in populated_manager, "Deleting from copy must not affect original"


class TestStyleManagerRemapStyles:
    """remap_styles for alignment operations."""

    @pytest.mark.parametrize(
        "visible_only, expected_key",
        [
            pytest.param(True, 2, id="visible-only"),
            pytest.param(False, 2, id="all"),
        ],
    )
    def test_remap_pads(self, red_style: Style, visible_only: bool, expected_key: int):
        sm = StyleManager()
        sm[0] = red_style
        result = sm.remap("Hello", "  Hello  ", visible_only=visible_only)
        assert expected_key in result, (
            f"Key {expected_key} must be present after"
            f" remap (visible_only={visible_only})"
        )

    def test_remap_same_string(self, red_style: Style):
        sm = StyleManager()
        sm[0] = red_style
        result = sm.remap("Hi", "Hi")
        assert result == {0: red_style}, (
            "Remap with identical strings should be identity"
        )

    def test_remap_raises_if_not_found(self, empty_style_manager: StyleManager):
        with pytest.raises(ValueError):
            empty_style_manager.remap("abc", "xyz")
