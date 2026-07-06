from __future__ import annotations

from ..ast_nodes import (
    App,
    Button,
    Card,
    Chart,
    FormView,
    Layout,
    Modal,
    Navigation,
    Sidebar,
    TableView,
)


def build_component_tree(app: App) -> dict:
    return {
        "app": app.name,
        "theme": app.active_theme,
        "routes": [
            {
                "name": page.name,
                "path": page.route_path,
                "title": page.display_title(),
                "requiresAuth": page.requires_auth,
                "requiredRole": page.required_role,
            }
            for page in app.pages
        ],
        "pages": [page_to_dict(page) for page in app.pages],
    }


def page_to_dict(page) -> dict:
    return {
        "name": page.name,
        "path": page.route_path,
        "title": page.display_title(),
        "requiresAuth": page.requires_auth,
        "requiredRole": page.required_role,
        "components": [component_to_dict(component) for component in page.components],
    }


def component_to_dict(component) -> dict:
    if isinstance(component, Layout):
        return {"type": "layout", "name": component.name}
    if isinstance(component, Sidebar):
        return {"type": "sidebar", "links": [link.__dict__ for link in component.links]}
    if isinstance(component, Navigation):
        return {"type": "navbar", "links": [link.__dict__ for link in component.links]}
    if isinstance(component, Card):
        return {
            "type": "card",
            "title": component.title,
            "value": component.value,
            "valueIsExpression": component.value_is_expression,
        }
    if isinstance(component, TableView):
        return {
            "type": "table",
            "table": component.table_name,
            "columns": component.columns,
            "actions": component.actions,
        }
    if isinstance(component, FormView):
        return {
            "type": "form",
            "table": component.table_name,
            "fields": component.fields,
            "submitLabel": component.submit_label,
        }
    if isinstance(component, Chart):
        return {
            "type": "chart",
            "source": component.source_name,
            "chartType": component.chart_type,
            "x": component.x_field,
            "y": component.y_field,
        }
    if isinstance(component, Button):
        return {"type": "button", "label": component.label, "action": component.action}
    if isinstance(component, Modal):
        return {
            "type": "modal",
            "title": component.title,
            "body": component.body,
            "buttonLabel": component.button_label,
        }
    return {"type": component.__class__.__name__}
