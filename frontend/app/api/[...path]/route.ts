const allowedResources = new Set([
  "missions",
  "agencies",
  "spacecraft",
  "launches"
]);

const isId = (segment: string) => /^\d+$/.test(segment);

// GET: /v1/{resource}, /v1/{resource}/{id}, and /v1/tags
function isAllowedGetPath(path: string[]) {
  if (path.length === 2 && path[0] === "v1" && path[1] === "tags") return true;
  return (
    path.length >= 2 &&
    path[0] === "v1" &&
    allowedResources.has(path[1]) &&
    path.length <= 3 &&
    path.slice(2).every(isId)
  );
}

// POST: /v1/missions/{id}/tags
function isAllowedPostPath(path: string[]) {
  return (
    path.length === 4 &&
    path[0] === "v1" &&
    path[1] === "missions" &&
    isId(path[2]) &&
    path[3] === "tags"
  );
}

// DELETE: /v1/missions/{id}/tags/{tagId}
function isAllowedDeletePath(path: string[]) {
  return path.length === 5 && isAllowedPostPath(path.slice(0, 4)) && isId(path[4]);
}

// Writes must come from this site's own pages, not from another origin
function isSameOrigin(request: Request) {
  const origin = request.headers.get("origin");
  return origin === null || origin === new URL(request.url).origin;
}

async function forward(request: Request, path: string[], body?: string) {
  const backendUrl = process.env.CRKL_BACKEND_URL || "http://127.0.0.1:8000";
  const target = new URL(`/api/${path.join("/")}`, backendUrl);
  target.search = new URL(request.url).search;

  const requestHeaders: Record<string, string> = { Accept: "application/json" };
  if (body !== undefined) requestHeaders["Content-Type"] = "application/json";

  try {
    const response = await fetch(target, {
      method: request.method,
      headers: requestHeaders,
      body,
      cache: "no-store"
    });
    const headers = new Headers();
    const contentType = response.headers.get("content-type");
    if (contentType) headers.set("content-type", contentType);

    return new Response(response.body, {
      headers,
      status: response.status,
      statusText: response.statusText
    });
  } catch {
    return Response.json(
      { detail: "The backend service is unavailable." },
      { status: 502 }
    );
  }
}

type RouteContext = { params: Promise<{ path: string[] }> };

export async function GET(request: Request, { params }: RouteContext) {
  const { path } = await params;
  if (!isAllowedGetPath(path)) {
    return Response.json({ detail: "Not found" }, { status: 404 });
  }
  return forward(request, path);
}

export async function POST(request: Request, { params }: RouteContext) {
  const { path } = await params;
  if (!isAllowedPostPath(path)) {
    return Response.json({ detail: "Not found" }, { status: 404 });
  }
  if (!isSameOrigin(request)) {
    return Response.json({ detail: "Forbidden" }, { status: 403 });
  }
  const body = await request.text();
  if (body.length > 1000) {
    return Response.json({ detail: "Request body is too large." }, { status: 413 });
  }
  return forward(request, path, body);
}

export async function DELETE(request: Request, { params }: RouteContext) {
  const { path } = await params;
  if (!isAllowedDeletePath(path)) {
    return Response.json({ detail: "Not found" }, { status: 404 });
  }
  if (!isSameOrigin(request)) {
    return Response.json({ detail: "Forbidden" }, { status: 403 });
  }
  return forward(request, path);
}
