#!/usr/bin/env python3
"""art_registry_demo.py — ArtRegistry walkthrough with a custom zigzag generator.

Run with:
    python examples/art_registry_demo.py
"""

from pyansistring import (
    ArtRegistry,
    ColorGeneratorContext,
    register_color_generator,
    unregister_color_generator,
)


def zigzag_generator(context: ColorGeneratorContext) -> list[tuple[int, int, int]]:
    """Return a mirrored zigzag palette sized to the requested step count."""
    palette = [
        (84, 161, 255),
        (255, 99, 71),
        (255, 215, 0),
        (120, 220, 160),
    ]
    out: list[tuple[int, int, int]] = []
    for index in range(max(2, context["step_count"])):
        phase = (index // len(palette)) % 2
        slot = index % len(palette)
        out.append(palette[slot] if phase == 0 else palette[-slot - 1])
    return out


def main() -> None:
    register_color_generator("zigzag_demo_v1", zigzag_generator)
    try:
        registry = ArtRegistry()
        registry.register(
            "ZIGZAG",
            " /\\/\\/\\/\\\n \\/\\/\\/\\/",
            colorings=(
                {
                    "mode": "gradient",
                    "colors": {
                        "generator": "zigzag_demo_v1",
                        "mode": "seeded",
                        "seed": 12,
                    },
                    "skip_whitespace": True,
                    "fg": True,
                },
            ),
            metadata={
                "description": (
                    "Simple custom art with a generator-driven zigzag palette."
                ),
                "tags": ["demo", "zigzag", "generator"],
            },
        )

        print("\nCustom art (ZIGZAG):")
        print(registry.get_colored_art("ZIGZAG"))
    finally:
        unregister_color_generator("zigzag_demo_v1")


if __name__ == "__main__":
    main()
