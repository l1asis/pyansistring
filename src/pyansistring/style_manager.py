from functools import wraps
from types import MethodType
from typing import Any, Callable, ParamSpec, TypeVar, cast

from .style import Style

P = ParamSpec("P")
R = TypeVar("R")

def _detect_style_change(
    method: Callable[P, R],
    is_method_bound: bool = False
) -> Callable[P, R]:
    """Decorator to detect changes in the StyleManager and set the modified flag."""
    @wraps(method)
    def wrapped(self: "StyleManager", *args: P.args, **kwargs: P.kwargs) -> R:
        previous_length = len(self)
        if not is_method_bound:
            result = method(self, *args, **kwargs)  # type: ignore
        else:
            result = method(*args, **kwargs)
        if not self._has_been_modified and previous_length != len(self):  # type: ignore
            self._has_been_modified = True  # type: ignore
        return result # type: ignore
    return cast(Callable[P, R], wrapped)

class StyleManager(dict[int, Style]):
    """
    A dictionary-like class for managing `Style` instances and tracking style modifications.

    This class behaves similarly to a dictionary, allowing storage and retrieval of `Style`
    instances. It also maintains an internal flag to indicate whether any style has been modified 
    since the last access.

    Attributes
    ----------
    _has_been_modified : bool
        Indicates whether the styles have been modified since the last check.
    has_been_modified : bool
        Property. Returns `True` if styles have been modified since the last access;
        accessing this resets the flag to `False`.

    Examples
    --------
    >>> style_manager = StyleManager()
    >>> style_manager[key] = value
    >>> style_manager.has_been_modified
    True
    >>> style_manager.has_been_modified
    False
    """
    _style_cache: dict[int, Style] = {}

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._has_been_modified = False
        # TODO: wrap methods manually, with @is_method_bound
        for name in {"clear", "pop", "popitem", "setdefault", "update"}:
            method = getattr(self, name)
            wrapped = _detect_style_change(method, is_method_bound=True)
            setattr(self, name, MethodType(wrapped, self))  # NOTE: wrapped.__get__(self, self.__class__)

    @property
    def has_been_modified(self) -> bool:
        """Check if the styles have been modified since the last access."""
        result = self._has_been_modified
        if self._has_been_modified:
            self._has_been_modified = False
        return result

    def __repr__(self) -> str:
        """Return a string representation of the StyleManager."""
        # TODO: it is too verbose, but it is useful for debugging
        return f"StyleManager({dict.__repr__(self)})"  # type: ignore

    def __setitem__(self, key: Any, value: Any) -> None:
        """ Set a `Style` instance in the dictionary."""
        if not isinstance(value, Style):
            raise TypeError("StyleManager values must be Style instances")
        # NOTE: Cache identical Style objects by their hash
        style_hash = hash(value)
        cached = self._style_cache.get(style_hash)
        if cached is not None and cached == value:
            value = cached
        else:
            self._style_cache[style_hash] = value
        self._has_been_modified = True
        return super().__setitem__(key, value)

    @_detect_style_change
    def __delitem__(self, key: Any) -> None:
        """Delete a style from the dictionary."""
        return super().__delitem__(key)

    def copy(self) -> "StyleManager":
        """Create a shallow copy of the StyleManager."""
        copied = StyleManager(dict[Any, Any].copy(self))
        copied._has_been_modified = self._has_been_modified
        return copied

    def remap_styles(
        self,
        original: str,
        formatted: str,
        visible_only: bool = True
    ) -> dict[int, Style]:
        """Remap styles from the original string to the formatted string."""
        if formatted == original:
            return dict(self)

        pad_left = formatted.find(original)
        if pad_left == -1:
            raise ValueError("Original string not found inside formatted string.")

        if visible_only:
            # Copy only styles that fall within the visible range of `original` inside `formatted`
            styles = {
                index: self[index - pad_left]
                for index in range(pad_left, pad_left + len(original))
                if (index - pad_left) in self  # avoid KeyError if self is missing some indexes
            }
        else:
            # Remap all style indexes, shifted by pad_left
            styles = {
                index + pad_left: self[index]
                for index in self.keys()
            }

        return styles
