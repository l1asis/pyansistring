from __future__ import annotations

from collections.abc import Iterable as _Iterable
from importlib import import_module as _import_module
from typing import Callable as _Callable

from pyansistring._types import ArtColoring, ArtDefinition, ArtMetadata
from pyansistring.art_registry import ArtRegistry


def _default_cowsay_renderer(cow: str, message: str) -> str:
    try:
        cowsay = _import_module("cowsay")
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "cowsay adapter requires optional dependency 'cowsay'. "
            "Install with: pip install pyansistring[adapter-cowsay]"
        ) from exc

    get_output_string = getattr(cowsay, "get_output_string", None)
    if callable(get_output_string):
        return str(get_output_string(cow, message))

    cow_fn = getattr(cowsay, cow, None)
    if callable(cow_fn):
        return str(cow_fn(message))

    fallback_fn = getattr(cowsay, "cow", None)
    if cow == "default" and callable(fallback_fn):
        return str(fallback_fn(message))

    raise RuntimeError(
        "Unsupported cowsay API in installed package: expected "
        "get_output_string(cow, message) or callable cow functions"
    )


def render_cowsay(
    message: str,
    *,
    cow: str = "default",
    renderer: _Callable[[str, str], str] | None = None,
) -> str:
    renderer_fn = renderer or _default_cowsay_renderer
    return renderer_fn(cow, message)


def cowsay_art_definition(
    message: str,
    *,
    name: str | None = None,
    cow: str = "default",
    colorings: _Iterable[ArtColoring] = (),
    metadata: ArtMetadata | None = None,
    renderer: _Callable[[str, str], str] | None = None,
) -> ArtDefinition:
    plain_art = render_cowsay(message, cow=cow, renderer=renderer)

    merged_metadata: ArtMetadata = {
        "source": "cowsay",
        "tags": ["adapter", "cowsay"],
    }
    if name:
        merged_metadata["name"] = name
    if metadata:
        merged_metadata.update(metadata)

    return {
        "plain_art": plain_art,
        "colorings": tuple(colorings),
        "metadata": merged_metadata,
    }


def register_cowsay_art(
    registry: ArtRegistry,
    key: str,
    message: str,
    *,
    cow: str = "default",
    colorings: _Iterable[ArtColoring] = (),
    metadata: ArtMetadata | None = None,
    renderer: _Callable[[str, str], str] | None = None,
) -> None:
    definition = cowsay_art_definition(
        message,
        name=key,
        cow=cow,
        colorings=colorings,
        metadata=metadata,
        renderer=renderer,
    )
    registry.register(
        key,
        definition["plain_art"],
        colorings=definition["colorings"],
        metadata=definition.get("metadata"),
    )
