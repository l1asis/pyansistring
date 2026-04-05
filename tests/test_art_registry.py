from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from pyansistring import (
    DEFAULT_ART_REGISTRY,
    ANSIString,
    ArtRegistry,
    ColorGeneratorContext,
    load_art_pack_toml,
    register_color_generator,
    unregister_color_generator,
)
from pyansistring.art_registry import normalize_art_coloring


def test_register_art_and_build_colored_art():
    registry = ArtRegistry()
    registry.register(
        "demo",
        "AB",
        colorings=(
            {
                "mode": "gradient",
                "colors": [(255, 0, 0), (0, 0, 255)],
                "slices": ((0, 1), (1, 2)),
                "fg": True,
            },
        ),
    )

    colored = registry.get_colored_art("demo")

    assert isinstance(colored, ANSIString)
    assert len(colored.style_manager) == 2
    assert colored.style_manager[0].foreground.to_rgb() == (255, 0, 0)
    assert colored.style_manager[1].foreground.to_rgb() == (0, 0, 255)


def test_load_art_pack_toml(tmp_path: Path):
    art_pack = tmp_path / "art_pack.toml"
    art_pack.write_text(
        r"""
[[arts]]
name = "banner"
plain_art = '''
 /\_/\\
( o.o )
 > ^ <
'''
metadata = { source = "cowsay", tags = ["animal", "cli"] }

[[arts.colorings]]
mode = "gradient"
colors = [[255, 0, 0], [0, 0, 255]]
slices = [[0, 1], [2, 3]]
fg = true

[[arts]]
name = "demo"
plain_art = "AB"

[[arts.colorings]]
mode = "gradient"
colors = [[0, 255, 0], [0, 128, 255]]
slices = [[0, 1], [1, 2]]
fg = true
""".strip(),
        encoding="utf-8",
    )

    registry = load_art_pack_toml(art_pack)

    assert registry.names() == ("banner", "demo")
    metadata = registry.get_metadata("banner")
    assert metadata is not None
    assert metadata.get("source") == "cowsay"
    assert len(registry.get_colored_art("banner").style_manager) == 2
    assert len(registry.get_colored_art("demo").style_manager) == 2


def test_builtin_registry_matches_existing_showcase():
    assert DEFAULT_ART_REGISTRY.names() == ("BANNER", "MESSAGE")
    definition = DEFAULT_ART_REGISTRY.definition("BANNER")
    from_registry = DEFAULT_ART_REGISTRY.get_colored_art("BANNER")

    assert from_registry.plain_text == definition["plain_art"]
    assert len(from_registry.style_manager) > 0


def test_load_art_pack_toml_color_generator_seeded_is_stable(tmp_path: Path):
    art_pack = tmp_path / "seeded.toml"
    art_pack.write_text(
        """
[[arts]]
name = "gen"
plain_art = "ABCDEFG"

[[arts.colorings]]
mode = "gradient"
colors = { generator = "banner_tree_v1", mode = "seeded", seed = 7, step_count = 7 }
slices = [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7]]
fg = true
""".strip(),
        encoding="utf-8",
    )

    registry = load_art_pack_toml(art_pack)
    a = registry.get_colored_art("gen")
    b = registry.get_colored_art("gen")
    assert str(a) == str(b)


def test_load_art_pack_toml_color_generator_random_varies(tmp_path: Path):
    art_pack = tmp_path / "random.toml"
    slices = ", ".join(f"[{i}, {i + 1}]" for i in range(26))
    art_pack.write_text(
        f"""
[[arts]]
name = "gen"
plain_art = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

[[arts.colorings]]
mode = "gradient"
colors = {{ generator = "banner_tree_v1", mode = "random", step_count = 26 }}
slices = [{slices}]
fg = true
""".strip(),
        encoding="utf-8",
    )

    registry = load_art_pack_toml(art_pack)
    samples = {str(registry.get_colored_art("gen")) for _ in range(4)}
    assert len(samples) > 1


def test_register_custom_color_generator_and_derive_step_count(tmp_path: Path):
    seen_step_counts: list[int] = []

    def custom_generator(context: ColorGeneratorContext) -> list[tuple[int, int, int]]:
        seen_step_counts.append(context["step_count"])
        return [
            (255, 0, 0) if index % 2 == 0 else (0, 0, 255)
            for index in range(context["step_count"])
        ]

    register_color_generator("test_pattern_v1", custom_generator)
    try:
        art_pack = tmp_path / "custom_generator.toml"
        art_pack.write_text(
            """
[[arts]]
name = "gen"
plain_art = "ABCD"

[[arts.colorings]]
mode = "gradient"
colors = { generator = "test_pattern_v1", mode = "random" }
slices = [[0, 1], [1, 2], [2, 3], [3, 4]]
fg = true
""".strip(),
            encoding="utf-8",
        )

        registry = load_art_pack_toml(art_pack)
        colored = registry.get_colored_art("gen")

        assert seen_step_counts == [4]
        assert len(colored.style_manager) == 4
        assert colored.style_manager[0].foreground.to_rgb() == (255, 0, 0)
        assert colored.style_manager[1].foreground.to_rgb() == (0, 0, 255)
    finally:
        unregister_color_generator("test_pattern_v1")


def test_register_custom_color_generator_step_count_override(tmp_path: Path):
    seen_step_counts: list[int] = []

    def custom_generator(context: ColorGeneratorContext) -> list[tuple[int, int, int]]:
        seen_step_counts.append(context["step_count"])
        return [(0, 255, 0) for _ in range(context["step_count"])]

    register_color_generator("test_override_v1", custom_generator)
    try:
        art_pack = tmp_path / "override_generator.toml"
        art_pack.write_text(
            """
[[arts]]
name = "gen"
plain_art = "ABCD"

[[arts.colorings]]
mode = "gradient"
colors = { generator = "test_override_v1", mode = "random", step_count = 7 }
slices = [[0, 1], [1, 2], [2, 3], [3, 4]]
fg = true
""".strip(),
            encoding="utf-8",
        )

        registry = load_art_pack_toml(art_pack)
        colored = registry.get_colored_art("gen")

        assert seen_step_counts == [7]
        assert len(colored.style_manager) == 4
    finally:
        unregister_color_generator("test_override_v1")


def test_normalize_art_coloring_gradient_rejects_invalid_space():
    with pytest.raises(TypeError, match="Expected color space"):
        normalize_art_coloring(
            {
                "mode": "gradient",
                "colors": [(255, 0, 0), (0, 0, 255)],
                "slices": ((0, 1),),
                "space": "lab",
            }
        )


def test_normalize_art_coloring_coordinates_rejects_invalid_origin():
    with pytest.raises(TypeError, match="Expected origin"):
        normalize_art_coloring(
            {
                "mode": "gradient_coordinates",
                "colors": [(255, 0, 0), (0, 0, 255)],
                "coordinates": ((0, 0),),
                "origin": (1,),
            }
        )


def test_normalize_art_coloring_coordinates_rejects_invalid_system():
    with pytest.raises(TypeError, match="Expected system"):
        normalize_art_coloring(
            {
                "mode": "gradient_coordinates",
                "colors": [(255, 0, 0), (0, 0, 255)],
                "coordinates": ((0, 0),),
                "system": "screen",
            }
        )


def test_normalize_art_coloring_coordinates_rejects_invalid_on_out_of_bounds():
    with pytest.raises(TypeError, match="Expected on_out_of_bounds"):
        normalize_art_coloring(
            {
                "mode": "gradient_coordinates",
                "colors": [(255, 0, 0), (0, 0, 255)],
                "coordinates": ((0, 0),),
                "on_out_of_bounds": "wrap",
            }
        )


def test_normalize_art_coloring_coordinates_rejects_non_int_index_base():
    with pytest.raises(TypeError, match="Expected index_base"):
        normalize_art_coloring(
            {
                "mode": "gradient_coordinates",
                "colors": [(255, 0, 0), (0, 0, 255)],
                "coordinates": ((0, 0),),
                "index_base": "0",
            }
        )


def test_from_builtin_propagates_unexpected_errors(monkeypatch: pytest.MonkeyPatch):
    def _explode(*args: object, **kwargs: object) -> object:
        raise RuntimeError("boom")

    monkeypatch.setattr(tomllib, "load", _explode)

    with pytest.raises(RuntimeError, match="boom"):
        ArtRegistry.from_builtin()
