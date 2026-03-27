__all__ = [
    "FMT",
    "MAP_FMT",
    "remap_format",
]

from string import Formatter as _Formatter
from typing import Any as _Any

from pyansistring.style import Style, StyleManager

FMT = _Formatter()


class _MapFmt(_Formatter):
    """Formatter that resolves all field names through *kwargs* (the mapping)."""

    def get_value(
        self, key: int | str, args: _Any, kwargs: _Any
    ) -> _Any:  # pragma: no cover
        return kwargs[key]


MAP_FMT = _MapFmt()


def _resolve_format_spec(
    spec: str,
    fmt: _Formatter,
    args: tuple[_Any, ...],
    kwargs: _Any,
    auto_idx: int,
) -> tuple[str, int]:
    """Resolve nested replacement fields inside a format spec."""
    if "{" not in spec:
        return spec, auto_idx
    parts: list[str] = []
    for literal, field_name, sub_spec, conv in fmt.parse(spec):
        parts.append(literal)
        if field_name is not None:
            if field_name == "":
                field_name = str(auto_idx)
                auto_idx += 1
            obj, _ = fmt.get_field(field_name, args, kwargs)
            if conv:
                obj = fmt.convert_field(obj, conv)
            resolved_sub, auto_idx = _resolve_format_spec(
                sub_spec or "", fmt, args, kwargs, auto_idx
            )
            parts.append(format(obj, resolved_sub))
    return "".join(parts), auto_idx


def remap_format(
    template: str,
    sm: StyleManager,
    fmt: _Formatter,
    args: tuple[_Any, ...],
    kwargs: _Any,
) -> dict[int, Style]:
    """Map styles from a format template onto the formatted output positions."""
    styles: dict[int, Style] = {}
    src = 0
    dest = 0
    auto_idx = 0

    for literal, field_name, spec, conv in fmt.parse(template):
        # Literal chars, {{ and }}, each occupy 2 source chars
        for ch in literal:
            if src in sm:
                styles[dest] = sm[src]
            src += 2 if ch in "{}" else 1
            dest += 1

        if field_name is not None:
            # Resolve auto-numbering
            if field_name == "":
                resolved = str(auto_idx)
                auto_idx += 1
            else:
                resolved = field_name

            obj, _ = fmt.get_field(resolved, args, kwargs)
            if conv:
                obj = fmt.convert_field(obj, conv)

            resolved_spec, auto_idx = _resolve_format_spec(
                spec or "", fmt, args, kwargs, auto_idx
            )
            dest += len(format(obj, resolved_spec))

            # Advance src past the {…} replacement field
            depth = 1
            src += 1  # skip opening '{'
            while depth:
                if template[src] == "{":
                    depth += 1
                elif template[src] == "}":
                    depth -= 1
                src += 1

    return styles
