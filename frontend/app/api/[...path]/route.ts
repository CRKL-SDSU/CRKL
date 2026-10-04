const allowedResources = new Set([
  "missions",
  "agencies",
  "spacecraft",
  "launches"
]);

function isAllowedPath(path: string[]) {
  return (
    path.length >= 2 &&
    path[0] === "v1" &&
    allowedResources.has(path[1]) &&
    path.length <= 3 &&
    path.slice(2).every((segment) => /^\d+$/.test(segment))
  );
}

export async function GET(
  request: Request,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  if (!isAllowedPath(path)) {
    return Response.json({ detail: "Not found" }, { status: 404 });
  }

  const backendUrl = process.env.CRKL_BACKEND_URL || "http://127.0.0.1:8000";
  const target = new URL(`/api/${path.join("/")}`, backendUrl);
  target.search = new URL(request.url).search;

  try {
    const response = await fetch(target, {
      headers: { Accept: "application/json" },
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
