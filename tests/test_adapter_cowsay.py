from __future__ import annotations

import pytest

from pyansistring.adapters import cowsay as cowsay_adapter
from pyansistring.adapters.cowsay import (
    cowsay_art_definition,
    register_cowsay_art,
    render_cowsay,
)
from pyansistring.art_registry import ArtRegistry


def test_render_cowsay_uses_injected_renderer():
    calls: list[tuple[str, str]] = []

    def fake_renderer(cow: str, message: str) -> str:
        calls.append((cow, message))
        return f"<{cow}> {message}"

    out = render_cowsay("hello", cow="dragon", renderer=fake_renderer)
    assert out == "<dragon> hello"
    assert calls == [("dragon", "hello")]


def test_cowsay_art_definition_includes_metadata_and_colorings():
    definition = cowsay_art_definition(
        "hello",
        name="hello-cow",
        cow="tux",
        colorings=(
            {
                "mode": "gradient",
                "colors": [(255, 0, 0), (0, 0, 255)],
                "slices": ((0, 1),),
            },
        ),
        metadata={"version": "1"},
        renderer=lambda cow, message: f"{cow}:{message}",
    )

    assert definition["plain_art"] == "tux:hello"
    assert len(definition["colorings"]) == 1
    metadata = definition.get("metadata")
    assert metadata is not None
    assert metadata.get("source") == "cowsay"
    assert "cowsay" in metadata.get("tags", [])
    assert metadata.get("name") == "hello-cow"
    assert metadata.get("version") == "1"


def test_register_cowsay_art_registers_definition():
    registry = ArtRegistry()

    register_cowsay_art(
        registry,
        "cow-demo",
        "moo",
        cow="default",
        renderer=lambda cow, message: f"{cow}:{message}",
    )

    assert registry.names() == ("cow-demo",)
    assert registry.get_plain_art("cow-demo") == "default:moo"
    metadata = registry.get_metadata("cow-demo")
    assert metadata is not None
    assert metadata.get("source") == "cowsay"


def test_render_cowsay_missing_dependency_raises_helpful_error(
    monkeypatch: pytest.MonkeyPatch,
):
    def fake_import(name: str):
        if name == "cowsay":
            raise ModuleNotFoundError("No module named cowsay")
        raise AssertionError(f"Unexpected import: {name}")

    monkeypatch.setattr(cowsay_adapter, "_import_module", fake_import)

    with pytest.raises(ModuleNotFoundError, match="adapter-cowsay"):
        render_cowsay("hello")
