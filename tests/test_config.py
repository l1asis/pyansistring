import pytest

from pyansistring.config import (
    _detect_color_support,  # type: ignore
    _detect_downsample,  # type: ignore
    _detect_separator,  # type: ignore
    _detect_theme,  # type: ignore
    _env_force_color,  # type: ignore
    config,
)
from pyansistring.constants import ColorSupportLevel


@pytest.fixture
def isolated_env(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """
    Provides a completely empty, isolated environment dictionary.
    Prevents host variables (like VSCode's TERM_PROGRAM) from leaking into tests.
    """
    clean_env: dict[str, str] = {}
    monkeypatch.setattr("os.environ", clean_env)
    return clean_env


def test_default_autouse_fixture_baseline():
    """
    Verify that the `set_up_default_config` autouse fixture from conftest.py
    correctly forces the global config state for testing.
    """
    assert config.separator == ":"
    assert config.color_support == ColorSupportLevel.BIT24
    assert config.downsample is True
    assert config.theme == "vga"


def test_detect_separator(isolated_env: dict[str, str]):
    """Test the PYANSISTRING_SEPARATOR environment variable detection."""
    assert _detect_separator() == ";"

    isolated_env["PYANSISTRING_SEPARATOR"] = "colon"
    assert _detect_separator() == ":"

    isolated_env["PYANSISTRING_SEPARATOR"] = ":"
    assert _detect_separator() == ":"


def test_detect_downsample(isolated_env: dict[str, str]):
    """Test the PYANSISTRING_DOWNSAMPLE environment variable detection."""
    assert _detect_downsample() is True

    isolated_env["PYANSISTRING_DOWNSAMPLE"] = "0"
    assert _detect_downsample() is False

    isolated_env["PYANSISTRING_DOWNSAMPLE"] = "false"
    assert _detect_downsample() is False


@pytest.mark.parametrize(
    "env_val, expected",
    [
        ("true", ColorSupportLevel.BIT4),
        ("false", ColorSupportLevel.NONE),
        ("", ColorSupportLevel.BIT4),
        ("0", ColorSupportLevel.NONE),
        ("1", ColorSupportLevel.BIT4),
        ("2", ColorSupportLevel.BIT8),
        ("3", ColorSupportLevel.BIT24),
        ("invalid_value", None),
    ],
)
def test_env_force_color(
    isolated_env: dict[str, str], env_val: str, expected: ColorSupportLevel | None
):
    """Test standard FORCE_COLOR parsing levels."""
    isolated_env["FORCE_COLOR"] = env_val
    assert _env_force_color() == expected


def test_detect_color_support_cli_flags(
    monkeypatch: pytest.MonkeyPatch, isolated_env: dict[str, str]
):
    """Test color support detection via simulated CLI flags."""

    # Test forcing truecolor via CLI
    monkeypatch.setattr("sys.argv", ["script.py", "--color=16m"])
    assert _detect_color_support() == ColorSupportLevel.BIT24

    # Test disabling color via CLI
    monkeypatch.setattr("sys.argv", ["script.py", "--no-color"])
    assert _detect_color_support() == ColorSupportLevel.NONE


def test_detect_color_support_ci_environments(isolated_env: dict[str, str]):
    """Test color depth mapping for continuous integration environments."""
    isolated_env["CI"] = "1"

    # GitHub Actions supports 24-bit
    isolated_env["GITHUB_ACTIONS"] = "true"
    assert _detect_color_support(is_tty=False) == ColorSupportLevel.BIT24

    del isolated_env["GITHUB_ACTIONS"]

    # Travis supports 4-bit
    isolated_env["TRAVIS"] = "true"
    assert _detect_color_support(is_tty=False) == ColorSupportLevel.BIT4


def test_detect_theme_platform_matching(
    monkeypatch: pytest.MonkeyPatch, isolated_env: dict[str, str]
):
    """Test theme auto-detection across different simulated operating systems."""
    # Simulate Windows Terminal
    monkeypatch.setattr("sys.platform", "win32")
    isolated_env["WT_SESSION"] = "1"
    assert _detect_theme() == "windows_10"

    # Simulate macOS VSCode
    monkeypatch.setattr("sys.platform", "darwin")
    isolated_env.clear()
    isolated_env["TERM_PROGRAM"] = "vscode"
    assert _detect_theme() == "vscode"

    # Simulate Linux Putty
    monkeypatch.setattr("sys.platform", "linux")
    isolated_env.clear()
    isolated_env["TERM"] = "putty-256color"
    assert _detect_theme() == "putty"


def test_config_refresh_updates_state(
    monkeypatch: pytest.MonkeyPatch, isolated_env: dict[str, str]
):
    """
    Ensure the Config.refresh() method correctly reads the live environment
    and overrides the initial setup fixture.
    """
    # Verify the baseline from the conftest.py autouse fixture is active
    assert config.theme == "vga"
    assert config.downsample is True
    assert config.separator == ":"

    # Alter the environment completely
    monkeypatch.setattr("sys.platform", "darwin")
    isolated_env["TERM_PROGRAM"] = "Apple_Terminal"

    # Refresh the global config
    config.refresh()

    # Assert changes took effect
    assert config.theme == "terminal_app"
    assert config.downsample is True
    assert config.separator == ";"
