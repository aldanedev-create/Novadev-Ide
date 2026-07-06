from __future__ import annotations

from typing import Dict, List

from ..ast_nodes import App, Field, Table


def bind_sample_data(app: App) -> Dict[str, List[dict]]:
    return {table.name: sample_records(table) for table in app.tables.values()}


def sample_records(table: Table) -> List[dict]:
    rows = []
    for index in range(1, 4):
        row = {}
        for field in table.fields:
            row[field.name] = sample_value(table.name, field, index)
        rows.append(row)
    return rows


def sample_value(table_name: str, field: Field, index: int):
    name = field.name.lower()
    kind = field.kind.lower()

    if field.auto or name == "id":
        return index
    if name == "name":
        return f"{table_name} {index}"
    if name == "email":
        return f"{table_name.lower()}{index}@example.com"
    if name == "role":
        return ["Admin", "Editor", "User"][(index - 1) % 3]
    if "created" in name or kind in {"date", "datetime"}:
        return f"2026-06-{20 + index:02d}"
    if kind in {"money", "currency"} or name in {"price", "total", "revenue"}:
        return index * 1250
    if kind in {"int", "number"} or name in {"stock", "count", "quantity"}:
        return index * 12
    if kind in {"bool", "boolean"}:
        return index % 2 == 0
    if field.secure:
        return "********"
    if kind == "markdown":
        return f"Generated {table_name.lower()} markdown {index}"
    return f"{field.name.title()} {index}"


def app_schema(app: App) -> dict:
    return {
        "name": app.name,
        "auth": app.auth.table_name if app.auth else None,
        "tables": {
            table.name: {
                "fields": [
                    {
                        "name": field.name,
                        "kind": field.kind,
                        "attributes": field.attributes,
                        "auto": field.auto,
                        "secure": field.secure,
                        "unique": field.unique,
                    }
                    for field in table.fields
                ]
            }
            for table in app.tables.values()
        },
    }
