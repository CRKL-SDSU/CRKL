"use client";

import Link from "next/link";
import { FormEvent, useMemo, useState } from "react";

import { aboutUrl } from "./site";

type Resource = "missions" | "agencies" | "spacecraft" | "launches";
type Operation = "collection" | "detail";

type RequestRecord = {
  method: string;
  url: string;
  status: number | "ERR";
  duration: number;
};

const resources: Record<
  Resource,
  { label: string; description: string; idLabel: string }
> = {
  missions: {
    label: "Missions",
    description: "Explore spaceflight missions and their related entities.",
    idLabel: "Mission ID"
  },
  agencies: {
    label: "Agencies",
    description: "Browse organizations involved in space exploration.",
    idLabel: "Agency ID"
  },
  spacecraft: {
    label: "Spacecraft",
    description: "Inspect spacecraft and their mission relationships.",
    idLabel: "Spacecraft ID"
  },
  launches: {
    label: "Launches",
    description: "View launch schedules, statuses, and mission links.",
    idLabel: "Launch ID"
  }
};

const apiBaseUrl = "/api/v1";

function formatJson(value: unknown) {
  return JSON.stringify(value, null, 2);
}

export default function Home() {
  const [resource, setResource] = useState<Resource>("missions");
  const [operation, setOperation] = useState<Operation>("collection");
  const [limit, setLimit] = useState("20");
  const [offset, setOffset] = useState("0");
  const [id, setId] = useState("");
  const [response, setResponse] = useState<unknown>(null);
  const [status, setStatus] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [lastUrl, setLastUrl] = useState("");
  const [duration, setDuration] = useState<number | null>(null);
  const [history, setHistory] = useState<RequestRecord[]>([]);

  const resourceInfo = resources[resource];
  const path = useMemo(
    () => `${apiBaseUrl.replace(/\/$/, "")}/${resource}`,
    [resource]
  );

  function changeResource(value: Resource) {
    setResource(value);
    setResponse(null);
    setStatus(null);
    setError("");
  }

  function changeOperation(value: Operation) {
    setOperation(value);
    setResponse(null);
    setStatus(null);
    setError("");
  }

  async function sendRequest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (operation === "detail" && !id.trim()) {
      setError(`Enter a ${resourceInfo.idLabel.toLowerCase()} first.`);
      return;
    }

    const requestPath =
      operation === "detail" ? `${path}/${encodeURIComponent(id.trim())}` : path;
    const url = new URL(requestPath, window.location.origin);
    if (operation === "collection") {
      url.searchParams.set("limit", limit);
      url.searchParams.set("offset", offset);
    }

    const started = performance.now();
    setLoading(true);
    setError("");
    setStatus(null);
    setResponse(null);
    setLastUrl(url.toString());

    try {
      const result = await fetch(url.toString(), {
        headers: { Accept: "application/json" }
      });
      const contentType = result.headers.get("content-type") || "";
      const body = contentType.includes("application/json")
        ? await result.json()
        : await result.text();
      const requestDuration = Math.round(performance.now() - started);

      setStatus(result.status);
      setDuration(requestDuration);
      setResponse(body);
      setHistory((current) => [
        {
          method: "GET",
          url: url.toString(),
          status: result.status,
          duration: requestDuration
        },
        ...current
      ].slice(0, 5));

      if (!result.ok) {
        setError(`The API returned ${result.status} ${result.statusText}.`);
      }
    } catch (requestError) {
      const requestDuration = Math.round(performance.now() - started);
      setDuration(requestDuration);
      setStatus(null);
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to reach the API server."
      );
      setHistory((current) => [
        { method: "GET", url: url.toString(), status: "ERR" as const, duration: requestDuration },
        ...current
      ].slice(0, 5));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">C</span>
          <span>CRKL</span>
        </div>
        <nav className="topnav">
          <Link href="/explore">Explore data</Link>
          <span className="api-badge">SPACE EXPLORATION API</span>
        </nav>
      </header>

      <section className="hero">
        <div>
          <p className="eyebrow">API WORKBENCH / v1.0.0</p>
          <h1>Explore the final frontier.</h1>
          <p className="hero-copy">
            A simple request console for the CRKL space data API. Choose a
            resource, send a JSON request, and inspect the response.
          </p>
        </div>
        <div className="orbit-art" aria-hidden="true">
          <div className="planet" />
          <div className="orbit orbit-one" />
          <div className="orbit orbit-two" />
          <span className="star star-one">✦</span>
          <span className="star star-two">·</span>
        </div>
      </section>

      <div className="workspace">
        <aside className="sidebar">
          <p className="section-label">RESOURCES</p>
          {(Object.keys(resources) as Resource[]).map((key) => (
            <button
              className={`resource-button ${resource === key ? "selected" : ""}`}
              key={key}
              onClick={() => changeResource(key)}
              type="button"
            >
              <span className="resource-icon">{key === "missions" ? "✦" : key === "agencies" ? "◎" : key === "spacecraft" ? "◇" : "↗"}</span>
              <span>{resources[key].label}</span>
              {resource === key && <span className="selected-dot" />}
            </button>
          ))}
          <div className="server-card">
            <span className="status-dot" />
            <div>
              <strong>API server</strong>
              <small>{apiBaseUrl}</small>
            </div>
          </div>
        </aside>

        <section className="console">
          <div className="console-heading">
            <div>
              <p className="eyebrow">REQUEST BUILDER</p>
              <h2>{resourceInfo.label}</h2>
              <p>{resourceInfo.description}</p>
            </div>
            <span className="method-pill">GET</span>
          </div>

          <form className="request-form" onSubmit={sendRequest}>
            <div className="field-group">
              <label>Operation</label>
              <div className="operation-tabs">
                <button
                  className={operation === "collection" ? "active" : ""}
                  onClick={() => changeOperation("collection")}
                  type="button"
                >
                  List all
                </button>
                <button
                  className={operation === "detail" ? "active" : ""}
                  onClick={() => changeOperation("detail")}
                  type="button"
                >
                  Get by ID
                </button>
              </div>
            </div>

            <div className="url-preview">
              <span>GET</span>
              {operation === "detail" ? `${path}/` : `${path}?limit=${limit}&offset=${offset}`}
              {operation === "detail" && <em>{id || "id"}</em>}
            </div>

            <div className="fields-row">
              {operation === "collection" ? (
                <>
                  <label>
                    Limit
                    <input min="1" type="number" value={limit} onChange={(event) => setLimit(event.target.value)} />
                  </label>
                  <label>
                    Offset
                    <input min="0" type="number" value={offset} onChange={(event) => setOffset(event.target.value)} />
                  </label>
                </>
              ) : (
                <label>
                  {resourceInfo.idLabel}
                  <input min="1" placeholder="e.g. 1" type="number" value={id} onChange={(event) => setId(event.target.value)} />
                </label>
              )}
              <button className="send-button" disabled={loading} type="submit">
                {loading ? "Sending..." : "Send request  →"}
              </button>
            </div>
          </form>

          <div className="response-heading">
            <div>
              <p className="eyebrow">RESPONSE</p>
              <h3>
                {status ? `HTTP ${status}` : "No response yet"}
                {duration !== null && <small>{duration} ms</small>}
              </h3>
            </div>
            {status && <span className={`response-status ${status < 400 ? "success" : "failure"}`}>{status < 400 ? "SUCCESS" : "ERROR"}</span>}
          </div>
          {error && <div className="error-message">{error}</div>}
          <pre className="response-panel">
            {response === null ? "// Send a request to see the JSON response here." : formatJson(response)}
          </pre>

          {history.length > 0 && (
            <div className="history">
              <p className="section-label">RECENT REQUESTS</p>
              {history.map((request, index) => (
                <div className="history-row" key={`${request.url}-${index}`}>
                  <span className="history-method">{request.method}</span>
                  <span className="history-url">{request.url}</span>
                  <span className={request.status === "ERR" || request.status >= 400 ? "history-failure" : "history-success"}>{request.status}</span>
                  <span className="history-time">{request.duration} ms</span>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
      <footer>
        Built from the CRKL OpenAPI specification · JSON over REST ·{" "}
        <a href={aboutUrl}>About Us</a>
      </footer>
    </main>
  );
}
