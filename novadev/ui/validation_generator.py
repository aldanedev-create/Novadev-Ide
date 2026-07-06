from __future__ import annotations

from ..ast_nodes import Field


def input_type(field: Field) -> str:
    kind = field.kind.lower()
    name = field.name.lower()
    if field.secure:
        return "password"
    if kind in {"int", "number", "money", "currency"}:
        return "number"
    if kind in {"date", "datetime"}:
        return "date"
    if name == "email" or kind == "email":
        return "email"
    if kind in {"bool", "boolean"}:
        return "checkbox"
    return "text"


def validation_attributes(field: Field) -> str:
    attrs = []
    if not field.auto:
        attrs.append("required")
    if field.unique:
        attrs.append('data-unique="true"')
    if field.kind.lower() in {"money", "currency"}:
        attrs.append('step="0.01"')
        attrs.append('min="0"')
    if field.kind.lower() in {"int", "number"}:
        attrs.append('step="1"')
    return " ".join(attrs)
