from functools import wraps
from typing import Any, Callable

from .style import Style


def _detect_style_change(
    method: Callable[..., Any],
) -> Callable[..., Any]:
    """Detect changes in the StyleManager and set the modified flag."""

    @wraps(method)
    def wrapped(self: "StyleManager", *args: Any, **kwargs: Any) -> Any:
        previous_length = len(self)
        result = method(self, *args, **kwargs)
        self._update_modified(previous_length)  # type: ignore
        return result

    return wrapped


class StyleManager(dict[int, Style]):
    """A dict subclass for managing :class:`Style` instances with change tracking.

    Attributes
    ----------
    has_changes : bool
        Modification state of the StyleManager.

    Methods
    -------
    pop_modified() -> bool
        Consume the ``has_changes`` flag and reset it.

    Examples
    --------
    >>> style_manager = StyleManager()
    >>> style_manager[key] = value
    >>> style_manager.pop_modified()
    True
    >>> style_manager.pop_modified()
    False
    """

    _style_cache: dict[int, Style] = {}

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._has_changes = False

    @property
    def has_changes(self) -> bool:
        return self._has_changes

    def pop_modified(self) -> bool:
        """Consume the ``has_changes`` flag and reset it."""
        result = self._has_changes
        if self._has_changes:
            self._has_changes = False
        return result

    def _update_modified(self, previous_length: int) -> None:
        """Update the ``has_changes`` flag if the collection length changed."""
        if not self._has_changes and previous_length != len(self):
            self._has_changes = True

    def __repr__(self) -> str:
        """Return a string representation of the StyleManager."""
        # TODO: it is too verbose, but it is useful for debugging
        return f"StyleManager({super().__repr__()})"

    def __setitem__(self, key: Any, value: Any) -> None:
        """Set a `Style` instance in the dictionary."""
        if not isinstance(value, Style):
            raise TypeError("StyleManager values must be Style instances")
        # NOTE: Cache identical Style objects by their hash
        style_hash = hash(value)
        cached = self._style_cache.get(style_hash)
        if cached is not None and cached == value:
            value = cached
        else:
            self._style_cache[style_hash] = value
        self._has_changes = True
        return super().__setitem__(key, value)

    @_detect_style_change
    def __delitem__(self, key: Any) -> None:
        """Delete a style from the dictionary."""
        return super().__delitem__(key)

    @_detect_style_change  # type: ignore[override]
    def clear(self) -> None:
        return super().clear()

    @_detect_style_change  # type: ignore[override]
    def pop(self, *args: Any) -> Any:
        return super().pop(*args)

    @_detect_style_change  # type: ignore[override]
    def popitem(self) -> tuple[int, Style]:
        return super().popitem()

    @_detect_style_change  # type: ignore[override]
    def setdefault(self, *args: Any, **kwargs: Any) -> Any:
        return super().setdefault(*args, **kwargs)

    @_detect_style_change  # type: ignore[override]
    def update(self, *args: Any, **kwargs: Any) -> None:
        return super().update(*args, **kwargs)

    def copy(self) -> "StyleManager":
        """Create a shallow copy of the StyleManager."""
        copied = StyleManager(dict[Any, Any].copy(self))
        copied._has_changes = self._has_changes
        return copied

    def copy_range(
        self, src_start: int, src_end: int, dest_start: int
    ) -> dict[int, Style]:
        """Copy styles from [src_start, src_end) offset to dest_start."""
        offset = dest_start - src_start
        return {i + offset: self[i] for i in range(src_start, src_end) if i in self}

    def remap(
        self, original: str, formatted: str, visible_only: bool = True
    ) -> dict[int, Style]:
        """Remap styles from the original string to the formatted string."""
        if formatted == original:
            return dict(self)

        pad_left = formatted.find(original)
        if pad_left == -1:
            raise ValueError("Original string not found inside formatted string.")

        if visible_only:
            return self.copy_range(0, len(original), pad_left)
        else:
            return self.shift(pad_left)

    def shift(self, offset: int) -> dict[int, Style]:
        """Shift all style indexes by a given offset."""
        return {index + offset: style for index, style in self.items()}

    def shift_in_range(
        self, offset: int, start: int, end: int, step: int = 1
    ) -> dict[int, Style]:
        """Shift styles within a specific range by a given offset."""
        return {
            index + offset: self[index]
            for index in range(start, end, step)
            if index in self
        }

    def reverse(self, length: int) -> dict[int, Style]:
        """Reverse style indexes based on the given length."""
        return {length - index - 1: style for index, style in self.items()}
