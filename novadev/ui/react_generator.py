from __future__ import annotations

import json

from ..ast_nodes import App
from .component_tree import build_component_tree


def generate_react_app(app: App) -> str:
    tree = build_component_tree(app)
    return """import React, { useMemo, useState } from "react";

const componentTree = """ + json.dumps(tree, indent=2) + """;

export default function App() {
  const [role, setRole] = useState("Admin");
  const routes = componentTree.routes;
  const firstRoute = routes[0]?.path || "/";
  const [route, setRoute] = useState(firstRoute);
  const current = useMemo(() => routes.find((item) => item.path === route) || routes[0], [route, routes]);
  const page = componentTree.pages.find((item) => item.path === current?.path);
  const allowed = !current?.requiredRole || current.requiredRole === role;

  return (
    <main className="nova-app">
      <aside>
        <strong>{componentTree.app}</strong>
        <nav>
          {routes.map((item) => (
            <button key={item.path} type="button" onClick={() => setRoute(item.path)}>
              {item.title}
            </button>
          ))}
        </nav>
      </aside>
      <section>
        <header>
          <h1>{current?.title}</h1>
          <select value={role} onChange={(event) => setRole(event.target.value)}>
            <option>Admin</option>
            <option>Editor</option>
            <option>User</option>
          </select>
        </header>
        {!allowed ? (
          <p>Access restricted to {current.requiredRole}.</p>
        ) : (
          <pre>{JSON.stringify(page?.components || [], null, 2)}</pre>
        )}
      </section>
    </main>
  );
}
"""
