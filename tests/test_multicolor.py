"""Tests for ANSIString.multicolor() and multicolor_c()."""

import pytest

from pyansistring import ANSIString
from pyansistring.constants import MulticolorSequences

ALPHABET = "abcdefghijklmnopqrstuvwxyz"


@pytest.fixture
def alpha_string():
    """Plain 26-char alphabet ANSIString."""
    return ANSIString(ALPHABET)


class TestMulticolorBuiltin:
    """Builtin multicolor sequences produce deterministic style maps."""

    @pytest.mark.parametrize(
        "sequence",
        [
            pytest.param(MulticolorSequences.RAINBOW, id="rainbow"),
            pytest.param(MulticolorSequences.REVERSED_RAINBOW, id="reversed-rainbow"),
        ],
    )
    def test_styles_all_chars(self, alpha_string: ANSIString, sequence: str):
        s = alpha_string.multicolor(sequence)
        assert len(s.style_manager) == len(ALPHABET), (
            f"{sequence!r} should style every character"
        )

    def test_rainbow_and_reversed_are_mirrors(self):
        fwd = ANSIString(ALPHABET).multicolor(MulticolorSequences.RAINBOW)
        rev = ANSIString(ALPHABET).multicolor(MulticolorSequences.REVERSED_RAINBOW)
        fwd_values = list(fwd.style_manager.values())
        rev_values = list(rev.style_manager.values())
        assert fwd_values == list(reversed(rev_values)), (
            "RAINBOW and REVERSED_RAINBOW should be exact mirrors"
        )


_CUSTOM_CMD = "r=84:|g=161:|b=255: $ r+9:minmax(0,inf)|g+4:minmax(0,inf) &*"
_CUSTOM_CMD_REVERSE = _CUSTOM_CMD.replace("&*", "@&*")
_CUSTOM_CMD_MIRROR = (
    "r=84:|g=161:|b=255: $ r+50:minmax(0,inf)|g+25:minmax(0,inf)"
    " # b-70:minmax(0,inf) !&*"
)


class TestMulticolorCustom:
    """Custom multicolor command strings."""

    @pytest.mark.parametrize(
        "cmd, description",
        [
            pytest.param(_CUSTOM_CMD, "skipfirst (*)", id="skipfirst"),
            pytest.param(_CUSTOM_CMD_MIRROR, "mirror (!)", id="mirror"),
        ],
    )
    def test_custom_cmd_styles_all(
        self, alpha_string: ANSIString, cmd: str, description: str
    ):
        s = alpha_string.multicolor(cmd)
        assert len(s.style_manager) == len(ALPHABET), (
            f"Custom cmd ({description}) should style every character"
        )

    def test_reverse_flag(self):
        """The '@' flag reverses the multicolour direction."""
        fwd = ANSIString(ALPHABET).multicolor(_CUSTOM_CMD)
        rev = ANSIString(ALPHABET).multicolor(_CUSTOM_CMD_REVERSE)
        fwd_values = list(fwd.style_manager.values())
        rev_values = list(rev.style_manager.values())
        assert fwd_values == list(reversed(rev_values)), (
            "@ flag should reverse color direction"
        )

    def test_explicit_slice(self, alpha_string: ANSIString):
        s = alpha_string.multicolor(
            MulticolorSequences.RAINBOW,
            *((i, i + 1) for i in range(10)),
        )
        assert len(s.style_manager) == 10, (
            "Explicit slices should limit multicolor to 10 chars"
        )


class TestMulticolorC:
    """multicolor_c — coordinate-based multicolor."""

    def test_same_as_multicolor_on_multiline(self):
        multi = ANSIString("Hello, \nWorld!\n It's pyansistring!")
        s_c = multi.multicolor_c(MulticolorSequences.RAINBOW).style_manager.values()
        flat = (
            ANSIString("Hello, World! It's pyansistring!")
            .multicolor(MulticolorSequences.RAINBOW)
            .style_manager.values()
        )
        for idx, (a, e) in enumerate(zip(s_c, flat)):
            assert a == e, (
                f"multicolor_c style at position {idx} differs from flat multicolor"
            )
