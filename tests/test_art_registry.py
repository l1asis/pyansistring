from __future__ import annotations

from pathlib import Path

from pyansistring import (
    DEFAULT_ART_REGISTRY,
    ANSIString,
    ArtRegistry,
    load_art_pack_toml,
)
from pyansistring.arts import COLORED_ARTS


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
    assert str(DEFAULT_ART_REGISTRY.get_colored_art("BANNER")) == str(
        COLORED_ARTS["BANNER"]
    )
