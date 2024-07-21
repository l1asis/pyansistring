from enum import IntEnum

"""
Sources used:
https://en.wikipedia.org/wiki/ANSI_escape_code
"""

WHITESPACE = {" ", "\t", "\n", "\r", "\x0b", "\x0c"}
UNIVERSAL_NEWLINES = {"\n", "\r", "\r\n", "\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029"}
PUNCTUATION = {'~', '\\', '%', "'", '@', '_', '(', '.', ':', '$', '&', '"', '=', '<', '-', '*', ']', ')', '^', '/', '[', '{', ',', ';', '|', '+', '>', '?', '}', '`', '!', '#'}
PUNCTUATION_AND_WHITESPACE = PUNCTUATION.union(WHITESPACE)

class Foreground(IntEnum):
    """SGR foreground color parameters."""
    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    WHITE = 37
    SET = 38 # Next arguments are 5;n or 2;r;g;b
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
    """SGR background color parameters."""
    BLACK = 40
    RED = 41
    GREEN = 42
    YELLOW = 43
    BLUE = 44
    MAGENTA = 45
    CYAN = 46
    WHITE = 47
    SET = 48 # Next arguments are 5;n or 2;r;g;b
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
    """SGR underline color parameters."""
    SET = 58 # Next arguments are 5;n or 2;r;g;b
    DEFAULT = 59

class SGR(IntEnum):
    """SGR (Select Graphic Rendition) parameters."""
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
    ALTERNATIVE_1 = 11
    ALTERNATIVE_2 = 12
    ALTERNATIVE_3 = 13
    ALTERNATIVE_4 = 14
    ALTERNATIVE_5 = 15
    ALTERNATIVE_6 = 16
    ALTERNATIVE_7 = 17
    ALTERNATIVE_8 = 18
    ALTERNATIVE_9 = 19
    GOTHIC = 20
    DOUBLE_UNDERLINE = 21
    NORMAL_INTENSITY = 22
    NEITHER_ITALIC_NOR_BLACKLETTER = 23
    NOT_UNDERLINED = 24
    NOT_BLINKING = 25
    PROPORTIONAL_SPACING = 26
    NOT_REVERSED = 27
    REVEAL = 28
    NOT_CROSSED_OUT = 29
    DISABLE_PROPORTIONAL_SPACING = 50
    FRAMED = 51
    ENCIRCLED = 52
    OVERLINED = 53
    NEITHER_FRAMED_NOR_ENCIRCLED = 54
    NOT_OVERLINED = 55
    IDEOGRAM_UNDERLINE = 60
    IDEOGRAD_DOUBLE_UNDERLINE = 61
    IDEOGRAM_OVERLINE = 62
    IDEOGRAM_DOUBLE_OVERLINE = 63
    IDEOGRAM_STRESS_MARKING = 64
    NO_IDEOGRAM_ATTRIBUTES = 65
    SUPERSCRIPT = 73
    SUBSCRIPT = 74
    NEITHER_SUPERSCRIPT_NOR_SUBSCRIPT = 75