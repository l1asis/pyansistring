"""Shared pytest fixtures and helpers for pyansistring tests."""

from typing import Any

import pytest

from pyansistring import ANSIString, StyleManager
from pyansistring.constants import (
    SGR,
    Foreground,
)
from pyansistring.style import Color, Style

# ── Constants ─────────────────────────────────────────────────────────────

RESET = "\x1b[0m"


# ── Helper functions ──────────────────────────────────────────────────────


def ansi_wrap(chars: str, code: str) -> str:
    """Wrap *chars* with ``code`` + RESET as a single run."""
    return f"{code}{chars}{RESET}"


def style_ansi(style_enum: Any, *args: int) -> str:
    """Shortcut: `Style().with_style(style_enum, *args).to_ansi()`."""
    return Style().with_style(style_enum, *args).to_ansi()


# ── Reusable pytest fixtures ─────────────────────────────────────────────


@pytest.fixture
def hello_world():
    """A plain ANSIString `'Hello, World!'`."""
    return ANSIString("Hello, World!")


@pytest.fixture
def bold_hello_world():
    """`'Hello, World!'` fully formatted with BOLD."""
    return ANSIString("Hello, World!").style(SGR.BOLD)


@pytest.fixture
def bold_code():
    """ANSI escape sequence for BOLD."""
    return style_ansi(SGR.BOLD)


@pytest.fixture
def italic_code():
    """ANSI escape sequence for ITALIC."""
    return style_ansi(SGR.ITALIC)


@pytest.fixture
def empty_style():
    """An empty `Style()` instance."""
    return Style()


@pytest.fixture
def bold_style():
    """`Style(attributes=frozenset({SGR.BOLD}))`."""
    return Style(attributes=frozenset({SGR.BOLD}))


@pytest.fixture
def red_fg_style():
    """Style with 4-bit red foreground."""
    return Style(foreground=Color.from_4bit(Foreground.RED))


@pytest.fixture
def empty_style_manager():
    """An empty `StyleManager()`."""
    return StyleManager()
