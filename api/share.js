function encodeBase64Url(value) {
  return Buffer.from(value, "utf8")
    .toString("base64")
    .replaceAll("+", "-")
    .replaceAll("/", "_")
    .replaceAll("=", "");
}

export default function handler(request, response) {
  if (request.method === "OPTIONS") {
    response.setHeader("access-control-allow-origin", "*");
    response.setHeader("access-control-allow-methods", "POST, OPTIONS");
    response.setHeader("access-control-allow-headers", "content-type");
    response.status(200).json({ ok: true });
    return;
  }

  if (request.method !== "POST") {
    response.status(405).json({ ok: false, error: "Use POST" });
    return;
  }

  const code = request.body?.code || "";
  if (typeof code !== "string") {
    response.status(400).json({ ok: false, error: "code must be a string" });
    return;
  }

  if (Buffer.byteLength(code, "utf8") > 64000) {
    response.status(413).json({ ok: false, error: "Code is too large to share" });
    return;
  }

  const host = request.headers["x-forwarded-host"] || request.headers.host || "localhost";
  const protocol = request.headers["x-forwarded-proto"] || "https";
  const encoded = encodeBase64Url(code);
  response.status(200).json({
    ok: true,
    url: `${protocol}://${host}/#code=${encoded}`,
  });
}
