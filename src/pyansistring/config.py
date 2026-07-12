from __future__ import annotations

import os as _os
import platform as _platform
import re as _re
import sys as _sys
from dataclasses import dataclass as _dataclass
from typing import TYPE_CHECKING, Literal as _Literal

if TYPE_CHECKING:
    from ._types import ThemeName as _ThemeName

from .constants import (
    THEME_NAMES as _THEME_NAMES,
    ColorSupportLevel as _ColorSupportLevel,
)


def _get_flags() -> set[str]:
    """
    Retrieve command-line flags passed to the host process.

    Parses `sys.argv` to extract all arguments starting with a hyphen (`-`).
    Stops parsing if the double-hyphen terminator (`--`) is encountered,
    as subsequent arguments are treated as positional.

    Returns
    -------
    set[str]
        A set containing the extracted command-line flags in lowercase.
    """
    if not hasattr(_sys, "argv"):
        return set()
    try:
        term_pos = _sys.argv.index("--")
        args = _sys.argv[1:term_pos]
    except ValueError:
        args = _sys.argv[1:]

    return {arg.lower().lstrip("-") for arg in args if arg.startswith("-")}


def _env_force_color() -> _ColorSupportLevel | None:
    """
    Determine the color support level from the FORCE_COLOR environment variable.

    Evaluates `FORCE_COLOR` according to community standards. "true" or an
    empty string defaults to 4-bit support. Numeric values 1, 2, and 3 map
    to 4-bit, 8-bit, and 24-bit TrueColor respectively. "false" or "0"
    disables color entirely.

    Returns
    -------
    ColorSupportLevel | None
        The corresponding color support level if `FORCE_COLOR` is present
        and valid, otherwise `None`.
    """
    if "FORCE_COLOR" not in _os.environ:
        return None

    val = _os.environ["FORCE_COLOR"]
    if val.lower() == "true":
        return _ColorSupportLevel.BIT4
    if val.lower() == "false":
        return _ColorSupportLevel.NONE
    if not val:
        return _ColorSupportLevel.BIT4

    try:
        level = min(int(val), 3)
        if level in [0, 1, 2, 3]:
            return _ColorSupportLevel(level)
    except ValueError:
        pass

    return None


def _detect_color_support(
    is_tty: bool | None = None, sniff_flags: bool = True
) -> _ColorSupportLevel:
    """
    Detect the level of color support in the current terminal environment.

    Respects standard environment variables (NO_COLOR, CLICOLOR, FORCE_COLOR)
    and the library-specific `PYANSISTRING_COLOR_SUPPORT` (highest precedence),
    inspecting terminal and OS capabilities to determine maximum safe depth.

    Parameters
    ----------
    is_tty : bool | None, default None
        Whether the output stream is a TTY. If None, it is auto-detected
        from `sys.stdout.isatty()`.
    sniff_flags : bool, default True
        Whether to check `sys.argv` for color-forcing CLI flags (e.g., --color).

    Returns
    -------
    ColorSupportLevel
        The detected color support level ranging from NONE (0) to TRUECOLOR (3).
    """
    env = _os.environ
    flags = _get_flags()

    if env_override := env.get("PYANSISTRING_COLOR_SUPPORT"):
        mapping = {
            "none": _ColorSupportLevel.NONE,
            "4bit": _ColorSupportLevel.BIT4,
            "8bit": _ColorSupportLevel.BIT8,
            "24bit": _ColorSupportLevel.BIT24,
        }
        if (value := mapping.get(env_override.lower())) is not None:
            return value

    flag_force_color = None
    if sniff_flags:
        if (
            "no-color" in flags
            or "no-colors" in flags
            or "color=false" in flags
            or "color=never" in flags
        ):
            flag_force_color = _ColorSupportLevel.NONE
        elif (
            "color=16m" in flags or "color=full" in flags or "color=truecolor" in flags
        ):
            flag_force_color = _ColorSupportLevel.BIT24
        elif "color=256" in flags:
            flag_force_color = _ColorSupportLevel.BIT8
        elif (
            "color" in flags
            or "colors" in flags
            or "color=true" in flags
            or "color=always" in flags
        ):
            flag_force_color = _ColorSupportLevel.BIT4

    if flag_force_color is None and env.get("NO_COLOR", "") != "":
        return _ColorSupportLevel.NONE

    force_color = (
        flag_force_color if flag_force_color is not None else _env_force_color()
    )
    if force_color is None and env.get("CLICOLOR_FORCE", "0") != "0":
        force_color = _ColorSupportLevel.BIT4

    if force_color is not None:
        return force_color

    if env.get("TERM") == "dumb":
        return _ColorSupportLevel.NONE

    if "CI" in env:
        if any(k in env for k in ["GITHUB_ACTIONS", "GITEA_ACTIONS", "CIRCLECI"]):
            return _ColorSupportLevel.BIT24
        if (
            any(
                k in env
                for k in ["TRAVIS", "APPVEYOR", "GITLAB_CI", "BUILDKITE", "DRONE"]
            )
            or env.get("CI_NAME") == "codeship"
        ):
            return _ColorSupportLevel.BIT4

    if "TEAMCITY_VERSION" in env:
        if _re.match(r"^(9\.(0*[1-9]\d*)\.|\d{2,}\.)", env["TEAMCITY_VERSION"]):
            return _ColorSupportLevel.BIT4
        return _ColorSupportLevel.NONE

    if is_tty is None:
        is_tty = hasattr(_sys.stdout, "isatty") and _sys.stdout.isatty()

    if not is_tty or env.get("CLICOLOR") == "0":
        return _ColorSupportLevel.NONE

    if _platform.system() == "Windows":
        if hasattr(_sys, "getwindowsversion"):
            build = _sys.getwindowsversion().build
            if build >= 14931:
                return _ColorSupportLevel.BIT24
            if build >= 10586:
                return _ColorSupportLevel.BIT8
        return _ColorSupportLevel.BIT4

    if env.get("COLORTERM") == "truecolor":
        return _ColorSupportLevel.BIT24

    term = env.get("TERM", "")
    if term in ["xterm-kitty", "xterm-ghostty", "wezterm"]:
        return _ColorSupportLevel.BIT24

    if "TERM_PROGRAM" in env:
        prog = env["TERM_PROGRAM"]
        ver_str = env.get("TERM_PROGRAM_VERSION", "").split(".")[0]
        ver = int(ver_str) if ver_str.isdigit() else 0

        if prog == "iTerm.app":
            return _ColorSupportLevel.BIT24 if ver >= 3 else _ColorSupportLevel.BIT8
        if prog == "Apple_Terminal":
            return _ColorSupportLevel.BIT8

    if _re.search(r"-256(color)?$", term, _re.IGNORECASE):
        return _ColorSupportLevel.BIT8

    if _re.search(
        r"^screen|^xterm|^vt100|^vt220|^rxvt|color|ansi|cygwin|linux",
        term,
        _re.IGNORECASE,
    ):
        return _ColorSupportLevel.BIT4

    if "COLORTERM" in env:
        return _ColorSupportLevel.BIT4

    return _ColorSupportLevel.NONE


def _detect_separator() -> _Literal[":", ";"]:
    """
    Detect the preferred SGR (Select Graphic Rendition) separator.

    Reads the `PYANSISTRING_SEPARATOR` environment variable to determine
    whether to use a colon (`:`) or semicolon (`;`) as the separator
    for ANSI escape sequences. Defaults to semicolon for compatibility.

    Returns
    -------
    Literal[":", ";"]
        `":"` if the environment variable is set to ":" or "colon",
        otherwise `";"`.
    """
    separator = _os.getenv("PYANSISTRING_SEPARATOR")
    return ";" if separator not in (":", "colon") else ":"


def _detect_downsample() -> bool:
    """
    Determine whether color downsampling should be enabled.

    Reads the `PYANSISTRING_DOWNSAMPLE` environment variable. If set to
    "0" or "false", color reduction (e.g., converting 24-bit to 8-bit)
    is disabled.

    Returns
    -------
    bool
        `False` if downsampling is explicitly disabled via the environment
        variable, otherwise `True`.
    """
    downsample = _os.getenv("PYANSISTRING_DOWNSAMPLE")
    return False if downsample in ("0", "false") else True


def _detect_theme() -> _ThemeName:
    """
    Detect the default terminal color theme based on the environment.

    Inspects `PYANSISTRING_THEME` (highest precedence), followed by environment
    variables (such as `TERM`, `TERM_PROGRAM`, and `WT_SESSION`) and the host
    operating system to determine the most appropriate 4-bit color palette.

    Returns
    -------
    ThemeName
        The identifier string of the detected terminal theme.
    """

    if env_override := _os.environ.get("PYANSISTRING_THEME"):
        if (env_override := env_override.lower()) in _THEME_NAMES:
            return env_override

    if _sys.platform == "win32":
        if (
            "pwsh" in _os.environ.get("SHELL", "").lower()
            or "powershell" in _os.environ.get("TERM", "").lower()
        ):
            return "powershell"
        elif "vscode" in _os.environ.get("TERM_PROGRAM", "").lower():
            return "vscode"
        elif _os.environ.get("WT_SESSION"):
            return "windows_10"
        return "windows_xp"

    if _sys.platform == "darwin":
        if "vscode" in _os.environ.get("TERM_PROGRAM", "").lower():
            return "vscode"
        return "terminal_app"

    term_program = _os.environ.get("TERM_PROGRAM", "").lower()
    term = _os.environ.get("TERM", "").lower()

    if "vscode" in term_program:
        return "vscode"
    if "putty" in term:
        return "putty"
    if "mirc" in term:
        return "mirc"
    if "ubuntu" in term:
        return "ubuntu"
    if "eclipse" in term_program:
        return "eclipse"

    return "xterm"


@_dataclass
class Config:
    """
    Global configuration state for the `pyansistring` library.

    Attributes
    ----------
    separator : Literal[":", ";"], default ";"
        The SGR sequence delimiter.
        - `":"` (Standard mode): Uses colons, e.g., `\\x1b[38:2::r:g:bm`.
        - `";"` (Compatible mode): Uses semicolons, e.g., `\\x1b[38;2;r;g;bm`.
    color_support : ColorSupportLevel, default auto
        The maximum allowed color level.
    downsample : bool, default True
        Whether sequences should be mathematically downsampled
        to 8-bit or 4-bit colors when printed in restricted environments.
    theme : ThemeName, default auto
        The color theme used for mapping 4-bit ANSI color codes to RGB
        values. Auto-detected based on the host terminal environment.
    """

    separator: _Literal[":", ";"] = _detect_separator()
    color_support: _ColorSupportLevel = _detect_color_support()
    downsample: bool = _detect_downsample()
    theme: _ThemeName = _detect_theme()

    def refresh(
        self,
        *,
        separator: bool = True,
        color_support: bool = True,
        downsample: bool = True,
        theme: bool = True,
    ) -> None:
        """Re-evaluate the environment and update the configuration state."""
        if separator:
            self.separator = _detect_separator()
        if color_support:
            self.color_support = _detect_color_support()
        if downsample:
            self.downsample = _detect_downsample()
        if theme:
            self.theme = _detect_theme()


config = Config()
