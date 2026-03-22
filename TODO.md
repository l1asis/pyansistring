> [!NOTE]
> - [X] — Overridden (custom implementation)
> - [D] — Delegated (wrapped via `__getattribute__`)
> - [\*] — Skipped (should not be implemented)
> - [ ] — Planned
> - ~~text~~ — Cancelled

### `str` magic or dunder methods
- [X] `__add__`
- [\*] `__class__`
- [X] `__contains__`
- [\*] `__delattr__`
- [D] `__dir__`
- [D] `__doc__`
- [X] `__eq__`
- [X] `__format__`
- [\*] `__ge__`
- [X] `__getattribute__`
- [X] `__getitem__`
- [X] `__getnewargs__`
- [\*] `__getstate__` (mutable class)
- [\*] `__gt__`
- [\*] `__hash__` (mutable class)
- [\*] `__init__`
- [\*] `__init_subclass__`
- [X] `__iter__`
- [\*] `__le__`
- [D] `__len__`
- [\*] `__lt__`
- [X] `__mod__`
- [X] `__mul__`
- [X] `__ne__`
- [X] `__new__`
- [X] `__reduce__`
- [\*] `__reduce_ex__`
- [X] `__repr__`
- [X] `__radd__`
- [\*] `__rmod__`
- [X] `__rmul__`
- [\*] `__setattr__`
- [X] `__sizeof__`
- [X] `__str__`
- [\*] `__subclasshook__`

### `str` public methods (overridden)
- [X] `casefold`
- [X] `center`
- [X] `encode`
- [X] `expandtabs`
- [X] `format`
- [X] `format_map`
- [X] `join`
- [X] `ljust`
- [X] `lstrip`
- [\*] `maketrans` (static method)
- [X] `partition`
- [X] `removeprefix`
- [X] `removesuffix`
- [X] `replace`
- [X] `rjust`
- [X] `rpartition`
- [X] `rsplit`
  - [X] whitespace
  - [X] one char
  - [X] two or more chars
- [X] `rstrip`
- [X] `split`
  - [X] whitespace
  - [X] one char
  - [X] two or more chars
- [X] `splitlines`
- [X] `strip`
- [X] `translate`
- [X] `zfill`

### `str` public methods (delegated)
- [D] `capitalize`
- [D] `count`
- [D] `endswith`
- [D] `find`
- [D] `index`
- [D] `isalnum`
- [D] `isalpha`
- [D] `isascii`
- [D] `isdecimal`
- [D] `isdigit`
- [D] `isidentifier`
- [D] `islower`
- [D] `isnumeric`
- [D] `isprintable`
- [D] `isspace`
- [D] `istitle`
- [D] `isupper`
- [D] `lower`
- [D] `rfind`
- [D] `rindex`
- [D] `startswith`
- [D] `swapcase`
- [D] `title`
- [D] `upper`

### `ANSIString` featured methods (magic, private and public)

- [ ] `__copy__`
- [ ] `__deepcopy__`

> [!NOTE]
> The following should probably be renamed to more intuitive names.

- [ ] ~~`fm` (set SGR styling parameters)~~
- [ ] ~~`fm_w` (`fm` per word)~~
- [ ] ~~`unfm` (remove styles from the string)~~

- [X] `style` (set SGR styling parameters)
- [X] `style_words` (`style` per word)
- [X] `unstyle` (remove styles from the string)
- [X] `unstyle_words` (`unstyle` per word)

- [ ] ~~`fg` (shortcut to `fg_24b`)~~
- [ ] ~~`fg_w` (shortcut to `fg_24b_words`)~~

- [X] `fg_4b` (set foreground color using 4-bit color code)
- [X] `fg_4b_words` (`fg_4b` per word)
- [X] `fg_8b` (set foreground color using a pre-defined set of 256 colors)
- [X] `fg_8b_words` (`fg_8b` per word)
- [X] `fg_24b` (set foreground color using RGB color model, a.k.a. true color)
- [X] `fg_24b_words` (`fg_24b` per word)

- [ ] ~~`bg` (shortcut to `bg_24b`)~~
- [ ] ~~`bg_w` (shortcut to `bg_24b_words`)~~

- [X] `bg_4b` (set background color using 4-bit color code)
- [X] `bg_4b_words` (`bg_4b` per word)
- [X] `bg_8b` (set background color using a pre-defined set of 256 colors)
- [X] `bg_8b_words` (`bg_8b` per word)
- [X] `bg_24b` (set background color using RGB color model, a.k.a. true color)
- [X] `bg_24b_words` (`bg_24b` per word)

- [X] `ul_8b` (set underline color using a pre-defined set of 256 colors)
- [X] `ul_8b_words` (`ul_8b` per word)
- [X] `ul_24b` (set underline color using RGB color model, a.k.a. true color)
- [X] `ul_24b_words` (`ul_24b` per word)

- [ ] `multicolor` (apply a specific custom coloring using the provided coloring system)
- [ ] `multicolor_c` (`multicolor` using coordinates, it's useful for multiline strings)
- [ ] `colormap` (apply a specific predefined coloring)
- [X] `rainbow` (apply rainbow coloring (using a separate algorithm))
- [ ] `random_art` (return random color art)
- [X] `from_ansi` (create `ANSIString` from plain `str` with ANSI escape sequences)
- [ ] ~~`to_html` (create HTML colored text from `ANSIString`)~~
- [X] `to_svg` (create svg image from `ANSIString`)
  - [X] plain conversion
  - [X] colored conversion
  - [X] automatic height and width calculation
  - [X] bold weight support
  - [X] italic style support
  - [X] dim style support
  - [X] transparent background support
  - [X] to-path-elements functionality
  - [X] background color support (depending on the bbox, rectangles)
  - [ ] ~~add viewBox attribute (min-x, min-y, width, height)~~
- [ ] `to_png`
- [ ] `to_jpeg`
- [ ] `to_img` (create image (with format specified) from `ANSIString`)
