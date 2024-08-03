from random import randint
from re import finditer

from pyansistring import ANSIString


def clamp(value: int|float, min = -float("inf"), max = float("inf")) -> int|float:
    return min if value < min else max if value > max else value

def get_index(x: int, y: int, width: int = 80) -> int:
    return (y+1) * width - (width-(x+1)) + (y-1)

def batch_coloring(string: ANSIString, batch: tuple[tuple[int, int]|tuple[tuple[int, int]]],
                   r: int, g: int, b: int, shift: str = ""):
    colors = {"r": r, "g": g, "b": b,
              "base": {"r": r, "g": g, "b": b}}
    if shift:
        pattern = r"(?P<color>[rgb])(?P<sign>[+-])(?P<action>(?P<random>random\((?P<range>\s*\-?\d+\s*\,\s*\-?\d+\s*)\))|(?P<constant>\d+))"
        table = [{"color": match["color"],
                  "sign": match["sign"],
                  "type": ("random" if match["random"] else "constant"),
                  "range": (tuple(map(int, match["range"].split(","))) if match["range"] else None),
                  "constant": (int(match["constant"]) if match["constant"] else None)} for match in finditer(pattern, shift)]
    else: table = {}

    for position in batch:
        if type(position[0]) is tuple:
            for sub_position in position:
                string.fg_24b(colors["r"], colors["g"], colors["b"], ((index := get_index(*sub_position)), index+1))
        else:
            string.fg_24b(colors["r"], colors["g"], colors["b"], ((index := get_index(*position)), index+1))
    
        for case in table:
            colors[case["color"]] = clamp((colors["base"][case["color"]] if case["type"] == "random" else colors[case["color"]]) + \
                                          (-1 if case["sign"] == "-" else 1) * \
                                          (randint(*case["range"]) if case["type"] == "random" else case["constant"]), 0, 255)

    return string


DEFAULT_BANNER = """                 ^___^           ░░░                                            
                ╱ . .│          ░*░░░░░                                         
           /‾\__╱   ╲         ░░░░╲ ░.░░                ▄                       
           ╰    ╲   ╱       ░░░░._╱╲╱░░░_                                       
      __________╱╲_╱ ╔▄▄▄▄▄   ░░░░\*╲  ╱╱        ╭────╮  █▄-.-.---.--.-         
     ╱     ╱         ║█╝  █╗    __ ╱ ╲╱╱*░░░     │   .╯ -.█▄---.-.----.-        
    ╱     ╱ ╱    ╱   ║█▄▄▄█║   ╱╱╲╲  ╱╱╲ ╲░░     ╰────╮ ---█▄-.---.--.-- string 
   ╱ ‾‾‾‾‾ ╱    ╱    ╚█░  █║  ╱╱ ╱╲╲╱╱ ╱╲╱░░░░        │ -.-██▄ .----.--.        
  ╱        ╲___╱      █░  █╝ ╱╱ ╱  ‾‾ ╱  ╲_.░░░ ╭─────╯ --.-███--.----.-        
 ╱            ╱              ‾ *   ░░╱╲_*░░░░░  ╰─.                             
             ╱                    ░░.░░░░░░                                     
            ╱                      ░░░ ░░░                                      """
BANNER = ANSIString(DEFAULT_BANNER)

# /-----------/ P LETTER: BLUE
P = ((1, 9), (2, 8), ((3, 7), (5, 7)), ((4, 6), (6, 7)), ((5, 5), (7, 7)), ((6, 4), (8, 7)), ((7, 4), (9, 7)), 
     ((8, 4), (10, 6)), ((9, 4), (11, 5)), (10, 4), (11, 4), (12, 4), (13, 4), (14, 4), (15, 4))
# /-----------/ Y LETTER: YELLOW
Y = ((12, 11), (13, 10), (14, 9), ((15, 8), (14, 8)), ((16, 7), (13, 8)), ((17, 6), (12, 8)), (11, 8), (11, 7), (12, 6))
# /-----------/ A LETTER: LEFT CELL
CELL1 = ((23, 5), (21, 4), (21, 5), (21, 6), (21, 7))
# /-----------/ A LETTER: RIGHT CELL
CELL2 = ((27, 8), (27, 7), (27, 6), (27, 5))
# /-----------/ A LETTER: GRAY
A = ((22, 8), (22, 7), (22, 6), (22, 5), (22, 4), ((23, 4), (23, 6)), ((24, 4), (24, 6)),
     ((25, 4), (25, 6)), (26, 4), (26, 5), (26, 6), (26, 7), (26, 8))
# /-----------/ N LETTER: TREE
TREE = ((33, 0), (34, 0), (35, 0), (32, 1), (34, 1), (35, 1), (36, 1), (37, 1), (38, 1), (30, 2), (31, 2), (32, 2), (33, 2),
        (36, 2), (38, 2), (39, 2), (28, 3), (29, 3), (30, 3), (31, 3), (37, 3), (38, 3), (39, 3), (30, 4), (31, 4),
        (32, 4), (33, 4), (41, 5), (42, 5), (43, 5), (42, 6), (43, 6), (42, 7), (43, 7), (44, 7), (45, 7), (44, 8),
        (45, 8), (46, 8), (35, 9), (36, 9), (41, 9), (42, 9), (43, 9), (44, 9), (45, 9), (34, 10), (35, 10), (37, 10),
        (38, 10), (39, 10), (40, 10), (41, 10), (42, 10), (35, 11), (36, 11), (37, 11), (39, 11), (40, 11), (41, 11))
# /-----------/ N LETTER: APPLES AND CHERRIES
APPLES_N_CHERRIES = ((33, 1), (37, 2), (32, 3), (35, 4), (40, 5), (43, 8), (40, 9), (36, 10), (31, 9))
# /-----------/ N LETTER: TREE BRANCHES
TREE_BRANCHES = ((34, 2), (33, 3), (34, 3), (35, 3), (36, 3), (34, 4), (36, 4), (35, 5), (37, 5), (39, 6), (41, 6), (33, 7), 
                 (39, 7), (40, 7), (41, 7), (32, 8), (38, 8), (41, 8), (42, 8), (37, 9), (38, 9), (39, 9))
# /-----------/ N LETTER: CYAN
N = ((29, 8), (30, 7), (31, 6), (32, 5), (33, 5), (34, 6), (35, 7), (36, 7), (37, 6), (38, 5), (39, 4), (40, 3), 
     (40, 4), (39, 5), (38, 6), (37, 7), (36, 8), (35, 8), (34, 7), (33, 6), (32, 6), (31, 7), (30, 8), (29, 9))
# /-----------/ S LETTER: SNAKE
SNAKE = ((50, 9), (49, 9), (48, 9), (48, 8), (49, 8), (50, 8), (51, 8), (52, 8), (53, 8), (54, 8), (54, 7), (54, 6), 
         (53, 6), (52, 6), (51, 6), (50, 6), (49, 6), (49, 5), (49, 4), (50, 4), (51, 4), (52, 4), (53, 4), (54, 4), 
         (54, 5), (53, 5))
# /-----------/ I LETTER: DOTS
DOTS = ((60, 4), (62, 4), (66, 4), (69, 4),
        (57, 5), (63, 5), (65, 5), (70, 5),
        (62, 6), (66, 6), (69, 6), 
        (57, 7), (63, 7), (68, 7), (71, 7),
        (58, 8), (65, 8), (70, 8))
# /-----------/ I LETTER: WATER
WATER = ((59, 4), (61, 4), (63, 4), (64, 4), (65, 4), (67, 4), (68, 4), (70, 4),
        (56, 5), (60, 5), (61, 5), (62, 5), (64, 5), (66, 5), (67, 5), (68, 5), (69, 5), (71, 5),
        (56, 6), (57, 6), (58, 6), (61, 6), (63, 6), (64, 6), (65, 6), (67, 6), (68, 6), (70, 6), (71, 6),
        (56, 7), (58, 7), (64, 7), (65, 7), (66, 7), (67, 7), (69, 7), (70, 7),
        (56, 8), (57, 8), (59, 8), (63, 8), (64, 8), (66, 8), (67, 8), (68, 8), (69, 8), (71, 8))
# /-----------/ I LETTER: MOON AND REFLECTION
MOON_N_REFLECTION = ((56, 2), (57, 4), (58, 4), (58, 5), (59, 5), (59, 6), (60, 6), (59, 7), (60, 7),
                     (61, 7), (60, 8), (61, 8), (62, 8))

BANNER_COORDINATES = (P, Y, CELL1, CELL2, A, TREE, APPLES_N_CHERRIES,
                      TREE_BRANCHES, N, SNAKE, DOTS, WATER, MOON_N_REFLECTION)

BANNER_SEQUENCES = ((0, 0, 255, "g+14|r+8"), (255, 255, 0, "b+21"), (255, 166, 166, "g-10|b-10"),
                    (255, 218, 110, "g+5|b+25"), (100, 100, 100, "r+8|g+7|b+6"),
                    (40, 189, 38, "r+random(-40, 0)|g+random(-50, 50)"), (255, 46, 81, ""),
                    (150, 91, 35, ""), (229, 255, 185, "r-5"), (100, 100, 150, "r+5"),
                    (176, 226, 255, ""), (22, 113, 217, ""), (84, 161, 255, "r+9|g+4"))

for coordinates, sequences in zip(BANNER_COORDINATES, BANNER_SEQUENCES):
    batch_coloring(BANNER, coordinates, *sequences)

if __name__ == "__main__":
    print(BANNER)