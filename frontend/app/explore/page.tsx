"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";

type Resource = "missions" | "agencies" | "spacecraft" | "launches";
type ApiRecord = Record<string, unknown>;
type DetailState = {
  resource: Resource;
  id: string | number;
  record: ApiRecord | null;
  loading: boolean;
  error: string;
};
type DetailTarget = Pick<DetailState, "resource" | "id">;

const resources: { value: Resource; label: string }[] = [
  { value: "missions", label: "Missions" },
  { value: "agencies", label: "Agencies" },
  { value: "spacecraft", label: "Spacecraft" },
  { value: "launches", label: "Launches" }
];

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

function displayValue(value: unknown) {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function titleFor(record: ApiRecord) {
  return displayValue(record.name || record.title || record.mission_name);
}

const resourceIdKeys: Record<Resource, string> = {
  missions: "mission_id",
  agencies: "agency_id",
  spacecraft: "spacecraft_id",
  launches: "launch_id"
};

const relatedResourceByField: Record<string, Resource> = {
  missions: "missions",
  agencies: "agencies",
  spacecraft: "spacecraft",
  launches: "launches"
};

function resourceLabel(resource: Resource) {
  return resource.slice(0, -1);
}

export default function ExplorePage() {
  const [query, setQuery] = useState("");
  const [resource, setResource] = useState<Resource>("missions");
  const [includeRelated, setIncludeRelated] = useState(true);
  const [results, setResults] = useState<ApiRecord[]>([]);
  const [total, setTotal] = useState<number | null>(null);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [detail, setDetail] = useState<DetailState | null>(null);
  const [detailHistory, setDetailHistory] = useState<DetailTarget[]>([]);
  const [detailHistoryIndex, setDetailHistoryIndex] = useState(-1);

  const endpoint = useMemo(
    () => `${apiBaseUrl.replace(/\/$/, "")}/${resource}`,
    [resource]
  );

  async function loadDetail(target: DetailTarget) {
    setDetail({ ...target, record: null, loading: true, error: "" });
    try {
      const response = await fetch(
        `${apiBaseUrl.replace(/\/$/, "")}/${target.resource}/${encodeURIComponent(String(target.id))}`,
        { headers: { Accept: "application/json" } }
      );
      const body: unknown = await response.json();
      if (!response.ok || typeof body !== "object" || body === null) {
        throw new Error(`API returned ${response.status} ${response.statusText}`);
      }
      setDetail((current) =>
        current ? { ...current, record: body as ApiRecord, loading: false } : current
      );
    } catch (requestError) {
      setDetail((current) =>
        current
          ? {
              ...current,
              loading: false,
              error:
                requestError instanceof Error
                  ? requestError.message
                  : "Unable to load this record."
            }
          : current
      );
    }
  }

  function openDetail(nextResource: Resource, id: string | number) {
    const target = { resource: nextResource, id };
    setDetailHistory((current) => [
      ...current.slice(0, detailHistoryIndex + 1),
      target
    ]);
    setDetailHistoryIndex((current) => current + 1);
    void loadDetail(target);
  }

  function moveDetailHistory(direction: -1 | 1) {
    const nextIndex = detailHistoryIndex + direction;
    const target = detailHistory[nextIndex];
    if (!target) return;
    setDetailHistoryIndex(nextIndex);
    void loadDetail(target);
  }

  function closeDetail() {
    setDetail(null);
    setDetailHistory([]);
    setDetailHistoryIndex(-1);
  }

  useEffect(() => {
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") closeDetail();
    }
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, []);

  async function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSearched(true);
    setLoading(true);
    setError("");

    try {
      const params = new URLSearchParams({ limit: "100", offset: "0" });
      if (query.trim()) params.set("search", query.trim());
      params.set("related", String(includeRelated));
      const response = await fetch(`${endpoint}?${params.toString()}`, {
        headers: { Accept: "application/json" }
      });
      const body: unknown = await response.json();
      if (!response.ok) {
        throw new Error(`API returned ${response.status} ${response.statusText}`);
      }

      const records =
        typeof body === "object" &&
        body !== null &&
        Array.isArray((body as { results?: unknown }).results)
          ? ((body as { results: ApiRecord[] }).results)
          : Array.isArray(body)
            ? body.filter((item): item is ApiRecord => typeof item === "object" && item !== null)
            : [];

      setResults(records);
      setTotal(
        typeof body === "object" &&
          body !== null &&
          typeof (body as { count?: unknown }).count === "number"
          ? (body as { count: number }).count
          : records.length
      );
    } catch (requestError) {
      setResults([]);
      setTotal(null);
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to reach the API server."
      );
    } finally {
      setLoading(false);
    }
  }

  function changeResource(value: Resource) {
    setResource(value);
    setResults([]);
    setTotal(null);
    setSearched(false);
    setError("");
  }

  return (
    <main className="explore-shell">
      <header className="topbar">
        <Link className="brand" href="/">
          <span className="brand-mark">C</span>
          <span>CRKL</span>
        </Link>
        <nav className="topnav">
          <Link href="/">API console</Link>
          <span className="api-badge">SPACE EXPLORATION</span>
        </nav>
      </header>

      <section className="search-hero">
        <p className="eyebrow">CRKL SPACE INDEX</p>
        <h1>Find what&apos;s out there.</h1>
        <p>Search missions, agencies, spacecraft, and launches from the CRKL catalog.</p>
        <form className="search-form" onSubmit={search}>
          <span className="search-icon">⌕</span>
          <input
            aria-label="Search the space catalog"
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search the space catalog..."
            type="search"
            value={query}
          />
          <button disabled={loading} type="submit">
            {loading ? "Searching..." : "Search"}
          </button>
        </form>
        <div className="search-filters" role="group" aria-label="Search resource">
          <span>Search in</span>
          {resources.map((item) => (
            <button
              className={resource === item.value ? "active" : ""}
              key={item.value}
              onClick={() => changeResource(item.value)}
              type="button"
            >
              {item.label}
            </button>
          ))}
        </div>
        <label className="related-search-toggle">
          <input
            checked={includeRelated}
            onChange={(event) => setIncludeRelated(event.target.checked)}
            type="checkbox"
          />
          <span>Include related records</span>
          <small>Search linked missions, agencies, spacecraft, and launches</small>
        </label>
      </section>

      <section className="results-section">
        {error && <div className="error-message">{error}</div>}
        {!searched && !error && (
          <div className="empty-search">
            <span>✦</span>
            <h2>Start exploring</h2>
            <p>Enter a keyword to search the {resource} catalog.</p>
          </div>
        )}
        {searched && !loading && !error && (
          <>
            <div className="results-heading">
              <div>
                <p className="eyebrow">SEARCH RESULTS</p>
                <h2>{results.length} results for {query.trim() ? `"${query.trim()}"` : "all records"}</h2>
              </div>
              <span>{total ?? results.length} records in catalog</span>
            </div>
            {results.length === 0 ? (
              <div className="no-results">No records matched your search.</div>
            ) : (
              <div className="result-grid">
                {results.map((record, index) => {
                  const identifier = [
                    record.mission_id,
                    record.agency_id,
                    record.spacecraft_id,
                    record.launch_id
                  ].find(
                    (value): value is string | number =>
                      typeof value === "string" || typeof value === "number"
                  );
                  const details = Object.entries(record)
                    .filter(([key, value]) => key !== "name" && key !== "title" && typeof value !== "object")
                    .slice(0, 3);
                  return (
                    <button
                      className="result-card"
                      key={`${String(identifier || "record")}-${index}`}
                      onClick={() => identifier && openDetail(resource, identifier)}
                      type="button"
                    >
                      <div className="result-card-top">
                        <span className="result-type">{resource.slice(0, -1)}</span>
                        {identifier && <span className="result-id">#{String(identifier)}</span>}
                      </div>
                      <h3>{titleFor(record)}</h3>
                      <div className="result-details">
                        {details.map(([key, value]) => (
                          <span key={key}><b>{key.replaceAll("_", " ")}</b>{displayValue(value)}</span>
                        ))}
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </>
        )}
      </section>
      <footer>CRKL · Space data for curious minds</footer>
      {detail && (
        <div
          aria-label="Record details"
          className="detail-backdrop"
          onClick={closeDetail}
          role="presentation"
        >
          <section
            aria-label={`${resourceLabel(detail.resource)} details`}
            aria-modal="true"
            className="detail-panel"
            onClick={(event) => event.stopPropagation()}
            role="dialog"
          >
            <div className="detail-header">
              <div>
                <p className="eyebrow">{resourceLabel(detail.resource)} detail</p>
                <h2>{detail.record ? titleFor(detail.record) : "Loading record..."}</h2>
              </div>
              <div className="detail-actions">
                <button
                  aria-label="Previous detail"
                  className="detail-nav"
                  disabled={detailHistoryIndex <= 0}
                  onClick={() => moveDetailHistory(-1)}
                  type="button"
                >
                  ← Back
                </button>
                <button
                  aria-label="Next detail"
                  className="detail-nav"
                  disabled={detailHistoryIndex >= detailHistory.length - 1}
                  onClick={() => moveDetailHistory(1)}
                  type="button"
                >
                  Forward →
                </button>
                <button
                  aria-label="Close details"
                  className="detail-close"
                  onClick={closeDetail}
                  type="button"
                >
                  ×
                </button>
              </div>
            </div>
            {detail.loading && <div className="detail-loading">Loading record...</div>}
            {detail.error && <div className="error-message">{detail.error}</div>}
            {detail.record && !detail.loading && (
              <>
                <div className="detail-fields">
                  {Object.entries(detail.record)
                    .filter(([, value]) => !Array.isArray(value) && typeof value !== "object")
                    .map(([key, value]) => (
                      <div key={key}>
                        <b>{key.replaceAll("_", " ")}</b>
                        <span>{displayValue(value)}</span>
                      </div>
                    ))}
                </div>
                {Object.entries(detail.record)
                  .filter(([, value]) => Array.isArray(value))
                  .map(([field, value]) => (
                    <section className="related-section" key={field}>
                      <h3>{field.replaceAll("_", " ")}</h3>
                      <div className="related-grid">
                        {(value as unknown[]).map((item, index) => {
                          if (typeof item !== "object" || item === null) return null;
                          const relatedRecord = item as ApiRecord;
                          const relatedResource = relatedResourceByField[field];
                          const relatedId = relatedResource
                            ? relatedRecord[resourceIdKeys[relatedResource]]
                            : undefined;
                          return (
                            <button
                              className="related-card"
                              disabled={!relatedResource || (typeof relatedId !== "string" && typeof relatedId !== "number")}
                              key={`${field}-${String(relatedId || index)}`}
                              onClick={() =>
                                relatedResource &&
                                (typeof relatedId === "string" || typeof relatedId === "number") &&
                                openDetail(relatedResource, relatedId)
                              }
                              type="button"
                            >
                              <span>{titleFor(relatedRecord)}</span>
                              {relatedId !== undefined && <small>#{String(relatedId)}</small>}
                            </button>
                          );
                        })}
                      </div>
                    </section>
                  ))}
              </>
            )}
          </section>
        </div>
      )}
    </main>
  );
}
