__all__ = [
    "WHITESPACE",
    "UNIVERSAL_NEWLINES",
    "PUNCTUATION",
    "PUNCTUATION_AND_WHITESPACE",
    "Foreground",
    "Background",
    "Underline",
    "SGR",
    "Regex",
    "MulticolorSequences",
]

from enum import IntEnum
from re import compile

"""
Sources used:
https://en.wikipedia.org/wiki/ANSI_escape_code
"""

WHITESPACE = {" ", "\t", "\n", "\r", "\x0b", "\x0c"}
UNIVERSAL_NEWLINES = {
    "\n", "\r", "\r\n", "\x0b",
    "\x0c", "\x1c", "\x1d", "\x1e", 
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
    SET = 38  # Next arguments are 5;n or 2;r;g;b
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
    SET = 48  # Next arguments are 5;n or 2;r;g;b
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

    SET = 58  # Next arguments are 5;n or 2;r;g;b
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


class Regex:
    """Compiled REs used in the library."""

    INT8 = compile(r"(?:25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})")
    SET8 = compile(rf"(?:(?:38|48|58);5;{INT8.pattern})")
    SET24 = compile(rf"(?:(?:38|48|58);2;{INT8.pattern}(?:;{INT8.pattern}){r'{0,2}'})")
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
