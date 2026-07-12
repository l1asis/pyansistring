"""Tests for Color class."""

from colorsys import rgb_to_hls
from typing import Any, Callable, Literal

import pytest

from pyansistring.color import Color, ColorMap, ColorScale, SegmentedColorMap
from pyansistring.constants import Foreground, Underline


class TestColorConstruction:
    """Color(...) creation and truthiness."""

    def test_unset_color_is_falsy(self):
        c = Color()
        assert not c, "Unset Color should be falsy"
        assert c.depth is None, "Unset Color.depth must be None"
        assert c.value is None, "Unset Color.value must be None"

    def test_unset_classmethod(self):
        c = Color.unset()
        assert not c, "Color.unset() should produce a falsy Color"

    @pytest.mark.parametrize(
        "factory, args, expected_depth, expected_value",
        [
            pytest.param(
                Color.from_4bit,
                (Foreground.RED,),
                "4bit",
                Foreground.RED.value,
                id="4bit-red",
            ),
            pytest.param(
                Color.from_4bit,
                (Foreground.GREEN,),
                "4bit",
                Foreground.GREEN.value,
                id="4bit-green",
            ),
            pytest.param(Color.from_8bit, (135,), "8bit", 135, id="8bit-135"),
            pytest.param(Color.from_8bit, (200,), "8bit", 200, id="8bit-200"),
            pytest.param(
                Color.from_24bit, (10, 20, 30), "24bit", (10, 20, 30), id="24bit-rgb"
            ),
            pytest.param(
                Color.from_24bit, (0, 0, 0), "24bit", (0, 0, 0), id="24bit-black"
            ),
            pytest.param(
                Color.from_24bit,
                (255, 255, 255),
                "24bit",
                (255, 255, 255),
                id="24bit-white",
            ),
        ],
    )
    def test_factory_methods(
        self,
        factory: Callable[[Any], Color],
        args: tuple[Foreground | int, ...],
        expected_depth: str,
        expected_value: tuple[int, int, int] | int,
    ):
        c = factory(*args)
        assert c, f"Color created via {factory.__name__}{args} should be truthy"
        assert c.depth == expected_depth, (
            f"Expected depth {expected_depth!r}, got {c.depth!r}"
        )
        assert c.value == expected_value, (
            f"Expected value {expected_value!r}, got {c.value!r}"
        )

    def test_invalid_mode_ignored(self):
        with pytest.raises(ValueError, match="Invalid Color state"):
            Color("invalid", 42)  # type: ignore

    def test_enum_value_unwrapped(self):
        c = Color("4bit", Foreground.GREEN)
        assert c.value == Foreground.GREEN.value, (
            "Enum values should be unwrapped to int"
        )


class TestColorEquality:
    def test_same_colors_equal(self):
        assert Color.from_8bit(100) == Color.from_8bit(100), (
            "Identical 8-bit Colors must be equal"
        )

    def test_different_colors_not_equal(self):
        assert Color.from_8bit(100) != Color.from_8bit(101), (
            "Different 8-bit Colors must differ"
        )

    def test_not_equal_to_non_color(self):
        assert Color.from_8bit(100).__eq__("foo") is NotImplemented

    def test_hashing(self):
        s = {Color.from_8bit(1), Color.from_8bit(1), Color.from_8bit(2)}
        assert len(s) == 2, "Set of Colors should deduplicate equal instances"


class TestColorSGRParam:
    """Color.to_sgr_param() output."""

    def test_4bit_foreground(self):
        c = Color.from_4bit(Foreground.RED)
        assert c.to_sgr_param() == str(Foreground.RED.value)

    @pytest.mark.parametrize(
        "color, prefix, expected_fragment",
        [
            pytest.param(
                Color.from_8bit(135), str(Foreground.SET), "135", id="8bit-fg"
            ),
            pytest.param(Color.from_8bit(0), str(Foreground.SET), "0", id="8bit-fg-0"),
        ],
    )
    def test_8bit_with_prefix(self, color: Color, prefix: str, expected_fragment: str):
        out = color.to_sgr_param(prefix)
        assert "5" in out, "8-bit SGR must contain '5' marker"
        assert expected_fragment in out, f"Expected {expected_fragment!r} in {out!r}"

    def test_24bit_standard(self):
        c = Color.from_24bit(10, 20, 30)
        out = c.to_sgr_param(str(Foreground.SET))
        assert "2" in out and "10" in out, (
            f"24-bit standard format missing components: {out}"
        )

    def test_24bit_compatible(self):
        c = Color.from_24bit(10, 20, 30)
        out = c.to_sgr_param(str(Foreground.SET), separator=";")
        assert ";" in out, "Compatible format must use semicolons"

    def test_unset_returns_empty(self):
        assert Color().to_sgr_param() == "", (
            "Unset Color should produce empty SGR param"
        )


class TestColorToRGB:
    @pytest.mark.parametrize(
        "color, expected",
        [
            pytest.param(Color.from_24bit(1, 2, 3), (1, 2, 3), id="24bit-passthrough"),
            pytest.param(Color(), (0, 0, 0), id="unset-defaults-black"),
        ],
    )
    def test_known_rgb(self, color: Color, expected: tuple[int, int, int]):
        assert color.to_rgb() == expected, f"Expected {expected}, got {color.to_rgb()}"

    @pytest.mark.parametrize(
        "color",
        [
            pytest.param(Color.from_8bit(0), id="8bit"),
            pytest.param(Color.from_4bit(Foreground.RED), id="4bit"),
        ],
    )
    def test_returns_3_tuple_of_ints(self, color: Color):
        rgb = color.to_rgb()
        assert isinstance(rgb, tuple) and len(rgb) == 3, f"Expected 3-tuple, got {rgb}"
        assert all(isinstance(v, int) for v in rgb), (
            f"All RGB values must be int, got {rgb}"
        )


class TestColorToHSL:
    """Color.to_hsl() conversion contract."""

    @pytest.mark.parametrize(
        "color",
        [
            pytest.param(Color.from_24bit(255, 0, 0), id="24bit-red"),
            pytest.param(Color.from_8bit(135), id="8bit"),
            pytest.param(Color.from_4bit(Foreground.BLUE), id="4bit"),
        ],
    )
    def test_matches_colorsys_from_to_rgb(self, color: Color):
        expected = rgb_to_hls(*map(lambda x: x / 255, color.to_rgb()))
        actual = color.to_hsl()
        assert (actual[0], actual[2], actual[1]) == expected, (
            "to_hsl() should match colorsys.rgb_to_hls on the resolved RGB value"
        )

    def test_theme_argument_is_applied(self):
        color = Color.from_4bit(Foreground.RED)
        expected = rgb_to_hls(*map(lambda x: x / 255, color.to_rgb("vga")))
        actual = color.to_hsl("vga")
        assert (actual[0], actual[2], actual[1]) == expected

    def test_returns_3_tuple_of_floats(self):
        hsl = Color.from_24bit(12, 34, 56).to_hsl()
        assert isinstance(hsl, tuple) and len(hsl) == 3
        assert all(isinstance(v, float) for v in hsl)


class TestColorScale:
    """ColorScale.interpolate() behaviour in rgb and hsl spaces."""

    def test_empty_scale_returns_unset(self):
        scale = ColorScale([], "rgb")
        assert scale.interpolate(0.5) == Color.unset()

    def test_invalid_space_raises_value_error(self):
        scale = ColorScale([(0, 0, 0), (255, 255, 255)], "lab")  # type: ignore
        with pytest.raises(ValueError, match="Unsupported color space"):
            scale.interpolate(0.5)

    @pytest.mark.parametrize(
        "t, expected",
        [
            pytest.param(0.0, (255, 0, 0), id="left-end"),
            pytest.param(0.25, (128, 128, 0), id="quarter-point"),
            pytest.param(0.5, (0, 255, 0), id="midpoint"),
            pytest.param(0.75, (0, 128, 128), id="three-quarters"),
            pytest.param(1.0, (0, 0, 255), id="right-end"),
        ],
    )
    def test_rgb_interpolation_three_stops(
        self, t: float, expected: tuple[int, int, int]
    ):
        scale = ColorScale([(255, 0, 0), (0, 255, 0), (0, 0, 255)], "rgb")
        out = scale.interpolate(t)
        assert out.depth == "24bit"
        assert out.value == expected

    @pytest.mark.parametrize(
        "t, expected",
        [
            pytest.param(0.0, (255, 0, 0), id="left-end"),
            pytest.param(0.25, (255, 255, 0), id="quarter-point"),
            pytest.param(0.5, (0, 255, 0), id="midpoint"),
            pytest.param(0.75, (0, 255, 255), id="three-quarters"),
            pytest.param(1.0, (0, 0, 255), id="right-end"),
        ],
    )
    def test_hsl_interpolation_three_stops(
        self, t: float, expected: tuple[int, int, int]
    ):
        scale = ColorScale([(255, 0, 0), (0, 255, 0), (0, 0, 255)], "hsl")
        out = scale.interpolate(t)
        assert out.depth == "24bit"
        assert out.value == expected

    @pytest.mark.parametrize(
        "t, expected",
        [
            pytest.param(-1.0, (255, 0, 0), id="clamp-left"),
            pytest.param(2.0, (0, 0, 255), id="clamp-right"),
        ],
    )
    def test_rgb_clamps_t_to_range(self, t: float, expected: tuple[int, int, int]):
        scale = ColorScale([(255, 0, 0), (0, 0, 255)], "rgb")
        assert scale.interpolate(t).value == expected

    def test_accepts_color_instances(self):
        scale = ColorScale(
            [Color.from_24bit(0, 0, 0), Color.from_24bit(255, 255, 255)], "rgb"
        )
        assert scale.interpolate(0.5).value == (128, 128, 128)

    def test_hsl_interpolation_accepts_mixed_stop_types(self):
        scale = ColorScale(
            [Color.from_24bit(255, 0, 0), (0, 255, 0), Color.from_24bit(0, 0, 255)],
            "hsl",
        )
        assert scale.interpolate(0.75).value == (0, 255, 255)

    @pytest.mark.parametrize("space", ["rgb", "hsl"])
    def test_single_stop_returns_same_color(self, space: Literal["rgb", "hsl"]):
        scale = ColorScale([Color.from_24bit(10, 20, 30)], space)
        assert scale.interpolate(0.25).value == (10, 20, 30)

    def test_hsl_interpolation_returns_24bit_color(self):
        scale = ColorScale([(255, 0, 0), (0, 255, 0)], "hsl")
        out = scale.interpolate(0.5)
        assert out.depth == "24bit"
        assert isinstance(out.value, tuple) and len(out.value) == 3
        assert all(isinstance(v, int) for v in out.value)

    @pytest.mark.parametrize(
        "space,t",
        [
            pytest.param("rgb", -0.5, id="rgb-clamp-left"),
            pytest.param("rgb", 0.25, id="rgb-mid"),
            pytest.param("rgb", 1.5, id="rgb-clamp-right"),
            pytest.param("hsl", -0.5, id="hsl-clamp-left"),
            pytest.param("hsl", 0.25, id="hsl-mid"),
            pytest.param("hsl", 1.5, id="hsl-clamp-right"),
        ],
    )
    def test_interpolate_rgb_matches_interpolate(self, space: str, t: float):
        scale = ColorScale([(255, 0, 0), (0, 255, 0), (0, 0, 255)], space)  # type: ignore[arg-type]
        assert scale.interpolate_rgb(t) == scale.interpolate(t).to_rgb()


class TestColorMap:
    """ColorMap.__call__ behavior, boundaries, and constructor coercion."""

    @staticmethod
    def _scale() -> ColorScale:
        return ColorScale([(255, 0, 0), (0, 0, 255)], "rgb")

    def test_under_color_applied_below_vmin(self):
        cmap = ColorMap(
            self._scale(),
            vmin=0,
            vmax=10,
            under_color=(1, 2, 3),
        )
        assert cmap(-0.01) == Color.from_24bit(1, 2, 3)

    def test_over_color_applied_above_vmax(self):
        cmap = ColorMap(
            self._scale(),
            vmin=0,
            vmax=10,
            over_color=Color.from_24bit(9, 8, 7),
        )
        assert cmap(10.01) == Color.from_24bit(9, 8, 7)

    @pytest.mark.parametrize(
        "value, expected",
        [
            pytest.param(0, (255, 0, 0), id="at-vmin"),
            pytest.param(2.5, (191, 0, 64), id="quarter"),
            pytest.param(5, (128, 0, 128), id="mid"),
            pytest.param(7.5, (64, 0, 191), id="three-quarters"),
            pytest.param(10, (0, 0, 255), id="at-vmax"),
        ],
    )
    def test_linear_mapping_within_range(
        self, value: float, expected: tuple[int, int, int]
    ):
        cmap = ColorMap(self._scale(), vmin=0, vmax=10)
        assert cmap(value).value == expected

    @pytest.mark.parametrize(
        "value, expected",
        [
            pytest.param(-999, (255, 0, 0), id="below-without-under"),
            pytest.param(999, (0, 0, 255), id="above-without-over"),
        ],
    )
    def test_out_of_range_clamps_when_no_under_or_over(
        self, value: float, expected: tuple[int, int, int]
    ):
        cmap = ColorMap(self._scale(), vmin=0, vmax=10)
        assert cmap(value).value == expected

    def test_equal_vmin_vmax_returns_midpoint_without_under_or_over(self):
        cmap = ColorMap(self._scale(), vmin=5, vmax=5)
        assert cmap(5).value == (128, 0, 128)
        assert cmap(-100).value == (128, 0, 128)
        assert cmap(100).value == (128, 0, 128)

    def test_equal_vmin_vmax_still_honors_under_and_over(self):
        cmap = ColorMap(
            self._scale(),
            vmin=5,
            vmax=5,
            under_color=(1, 1, 1),
            over_color=(2, 2, 2),
        )
        assert cmap(4) == Color.from_24bit(1, 1, 1)
        assert cmap(6) == Color.from_24bit(2, 2, 2)
        assert cmap(5).value == (128, 0, 128)

    def test_constructor_coerces_tuple_under_and_over_colors(self):
        cmap = ColorMap(
            self._scale(),
            vmin=0,
            vmax=1,
            under_color=(10, 20, 30),
            over_color=(40, 50, 60),
        )
        assert cmap.under_color == Color.from_24bit(10, 20, 30)
        assert cmap.over_color == Color.from_24bit(40, 50, 60)


class TestColorDownsampling:
    """Color.downsample() math and palette snapping."""

    def test_24bit_to_8bit(self):
        c = Color.from_24bit(10, 20, 30)
        downsampled = c.downsample("8bit")
        assert downsampled.depth == "8bit"
        assert isinstance(downsampled.value, int)

    def test_24bit_to_4bit(self):
        c = Color.from_24bit(255, 0, 0)  # Red
        downsampled = c.downsample("4bit", prefix=Foreground.SET)
        assert downsampled.depth == "4bit"
        assert downsampled.value == Foreground.RED.value

    def test_8bit_to_4bit(self):
        c = Color.from_8bit(135)
        downsampled = c.downsample("4bit", prefix=Foreground.SET)
        assert downsampled.depth == "4bit"
        assert downsampled.value == Foreground.BRIGHT_MAGENTA.value

    def test_downsample_invalid_returns_unset(self):
        c = Color.from_4bit(Foreground.RED)
        assert not c.downsample("4bit")

        c8 = Color.from_8bit(10)
        assert not c8.downsample("8bit")

    def test_underline_cannot_be_downsampled_to_4bit(self):
        c = Color.from_24bit(255, 0, 0)
        assert not c.downsample("4bit", prefix=Underline.SET)


class TestSegmentedColorMap:
    """SegmentedColorMap threshold behavior and edge cases."""

    @pytest.mark.parametrize(
        "value, expected",
        [
            pytest.param(-1, (255, 0, 0), id="below-first-threshold"),
            pytest.param(10, (255, 0, 0), id="exact-first-threshold"),
            pytest.param(15, (0, 255, 0), id="between-first-and-second"),
            pytest.param(20, (0, 255, 0), id="exact-second-threshold"),
            pytest.param(29.9, (0, 0, 255), id="before-third-threshold"),
            pytest.param(30, (0, 0, 255), id="exact-third-threshold"),
            pytest.param(31, (0, 0, 255), id="above-last-no-over"),
        ],
    )
    def test_threshold_mapping_with_bisect_left_semantics(
        self, value: float, expected: tuple[int, int, int]
    ):
        cmap = SegmentedColorMap(
            {
                10: (255, 0, 0),
                20: (0, 255, 0),
                30: (0, 0, 255),
            }
        )
        assert cmap(value).value == expected

    def test_unsorted_input_segments_are_sorted_internally(self):
        cmap = SegmentedColorMap(
            {
                30: (0, 0, 255),
                10: (255, 0, 0),
                20: (0, 255, 0),
            }
        )
        assert cmap(15).value == (0, 255, 0)

    def test_over_color_is_used_above_last_threshold(self):
        cmap = SegmentedColorMap(
            {10: (255, 0, 0), 20: (0, 255, 0)},
            over_color=(12, 34, 56),
        )
        assert cmap(999) == Color.from_24bit(12, 34, 56)

    def test_constructor_coerces_segment_and_over_colors(self):
        cmap = SegmentedColorMap(
            {
                0: Color.from_24bit(1, 2, 3),
                1: (4, 5, 6),
            },
            over_color=(7, 8, 9),
        )
        assert cmap(0) == Color.from_24bit(1, 2, 3)
        assert cmap(1) == Color.from_24bit(4, 5, 6)
        assert cmap.over_color == Color.from_24bit(7, 8, 9)

    def test_empty_segments_raises_index_error_on_call(self):
        cmap = SegmentedColorMap({})
        with pytest.raises(IndexError):
            cmap(0)
