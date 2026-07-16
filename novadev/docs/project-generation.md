# Project Generation

NovaDev 0.4 can generate a runnable Flask + frontend project.

Build:

```bash
python nova.py build examples/alchicken_app.nova
```

Run:

```bash
cd generated/al-chicken-store/backend
python -m pip install -r requirements.txt
python app.py
```

Open:

```txt
http://127.0.0.1:5000
```

## App Declaration

```nova
app ALChickenStore {
    stack JQueryFlask
    database sqlite

    table Product {
        id auto
        name text
        price money
    }

    page Storefront {
        title "Store"
        catalog Product {
            fields name price
            actions add_to_cart
        }
    }
}
```

## Filesystem DSL

The filesystem DSL creates extra folders and files inside the generated project.

```nova
filesystem {
    template JQueryFlask
    folder docs {
        file "plan.md" {
            text """
# Plan

Generated from NovaDev.
"""
        }
    }
    ignore {
        "__pycache__/"
        "*.pyc"
    }
}
```

## Generated Structure

```txt
generated/<app>/
  README.md
  frontend/
    index.html
    css/style.css
    js/app.js
  backend/
    app.py
    models.py
    routes.py
    requirements.txt
```

The backend serves the frontend and provides table APIs such as:

```txt
GET    /api/products
POST   /api/products
GET    /api/products/<id>
PUT    /api/products/<id>
DELETE /api/products/<id>
```
