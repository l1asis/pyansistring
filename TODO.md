### `str` magic or dunder methods
- [X] `__add__`
- [*] `__class__` <!-- Should not be implemented -->
- [X] `__contains__`
- [*] `__delattr__` <!-- Should not be implemented -->
- [X] `__dir__`
- [X] `__doc__`
- [X] `__eq__`
- [X] `__format__`
- [*] `__ge__` <!-- Should not be implemented -->
- [X] `__getattribute__`
- [X] `__getitem__`
- [X] `__getnewargs__`
- [*] `__getstate__` <!-- Should not be implemented because the class is mutable -->
- [*] `__gt__` <!-- Should not be implemented -->
- [*] `__hash__` <!-- Should not be implemented because the class is mutable -->
- [*] `__init__` <!-- Should not be implemented -->
- [*] `__init_subclass__` <!-- Should not be implemented -->
- [X] `__iter__`
- [*] `__le__` <!-- Should not be implemented -->
- [X] `__len__`
- [*] `__lt__` <!-- Should not be implemented -->
- [X] `__mod__`
- [X] `__mul__`
- [X] `__ne__`
- [X] `__new__`
- [X] `__reduce__`
- [*] `__reduce_ex__` <!-- Should not be implemented --> 
- [X] `__repr__`
- [X] `__radd__`
- [*] `__rmod__` <!-- Should not be implemented -->
- [X] `__rmul__`
- [*] `__setattr__` <!-- Should not be implemented -->
- [X] `__sizeof__`
- [X] `__str__`
- [*] `__subclasshook__` <!-- Should not be implemented -->

### `str` public methods
- [X] `capitalize`
- [ ] `casefold`
- [X] `center`
- [X] `count`
- [X] `encode`
- [X] `endswith`
- [X] `expandtabs`
- [X] `find`
- [ ] `format`
- [ ] `format_map`
- [X] `index`
- [X] `isalnum`
- [X] `isalpha`
- [X] `isascii`
- [X] `isdecimal`
- [X] `isdigit`
- [X] `isidentifier`
- [X] `islower`
- [X] `isnumeric`
- [X] `isprintable`
- [X] `isspace`
- [X] `istitle`
- [X] `isupper`
- [X] `join`
- [X] `ljust`
- [X] `lower`
- [X] `lstrip`
- [ ] `maketrans`
- [X] `partition`
- [X] `removeprefix`
- [X] `removesuffix`
- [X] `replace`
- [X] `rfind`
- [X] `rindex`
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
- [X] `startswith`
- [X] `strip`
- [X] `swapcase`
- [X] `title`
- [ ] `translate`
- [X] `upper`
- [X] `zfill`

### `ANSIString` featured methods (magic, private and public)

- [ ] `__copy__`
- [ ] `__deepcopy__`

> [!NOTE]
> The following should probably be renamed to more intuitive names.

- [X] `fm` (set SGR styling parameters)
- [X] `fm_w` (`fm` per word)
- [X] `unfm` (remove styles from the string)
- [X] `unfm_w` (`unfm` per word)

- [ ] ~~`fg` (shortcut to `fg_24b`)~~
- [ ] ~~`fg_w` (shortcut to `fg_24b_w`)~~

- [X] `fg_4b` (set foreground color using 4-bit color code)
- [X] `fg_4b_w` (`fg_4b` per word)
- [X] `fg_8b` (set foreground color using a pre-defined set of 256 colors)
- [X] `fg_8b_w` (`fg_8b` per word)
- [X] `fg_24b` (set foreground color using RGB color model, a.k.a. true color)
- [X] `fg_24b_w` (`fg_24b` per word)

- [ ] ~~`bg` (shortcut to `bg_24b`)~~
- [ ] ~~`bg_w` (shortcut to `bg_24b_w`)~~

- [X] `bg_4b` (set background color using 4-bit color code)
- [X] `bg_4b_w` (`bg_4b` per word)
- [X] `bg_8b` (set background color using a pre-defined set of 256 colors)
- [X] `bg_8b_w` (`bg_8b` per word)
- [X] `bg_24b` (set background color using RGB color model, a.k.a. true color)
- [X] `bg_24b_w` (`bg_24b` per word)

- [X] `ul_8b` (set underline color using a pre-defined set of 256 colors)
- [X] `ul_8b_w` (`ul_8b` per word)
- [X] `ul_24b` (set underline color using RGB color model, a.k.a. true color)
- [X] `ul_24b_w` (`ul_24b` per word)

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
