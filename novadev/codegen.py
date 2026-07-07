from __future__ import annotations

"""Flask backend generator for NovaDev 1.1.

The generated backend serves the UI from `dist/` and exposes JSON API endpoints
for table declarations. This makes `build-ui` and `build-backend` work together
like a small real web application.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List

from .ast_nodes import Program, TableNode, expression_to_source
from .project_ir import ProjectIR
from .project_ir_builder import ProjectIRBuilder
from .runtime import Runtime


class BackendGenerator:
    def generate(
        self,
        program: Program,
        output_dir: Path | str = "generated_backend",
        frontend_dir: Path | str = "dist",
    ) -> List[Path]:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        runtime = Runtime()
        runtime.load_declarations(program)
        ir = ProjectIRBuilder().build(program)
        frontend_relative = os.path.relpath(Path(frontend_dir), output_path)

        files = {
            output_path / "requirements.txt": "Flask>=3.0,<4.0\nSQLAlchemy>=2.0,<3.0\n",
            output_path / "config.py": self.config_py(frontend_relative),
            output_path / "models.py": self.models_py(runtime, ir),
            output_path / "routes.py": self.routes_py(runtime),
            output_path / "app.py": self.app_py(frontend_relative, enable_checkout_route=needs_checkout_route(ir)),
            output_path / "README.md": self.backend_readme(frontend_relative, ir),
        }
        for path, content in files.items():
            path.write_text(content, encoding="utf-8")
        return list(files.keys())

    def config_py(self, frontend_relative: str) -> str:
        return f'''"""Generated NovaDev 1.1 Flask backend config."""

import os
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BACKEND_DIR / "database.db"
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///" + DATABASE_PATH.as_posix())
FRONTEND_RELATIVE = {frontend_relative!r}
API_PREFIX = "/api"
'''

    def models_py(self, runtime: Runtime, ir: ProjectIR) -> str:
        tables = {
            name: [
                {
                    "name": field.name,
                    "type": field.field_type,
                    "attributes": field.attributes,
                    "auto": field.auto,
                    "secure": field.secure,
                    "unique": field.unique,
                }
                for field in table.fields
            ]
            for name, table in runtime.tables.items()
        }
        api_tables = {api_resource_name(name): name for name in runtime.tables}
        seed_data = {name: sample_rows(table, ir.mode) for name, table in runtime.tables.items()}
        primary_keys = {name: primary_key(table) for name, table in runtime.tables.items()}

        return (
            '''"""Generated NovaDev 1.1 SQLAlchemy model and data helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from sqlalchemy import (
    Boolean,
    Column,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    delete,
    event,
    func,
    insert,
    select,
    update,
)

from config import DATABASE_URL

TABLES = '''
            + repr(tables)
            + '''
API_TABLES = '''
            + repr(api_tables)
            + '''
PRIMARY_KEYS = '''
            + repr(primary_keys)
            + '''
SEED_DATA = '''
            + repr(seed_data)
            + '''


def table_for_resource(resource):
    return API_TABLES.get(resource.lower())


def table_schema(table_name):
    return TABLES.get(table_name, [])


def primary_key(table_name):
    return PRIMARY_KEYS.get(table_name, "id")


def sqlite_database_path():
    if not DATABASE_URL.startswith("sqlite:///"):
        return None
    raw_path = DATABASE_URL.replace("sqlite:///", "", 1)
    if raw_path in {"", ":memory:"}:
        return None
    database_path = Path(raw_path)
    if not database_path.is_absolute():
        database_path = Path(__file__).resolve().parent / raw_path
    return database_path


def prepare_sqlite_database():
    database_path = sqlite_database_path()
    if database_path is None:
        return
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")


def sql_type_for_field(field):
    lowered = str(field.get("type", "text")).lower()
    if field.get("auto"):
        return Integer
    if lowered in {"int", "integer"}:
        return Integer
    if lowered in {"number", "float", "double", "money", "currency", "decimal"}:
        return Float
    if lowered in {"bool", "boolean"}:
        return Boolean
    if lowered in {"string", "varchar", "email"}:
        return String(255)
    return Text


def column_for_field(field, key_name):
    name = field["name"]
    is_primary = name == key_name or bool(field.get("auto"))
    kwargs = {
        "primary_key": is_primary,
        "nullable": False if is_primary or "required" in field.get("attributes", []) else True,
    }
    if field.get("auto"):
        kwargs["autoincrement"] = True
    if field.get("unique"):
        kwargs["unique"] = True
    return Column(name, sql_type_for_field(field), **kwargs)


def build_sql_tables():
    sql_tables = {}
    for table_name, fields in TABLES.items():
        key_name = primary_key(table_name)
        columns = [column_for_field(field, key_name) for field in fields]
        if not columns:
            columns.append(Column("id", Integer, primary_key=True, autoincrement=True))
        sql_tables[table_name] = Table(table_name, metadata, *columns)
    return sql_tables


prepare_sqlite_database()
engine = create_engine(
    DATABASE_URL,
    future=True,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()


metadata = MetaData()
SQL_TABLES = build_sql_tables()


def sql_table(table_name):
    table = SQL_TABLES.get(table_name)
    if table is None:
        raise KeyError(f"Unknown table: {table_name}")
    return table


def row_to_dict(row):
    if row is None:
        return None
    return dict(row)


def list_rows(table_name):
    table = sql_table(table_name)
    with engine.connect() as connection:
        rows = connection.execute(select(table)).mappings().all()
    return [row_to_dict(row) for row in rows]


def public_row(table_name, row):
    if row is None:
        return None
    secure_fields = {field["name"] for field in table_schema(table_name) if field.get("secure")}
    return {name: value for name, value in row.items() if name not in secure_fields}


def public_rows(table_name):
    return [public_row(table_name, row) for row in list_rows(table_name)]


def count_rows(table_name):
    table = sql_table(table_name)
    with engine.connect() as connection:
        return int(connection.execute(select(func.count()).select_from(table)).scalar_one())


def sum_rows(table_name, field_name):
    table = sql_table(table_name)
    if field_name not in table.c.keys():
        return 0
    with engine.connect() as connection:
        value = connection.execute(select(func.coalesce(func.sum(table.c[field_name]), 0))).scalar_one()
    return float(value or 0)


def get_row(table_name, row_id):
    table = sql_table(table_name)
    key = primary_key(table_name)
    if key not in table.c.keys():
        return None
    with engine.connect() as connection:
        row = connection.execute(select(table).where(table.c[key] == row_id)).mappings().first()
    return row_to_dict(row)


def create_row(table_name, row):
    table = sql_table(table_name)
    clean = sanitize_row(table_name, row)
    with engine.begin() as connection:
        result = connection.execute(insert(table).values(**clean))
        inserted_key = result.inserted_primary_key[0] if result.inserted_primary_key else None
    key = primary_key(table_name)
    if inserted_key is not None:
        created = get_row(table_name, inserted_key)
        if created is not None:
            return created
    if key in clean:
        created = get_row(table_name, clean[key])
        if created is not None:
            return created
    return clean


def update_row(table_name, row_id, values):
    table = sql_table(table_name)
    key = primary_key(table_name)
    if key not in table.c.keys():
        return None
    clean = sanitize_row(table_name, values, partial=True)
    if clean:
        with engine.begin() as connection:
            connection.execute(update(table).where(table.c[key] == row_id).values(**clean))
    return get_row(table_name, row_id)


def delete_row(table_name, row_id):
    table = sql_table(table_name)
    key = primary_key(table_name)
    existing = get_row(table_name, row_id)
    if existing is None or key not in table.c.keys():
        return None
    with engine.begin() as connection:
        connection.execute(delete(table).where(table.c[key] == row_id))
    return existing


def clear_rows(table_name):
    table = sql_table(table_name)
    with engine.begin() as connection:
        connection.execute(delete(table))


def next_id(table_name):
    table = sql_table(table_name)
    key = primary_key(table_name)
    if key not in table.c.keys():
        return 1
    with engine.connect() as connection:
        value = connection.execute(select(func.max(table.c[key]))).scalar_one()
    return int(value or 0) + 1


def sanitize_row(table_name, values, partial=False, include_auto=False):
    fields = table_schema(table_name)
    allowed = {field["name"]: field for field in fields}
    clean = {}
    for name, value in (values or {}).items():
        if name not in allowed:
            continue
        field = allowed[name]
        if field.get("auto") and not include_auto:
            continue
        clean[name] = coerce_value(value, field.get("type", "text"))

    if not partial:
        for field in fields:
            name = field["name"]
            if field.get("auto") or name in clean:
                continue
            clean[name] = default_value(field.get("type", "text"))
    return clean


def coerce_value(value, field_type):
    lowered = str(field_type).lower()
    if lowered in {"int", "integer", "auto"}:
        try:
            return int(float(value or 0))
        except (TypeError, ValueError):
            return 0
    if lowered in {"number", "float", "double", "money", "currency", "decimal"}:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0
    if lowered in {"bool", "boolean"}:
        if isinstance(value, bool):
            return value
        return str(value).lower() in {"true", "1", "yes", "on"}
    return "" if value is None else value


def default_value(field_type):
    lowered = str(field_type).lower()
    if lowered in {"int", "integer", "auto"}:
        return 0
    if lowered in {"number", "float", "double", "money", "currency", "decimal"}:
        return 0.0
    if lowered in {"bool", "boolean"}:
        return False
    return ""


def seed_database():
    for table_name, rows in SEED_DATA.items():
        if not rows or count_rows(table_name) > 0:
            continue
        table = sql_table(table_name)
        with engine.begin() as connection:
            for row in rows:
                connection.execute(insert(table).values(**sanitize_row(table_name, row, include_auto=True)))


def init_db():
    metadata.create_all(engine)
    seed_database()


def database_status():
    database_path = sqlite_database_path()
    return {
        "url": DATABASE_URL,
        "path": str(database_path) if database_path else "",
        "tables": list(SQL_TABLES.keys()),
    }


init_db()
'''
        )

    def routes_py(self, runtime: Runtime) -> str:
        route_entries = []
        handlers = []
        for index, route in enumerate(runtime.routes):
            handler = f"route_{index}"
            route_entries.append(
                {
                    "method": route.method,
                    "path": route.path,
                    "handler": handler,
                    "requires_auth": route.requires_auth,
                    "required_role": route.required_role,
                }
            )
            handlers.append(self.handler_py(handler, route.return_expr))

        return f'''"""Generated NovaDev 1.1 declared route handlers."""

from models import count_rows, create_row, public_row, public_rows, sum_rows, table_schema

ROUTES = {route_entries!r}


def handle_declared_route(method, path, body=None):
    for route in ROUTES:
        if route["method"] == method and route["path"] == path:
            return globals()[route["handler"]](body or {{}})
    return None

{chr(10).join(handlers)}
'''

    def handler_py(self, name: str, expression) -> str:
        source = expression_to_source(expression)
        if source.endswith(".all()"):
            table = source[:-6]
            body = f'return public_rows("{table}"), 200'
        elif source.endswith(".count()"):
            table = source[:-8]
            body = f'return {{"count": count_rows("{table}")}}, 200'
        else:
            create_match = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\.create\(request\.body\)$", source)
            sum_match = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\.sum\(([A-Za-z_][A-Za-z0-9_]*)\)$", source)
            if create_match:
                table = create_match.group(1)
                body = f'return public_row("{table}", create_row("{table}", body)), 201'
            elif sum_match:
                table, field = sum_match.groups()
                body = f'return {{"sum": sum_rows("{table}", "{field}")}}, 200'
            elif source:
                body = f'return {{"result": {source!r}}}, 200'
            else:
                body = 'return {"ok": True}, 200'
        return f"""def {name}(body):
    {body}
"""

    def app_py(self, frontend_relative: str, enable_checkout_route: bool = False) -> str:
        checkout_route = self.checkout_route_py() if enable_checkout_route else ""
        return f'''"""Generated NovaDev 1.1 Flask app.

Run with:
    python -m pip install -r requirements.txt
    python app.py

Then open:
    http://127.0.0.1:5000
"""

import os
import sys
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory


BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from models import (
    API_TABLES,
    TABLES,
    clear_rows,
    count_rows,
    create_row,
    database_status,
    delete_row,
    get_row,
    list_rows,
    primary_key,
    public_row,
    public_rows,
    sum_rows,
    table_for_resource,
    update_row,
)
from routes import ROUTES, handle_declared_route


FRONTEND_DIR = (BACKEND_DIR / {frontend_relative!r}).resolve()

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")


@app.get("/")
def index():
    return send_frontend_file("index.html")


@app.get("/<path:asset_path>")
def frontend_asset(asset_path):
    if asset_path.startswith("api/"):
        return jsonify({{"error": "API route not found", "path": "/" + asset_path}}), 404
    candidate = FRONTEND_DIR / asset_path
    if candidate.is_file():
        return send_frontend_file(asset_path)
    return send_frontend_file("index.html")


def send_frontend_file(name):
    if not FRONTEND_DIR.exists():
        return (
            "Frontend files were not found. Run `python nova.py build-ui examples/business_admin.nova` first.",
            404,
        )
    return send_from_directory(FRONTEND_DIR, name)


def find_table(*names):
    for wanted in names:
        for table_name in TABLES:
            if table_name.lower() == wanted.lower():
                return table_name
    for wanted in names:
        for table_name in TABLES:
            if wanted.lower() in table_name.lower():
                return table_name
    return None


def find_field(table_name, *names):
    fields = TABLES.get(table_name, [])
    for wanted in names:
        for field in fields:
            if field["name"].lower() == wanted.lower():
                return field["name"]
    for wanted in names:
        for field in fields:
            if wanted.lower() in field["name"].lower():
                return field["name"]
    return None


def set_if_field(payload, table_name, value, *field_names):
    field = find_field(table_name, *field_names)
    if field:
        payload[field] = value


{checkout_route}
@app.route("/api/<path:api_path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
def api(api_path):
    path = "/api/" + api_path.strip("/")
    body = request.get_json(silent=True) or {{}}

    declared = handle_declared_route(request.method, path, body)
    if declared is not None:
        payload, status = declared
        return jsonify(payload), status

    parts = [part for part in api_path.split("/") if part]
    if not parts:
        return jsonify({{"error": "missing API resource"}}), 400

    table_name = table_for_resource(parts[0])
    if table_name is None:
        return jsonify({{"error": "unknown API resource", "resource": parts[0]}}), 404

    if len(parts) == 1:
        if request.method == "GET":
            return jsonify({{"rows": public_rows(table_name), "table": table_name}})
        if request.method == "POST":
            return jsonify({{"row": public_row(table_name, create_row(table_name, body)), "table": table_name}}), 201
        return jsonify({{"error": "method not allowed"}}), 405

    if len(parts) == 2 and parts[1] == "count" and request.method == "GET":
        return jsonify({{"count": count_rows(table_name), "table": table_name}})

    if len(parts) == 3 and parts[1] == "sum" and request.method == "GET":
        return jsonify({{"sum": sum_rows(table_name, parts[2]), "table": table_name, "field": parts[2]}})

    if len(parts) == 2:
        row_id = parts[1]
        if request.method == "GET":
            row = get_row(table_name, row_id)
            if row is None:
                return jsonify({{"error": "row not found"}}), 404
            return jsonify({{"row": public_row(table_name, row), "table": table_name}})
        if request.method in {{"PUT", "PATCH"}}:
            from models import update_row

            row = update_row(table_name, row_id, body)
            if row is None:
                return jsonify({{"error": "row not found"}}), 404
            return jsonify({{"row": public_row(table_name, row), "table": table_name}})
        if request.method == "DELETE":
            row = delete_row(table_name, row_id)
            if row is None:
                return jsonify({{"error": "row not found"}}), 404
            return jsonify({{"deleted": public_row(table_name, row), "table": table_name}})

    return jsonify({{"error": "unsupported API shape", "path": path}}), 404


@app.get("/api/schema")
def schema():
    return jsonify(
        {{
            "tables": TABLES,
            "resources": API_TABLES,
            "primaryKeys": {{name: primary_key(name) for name in TABLES}},
            "routes": ROUTES,
        }}
    )


@app.get("/api/health")
def health():
    return jsonify({{"ok": True, "frontend": FRONTEND_DIR.exists(), "database": database_status()}})


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("DEBUG", "1") != "0"
    app.run(host=host, port=port, debug=debug, use_reloader=False)
'''

    def checkout_route_py(self) -> str:
        return '''@app.post("/api/checkout")
def checkout():
    body = request.get_json(silent=True) or {}
    cart_table = find_table("CartItem", "CartLine", "Cart")
    product_table = find_table("Product")
    order_table = find_table("Order", "Purchase")
    order_item_table = find_table("OrderItem", "OrderLine")

    if not cart_table or not order_table:
        return jsonify({"error": "checkout needs CartItem and Order tables"}), 400

    cart_rows = list(list_rows(cart_table))
    if not cart_rows:
        return jsonify({"error": "cart is empty"}), 400

    cart_product_id = find_field(cart_table, "productId", "product_id", "product")
    cart_product_name = find_field(cart_table, "productName", "product_name", "name")
    cart_price = find_field(cart_table, "price", "unitPrice", "amount")
    cart_quantity = find_field(cart_table, "quantity", "qty", "count")

    total = sum(float(row.get(cart_price) or 0) * int(row.get(cart_quantity) or 1) for row in cart_rows)

    order_payload = {}
    for key, value in body.items():
        set_if_field(order_payload, order_table, value, key)
    set_if_field(order_payload, order_table, body.get("customerName") or body.get("name") or "", "customerName", "customer", "name")
    set_if_field(order_payload, order_table, body.get("email") or "", "email")
    set_if_field(order_payload, order_table, body.get("address") or "", "address", "shipping")
    set_if_field(order_payload, order_table, total, "total", "amount")
    set_if_field(order_payload, order_table, "Paid", "status", "state")

    order = create_row(order_table, order_payload)
    order_id = order.get(primary_key(order_table))
    created_items = []

    if order_item_table:
        for cart_row in cart_rows:
            item_payload = {}
            set_if_field(item_payload, order_item_table, order_id, "orderId", "order_id", "order")
            set_if_field(item_payload, order_item_table, cart_row.get(cart_product_id), "productId", "product_id", "product")
            set_if_field(item_payload, order_item_table, cart_row.get(cart_product_name), "productName", "product_name", "name")
            set_if_field(item_payload, order_item_table, cart_row.get(cart_price), "price", "unitPrice", "amount")
            set_if_field(item_payload, order_item_table, cart_row.get(cart_quantity), "quantity", "qty", "count")
            created_items.append(create_row(order_item_table, item_payload))

    if product_table and cart_product_id:
        stock_field = find_field(product_table, "stock", "inventory", "quantity")
        if stock_field:
            for cart_row in cart_rows:
                product = get_row(product_table, cart_row.get(cart_product_id))
                if product:
                    next_stock = max(0, int(product.get(stock_field) or 0) - int(cart_row.get(cart_quantity) or 1))
                    update_row(product_table, product.get(primary_key(product_table)), {stock_field: next_stock})

    clear_rows(cart_table)
    return jsonify(
        {
            "order": public_row(order_table, order),
            "items": [public_row(order_item_table, item) for item in created_items] if order_item_table else [],
            "total": total,
        }
    ), 201


'''

    def backend_readme(self, frontend_relative: str, ir: ProjectIR) -> str:
        workflow_lines = "\n".join(f"POST /api/workflows/{slug_name(workflow.name)}" for workflow in ir.workflows) or "No workflow endpoints declared."
        return f"""# Generated NovaDev Flask Backend

This backend serves the generated NovaDev UI and JSON APIs from one Flask app.
It stores table data in `database.db` using SQLite plus SQLAlchemy.

## Setup

```bash
python -m pip install -r requirements.txt
python app.py
```

Open:

```txt
http://127.0.0.1:5000
```

The app expects frontend files at:

```txt
{frontend_relative}
```

Database file:

```txt
backend/database.db
```

The first app start creates SQLite tables from NovaDev `table` declarations and
seeds sample rows when a table is empty.

Build them from the project root with:

```bash
python nova.py build-ui examples/business_admin.nova
```

Useful API endpoints:

```txt
GET  /api/health
GET  /api/schema
GET  /api/<resource>
POST /api/<resource>
GET  /api/<resource>/count
```

Workflow endpoints generated from this project:

```txt
{workflow_lines}
```
"""


def api_resource_name(table_name: str) -> str:
    words = re.sub(r"(?<!^)(?=[A-Z])", "-", table_name).replace("_", "-").lower()
    base = re.sub(r"[^a-z0-9-]+", "-", words).strip("-") or "rows"
    if base.endswith("y") and not base.endswith(("ay", "ey", "iy", "oy", "uy")):
        return base[:-1] + "ies"
    if base.endswith("s"):
        return base + "es"
    return base + "s"


def primary_key(table: TableNode) -> str:
    for field in table.fields:
        if field.auto:
            return field.name
    for field in table.fields:
        if field.name == "id":
            return field.name
    return table.fields[0].name if table.fields else "id"


def sample_rows(table: TableNode, mode: str = "") -> List[Dict[str, Any]]:
    if table.name.lower() in {"cart", "cartitem", "cartline", "order", "orderitem", "orderline"}:
        return []
    if table.name.lower() == "product":
        return sample_product_rows(table)
    domain_rows = domain_sample_rows(table, mode)
    if domain_rows:
        return domain_rows
    rows: List[Dict[str, Any]] = []
    for index in range(1, 4):
        row: Dict[str, Any] = {}
        for field in table.fields:
            row[field.name] = sample_value(field, index, table.name, mode)
        rows.append(row)
    return rows


def domain_sample_rows(table: TableNode, mode: str = "") -> List[Dict[str, Any]]:
    mode = (mode or "").lower()
    name = table.name.lower()
    seeds = {
        ("construction", "service"): [
            {"name": "Kitchen Renovation", "description": "Full planning, demolition, and finish work.", "startingPrice": 12500},
            {"name": "Roof Replacement", "description": "Weather-ready roofing with clean project tracking.", "startingPrice": 9800},
            {"name": "Commercial Buildout", "description": "Interior buildout for growing local businesses.", "startingPrice": 34000},
        ],
        ("construction", "project"): [
            {"name": "Harbor View Remodel", "location": "Kingston", "budget": 68000},
            {"name": "Northside Office Fitout", "location": "Montego Bay", "budget": 92000},
            {"name": "Family Home Extension", "location": "Spanish Town", "budget": 41000},
        ],
        ("crm", "deal"): [
            {"clientName": "Aster Foods", "value": 18000, "stage": "new"},
            {"clientName": "Blue Peak Logistics", "value": 42000, "stage": "proposal"},
            {"clientName": "Cedar Retail", "value": 26000, "stage": "qualified"},
        ],
        ("crm", "client"): [
            {"name": "Aster Foods", "email": "hello@aster.example"},
            {"name": "Blue Peak Logistics", "email": "ops@bluepeak.example"},
            {"name": "Cedar Retail", "email": "team@cedar.example"},
        ],
        ("custom", "sermon"): [
            {"title": "Faith for the Week", "speaker": "Pastor Allen", "videoUrl": "https://example.com/sermon-1"},
            {"title": "Serving With Joy", "speaker": "Minister Cole", "videoUrl": "https://example.com/sermon-2"},
            {"title": "Hope in Motion", "speaker": "Pastor Allen", "videoUrl": "https://example.com/sermon-3"},
        ],
        ("security", "target"): [
            {"url": "https://example.com", "status": "ready"},
            {"url": "https://shop.example.com", "status": "queued"},
            {"url": "https://admin.example.com", "status": "review"},
        ],
    }
    raw_rows = seeds.get((mode, name), [])
    if not raw_rows:
        return []
    rows: List[Dict[str, Any]] = []
    for index, raw in enumerate(raw_rows, start=1):
        row: Dict[str, Any] = {}
        for field in table.fields:
            if field.auto:
                row[field.name] = index
            elif field.name in raw:
                row[field.name] = raw[field.name]
            else:
                row[field.name] = sample_value(field, index, table.name, mode)
        rows.append(row)
    return rows


def sample_product_rows(table: TableNode) -> List[Dict[str, Any]]:
    products = [
        ("Aurora Hoodie", "Soft heavyweight fleece for everyday wear.", "Apparel", 68, 24),
        ("Orbit Desk Lamp", "Adjustable LED lamp with warm and cool modes.", "Home", 89, 18),
        ("Nova Tote", "Durable canvas tote for work, gym, and errands.", "Accessories", 32, 40),
        ("Focus Bottle", "Insulated stainless bottle that keeps drinks cold.", "Drinkware", 28, 35),
    ]
    rows: List[Dict[str, Any]] = []
    for index, (name, description, category, price, stock) in enumerate(products, start=1):
        row: Dict[str, Any] = {}
        for field in table.fields:
            lowered = field.name.lower()
            if field.auto:
                row[field.name] = index
            elif "description" in lowered:
                row[field.name] = description
            elif "category" in lowered:
                row[field.name] = category
            elif "price" in lowered or field.field_type.lower() in {"money", "currency"}:
                row[field.name] = price
            elif "stock" in lowered or "inventory" in lowered:
                row[field.name] = stock
            elif lowered in {"active", "enabled"} or field.field_type.lower() in {"bool", "boolean"}:
                row[field.name] = True
            elif "name" in lowered or "title" in lowered:
                row[field.name] = name
            else:
                row[field.name] = sample_value(field, index)
        rows.append(row)
    return rows


def sample_value(field, index: int, table_name: str = "", mode: str = "") -> Any:
    kind = field.field_type.lower()
    if field.auto:
        return index
    if kind in {"int", "number"}:
        return index * 10
    if kind in {"money", "currency"}:
        return index * 25
    if kind in {"bool", "boolean"}:
        return index % 2 == 1
    if kind == "email":
        return f"{field.name}{index}@example.com"
    if kind == "date":
        return f"2026-07-{index:02d}"
    if "status" in field.name.lower():
        return ["new", "active", "review"][index - 1 if index <= 3 else 0]
    if "message" in field.name.lower():
        return f"{table_name} message {index}"
    if "name" in field.name.lower():
        return f"{field.name.title()} {index}"
    return f"{field.name.title()} {index}"


def needs_checkout_route(ir: ProjectIR) -> bool:
    if ir.mode != "ecommerce":
        return False
    entity_names = {entity.name.lower() for entity in ir.entities}
    has_cart_and_order = bool(entity_names & {"cart", "cartitem", "cartline"}) and bool(entity_names & {"order", "purchase"})
    if not has_cart_and_order:
        return False
    for workflow in ir.workflows:
        workflow_text = " ".join([workflow.name, workflow.input, workflow.uses, *workflow.creates]).lower()
        if "checkout" in workflow_text or "cart" in workflow_text:
            return True
    for page in ir.pages:
        page_text = " ".join([page.name, page.type, *[component.get("kind", "") for component in page.components]]).lower()
        if "checkout" in page_text or "cart" in page_text or "catalog" in page_text:
            return True
    return False


def slug_name(name: str) -> str:
    separated = re.sub(r"(.)([A-Z][a-z]+)", r"\1-\2", name)
    separated = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", separated)
    separated = separated.replace("_", "-")
    return re.sub(r"[^a-zA-Z0-9-]+", "-", separated).strip("-").lower() or "item"
