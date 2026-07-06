from __future__ import annotations

import json

from ..ast_nodes import App
from .api_binder import app_schema, bind_sample_data
from .component_tree import build_component_tree


def generate_js(app: App) -> str:
    payload = {
        "name": app.name,
        "schema": app_schema(app),
        "data": bind_sample_data(app),
        "tree": build_component_tree(app),
    }
    return "const NOVA_APP = " + json.dumps(payload, indent=2) + ";\n" + JAVASCRIPT_RUNTIME


JAVASCRIPT_RUNTIME = r'''

const state = {
  mode: localStorage.getItem("nova-mode") || "dark",
  role: localStorage.getItem("nova-role") || "Admin"
};

function $(selector, parent = document) {
  return parent.querySelector(selector);
}

function $all(selector, parent = document) {
  return Array.from(parent.querySelectorAll(selector));
}

function fieldSchema(tableName) {
  return NOVA_APP.schema.tables[tableName]?.fields || [];
}

function visibleFields(tableName) {
  return fieldSchema(tableName).filter((field) => !field.auto && !field.secure);
}

function selectedColumns(tableName, rawColumns) {
  const declared = rawColumns ? rawColumns.split(",").filter(Boolean) : [];
  if (declared.length) return declared;
  return visibleFields(tableName).map((field) => field.name);
}

function fieldKind(tableName, fieldName) {
  return fieldSchema(tableName).find((field) => field.name === fieldName)?.kind || "text";
}

function isNumericKind(kind) {
  return ["int", "number", "money", "currency"].includes(String(kind).toLowerCase());
}

function formatValue(tableName, fieldName, value) {
  const kind = fieldKind(tableName, fieldName).toLowerCase();
  if (kind === "money" || kind === "currency") {
    return new Intl.NumberFormat(undefined, { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(Number(value || 0));
  }
  if (kind === "bool" || kind === "boolean") return value ? "Yes" : "No";
  return value == null ? "" : String(value);
}

function expressionValue(expression) {
  const countMatch = expression.match(/^([A-Za-z_][A-Za-z0-9_]*)\.count\(\)$/);
  if (countMatch) return String((NOVA_APP.data[countMatch[1]] || []).length);

  const sumMatch = expression.match(/^([A-Za-z_][A-Za-z0-9_]*)\.sum\(([A-Za-z_][A-Za-z0-9_]*)\)$/);
  if (sumMatch) {
    const rows = NOVA_APP.data[sumMatch[1]] || [];
    const total = rows.reduce((sum, row) => sum + Number(row[sumMatch[2]] || 0), 0);
    return new Intl.NumberFormat(undefined, { maximumFractionDigits: 0 }).format(total);
  }

  return expression;
}

function updateBoundValues() {
  $all("[data-bind]").forEach((node) => {
    node.textContent = expressionValue(node.dataset.bind || "");
  });
}

function makeCell(text) {
  const cell = document.createElement("td");
  cell.textContent = text;
  return cell;
}

function makeButton(label, className = "secondary-action") {
  const button = document.createElement("button");
  button.type = "button";
  button.className = className;
  button.textContent = label;
  return button;
}

function renderTables() {
  $all("table[data-table]").forEach((table) => {
    const tableName = table.dataset.table;
    const columns = selectedColumns(tableName, table.dataset.columns);
    const actions = table.dataset.actions ? table.dataset.actions.split(",").filter(Boolean) : [];
    const rows = NOVA_APP.data[tableName] || [];
    const body = $("tbody", table);
    if (!body) return;
    body.replaceChildren();

    rows.forEach((row, rowIndex) => {
      const tr = document.createElement("tr");
      columns.forEach((column) => {
        tr.appendChild(makeCell(formatValue(tableName, column, row[column])));
      });

      if (actions.length) {
        const actionCell = document.createElement("td");
        const wrapper = document.createElement("div");
        wrapper.className = "row-actions";
        actions.forEach((action) => {
          const button = makeButton(action);
          button.dataset.action = action;
          button.dataset.table = tableName || "";
          button.dataset.index = String(rowIndex);
          wrapper.appendChild(button);
        });
        actionCell.appendChild(wrapper);
        tr.appendChild(actionCell);
      }

      body.appendChild(tr);
    });
  });
}

function setupForms() {
  $all("form[data-form]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const tableName = form.dataset.form;
      if (!tableName) return;
      const rows = NOVA_APP.data[tableName] || [];
      const row = {};
      let invalid = false;

      fieldSchema(tableName).forEach((field) => {
        if (field.auto) {
          row[field.name] = rows.length + 1;
          return;
        }
        const input = form.elements[field.name];
        if (!input) return;
        if (input.dataset.unique === "true") {
          const duplicate = rows.some((existing) => String(existing[field.name]).toLowerCase() === String(input.value).toLowerCase());
          if (duplicate) {
            input.setCustomValidity("Value must be unique");
            input.reportValidity();
            invalid = true;
            return;
          }
          input.setCustomValidity("");
        }
        if (input.type === "checkbox") {
          row[field.name] = input.checked;
        } else if (isNumericKind(field.kind)) {
          row[field.name] = Number(input.value || 0);
        } else {
          row[field.name] = input.value;
        }
      });

      if (invalid) return;
      rows.push(row);
      NOVA_APP.data[tableName] = rows;
      form.reset();
      renderAll();
    });
  });
}

function handleTableAction(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  const tableName = button.dataset.table;
  const index = Number(button.dataset.index);
  const action = button.dataset.action;
  const rows = NOVA_APP.data[tableName] || [];
  const row = rows[index];
  if (!row) return;

  if (action === "delete") {
    if (confirm(`Delete ${tableName} row ${index + 1}?`)) {
      rows.splice(index, 1);
      renderAll();
    }
    return;
  }

  if (action === "edit") {
    const editable = visibleFields(tableName)[0];
    if (!editable) return;
    const next = prompt(`Edit ${editable.name}`, row[editable.name]);
    if (next != null) {
      row[editable.name] = isNumericKind(editable.kind) ? Number(next) : next;
      renderAll();
    }
    return;
  }

  alert(JSON.stringify(row, null, 2));
}

function drawChart(canvas) {
  const tableName = canvas.dataset.chart;
  const chartType = canvas.dataset.chartType || "line";
  const xField = canvas.dataset.x || "";
  const yField = canvas.dataset.y || "";
  const rows = NOVA_APP.data[tableName] || [];
  const rect = canvas.getBoundingClientRect();
  if (rect.width < 10 || rect.height < 10) return;

  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.floor(rect.width * dpr);
  canvas.height = Math.floor(rect.height * dpr);

  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, rect.width, rect.height);

  const padding = 34;
  const width = rect.width - padding * 2;
  const height = rect.height - padding * 2;
  const values = rows.map((row, index) => Number(row[yField] ?? row.total ?? row.price ?? index + 1));
  const labels = rows.map((row, index) => String(row[xField] ?? index + 1));
  const max = Math.max(...values, 1);

  ctx.strokeStyle = getComputedStyle(document.body).getPropertyValue("--border").trim();
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(padding, padding);
  ctx.lineTo(padding, padding + height);
  ctx.lineTo(padding + width, padding + height);
  ctx.stroke();

  ctx.fillStyle = getComputedStyle(document.body).getPropertyValue("--muted").trim();
  ctx.font = "12px system-ui";
  labels.forEach((label, index) => {
    const x = padding + (values.length <= 1 ? width / 2 : (index / (values.length - 1)) * width);
    ctx.fillText(label.slice(0, 10), Math.min(x, padding + width - 50), padding + height + 20);
  });

  const accent = getComputedStyle(document.body).getPropertyValue("--accent").trim();
  const alt = getComputedStyle(document.body).getPropertyValue("--accent-alt").trim();
  if (chartType === "bar") {
    const barWidth = Math.max(20, width / Math.max(values.length * 1.5, 1));
    values.forEach((value, index) => {
      const x = padding + (index + 0.3) * (width / Math.max(values.length, 1));
      const barHeight = (value / max) * height;
      ctx.fillStyle = index % 2 ? alt : accent;
      ctx.fillRect(x, padding + height - barHeight, barWidth, barHeight);
    });
    return;
  }

  ctx.strokeStyle = accent;
  ctx.fillStyle = accent;
  ctx.lineWidth = 3;
  ctx.beginPath();
  values.forEach((value, index) => {
    const x = padding + (values.length <= 1 ? width / 2 : (index / (values.length - 1)) * width);
    const y = padding + height - (value / max) * height;
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
  values.forEach((value, index) => {
    const x = padding + (values.length <= 1 ? width / 2 : (index / (values.length - 1)) * width);
    const y = padding + height - (value / max) * height;
    ctx.beginPath();
    ctx.arc(x, y, 4, 0, Math.PI * 2);
    ctx.fill();
  });
}

function renderCharts() {
  $all("canvas[data-chart]").forEach(drawChart);
}

function setupRoleSelect() {
  const roleSelect = $("#roleSelect");
  if (!roleSelect) return;
  roleSelect.value = state.role;
  roleSelect.addEventListener("change", () => {
    state.role = roleSelect.value;
    localStorage.setItem("nova-role", state.role);
    activateRoute();
  });
}

function setupThemeToggle() {
  document.body.dataset.mode = state.mode;
  const button = $("#themeToggle");
  if (!button) return;
  button.textContent = state.mode === "dark" ? "Light" : "Dark";
  button.addEventListener("click", () => {
    state.mode = state.mode === "dark" ? "light" : "dark";
    document.body.dataset.mode = state.mode;
    localStorage.setItem("nova-mode", state.mode);
    button.textContent = state.mode === "dark" ? "Light" : "Dark";
    renderCharts();
  });
}

function setupModals() {
  $all("[data-open-modal]").forEach((button) => {
    button.addEventListener("click", () => {
      const dialog = document.getElementById(button.dataset.openModal);
      if (dialog?.showModal) dialog.showModal();
    });
  });
  $all("[data-close-modal]").forEach((button) => {
    button.addEventListener("click", () => {
      button.closest("dialog")?.close();
    });
  });
}

function routeFromHash() {
  const path = location.hash.replace(/^#/, "") || NOVA_APP.tree.routes[0]?.path || "/";
  return NOVA_APP.tree.routes.find((route) => route.path === path) || NOVA_APP.tree.routes[0];
}

function roleCanAccess(route) {
  return !route?.requiredRole || route.requiredRole === state.role;
}

function activateRoute() {
  const route = routeFromHash();
  if (!route) return;
  const allowed = roleCanAccess(route);
  const title = $("#currentTitle");
  if (title) title.textContent = route.title;

  $all(".nav-link").forEach((link) => {
    link.classList.toggle("active", link.getAttribute("href") === `#${route.path}`);
  });

  $all(".page").forEach((page) => {
    page.classList.toggle("active", allowed && page.dataset.route === route.path);
  });

  const warning = $("#unauthorized");
  if (warning) {
    warning.classList.toggle("active", !allowed);
    const roleNode = $("[data-required-role]", warning);
    if (roleNode) roleNode.textContent = route.requiredRole || "";
  }

  requestAnimationFrame(renderAll);
}

function renderAll() {
  updateBoundValues();
  renderTables();
  renderCharts();
}

document.addEventListener("DOMContentLoaded", () => {
  setupRoleSelect();
  setupThemeToggle();
  setupForms();
  setupModals();
  document.addEventListener("click", handleTableAction);
  window.addEventListener("hashchange", activateRoute);
  window.addEventListener("resize", renderCharts);
  if (!location.hash && NOVA_APP.tree.routes[0]) {
    location.hash = NOVA_APP.tree.routes[0].path;
  }
  activateRoute();
});
'''
