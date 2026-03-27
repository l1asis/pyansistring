# pyansistring
![pyansistring Banner](https://raw.githubusercontent.com/l1asis/pyansistring/refs/heads/main/images/banner.png)

[![CI Build](https://github.com/l1asis/pyansistring/actions/workflows/test.yml/badge.svg)](https://github.com/l1asis/pyansistring/actions)
![Coverage](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2Fl1asis%2F9f30f8200703cf6886ab323e86b9f0a1%2Fraw%2Fb11b5516d18e6cf01332906bb9bcf3a4ebf14389%2Fpyansistring_coverage.json)
[![PyPI - Version](https://img.shields.io/pypi/v/pyansistring.svg)](https://pypi.org/project/pyansistring/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyansistring.svg)](https://pypi.org/project/pyansistring/)
![PyPI - Downloads](https://img.shields.io/pypi/dm/pyansistring)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## About The Project

[***pyansistring***](https://github.com/l1asis/pyansistring) is a library for **string color styling** using **ANSI escape sequences**. The base class inherits from Python's `str`. You can split, join, or slice the string while **preserving the styling**.

### Features

* Preservation of the str methods.
* Support for 4-, 8-, and 24-bit (True Color) color depths.
* Per-word coloring.
* Left, right, and center alignment without problems caused by string length.
* Support for multiple SGR (Select Graphic Rendition) parameters.
* Support for both the traditional ";" and the modern ":" SGR parameter separators.
* Automated coloring functionality, e.g., rainbow text.

For a more comprehensive list of what's been done so far, see the [TODO](./TODO.md) section.

Inspired by [***rich***](https://github.com/Textualize/rich) and [***colorama***](https://github.com/tartley/colorama) Python libraries.

## Getting Started

### Prerequisites

* Python 3.11 or higher
    * Linux: https://docs.python.org/3/using/unix.html
    * Windows: https://docs.python.org/3/using/windows.html
    * macOS: https://docs.python.org/3/using/mac.html
* Git (for local installation)
    * Linux: https://git-scm.com/downloads/linux
    * Windows: https://git-scm.com/downloads/win
    * macOS: https://git-scm.com/downloads/mac

### Installation

You can install the package **via pip**:
```sh
pip install pyansistring # or pip3 install pyansistring
pip install pyansistring[svg] # for SVG conversion support
```

Or locally **via git**:
1. Clone the repository
    ```sh
    git clone https://github.com/l1asis/pyansistring
    ```
2. Navigate to the cloned directory
    ```sh
    cd pyansistring
    ```
3. Change git remote url to avoid accidental pushes to base project
    ```sh
    git remote set-url origin github_username/repo_name
    # Verify the changes
    git remote -v
    ```
4. (Optional) Create and activate a virtual environment
    ```sh
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On Unix or MacOS
    source venv/bin/activate
    ``` 
5. Install the package
    ```sh
    pip install .
    pip install .[svg] # for SVG conversion support
    ```

<p align="right">(<a href="#pyansistring">back to top</a>)</p>

## Usage

#### Import the necessary classes and initialize an `ANSIString` instance:
```python
from pyansistring.pyansistring import ANSIString
from pyansistring.constants import SGR, Foreground, Background, UnderlineMode
```

#### Unstyled plain string:
```python
text = ANSIString("Hello, World!")
print(text)
```
![Result: unstyled plain string in black](https://raw.githubusercontent.com/l1asis/pyansistring/refs/heads/main/images/usage/unstyled.svg)

#### Style the whole string:
```python
print(
    ANSIString("Hello, World!")
        .fg_4b(Foreground.YELLOW)
        .bg_4b(Background.BLUE)
        .style(SGR.BOLD)
)
```
![Result: string with yellow foreground, blue background, and bold styling](https://raw.githubusercontent.com/l1asis/pyansistring/refs/heads/main/images/usage/whole.svg)

#### Style by slice (indices are \[start, end, step\]):
```python
print(
    ANSIString("Hello, World!")
        .fg_4b(Foreground.YELLOW, (0, 5), (7, 12))  # "Hello" and "World"
        .bg_4b(Background.BLUE, (7, 12))            # "World"
        .style(SGR.BOLD, (7, 12))                  # "World"
)
```
![Result: string where "Hello" and "World" have a yellow foreground. "World" also has a blue background and is in bold.](https://raw.githubusercontent.com/l1asis/pyansistring/refs/heads/main/images/usage/slice.svg)

#### Style by words:
```python
print(
    ANSIString("Hello, World!")
        .fg_4b_words(Foreground.YELLOW, "Hello", "World")
        .bg_4b_words(Background.BLUE, "World")
        .style_words(SGR.BOLD, "Hello", "World")
)
```
![Result: string where "Hello" and "World" have a yellow foreground and bold styling. "World" also has a blue background.](https://raw.githubusercontent.com/l1asis/pyansistring/refs/heads/main/images/usage/words.svg)

#### SGR parameters like bold and underline:
```python
print(
    ANSIString("Hello, World!")
        .style(SGR.BOLD)
        .style(SGR.UNDERLINE)
)
```
![Result: bold and single underlined string](https://raw.githubusercontent.com/l1asis/pyansistring/refs/heads/main/images/usage/sgr.svg)

#### 4-bit examples (doesn't exist for underline):
```python
print(
    ANSIString("Hello, World!")
        .fg_4b(Foreground.YELLOW)
        .bg_4b(Background.BLUE)
)
```
![Result: string with yellow foreground and blue background](https://raw.githubusercontent.com/l1asis/pyansistring/refs/heads/main/images/usage/4bit.svg)

#### 8-bit examples:
```python
print(
    ANSIString("Hello, World!")
        .fg_8b(11)  # Bright Yellow
        .bg_8b(4)   # Blue
        .ul_8b(74)  # Muted Sky Blue
)
```
![Result: string with bright yellow foreground, blue background, and muted sky blue underline](https://raw.githubusercontent.com/l1asis/pyansistring/refs/heads/main/images/usage/8bit.svg)

#### 24-bit (True Color) example:
```python
print(
    ANSIString("Hello, World!")
        .fg_24b(255, 255, 0)    # Bright Yellow
        .bg_24b(0, 0, 238)      # Blue
        .ul_24b(135, 175, 215)  # Light Steel Blue
)
```
![Result: string with bright yellow foreground, blue background, and light steel blue underline](https://raw.githubusercontent.com/l1asis/pyansistring/refs/heads/main/images/usage/rgb.svg)

#### Underline modes (not "styles" to avoid confusion with other styling):
```python
print(
    ANSIString("Hello, World!")
        .bg_24b(255, 255, 255)  # White
        .ul_24b(255, 0, 0)      # Red
        .style(UnderlineMode.DOUBLE)
)
```
![Result: string with white background and red double underline](https://raw.githubusercontent.com/l1asis/pyansistring/refs/heads/main/images/usage/underline.svg)

#### Lengths and plain text:
```python
styled = ANSIString("Hello, World!").fg_4b(Foreground.MAGENTA)

print(len(styled) == len("Hello, World!"))
# True (logical length ignores ANSI)
print(len(styled.styled_text) == len("Hello, World!"))
# False (includes ANSI codes)
print(styled.styled_length == len("Hello, World!"))
# False (includes ANSI codes)
print(styled.plain_text)
# "Hello, World!"
```

#### ANSIString conversion to SVG text:
```python
from fontTools.ttLib import TTFont

styled = ANSIString("Hello, World!").fg_4b(Foreground.MAGENTA)
styled.to_svg(
    font=TTFont("path/to/font.ttf"),
    font_size_px=16,
    output_file="hello_world.svg"
)
```

#### ANSIString conversion to SVG path (for better compatibility when font is not guaranteed to be present):
```python
from fontTools.ttLib import TTFont

styled = ANSIString("Hello, World!").fg_4b(Foreground.MAGENTA)
styled.to_svg(
    font=TTFont("path/to/font.ttf"),
    font_size_px=16,
    convert_text_to_path=True,
    output_file="hello_world_path.svg"
)
```

> [!NOTE]
> Please note that when `convert_text_to_path` is set to `True`, the characters will be converted into vector shapes, which can help ensure that the appearance of the text remains **consistent across different platforms and devices**, even if the specified font is not available. However, this also means that the text **will no longer be selectable or searchable** in the SVG file, as it will be treated as **graphical elements** rather than text. Neither will it be 100% identical to how it looks in the terminal or being rendered as text in the SVG.

> [!WARNING]
> Supported SGR parameters for SVG conversion include:
> * Foreground and background colors (4-bit, 8-bit, and 24-bit)
> * Underline colors with all modes (single, double, curly, dotted, dashed)
> * Bold and italic font styles
> Unsupported SGR parameters (e.g., strikethrough, inverse, etc.) will be ignored during SVG conversion.

#### Rainbow text as a separate function:
```python
print(
    ANSIString("Hello, World! This is rainbow text!")
        .rainbow(fg=True)
)
```
![Result: rainbow text with automatic transition](https://raw.githubusercontent.com/l1asis/pyansistring/refs/heads/main/images/usage/rainbow.svg)

#### Colored text using multicolor functionality:
```python
print(
    ANSIString("Hello, World! This is multicolor text!")
        .multicolor((
            "r=0:|g=0:|b=255:   $ "  # Start with blue
            "b>0:repeat(auto)   # "  # Decrease blue
            "r>255:repeat(auto) | "  # Increase green and combine with...
            "g>255:repeat(auto)   "  # Increase red
            "                   &*"  # Cycle & Start without apply flags
        ))
)
```
![Result: multicolor text with a transition effect from blue to yellow](https://raw.githubusercontent.com/l1asis/pyansistring/refs/heads/main/images/usage/multicolor.svg)

For more examples, see the [examples](./examples) directory.

<p align="right">(<a href="#pyansistring">back to top</a>)</p>

## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

**P.S.** I would love to see your arts made with ***pyansistring*** in the `arts.py` file, with proper attribution, of course!

<p align="right">(<a href="#pyansistring">back to top</a>)</p>

## License

Distributed under the MIT License. See `LICENSE` for more information.

<p align="right">(<a href="#pyansistring">back to top</a>)</p>

## Acknowledgements
* [Othneil Drew's Best README Template](https://github.com/othneildrew/Best-README-Template)

<p align="right">(<a href="#pyansistring">back to top</a>)</p>