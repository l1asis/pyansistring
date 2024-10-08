### `str` magic or dunder methods
- [X] `__add__`
- [ ] `__class__`
- [ ] `__contains__`
- [ ] `__delattr__`
- [X] `__dir__`
- [X] `__doc__`
- [X] `__eq__`
- [ ] `__format__`
- [ ] `__ge__`
- [ ] `__getattribute__`
- [X] `__getitem__`
- [ ] `__getnewargs__`
- [ ] `__getstate__`
- [ ] `__gt__`
- [ ] `__hash__`
- [X] `__init__`
- [ ] `__init_subclass__`
- [ ] `__iter__`
- [ ] `__le__`
- [X] `__len__`
- [ ] `__lt__`
- [ ] `__mod__`
- [ ] `__mul__`
- [X] `__ne__`
- [ ] `__new__`
- [ ] `__reduce__`
- [ ] `__reduce_ex__`
- [X] `__repr__`
- [ ] `__rmod__`
- [ ] `__rmul__`
- [ ] `__setattr__`
- [ ] `__sizeof__`
- [X] `__str__`
- [ ] `__subclasshook__`

### `str` public methods
- [X] `capitalize`
- [ ] `casefold`
- [X] `center`
- [X] `count`
- [ ] `encode`
- [X] `endswith`
- [ ] `expandtabs`
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
- [ ] `lstrip`
- [ ] `maketrans`
- [ ] `partition`
- [ ] `removeprefix`
- [ ] `removesuffix`
- [ ] `replace`
- [X] `rfind`
- [X] `rindex`
- [X] `rjust`
- [ ] `rpartition`
- [X] `rsplit`
  - [X] whitespace
  - [X] one char
  - [X] two or more chars
- [ ] `rstrip`
- [X] `split`
  - [X] whitespace
  - [X] one char
  - [X] two or more chars
- [X] `splitlines`
- [X] `startswith`
- [ ] `strip`
- [X] `swapcase`
- [X] `title`
- [ ] `translate`
- [X] `upper`
- [ ] `zfill`

### `ANSIString` featured methods (magic, private and public)
- [X] `__radd__`
- [ ] `__copy__`
- [ ] `__deepcopy__`

- [X] `_render` (apply current styles to the plain string)
- [X] `_get_indices` (...)
- [X] `_search_spans` (...)

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

- [ ] `ul_8b` (set underline color using a pre-defined set of 256 colors)
- [ ] `ul_8b_w` (`ul_8b` per word)
- [ ] `ul_24b` (set underline color using RGB color model, a.k.a. true color)
- [ ] `ul_24b_w` (`ul_24b` per word)


- [X] `multicolor` (apply a specific custom coloring using the provided coloring system)
- [X] `multicolor_c` (`multicolor` using coordinates, it's useful for multiline strings)
- [ ] `colormap` (apply a specific predefined coloring)
- [X] `rainbow` (apply rainbow coloring (using a separate algorithm))
- [ ] `random_art` (return random color art)
- [X] `from_ansi` (create `ANSIString` from plain `str` with ANSI escape sequences)
