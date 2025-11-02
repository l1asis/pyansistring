__all__ = [
    "WHITESPACE",
    "UNIVERSAL_NEWLINES",
    "PUNCTUATION",
    "PUNCTUATION_AND_WHITESPACE",
    "ColorMode",
    "Foreground",
    "Background",
    "Underline",
    "UnderlineMode",
    "SGR",
    "COLORS_8BIT",
    "VGA_COLORS",
    "WINDOWS_XP_CONSOLE_COLORS",
    "WINDOWS_POWERSHELL_COLORS",
    "VSCODE_COLORS",
    "WINDOWS_10_CONSOLE_COLORS",
    "TERMINAL_APP_COLORS",
    "PUTTY_COLORS",
    "MIRC_COLORS",
    "XTERM_COLORS",
    "UBUNTU_COLORS",
    "ECLIPSE_TERMINAL_COLORS",
    "COLOR_THEMES",
    "DEFAULT_THEME",
    "Regex",
    "MulticolorSequences",
]

import sys
import os
from enum import IntEnum
from re import compile

"""
Sources used:
https://en.wikipedia.org/wiki/ANSI_escape_code
"""

# fmt: off
WHITESPACE = {" ", "\t", "\n", "\r", "\x0b", "\x0c"}
UNIVERSAL_NEWLINES = {
    "\n",   "\r",     "\r\n",   "\x0b",
    "\x0c", "\x1c",   "\x1d",   "\x1e", 
    "\x85", "\u2028", "\u2029",
}
PUNCTUATION = {
    "~", "\\", "%", "'", "@", "_",
    "(", ".", ":", "$", "&", '"',
    "=", "<", "-", "*", "]", ")",
    "^", "/", "[", "{", ",", ";",
    "|", "+", ">", "?", "}", "`",
    "!", "#",
}
PUNCTUATION_AND_WHITESPACE = PUNCTUATION.union(WHITESPACE)
# fmt: on

class ColorMode(IntEnum):
    PALETTE = 5     # 8-bit
    TRUE_COLOR = 2  # 24-bit
    TRUECOLOR = 2   # alias

class Foreground(IntEnum):
    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    WHITE = 37
    SET = 38
    DEFAULT = 39
    BRIGHT_BLACK = 90
    BRIGHT_RED = 91
    BRIGHT_GREEN = 92
    BRIGHT_YELLOW = 93
    BRIGHT_BLUE = 94
    BRIGHT_MAGENTA = 95
    BRIGHT_CYAN = 96
    BRIGHT_WHITE = 97

class Background(IntEnum):
    BLACK = 40
    RED = 41
    GREEN = 42
    YELLOW = 43
    BLUE = 44
    MAGENTA = 45
    CYAN = 46
    WHITE = 47
    SET = 48
    DEFAULT = 49
    BRIGHT_BLACK = 100
    BRIGHT_RED = 101
    BRIGHT_GREEN = 102
    BRIGHT_YELLOW = 103
    BRIGHT_BLUE = 104
    BRIGHT_MAGENTA = 105
    BRIGHT_CYAN = 106
    BRIGHT_WHITE = 107

class Underline(IntEnum):
    SET = 58
    DEFAULT = 59

class UnderlineMode(IntEnum):
    SINGLE = 1
    DOUBLE = 2
    CURLY = 3
    DOTTED = 4
    DASHED = 5

class SGR(IntEnum):
    RESET = 0
    BOLD = 1
    DIM = 2
    ITALIC = 3
    UNDERLINE = 4
    SLOW_BLINK = 5
    RAPID_BLINK = 6
    INVERT = 7
    CONCEAL = 8
    STRIKETHROUGH = 9
    DEFAULT = 10
    DOUBLE_UNDERLINE = 21
    NORMAL_INTENSITY = 22
    NOT_ITALIC = 23
    NOT_UNDERLINED = 24
    NOT_BLINKING = 25
    INVERSE_OFF = 27
    REVEAL = 28
    NOT_CROSSED_OUT = 29
    FRAMED = 51
    ENCIRCLED = 52
    OVERLINED = 53
    NOT_FRAMED_OR_ENCIRCLED = 54
    NOT_OVERLINED = 55
    SUPERSCRIPT = 73
    SUBSCRIPT = 74
    RESET_SCRIPT = 75


# 8-bit to RGB mapping
COLORS_8BIT = {
    0: (  0,   0,   0),   # Black
    1: (205,   0,   0),   # Red
    2: (  0, 205,   0),   # Green
    3: (205, 205,   0),   # Yellow
    4: (  0,   0, 238),   # Blue
    5: (205,   0, 205),   # Magenta
    6: (  0, 205, 205),   # Cyan
    7: (229, 229, 229),   # White (light gray)
    8: (127, 127, 127),   # Bright Black (Gray)
    9: (255,   0,   0),   # Bright Red
    10: (  0, 255,   0),  # Bright Green
    11: (255, 255,   0),  # Bright Yellow
    12: ( 92,  92, 255),  # Bright Blue
    13: (255,   0, 255),  # Bright Magenta
    14: (  0, 255, 255),  # Bright Cyan
    15: (255, 255, 255),  # Bright White

    # 6x6x6 color cube (r,g,b ∈ {0,95,135,175,215,255})
    16: (  0,   0,   0),  # Black (cube)
    17: (  0,   0,  95),  # Very dark blue
    18: (  0,   0, 135),  # Dark blue
    19: (  0,   0, 175),  # Medium blue
    20: (  0,   0, 215),  # Bright blue
    21: (  0,   0, 255),  # Vivid blue
    22: (  0,  95,   0),  # Very dark green
    23: (  0,  95,  95),  # Very dark cyan (teal)
    24: (  0,  95, 135),  # Dark cyan (teal)
    25: (  0,  95, 175),  # Cyan-blue
    26: (  0,  95, 215),  # Bright cyan-blue
    27: (  0,  95, 255),  # Vivid cyan-blue
    28: (  0, 135,   0),  # Dark green
    29: (  0, 135,  95),  # Dark sea green
    30: (  0, 135, 135),  # Dark cyan
    31: (  0, 135, 175),  # Medium cyan
    32: (  0, 135, 215),  # Bright cyan
    33: (  0, 135, 255),  # Vivid cyan
    34: (  0, 175,   0),  # Medium green
    35: (  0, 175,  95),  # Medium sea green
    36: (  0, 175, 135),  # Sea green
    37: (  0, 175, 175),  # Medium aquamarine
    38: (  0, 175, 215),  # Bright aquamarine
    39: (  0, 175, 255),  # Vivid aquamarine
    40: (  0, 215,   0),  # Bright green
    41: (  0, 215,  95),  # Bright sea green
    42: (  0, 215, 135),  # Spring green
    43: (  0, 215, 175),  # Medium turquoise
    44: (  0, 215, 215),  # Bright turquoise
    45: (  0, 215, 255),  # Vivid turquoise
    46: (  0, 255,   0),  # Vivid green
    47: (  0, 255,  95),  # Vivid spring green
    48: (  0, 255, 135),  # Light spring green
    49: (  0, 255, 175),  # Medium spring green
    50: (  0, 255, 215),  # Light turquoise
    51: (  0, 255, 255),  # Vivid cyan
    52: ( 95,   0,   0),  # Very dark red
    53: ( 95,   0,  95),  # Very dark magenta
    54: ( 95,   0, 135),  # Dark magenta
    55: ( 95,   0, 175),  # Medium purple
    56: ( 95,   0, 215),  # Bright purple
    57: ( 95,   0, 255),  # Vivid purple
    58: ( 95,  95,   0),  # Very dark olive
    59: ( 95,  95,  95),  # Very dark gray
    60: ( 95,  95, 135),  # Very dark slate blue
    61: ( 95,  95, 175),  # Dark slate blue
    62: ( 95,  95, 215),  # Slate blue
    63: ( 95,  95, 255),  # Bright slate blue
    64: ( 95, 135,   0),  # Dark olive green
    65: ( 95, 135,  95),  # Dark desaturated green
    66: ( 95, 135, 135),  # Dark desaturated cyan
    67: ( 95, 135, 175),  # Steel blue (dark)
    68: ( 95, 135, 215),  # Steel blue
    69: ( 95, 135, 255),  # Light steel blue
    70: ( 95, 175,   0),  # Olive green
    71: ( 95, 175,  95),  # Medium desaturated green
    72: ( 95, 175, 135),  # Medium sea green
    73: ( 95, 175, 175),  # Cadet blue
    74: ( 95, 175, 215),  # Sky blue (muted)
    75: ( 95, 175, 255),  # Light sky blue
    76: ( 95, 215,   0),  # Yellow-green (olive)
    77: ( 95, 215,  95),  # Pale green
    78: ( 95, 215, 135),  # Sea green (light)
    79: ( 95, 215, 175),  # Aquamarine
    80: ( 95, 215, 215),  # Light aquamarine
    81: ( 95, 215, 255),  # Pale turquoise
    82: ( 95, 255,   0),  # Chartreuse
    83: ( 95, 255,  95),  # Light green
    84: ( 95, 255, 135),  # Mint green
    85: ( 95, 255, 175),  # Aquamarine (light)
    86: ( 95, 255, 215),  # Turquoise (light)
    87: ( 95, 255, 255),  # Light cyan
    88: (135,   0,   0),  # Dark red
    89: (135,   0,  95),  # Dark magenta (red-violet)
    90: (135,   0, 135),  # Magenta (dark)
    91: (135,   0, 175),  # Purple (dark)
    92: (135,   0, 215),  # Purple (bright)
    93: (135,   0, 255),  # Vivid violet
    94: (135,  95,   0),  # Dark orange-brown
    95: (135,  95,  95),  # Muted red (rose)
    96: (135,  95, 135),  # Muted magenta
    97: (135,  95, 175),  # Muted purple
    98: (135,  95, 215),  # Light purple
    99: (135,  95, 255),  # Lavender (vivid)
    100: (135, 135,   0), # Dark yellow-olive
    101: (135, 135,  95), # Olive drab (dark)
    102: (135, 135, 135), # Gray
    103: (135, 135, 175), # Grayish slate blue
    104: (135, 135, 215), # Light slate blue
    105: (135, 135, 255), # Periwinkle
    106: (135, 175,   0), # Olive green (brighter)
    107: (135, 175,  95), # Sage green
    108: (135, 175, 135), # Desaturated green
    109: (135, 175, 175), # Desaturated cyan
    110: (135, 175, 215), # Light steel blue
    111: (135, 175, 255), # Light sky blue (bright)
    112: (135, 215,   0), # Yellow-green
    113: (135, 215,  95), # Light yellow-green
    114: (135, 215, 135), # Pale green (light)
    115: (135, 215, 175), # Aquamarine (pale)
    116: (135, 215, 215), # Pale cyan
    117: (135, 215, 255), # Powder blue
    118: (135, 255,   0), # Lime green
    119: (135, 255,  95), # Light lime green
    120: (135, 255, 135), # Light green (pastel)
    121: (135, 255, 175), # Mint (light)
    122: (135, 255, 215), # Light turquoise (pastel)
    123: (135, 255, 255), # Very light cyan
    124: (175,   0,   0), # Medium red
    125: (175,   0,  95), # Crimson (dark)
    126: (175,   0, 135), # Medium magenta
    127: (175,   0, 175), # Purple
    128: (175,   0, 215), # Vivid purple
    129: (175,   0, 255), # Electric purple
    130: (175,  95,   0), # Brown (orange-brown)
    131: (175,  95,  95), # Rosy brown
    132: (175,  95, 135), # Rose
    133: (175,  95, 175), # Orchid (muted)
    134: (175,  95, 215), # Medium orchid
    135: (175,  95, 255), # Light orchid
    136: (175, 135,   0), # Olive (brownish)
    137: (175, 135,  95), # Tan
    138: (175, 135, 135), # Rosy tan
    139: (175, 135, 175), # Thistle
    140: (175, 135, 215), # Light purple (pastel)
    141: (175, 135, 255), # Lavender (light)
    142: (175, 175,   0), # Yellow (muted)
    143: (175, 175,  95), # Khaki
    144: (175, 175, 135), # Dark khaki
    145: (175, 175, 175), # Light gray
    146: (175, 175, 215), # Light periwinkle
    147: (175, 175, 255), # Very light periwinkle
    148: (175, 215,   0), # Yellow-green (bright)
    149: (175, 215,  95), # Light yellow-green
    150: (175, 215, 135), # Pale yellow-green
    151: (175, 215, 175), # Pale green
    152: (175, 215, 215), # Pale cyan (muted)
    153: (175, 215, 255), # Very light sky blue
    154: (175, 255,   0), # Chartreuse (bright)
    155: (175, 255,  95), # Light chartreuse
    156: (175, 255, 135), # Light lime
    157: (175, 255, 175), # Mint (pale)
    158: (175, 255, 215), # Mint cream (tinted)
    159: (175, 255, 255), # Very light cyan (pale)
    160: (215,   0,   0), # Bright red
    161: (215,   0,  95), # Bright crimson
    162: (215,   0, 135), # Bright magenta
    163: (215,   0, 175), # Bright purple-magenta
    164: (215,   0, 215), # Magenta (vivid)
    165: (215,   0, 255), # Electric magenta
    166: (215,  95,   0), # Orange
    167: (215,  95,  95), # Light coral
    168: (215,  95, 135), # Light crimson
    169: (215,  95, 175), # Orchid (light)
    170: (215,  95, 215), # Plum
    171: (215,  95, 255), # Light plum
    172: (215, 135,   0), # Goldenrod (dark)
    173: (215, 135,  95), # Sandy brown
    174: (215, 135, 135), # Rosy brown (light)
    175: (215, 135, 175), # Thistle (light)
    176: (215, 135, 215), # Violet (light)
    177: (215, 135, 255), # Lavender (bright)
    178: (215, 175,   0), # Goldenrod
    179: (215, 175,  95), # Tan (light)
    180: (215, 175, 135), # Peach
    181: (215, 175, 175), # Light rosy brown
    182: (215, 175, 215), # Mauve
    183: (215, 175, 255), # Lavender blush (tinted)
    184: (215, 215,   0), # Yellow
    185: (215, 215,  95), # Light khaki
    186: (215, 215, 135), # Pale khaki
    187: (215, 215, 175), # Very light khaki
    188: (215, 215, 215), # Very light gray
    189: (215, 215, 255), # Very light periwinkle (cool)
    190: (215, 255,   0), # Lime-yellow
    191: (215, 255,  95), # Light lime-yellow
    192: (215, 255, 135), # Light yellow-green (pastel)
    193: (215, 255, 175), # Pale lime
    194: (215, 255, 215), # Mint cream
    195: (215, 255, 255), # Very pale cyan
    196: (255,   0,   0), # Vivid red
    197: (255,   0,  95), # Vivid crimson
    198: (255,   0, 135), # Vivid magenta
    199: (255,   0, 175), # Hot pink (deep)
    200: (255,   0, 215), # Hot magenta
    201: (255,   0, 255), # Vivid magenta (fuchsia)
    202: (255,  95,   0), # Vivid orange
    203: (255,  95,  95), # Light salmon
    204: (255,  95, 135), # Light coral (bright)
    205: (255,  95, 175), # Pink (bright)
    206: (255,  95, 215), # Hot pink
    207: (255,  95, 255), # Pink (vivid)
    208: (255, 135,   0), # Orange (bright)
    209: (255, 135,  95), # Light orange
    210: (255, 135, 135), # Light salmon (soft)
    211: (255, 135, 175), # Light pink
    212: (255, 135, 215), # Orchid (light)
    213: (255, 135, 255), # Pink (light vivid)
    214: (255, 175,   0), # Orange (soft)
    215: (255, 175,  95), # Peach (bright)
    216: (255, 175, 135), # Peach
    217: (255, 175, 175), # Light pink (pale)
    218: (255, 175, 215), # Pink (pale)
    219: (255, 175, 255), # Light pink (very pale)
    220: (255, 215,   0), # Gold
    221: (255, 215,  95), # Light gold
    222: (255, 215, 135), # Light goldenrod
    223: (255, 215, 175), # Very light goldenrod
    224: (255, 215, 215), # Very light pink
    225: (255, 215, 255), # Very light pink (cool)
    226: (255, 255,   0), # Yellow (vivid)
    227: (255, 255,  95), # Light yellow (vivid)
    228: (255, 255, 135), # Light yellow
    229: (255, 255, 175), # Very light yellow
    230: (255, 255, 215), # Ivory (warm)
    231: (255, 255, 255), # White

    # Grayscale ramp
    232: (  8,   8,   8),  # Grey3
    233: ( 18,  18,  18),  # Grey7
    234: ( 28,  28,  28),  # Grey11
    235: ( 38,  38,  38),  # Grey15
    236: ( 48,  48,  48),  # Grey19
    237: ( 58,  58,  58),  # Grey23
    238: ( 68,  68,  68),  # Grey27
    239: ( 78,  78,  78),  # Grey30
    240: ( 88,  88,  88),  # Grey35
    241: ( 98,  98,  98),  # Grey39
    242: (108, 108, 108),  # Grey42
    243: (118, 118, 118),  # Grey46
    244: (128, 128, 128),  # Grey50
    245: (138, 138, 138),  # Grey54
    246: (148, 148, 148),  # Grey58
    247: (158, 158, 158),  # Grey62
    248: (168, 168, 168),  # Grey66
    249: (178, 178, 178),  # Grey70
    250: (188, 188, 188),  # Grey74
    251: (198, 198, 198),  # Grey78
    252: (208, 208, 208),  # Grey82
    253: (218, 218, 218),  # Grey85
    254: (228, 228, 228),  # Grey89
    255: (238, 238, 238),  # Grey93
}

# 4-bit to RGB mapping using themes
# VGA Theme RGB Values
VGA_COLORS = {
    30:  (0, 0, 0),        # FG Black
    31:  (170, 0, 0),      # FG Red
    32:  (0, 170, 0),      # FG Green
    33:  (170, 85, 0),     # FG Yellow
    34:  (0, 0, 170),      # FG Blue
    35:  (170, 0, 170),    # FG Magenta
    36:  (0, 170, 170),    # FG Cyan
    37:  (170, 170, 170),  # FG White
    40:  (0, 0, 0),        # BG Black
    41:  (170, 0, 0),      # BG Red
    42:  (0, 170, 0),      # BG Green
    43:  (170, 85, 0),     # BG Yellow
    44:  (0, 0, 170),      # BG Blue
    45:  (170, 0, 170),    # BG Magenta
    46:  (0, 170, 170),    # BG Cyan
    47:  (170, 170, 170),  # BG White
    90:  (85, 85, 85),     # FG Bright Black (Gray)
    91:  (255, 85, 85),    # FG Bright Red
    92:  (85, 255, 85),    # FG Bright Green
    93:  (255, 255, 85),   # FG Bright Yellow
    94:  (85, 85, 255),    # FG Bright Blue
    95:  (255, 85, 255),   # FG Bright Magenta
    96:  (85, 255, 255),   # FG Bright Cyan
    97:  (255, 255, 255),  # FG Bright White
    100: (85, 85, 85),     # BG Bright Black (Gray)
    101: (255, 85, 85),    # BG Bright Red
    102: (85, 255, 85),    # BG Bright Green
    103: (255, 255, 85),   # BG Bright Yellow
    104: (85, 85, 255),    # BG Bright Blue
    105: (255, 85, 255),   # BG Bright Magenta
    106: (85, 255, 255),   # BG Bright Cyan
    107: (255, 255, 255),  # BG Bright White
}

# Windows XP Console Theme RGB Values
WINDOWS_XP_CONSOLE_COLORS = {
    30:  (0, 0, 0),        # FG Black
    31:  (128, 0, 0),      # FG Red
    32:  (0, 128, 0),      # FG Green
    33:  (128, 128, 0),    # FG Yellow
    34:  (0, 0, 128),      # FG Blue
    35:  (128, 0, 128),    # FG Magenta
    36:  (0, 128, 128),    # FG Cyan
    37:  (192, 192, 192),  # FG White
    40:  (0, 0, 0),        # BG Black
    41:  (128, 0, 0),      # BG Red
    42:  (0, 128, 0),      # BG Green
    43:  (128, 128, 0),    # BG Yellow
    44:  (0, 0, 128),      # BG Blue
    45:  (128, 0, 128),    # BG Magenta
    46:  (0, 128, 128),    # BG Cyan
    47:  (192, 192, 192),  # BG White
    90:  (128, 128, 128),  # FG Bright Black (Gray)
    91:  (255, 0, 0),      # FG Bright Red
    92:  (0, 255, 0),      # FG Bright Green
    93:  (255, 255, 0),    # FG Bright Yellow
    94:  (0, 0, 255),      # FG Bright Blue
    95:  (255, 0, 255),    # FG Bright Magenta
    96:  (0, 255, 255),    # FG Bright Cyan
    97:  (255, 255, 255),  # FG Bright White
    100: (128, 128, 128),  # BG Bright Black (Gray)
    101: (255, 0, 0),      # BG Bright Red
    102: (0, 255, 0),      # BG Bright Green
    103: (255, 255, 0),    # BG Bright Yellow
    104: (0, 0, 255),      # BG Bright Blue
    105: (255, 0, 255),    # BG Bright Magenta
    106: (0, 255, 255),    # BG Bright Cyan
    107: (255, 255, 255),  # BG Bright White
}

# Windows PowerShell 1.0-6.0 Theme RGB Values
WINDOWS_POWERSHELL_COLORS = {
    30:  (0, 0, 0),        # FG Black
    31:  (128, 0, 0),      # FG Red
    32:  (0, 128, 0),      # FG Green
    33:  (238, 237, 240),  # FG Yellow
    34:  (0, 0, 128),      # FG Blue
    35:  (1, 36, 86),      # FG Magenta
    36:  (0, 128, 128),    # FG Cyan
    37:  (192, 192, 192),  # FG White
    40:  (0, 0, 0),        # BG Black
    41:  (128, 0, 0),      # BG Red
    42:  (0, 128, 0),      # BG Green
    43:  (238, 237, 240),  # BG Yellow
    44:  (0, 0, 128),      # BG Blue
    45:  (1, 36, 86),      # BG Magenta
    46:  (0, 128, 128),    # BG Cyan
    47:  (192, 192, 192),  # BG White
    90:  (128, 128, 128),  # FG Bright Black (Gray)
    91:  (255, 0, 0),      # FG Bright Red
    92:  (0, 255, 0),      # FG Bright Green
    93:  (255, 255, 0),    # FG Bright Yellow
    94:  (0, 0, 255),      # FG Bright Blue
    95:  (255, 0, 255),    # FG Bright Magenta
    96:  (0, 255, 255),    # FG Bright Cyan
    97:  (255, 255, 255),  # FG Bright White
    100: (128, 128, 128),  # BG Bright Black (Gray)
    101: (255, 0, 0),      # BG Bright Red
    102: (0, 255, 0),      # BG Bright Green
    103: (255, 255, 0),    # BG Bright Yellow
    104: (0, 0, 255),      # BG Bright Blue
    105: (255, 0, 255),    # BG Bright Magenta
    106: (0, 255, 255),    # BG Bright Cyan
    107: (255, 255, 255),  # BG Bright White
}

# Visual Studio Code Theme RGB Values
VSCODE_COLORS = {
    30:  (0, 0, 0),        # FG Black
    31:  (205, 49, 49),    # FG Red
    32:  (13, 188, 121),   # FG Green
    33:  (229, 229, 16),   # FG Yellow
    34:  (36, 114, 200),   # FG Blue
    35:  (188, 63, 188),   # FG Magenta
    36:  (17, 168, 205),   # FG Cyan
    37:  (229, 229, 229),  # FG White
    40:  (0, 0, 0),        # BG Black
    41:  (205, 49, 49),    # BG Red
    42:  (13, 188, 121),   # BG Green
    43:  (229, 229, 16),   # BG Yellow
    44:  (36, 114, 200),   # BG Blue
    45:  (188, 63, 188),   # BG Magenta
    46:  (17, 168, 205),   # BG Cyan
    47:  (229, 229, 229),  # BG White
    90:  (102, 102, 102),  # FG Bright Black (Gray)
    91:  (241, 76, 76),    # FG Bright Red
    92:  (35, 209, 139),   # FG Bright Green
    93:  (245, 245, 67),   # FG Bright Yellow
    94:  (59, 142, 234),   # FG Bright Blue
    95:  (214, 112, 214),  # FG Bright Magenta
    96:  (41, 184, 219),   # FG Bright Cyan
    97:  (229, 229, 229),  # FG Bright White
    100: (102, 102, 102),  # BG Bright Black (Gray)
    101: (241, 76, 76),    # BG Bright Red
    102: (35, 209, 139),   # BG Bright Green
    103: (245, 245, 67),   # BG Bright Yellow
    104: (59, 142, 234),   # BG Bright Blue
    105: (214, 112, 214),  # BG Bright Magenta
    106: (41, 184, 219),   # BG Bright Cyan
    107: (229, 229, 229),  # BG Bright White
}

# Windows 10 Console Theme RGB Values
WINDOWS_10_CONSOLE_COLORS = {
    30:  (12, 12, 12),     # FG Black
    31:  (197, 15, 31),    # FG Red
    32:  (19, 161, 14),    # FG Green
    33:  (193, 156, 0),    # FG Yellow
    34:  (0, 55, 218),     # FG Blue
    35:  (136, 23, 152),   # FG Magenta
    36:  (58, 150, 221),   # FG Cyan
    37:  (204, 204, 204),  # FG White
    40:  (12, 12, 12),     # BG Black
    41:  (197, 15, 31),    # BG Red
    42:  (19, 161, 14),    # BG Green
    43:  (193, 156, 0),    # BG Yellow
    44:  (0, 55, 218),     # BG Blue
    45:  (136, 23, 152),   # BG Magenta
    46:  (58, 150, 221),   # BG Cyan
    47:  (204, 204, 204),  # BG White
    90:  (118, 118, 118),  # FG Bright Black (Gray)
    91:  (231, 72, 86),    # FG Bright Red
    92:  (22, 198, 12),    # FG Bright Green
    93:  (249, 241, 165),  # FG Bright Yellow
    94:  (59, 120, 255),   # FG Bright Blue
    95:  (180, 0, 158),    # FG Bright Magenta
    96:  (97, 214, 214),   # FG Bright Cyan
    97:  (242, 242, 242),  # FG Bright White
    100: (118, 118, 118),  # BG Bright Black (Gray)
    101: (231, 72, 86),    # BG Bright Red
    102: (22, 198, 12),    # BG Bright Green
    103: (249, 241, 165),  # BG Bright Yellow
    104: (59, 120, 255),   # BG Bright Blue
    105: (180, 0, 158),    # BG Bright Magenta
    106: (97, 214, 214),   # BG Bright Cyan
    107: (242, 242, 242),  # BG Bright White
}

# Terminal.app (macOS) Theme RGB Values
TERMINAL_APP_COLORS = {
    30:  (0, 0, 0),        # FG Black
    31:  (153, 0, 0),      # FG Red
    32:  (0, 166, 0),      # FG Green
    33:  (153, 153, 0),    # FG Yellow
    34:  (0, 0, 178),      # FG Blue
    35:  (178, 0, 178),    # FG Magenta
    36:  (0, 166, 178),    # FG Cyan
    37:  (191, 191, 191),  # FG White
    40:  (0, 0, 0),        # BG Black
    41:  (153, 0, 0),      # BG Red
    42:  (0, 166, 0),      # BG Green
    43:  (153, 153, 0),    # BG Yellow
    44:  (0, 0, 178),      # BG Blue
    45:  (178, 0, 178),    # BG Magenta
    46:  (0, 166, 178),    # BG Cyan
    47:  (191, 191, 191),  # BG White
    90:  (102, 102, 102),  # FG Bright Black (Gray)
    91:  (230, 0, 0),      # FG Bright Red
    92:  (0, 217, 0),      # FG Bright Green
    93:  (230, 230, 0),    # FG Bright Yellow
    94:  (0, 0, 255),      # FG Bright Blue
    95:  (230, 0, 230),    # FG Bright Magenta
    96:  (0, 230, 230),    # FG Bright Cyan
    97:  (230, 230, 230),  # FG Bright White
    100: (102, 102, 102),  # BG Bright Black (Gray)
    101: (230, 0, 0),      # BG Bright Red
    102: (0, 217, 0),      # BG Bright Green
    103: (230, 230, 0),    # BG Bright Yellow
    104: (0, 0, 255),      # BG Bright Blue
    105: (230, 0, 230),    # BG Bright Magenta
    106: (0, 230, 230),    # BG Bright Cyan
    107: (230, 230, 230),  # BG Bright White
}

# PuTTY Theme RGB Values
PUTTY_COLORS = {
    30:  (0, 0, 0),        # FG Black
    31:  (187, 0, 0),      # FG Red
    32:  (0, 187, 0),      # FG Green
    33:  (187, 187, 0),    # FG Yellow
    34:  (0, 0, 187),      # FG Blue
    35:  (187, 0, 187),    # FG Magenta
    36:  (0, 187, 187),    # FG Cyan
    37:  (187, 187, 187),  # FG White
    40:  (0, 0, 0),        # BG Black
    41:  (187, 0, 0),      # BG Red
    42:  (0, 187, 0),      # BG Green
    43:  (187, 187, 0),    # BG Yellow
    44:  (0, 0, 187),      # BG Blue
    45:  (187, 0, 187),    # BG Magenta
    46:  (0, 187, 187),    # BG Cyan
    47:  (187, 187, 187),  # BG White
    90:  (85, 85, 85),     # FG Bright Black (Gray)
    91:  (255, 85, 85),    # FG Bright Red
    92:  (85, 255, 85),    # FG Bright Green
    93:  (255, 255, 85),   # FG Bright Yellow
    94:  (85, 85, 255),    # FG Bright Blue
    95:  (255, 85, 255),   # FG Bright Magenta
    96:  (85, 255, 255),   # FG Bright Cyan
    97:  (255, 255, 255),  # FG Bright White
    100: (85, 85, 85),     # BG Bright Black (Gray)
    101: (255, 85, 85),    # BG Bright Red
    102: (85, 255, 85),    # BG Bright Green
    103: (255, 255, 85),   # BG Bright Yellow
    104: (85, 85, 255),    # BG Bright Blue
    105: (255, 85, 255),   # BG Bright Magenta
    106: (85, 255, 255),   # BG Bright Cyan
    107: (255, 255, 255),  # BG Bright White
}

# mIRC Theme RGB Values
MIRC_COLORS = {
    30:  (0, 0, 0),        # FG Black
    31:  (127, 0, 0),      # FG Red
    32:  (0, 147, 0),      # FG Green
    33:  (252, 127, 0),    # FG Yellow
    34:  (0, 0, 127),      # FG Blue
    35:  (156, 0, 156),    # FG Magenta
    36:  (0, 147, 147),    # FG Cyan
    37:  (210, 210, 210),  # FG White
    40:  (0, 0, 0),        # BG Black
    41:  (127, 0, 0),      # BG Red
    42:  (0, 147, 0),      # BG Green
    43:  (252, 127, 0),    # BG Yellow
    44:  (0, 0, 127),      # BG Blue
    45:  (156, 0, 156),    # BG Magenta
    46:  (0, 147, 147),    # BG Cyan
    47:  (210, 210, 210),  # BG White
    90:  (127, 127, 127),  # FG Bright Black (Gray)
    91:  (255, 0, 0),      # FG Bright Red
    92:  (0, 252, 0),      # FG Bright Green
    93:  (255, 255, 0),    # FG Bright Yellow
    94:  (0, 0, 252),      # FG Bright Blue
    95:  (255, 0, 255),    # FG Bright Magenta
    96:  (0, 255, 255),    # FG Bright Cyan
    97:  (255, 255, 255),  # FG Bright White
    100: (127, 127, 127),  # BG Bright Black (Gray)
    101: (255, 0, 0),      # BG Bright Red
    102: (0, 252, 0),      # BG Bright Green
    103: (255, 255, 0),    # BG Bright Yellow
    104: (0, 0, 252),      # BG Bright Blue
    105: (255, 0, 255),    # BG Bright Magenta
    106: (0, 255, 255),    # BG Bright Cyan
    107: (255, 255, 255),  # BG Bright White
}

# xterm Theme RGB Values
XTERM_COLORS = {
    30:  (0, 0, 0),        # FG Black
    31:  (205, 0, 0),      # FG Red
    32:  (0, 205, 0),      # FG Green
    33:  (205, 205, 0),    # FG Yellow
    34:  (0, 0, 238),      # FG Blue
    35:  (205, 0, 205),    # FG Magenta
    36:  (0, 205, 205),    # FG Cyan
    37:  (229, 229, 229),  # FG White
    40:  (0, 0, 0),        # BG Black
    41:  (205, 0, 0),      # BG Red
    42:  (0, 205, 0),      # BG Green
    43:  (205, 205, 0),    # BG Yellow
    44:  (0, 0, 238),      # BG Blue
    45:  (205, 0, 205),    # BG Magenta
    46:  (0, 205, 205),    # BG Cyan
    47:  (229, 229, 229),  # BG White
    90:  (127, 127, 127),  # FG Bright Black (Gray)
    91:  (255, 0, 0),      # FG Bright Red
    92:  (0, 255, 0),      # FG Bright Green
    93:  (255, 255, 0),    # FG Bright Yellow
    94:  (92, 92, 255),    # FG Bright Blue
    95:  (255, 0, 255),    # FG Bright Magenta
    96:  (0, 255, 255),    # FG Bright Cyan
    97:  (255, 255, 255),  # FG Bright White
    100: (127, 127, 127),  # BG Bright Black (Gray)
    101: (255, 0, 0),      # BG Bright Red
    102: (0, 255, 0),      # BG Bright Green
    103: (255, 255, 0),    # BG Bright Yellow
    104: (92, 92, 255),    # BG Bright Blue
    105: (255, 0, 255),    # BG Bright Magenta
    106: (0, 255, 255),    # BG Bright Cyan
    107: (255, 255, 255),  # BG Bright White
}

# Ubuntu Theme RGB Values
UBUNTU_COLORS = {
    30:  (1, 1, 1),        # FG Black
    31:  (222, 56, 43),    # FG Red
    32:  (57, 181, 74),    # FG Green
    33:  (255, 199, 6),    # FG Yellow
    34:  (0, 111, 184),    # FG Blue
    35:  (118, 38, 113),   # FG Magenta
    36:  (44, 181, 233),   # FG Cyan
    37:  (204, 204, 204),  # FG White
    40:  (1, 1, 1),        # BG Black
    41:  (222, 56, 43),    # BG Red
    42:  (57, 181, 74),    # BG Green
    43:  (255, 199, 6),    # BG Yellow
    44:  (0, 111, 184),    # BG Blue
    45:  (118, 38, 113),   # BG Magenta
    46:  (44, 181, 233),   # BG Cyan
    47:  (204, 204, 204),  # BG White
    90:  (128, 128, 128),  # FG Bright Black (Gray)
    91:  (255, 0, 0),      # FG Bright Red
    92:  (0, 255, 0),      # FG Bright Green
    93:  (255, 255, 0),    # FG Bright Yellow
    94:  (0, 0, 255),      # FG Bright Blue
    95:  (255, 0, 255),    # FG Bright Magenta
    96:  (0, 255, 255),    # FG Bright Cyan
    97:  (255, 255, 255),  # FG Bright White
    100: (128, 128, 128),  # BG Bright Black (Gray)
    101: (255, 0, 0),      # BG Bright Red
    102: (0, 255, 0),      # BG Bright Green
    103: (255, 255, 0),    # BG Bright Yellow
    104: (0, 0, 255),      # BG Bright Blue
    105: (255, 0, 255),    # BG Bright Magenta
    106: (0, 255, 255),    # BG Bright Cyan
    107: (255, 255, 255),  # BG Bright White
}

# Eclipse Terminal Theme RGB Values
ECLIPSE_TERMINAL_COLORS = {
    30:  (0, 0, 0),        # FG Black
    31:  (205, 0, 0),      # FG Red
    32:  (0, 205, 0),      # FG Green
    33:  (205, 205, 0),    # FG Yellow
    34:  (0, 0, 238),      # FG Blue
    35:  (205, 0, 205),    # FG Magenta
    36:  (0, 205, 205),    # FG Cyan
    37:  (229, 229, 229),  # FG White
    40:  (0, 0, 0),        # BG Black
    41:  (205, 0, 0),      # BG Red
    42:  (0, 205, 0),      # BG Green
    43:  (205, 205, 0),    # BG Yellow
    44:  (0, 0, 238),      # BG Blue
    45:  (205, 0, 205),    # BG Magenta
    46:  (0, 205, 205),    # BG Cyan
    47:  (229, 229, 229),  # BG White
    90:  (0, 0, 0),        # FG Bright Black (Gray)
    91:  (255, 0, 0),      # FG Bright Red
    92:  (0, 255, 0),      # FG Bright Green
    93:  (255, 255, 0),    # FG Bright Yellow
    94:  (92, 92, 255),    # FG Bright Blue
    95:  (255, 0, 255),    # FG Bright Magenta
    96:  (0, 255, 255),    # FG Bright Cyan
    97:  (255, 255, 255),  # FG Bright White
    100: (0, 0, 0),        # BG Bright Black (Gray)
    101: (255, 0, 0),      # BG Bright Red
    102: (0, 255, 0),      # BG Bright Green
    103: (255, 255, 0),    # BG Bright Yellow
    104: (92, 92, 255),    # BG Bright Blue
    105: (255, 0, 255),    # BG Bright Magenta
    106: (0, 255, 255),    # BG Bright Cyan
    107: (255, 255, 255),  # BG Bright White
}

# Dictionary mapping theme names to their color dictionaries
COLOR_THEMES = {
    'vga': VGA_COLORS,
    'windows_xp': WINDOWS_XP_CONSOLE_COLORS,
    'powershell': WINDOWS_POWERSHELL_COLORS,
    'vscode': VSCODE_COLORS,
    'windows_10': WINDOWS_10_CONSOLE_COLORS,
    'terminal_app': TERMINAL_APP_COLORS,
    'putty': PUTTY_COLORS,
    'mirc': MIRC_COLORS,
    'xterm': XTERM_COLORS,
    'ubuntu': UBUNTU_COLORS,
    'eclipse': ECLIPSE_TERMINAL_COLORS,
}

if sys.platform == "win32":
    # Windows
    if "pwsh" in os.environ.get("SHELL", "").lower() or "powershell" in os.environ.get("TERM", "").lower():
        DEFAULT_THEME = "powershell"
    elif "vscode" in os.environ.get("TERM_PROGRAM", "").lower():
        DEFAULT_THEME = "vscode"
    elif os.environ.get("WT_SESSION"):
        DEFAULT_THEME = "windows_10"
    else:
        DEFAULT_THEME = "windows_xp"
elif sys.platform == "darwin":
    # macOS
    if "vscode" in os.environ.get("TERM_PROGRAM", "").lower():
        DEFAULT_THEME = "vscode"
    else:
        DEFAULT_THEME = "terminal_app"
else:
    # Linux/Unix systems
    term_program = os.environ.get("TERM_PROGRAM", "").lower()
    term = os.environ.get("TERM", "").lower()
    
    if "vscode" in term_program:
        DEFAULT_THEME = "vscode"
    elif "putty" in term:
        DEFAULT_THEME = "putty"
    elif "mirc" in term:
        DEFAULT_THEME = "mirc"
    elif "ubuntu" in term:
        DEFAULT_THEME = "ubuntu"
    elif "eclipse" in term_program:
        DEFAULT_THEME = "eclipse"
    else:
        DEFAULT_THEME = "xterm"

class Regex:
    """Compiled REs used in the library."""

    INT8 = compile(r"(?:25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})")
    SEP = r"(?:;|:)"
    SET8 = compile(rf"(?:(?:38|48|58){SEP}5{SEP}{INT8.pattern})")
    SET24 = compile(
        rf"(?:(?:38|48|58){SEP}2(?:;|:){{1,2}}{INT8.pattern}(?:{SEP}{INT8.pattern}){r'{0,2}'})"
    )
    SGR_PARAM = compile(
        rf"(?:{SET24.pattern}|{SET8.pattern}|[0-9]|2[0-9]|3[0-79]|4[0-79]|5[0-79]|[6-9][0-9]|10[0-7])"
    )
    ANSI_SEQ = compile(
        r"(?:\x1b[@-Z\\-_]|[\x80-\x9a\x9c-\x9f]|(?:\x1b\[|\x9b)[0-?]*[ -/]*[@-~])"
    )
    ARGUMENTS = r"\((?:\s*{}\s*(?:,\s*{}\s*){quantifier}\s*)\)"
    INT_OR_FLOAT = r"\-?\d+(?:\.\d+)?"
    INT_OR_FLOAT_OR_INF = rf"(?:{INT_OR_FLOAT}|\-?inf)"
    MULTICOLOR_INSTRUCTION = compile(
        r"(?P<color>[rgb])"
        r"(?P<operator>[\+\-\=\>])"
        r"(?P<value>"
        r"(?:\d+(?:\.\d+)?)|"
        rf"(?:random{ARGUMENTS.format(INT_OR_FLOAT, INT_OR_FLOAT, quantifier=r'{1}')})|"
        r"(?:(?:fg|bg|ul)_[rgb])"
        r")\:"
        r"(?P<mode>fg|bg|ul)?"
        rf"(?P<minmax>minmax{ARGUMENTS.format(INT_OR_FLOAT_OR_INF, INT_OR_FLOAT_OR_INF, quantifier=r'{1}')})?"
    )
    MULTICOLOR_COMMAND = compile(r"(?P<reset>\?|\?\?)?(?P<repeat>repeat\(\d+\))?$")


class MulticolorSequences:
    """
    MulticolorSequence specification:
    - start command is separated by "$"
    - commands are separated by "#"
    - instructions are concatenated with "|"

    SEQUENCE START:
        identical to INSTRUCTION BODY

    INSTRUCTION BODY:
        - [important] color:
            - "r": red
            - "g": green
            - "b": blue
        - [important] operator:
            - ">": goto, automatically expands to the given value
            - "=": equal, assigns a value
            - "+": add, adds a value
            - "-": sub, subtracts a value
        - [important] value:
            - int
            - float
            - random [format: "random(x,y)"]
            - special var ("fg" or "bg" or "ul") + "_" + ("r" or "g" or "b")
        - [important] options ":"
            - [optional] mode: [default: "fg"]
                - "fg": foreground
                - "bg": background
                - "ul": underline
            - [optional] min, max values: [format: "minmax(x,y)"] [default: "minmax(0,255)"]
                - int
                - float
                - inf

    COMMAND END:
        - [optional] reset:
            - "?": to the previous RGB values
            - "??": to the start RGB values
        - [optional] repeat:
            - int
            - "auto": calculates the repeat by itself

    SEQUENCE END:
        - [optional] flag:
            - "@": reverse
            - "!": mirror
            - "&": cycle
            - "*": skipfirst, start with the given r, g, b
    """

    RAINBOW = (
        "r=255:|g=0:|b=0:  $"
        "g>255:repeat(auto)#"
        "r>0:repeat(auto)  #"
        "b>255:repeat(auto)#"
        "g>0:repeat(auto)  #"
        "r>255:repeat(auto)#"
        "b>0:repeat(auto)  &*"
    )
    REVERSED_RAINBOW = f"{RAINBOW[:-2]} @&*"
