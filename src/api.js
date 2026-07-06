async function postJson(path, body) {
  const response = await fetch(path, {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify(body),
  });

  const payload = await response.json().catch(() => ({
    ok: false,
    error: "The server returned a non-JSON response.",
  }));

  if (!response.ok && payload.ok !== false) {
    payload.ok = false;
    payload.error = payload.error || `Request failed with status ${response.status}`;
  }

  return payload;
}

export function runNova(code) {
  return postJson("/api/run", { code });
}

export function getTokens(code) {
  return postJson("/api/tokens", { code });
}

export function getAst(code) {
  return postJson("/api/ast", { code });
}

export function buildUi(code) {
  return postJson("/api/build_ui", { code });
}

export function createShare(code) {
  return postJson("/api/share", { code });
}
