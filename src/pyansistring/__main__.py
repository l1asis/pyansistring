import argparse
import random
import sys

from .constants import Channel
from .core import ANSIString
from .targets import Chars, Coords

BANNER = """
                 ^___^           ░░░                                            
                ╱ . .│          ░*░░░░░                                         
           /‾\\__╱   ╲         ░░░░╲ ░.░░                ▄                       
           ╰    ╲   ╱       ░░░░._╱╲╱░░░_                                       
      ___________╲_╱ ╔▄▄▄▄▄   ░░░░\\*╲  ╱╱        ╭────╮  █▄-.-.---.--.-         
     ╱     ╱         ║█╝  █╗    __ ╱ ╲╱╱*░░░     │   .╯ -.█▄---.-.----.-        
    ╱     ╱ ╱    ╱   ║█▄▄▄█║   ╱╱╲╲  ╱╱╲ ╲░░     ╰────╮ ---█▄-.---.--.-- string 
   ╱ ‾‾‾‾‾ ╱    ╱    ╚█░  █║  ╱╱ ╱╲╲╱╱ ╱╲╱░░░░        │ -.-██▄ .----.--.        
  ╱        ╲___╱      █░  █╝ ╱╱ ╱  ‾‾ ╱  ╲_.░░░ ╭─────╯ --.-███--.----.-        
 ╱            ╱              ‾ *   ░░╱╲_*░░░░░  ╰─.                             
             ╱                    ░░.░░░░░░                                     
            ╱                      ░░░ ░░░                                      
"""


def get_tree_colors(step_count: int, randomize: bool) -> list[tuple[int, int, int]]:
    """Generates the colors for the tree leaves."""
    if randomize:
        rng = random.Random()
        return [
            (40 + rng.randint(-40, 0), 189 + rng.randint(-50, 50), 38)
            for _ in range(step_count)
        ]
    # Fallback to a smooth Green-to-Yellow gradient
    return [(34, 139, 34), (154, 205, 50)]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="pyansistring installation verification and banner display."
    )
    parser.add_argument(
        "--static-tree",
        action="store_true",
        help="Use a static gradient for the tree instead of random colors.",
    )
    args = parser.parse_args()

    # Initialize the canvas
    art = ANSIString(BANNER.strip("\n"))

    # Cat Body (Orange)
    # fmt: off
    art.gradient(
        [(255, 170, 50), (255, 70, 10)],
        Coords((
            (17, 0), (18, 0), (19, 0), (20, 0), (21, 0), (16, 1), (17, 1),
            (18, 1), (19, 1), (20, 1), (21, 1), (11, 2), (12, 2), (13, 2),
            (14, 2), (15, 2), (16, 2), (17, 2), (18, 2), (19, 2), (20, 2),
            (11, 3), (12, 3), (16, 3), (17, 3), (20, 3), (17, 4), (18, 4),
            (19, 4),
        )),
        channel=Channel.BG,
        space="hsl",
    )
    # fmt: on

    # Cat Belly (Gray)
    art.bg(
        (231, 231, 231),
        Coords(((18, 3), (19, 3))),
    )

    # Cat Outline (Black)
    # fmt: off
    art.fg(
        (0, 0, 0),
        Coords((
            (17, 0), (18, 0), (19, 0), (20, 0), (21, 0), (16, 1), (21, 1),
            (11, 2), (12, 2), (13, 2), (14, 2), (15, 2), (16, 2), (20, 2),
            (11, 3), (16, 3), (20, 3), (17, 4), (18, 4), (19, 4),
        ))
    )
    # fmt: on

    # Cat Eyes (Cyan)
    art.fg((0, 255, 255), Coords(((18, 1), (20, 1))))

    # "P" Letter (Blue, includes coordinate groups!)
    # fmt: off
    art.gradient(
        [(0, 0, 255), (112, 196, 255)],
        Coords((
            (1, 9), (2, 8), ((3, 7), (5, 7)), ((4, 6), (6, 7)), ((5, 5), (7, 7)),
            ((6, 4), (8, 7)), ((7, 4), (9, 7)), ((8, 4), (10, 6)), ((9, 4), (11, 5)),
            (10, 4), (11, 4), (12, 4), (13, 4), (14, 4), (15, 4), (16, 4),
        )),
        space="hsl",
    )
    # fmt: on

    # "Y" Letter (Gold)
    # fmt: off
    art.gradient(
        [(165, 125, 2), (213, 176, 56)],
        Coords((
            (12, 11), (13, 10), (14, 9), ((15, 8), (14, 8)),
            ((16, 7), (13, 8)), ((17, 6), (12, 8)), (11, 8),
            (11, 7), (12, 6),
        )),
        space="hsl",
    )
    # fmt: on

    # "A" Letter Left Cell (Red)
    # fmt: off
    art.gradient(
        [(255, 166, 166), (255, 126, 126)],
        Coords((
            (23, 5), (21, 4), (21, 5), (21, 6), (21, 7),
        )),
        space="hsl",
    )
    # fmt: on

    # "A" Letter Right Cell (Yellow)
    # fmt: off
    art.gradient(
        [(255, 218, 110), (255, 233, 185)],
        Coords((
            (27, 8), (27, 7), (27, 6), (27, 5),
        )),
        space="hsl",
    )
    # fmt: on

    # "A" Letter (Gray)
    # fmt: off
    art.gradient(
        [(100, 100, 100), (196, 184, 172)],
        Coords((
            (22, 8), (22, 7), (22, 6), (22, 5), (22, 4), ((23, 4), (23, 6)),
            ((24, 4), (24, 6)), ((25, 4), (25, 6)), (26, 4), (26, 5),
            (26, 6), (26, 7), (26, 8),
        )),
        space="hsl",
    )
    # fmt: on

    # Tree Leaves (Green)
    # fmt: off
    tree_coords = [
        (33, 0), (34, 0), (35, 0), (32, 1), (34, 1), (35, 1), (36, 1),
        (37, 1), (38, 1), (30, 2), (31, 2), (32, 2), (33, 2), (36, 2),
        (38, 2), (39, 2), (28, 3), (29, 3), (30, 3), (31, 3), (37, 3),
        (38, 3), (39, 3), (30, 4), (31, 4), (32, 4), (33, 4), (41, 5),
        (42, 5), (43, 5), (42, 6), (43, 6), (42, 7), (43, 7), (44, 7),
        (45, 7), (44, 8), (45, 8), (46, 8), (35, 9), (36, 9), (41, 9),
        (42, 9), (43, 9), (44, 9), (45, 9), (34, 10), (35, 10), (37, 10),
        (38, 10), (39, 10), (40, 10), (41, 10), (42, 10), (35, 11), 
        (36, 11), (37, 11), (39, 11), (40, 11), (41, 11),
    ]
    # fmt: on

    tree_colors = get_tree_colors(len(tree_coords), randomize=not args.static_tree)
    art.gradient(tree_colors, Coords(tuple(tree_coords)), space="hsl")

    # Apples/Berries (Red)
    # fmt: off
    art.fg(
        (255, 46, 81), 
        Coords((
            (33, 1), (37, 2), (32, 3), (35, 4), (40, 5), (43, 8), (40, 9),
            (36, 10), (31, 9),
        )),
    )
    # fmt: on

    # Tree Branches
    # fmt: off
    art.fg(
        (150, 91, 35),
        Coords((
            (34, 2), (33, 3), (34, 3), (35, 3), (36, 3), (34, 4), (36, 4),
            (35, 5), (37, 5), (39, 6), (41, 6), (33, 7), (39, 7), (40, 7),
            (41, 7), (32, 8), (38, 8), (41, 8), (42, 8), (37, 9), (38, 9),
            (39, 9),
        )),
    )
    # fmt: on

    # "N" Letter (Light Green - Cyan)
    # fmt: off
    art.gradient(
        [(229, 255, 185), (114, 255, 185)],
        Coords((
            (29, 8), (30, 7), (31, 6), (32, 5), (33, 5), (34, 6), (35, 7),
            (36, 7), (37, 6), (38, 5), (39, 4), (40, 3), (40, 4), (39, 5),
            (38, 6), (37, 7), (36, 8), (35, 8), (34, 7), (33, 6), (32, 6),
            (31, 7), (30, 8), (29, 9),
        )),
        space="hsl",
    )
    # fmt: on

    # "S" Letter Snake (Pink/Purple)
    # fmt: off
    art.gradient(
        [(100, 100, 150), (225, 100, 150)],
        Coords((
            (50, 9), (49, 9), (48, 9), (48, 8), (49, 8), (50, 8), (51, 8), 
            (52, 8), (53, 8), (54, 8), (54, 7), (54, 6), (53, 6), (52, 6),
            (51, 6), (50, 6), (49, 6), (49, 5), (49, 4), (50, 4), (51, 4),
            (52, 4), (53, 4), (54, 4), (54, 5), (53, 5),
        )),
        space="hsl",
    )
    # fmt: on

    # Dot Waves (Light Blue)
    # fmt: off
    art.fg(
        (176, 226, 255),
        Coords((
            (60, 4), (62, 4), (66, 4), (69, 4), (57, 5), (63, 5), (65, 5), 
            (70, 5), (62, 6), (66, 6), (69, 6), (57, 7), (63, 7), (68, 7), 
            (71, 7), (58, 8), (65, 8), (70, 8),
        )),
    )
    # fmt: on

    # Water/Sea (Dark Blue)
    # fmt: off
    art.fg(
        (22, 113, 217),
        Coords((
            (59, 4), (61, 4), (63, 4), (64, 4), (65, 4), (67, 4), (68, 4), 
            (70, 4), (56, 5), (60, 5), (61, 5), (62, 5), (64, 5), (66, 5),
            (67, 5), (68, 5), (69, 5), (71, 5), (56, 6), (57, 6), (58, 6),
            (61, 6), (63, 6), (64, 6), (65, 6), (67, 6), (68, 6), (70, 6),
            (71, 6), (56, 7), (58, 7), (64, 7), (65, 7), (66, 7), (67, 7),
            (69, 7), (70, 7), (56, 8), (57, 8), (59, 8), (63, 8), (64, 8), 
            (66, 8), (67, 8), (68, 8), (69, 8), (71, 8),
        )),
    )
    # fmt: on

    # "I" Letter Moon & Reflection (Ice Blue)
    # fmt: off
    art.gradient(
        [(84, 161, 255), (192, 209, 255)],
        Coords((
            (56, 2), (57, 4), (58, 4), (58, 5), (59, 5), (59, 6), (60, 6), 
            (59, 7), (60, 7), (61, 7), (60, 8), (61, 8), (62, 8),
        )),
        space="hsl",
    )
    # fmt: on

    # "string" (White Background)
    # fmt: off
    art.bg(
        (255, 255, 255),
        Coords((
            (73, 6), (74, 6), (75, 6), (76, 6), (77, 6), (78, 6),
        )),
    )
    # fmt: on

    # "string" (Black Foreground)
    # fmt: off
    art.fg(
        (0, 0, 0),
        Coords((
            (73, 6), (74, 6), (75, 6), (76, 6), (77, 6), (78, 6),
        )),
    )
    # fmt: on

    sys.stdout.write(f"\n{art}\n\n")

    footer = (
        ANSIString("✨ pyansistring installed successfully! ✨\n")
        .gradient([(0, 255, 255), (255, 0, 255)], Chars(skip_whitespace=True))
        .center(80)
    )
    sys.stdout.write(f"{footer}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
