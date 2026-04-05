#!/usr/bin/env python3
"""Example: create and render art using the optional cowsay adapter.

Run with:
    python examples/cowsay_adapter_usage.py

If cowsay is not installed, install optional extras with:
    pip install pyansistring[adapter-cowsay]
"""

from __future__ import annotations

from pyansistring import ArtRegistry, cowsay_art_definition


def _non_whitespace_slices(text: str) -> tuple[tuple[int, int], ...]:
    return tuple(
        (index, index + 1) for index, char in enumerate(text) if not char.isspace()
    )


def main() -> None:
    message = "Adapter API looks great"

    try:
        # Build one art definition from the cowsay output.
        plain_definition = cowsay_art_definition(message, name="cowsay-demo", cow="tux")
    except ModuleNotFoundError as exc:
        print(exc)
        return

    plain_art = plain_definition["plain_art"]
    slices = _non_whitespace_slices(plain_art)

    colored_definition = cowsay_art_definition(
        message,
        name="cowsay-demo",
        cow="tux",
        colorings=(
            {
                "mode": "gradient",
                "colors": [(90, 170, 255), (255, 170, 90)],
                "slices": slices,
                "skip_whitespace": True,
                "fg": True,
            },
        ),
    )

    registry = ArtRegistry()
    registry.register_definition("cowsay-demo", colored_definition)

    print("\n--- Plain cowsay output ---\n")
    print(plain_art)

    print("\n--- Colored cowsay output via ArtRegistry ---\n")
    print(registry.get_colored_art("cowsay-demo"))


if __name__ == "__main__":
    main()
