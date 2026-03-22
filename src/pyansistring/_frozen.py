from typing import Any


class FrozenMeta(type):
    """Metaclass that freezes instances after initialization."""

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        /,
        **kwds: Any,
    ):
        orig_init = namespace.get("__init__")

        def __init__(self: object, *args: Any, **kwargs: Any):
            if orig_init:
                orig_init(self, *args, **kwargs)
            object.__setattr__(self, "_is_frozen", True)

        def _attribute_exists(self: object, name: str) -> bool:
            return (
                name in getattr(self, "__dict__", {})
                or name in getattr(type(self), "__slots__", ())
                or name in getattr(type(self), "__annotations__", {})
            )

        def __setattr__(self: object, name: str, value: Any):
            if getattr(self, "_is_frozen", False):
                if _attribute_exists(self, name):
                    raise AttributeError(
                        f"{self.__class__.__name__} object"
                        f" attribute {name!r} is read-only"
                    )
                else:
                    raise AttributeError(
                        f"{self.__class__.__name__} object has not attribute {name!r}"
                    )
            super(cls, self).__setattr__(name, value)

        def __delattr__(self: object, name: str):
            if getattr(self, "_is_frozen", False):
                if _attribute_exists(self, name):
                    raise AttributeError(
                        f"{self.__class__.__name__} object"
                        f" attribute {name!r} is read-only"
                    )
                else:
                    raise AttributeError(
                        f"{self.__class__.__name__} object has not attribute {name!r}"
                    )
            super(cls, self).__delattr__(name)

        namespace["__init__"] = __init__
        namespace["__setattr__"] = __setattr__
        namespace["__delattr__"] = __delattr__

        cls = super().__new__(mcs, name, bases, namespace, **kwds)
        return cls


class FrozenMixin:
    """Mixin that prevents attribute mutation once frozen."""

    _is_frozen: bool = False

    # def __init__(self, *args: Any, **kwargs: Any) -> None:
    #     super().__init__(*args, **kwargs)
    #     self._freeze()

    def __init_subclass__(cls, **kwargs: Any):
        super().__init_subclass__(**kwargs)

    def __post_init__(self):
        self._freeze()

    def _freeze(self):
        object.__setattr__(self, "_is_frozen", True)

    def __setattr__(self, name: str, value: Any):
        if getattr(self, "_is_frozen", False):
            raise AttributeError(
                f"{self.__class__.__name__} object attribute {name!r} is read-only"
            )
        super().__setattr__(name, value)

    def __delattr__(self, name: str):
        if getattr(self, "_is_frozen", False):
            raise AttributeError(
                f"{self.__class__.__name__} object attribute {name!r} is read-only"
            )
        super().__delattr__(name)
