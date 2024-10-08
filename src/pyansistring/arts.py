__all__ = [
    "PLAIN_ARTS",
    "COLORED_ARTS",
]

from pyansistring.pyansistring import ANSIString


PLAIN_ARTS = {
    "BANNER": (
        "                 ^___^           ░░░                                            \n"
        "                ╱ . .│          ░*░░░░░                                         \n"
        "           /‾\__╱   ╲         ░░░░╲ ░.░░                ▄                       \n"
        "           ╰    ╲   ╱       ░░░░._╱╲╱░░░_                                       \n"
        "      __________╱╲_╱ ╔▄▄▄▄▄   ░░░░\*╲  ╱╱        ╭────╮  █▄-.-.---.--.-         \n"
        "     ╱     ╱         ║█╝  █╗    __ ╱ ╲╱╱*░░░     │   .╯ -.█▄---.-.----.-        \n"
        "    ╱     ╱ ╱    ╱   ║█▄▄▄█║   ╱╱╲╲  ╱╱╲ ╲░░     ╰────╮ ---█▄-.---.--.-- string \n"
        "   ╱ ‾‾‾‾‾ ╱    ╱    ╚█░  █║  ╱╱ ╱╲╲╱╱ ╱╲╱░░░░        │ -.-██▄ .----.--.        \n"
        "  ╱        ╲___╱      █░  █╝ ╱╱ ╱  ‾‾ ╱  ╲_.░░░ ╭─────╯ --.-███--.----.-        \n"
        " ╱            ╱              ‾ *   ░░╱╲_*░░░░░  ╰─.                             \n"
        "             ╱                    ░░.░░░░░░                                     \n"
        "            ╱                      ░░░ ░░░                                      "
    ),
    "LETTER": (
        "       .....    .     .    . . .     . . .    . . .     .     .      ....  ..   .\n"
        "        .      . .   .   .      .  .      .  .     .     .     .    ..    .. .   .\n"
        "       .      .   . .   . . . .   . . . .   .     .       .     .  .  .    .  .   .\n"
        "      .      .     .   .         .         .     .         .  .  ..   ..   ..  .   .\n"
        "     .      .           . . .     . . .   .    .                 ..    ..   ..  .   .  .\n"
        "  .....    .                             . . .                  .  .      ...     ... .\n"
        "                                                               .    .\n"
        "                                                               .    .\n"
        "                                                                 . .\n"
        "                  /\___/__./      .....   .    .  ...\n"
        "                ./ /  /   /      /____/  / \  /  /   \\\n"
        "               /  /  /   /      /    /  /   \/  /    /\n"
        "               \ /  /  ./      /    /  /    /  / .. /\n"
        "                .\_/_ /.                          __\n"
        "                  /          /      ///   /   /  /\n"
        "                 /.         /     /   /  /   /  /__\n"
        "                /...       /     /   /  /   /  /\n"
        "            .../  ..      /___.  ///    ///   /___.\n"
        "          ... /                 ___\n"
        "             /          /   /  /   \   /   /\n"
        "            /          /   /  /    /  /   /\n"
        "           /          /   /  /    /  /   /\n"
        "          .           \__/   \___/   \__/\_/\n"
        "                     __ /\n"
        "                    /  /\n"
        "                    \./"
    ),
}


STYLES = {
    "BANNER": {
        # /-----------/ P LETTER: BLUE
        "r=0:  |g=0:  |b=255: $ g+14:|r+8: &*": (
            (1, 9), (2, 8),
            ((3, 7), (5, 7)),
            ((4, 6), (6, 7)),
            ((5, 5), (7, 7)),
            ((6, 4), (8, 7)),
            ((7, 4), (9, 7)),
            ((8, 4), (10, 6)),
            ((9, 4), (11, 5)),
            (10, 4), (11, 4),
            (12, 4), (13, 4),
            (14, 4), (15, 4),
        ),
        # /-----------/ Y LETTER: YELLOW
        "r=255:|g=255:|b=0:   $ b+21: &*": (
            (12, 11), (13, 10), (14, 9),
            ((15, 8), (14, 8)),
            ((16, 7), (13, 8)),
            ((17, 6), (12, 8)),
            (11, 8), (11, 7), (12, 6),
        ),
        # /-----------/ A LETTER: LEFT CELL
        "r=255:|g=166:|b=166: $ g-10:|b-10: &*": (
            (23, 5), (21, 4), (21, 5), (21, 6), (21, 7)
        ),
        # /-----------/ A LETTER: RIGHT CELL
        "r=255:|g=218:|b=110: $ g+5: |b+25: &*": (
            (27, 8), (27, 7), (27, 6), (27, 5)
        ),
        # /-----------/ A LETTER: GRAY
        "r=100:|g=100:|b=100: $ r+8: |g+7: | b+6: &*": (
            (22, 8), (22, 7), (22, 6), 
            (22, 5), (22, 4),
            ((23, 4), (23, 6)),
            ((24, 4), (24, 6)),
            ((25, 4), (25, 6)),
            (26, 4), (26, 5), (26, 6),
            (26, 7), (26, 8),
        ),
        # /-----------/ N LETTER: TREE
        "r=40: |g=189:|b=38:  $ r+random(-40,0):|g+random(-50,50):? &": (
            (33, 0), (34, 0), (35, 0), (32, 1), (34, 1), (35, 1),
            (36, 1), (37, 1), (38, 1), (30, 2), (31, 2), (32, 2),
            (33, 2), (36, 2), (38, 2), (39, 2), (28, 3), (29, 3),
            (30, 3), (31, 3), (37, 3), (38, 3), (39, 3), (30, 4),
            (31, 4), (32, 4), (33, 4), (41, 5), (42, 5), (43, 5),
            (42, 6), (43, 6), (42, 7), (43, 7), (44, 7), (45, 7),
            (44, 8), (45, 8), (46, 8), (35, 9), (36, 9), (41, 9),
            (42, 9), (43, 9), (44, 9), (45, 9), (34, 10), (35, 10),
            (37, 10), (38, 10), (39, 10), (40, 10), (41, 10), (42, 10),
            (35, 11), (36, 11), (37, 11), (39, 11), (40, 11), (41, 11),
        ),
        # /-----------/ N LETTER: APPLES AND CHERRIES
        "r=255:|g=46: |b=81:  &": (
            (33, 1), (37, 2), (32, 3),
            (35, 4), (40, 5), (43, 8),
            (40, 9), (36, 10), (31, 9),
        ),
        # /-----------/ N LETTER: TREE BRANCHES
        "r=150:|g=91: |b=35:  &": (
            (34, 2), (33, 3), (34, 3), (35, 3), 
            (36, 3), (34, 4), (36, 4), (35, 5),
            (37, 5), (39, 6), (41, 6), (33, 7),
            (39, 7), (40, 7), (41, 7), (32, 8),
            (38, 8), (41, 8), (42, 8), (37, 9), 
            (38, 9), (39, 9),
        ),
        # /-----------/ N LETTER: CYAN
        "r=229:|g=255:|b=185: $ r-5: &*": (
            (29, 8), (30, 7), (31, 6), (32, 5),
            (33, 5), (34, 6), (35, 7), (36, 7),
            (37, 6), (38, 5), (39, 4), (40, 3),
            (40, 4), (39, 5), (38, 6), (37, 7),
            (36, 8), (35, 8), (34, 7), (33, 6),
            (32, 6), (31, 7), (30, 8), (29, 9),
        ),
        # /-----------/ S LETTER: SNAKE
        "r=100:|g=100:|b=150: $ r+5: &*": (
            (50, 9), (49, 9), (48, 9), (48, 8),
            (49, 8), (50, 8), (51, 8), (52, 8),
            (53, 8), (54, 8), (54, 7), (54, 6),
            (53, 6), (52, 6), (51, 6), (50, 6),
            (49, 6), (49, 5), (49, 4), (50, 4),
            (51, 4), (52, 4), (53, 4), (54, 4),
            (54, 5), (53, 5),
        ),
        # /-----------/ I LETTER: DOTS
        "r=176:|g=226:|b=255: &": (
            (60, 4), (62, 4), (66, 4), (69, 4),
            (57, 5), (63, 5), (65, 5), (70, 5),
            (62, 6), (66, 6), (69, 6), (57, 7),
            (63, 7), (68, 7), (71, 7), (58, 8),
            (65, 8), (70, 8),
        ),
        # /-----------/ I LETTER: WATER
        "r=22: |g=113:|b=217: &": (
            (59, 4), (61, 4), (63, 4), (64, 4), (65, 4), (67, 4),
            (68, 4), (70, 4), (56, 5), (60, 5), (61, 5), (62, 5),
            (64, 5), (66, 5), (67, 5), (68, 5), (69, 5), (71, 5),
            (56, 6), (57, 6), (58, 6), (61, 6), (63, 6), (64, 6),
            (65, 6), (67, 6), (68, 6), (70, 6), (71, 6), (56, 7),
            (58, 7), (64, 7), (65, 7), (66, 7), (67, 7), (69, 7),
            (70, 7), (56, 8), (57, 8), (59, 8), (63, 8), (64, 8),
            (66, 8), (67, 8), (68, 8), (69, 8), (71, 8),
        ),
        # /-----------/ I LETTER: MOON AND REFLECTION
        "r=84: |g=161:|b=255: $ r+9:|g+4: &*": (
            (56, 2), (57, 4), (58, 4), (58, 5),
            (59, 5), (59, 6), (60, 6), (59, 7),
            (60, 7), (61, 7), (60, 8), (61, 8),
            (62, 8),
        ),
    }
}


COLORED_ARTS = {}
for name, art in PLAIN_ARTS.items():
    colored = ANSIString(art)
    if name in STYLES:
        for sequence, coordinates in STYLES[name].items():
            colored.multicolor_c(sequence, *coordinates)
    COLORED_ARTS[name] = colored

if __name__ == "__main__":
    print(COLORED_ARTS["BANNER"])
