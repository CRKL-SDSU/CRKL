"use client";

import Link from "next/link";
import { FormEvent, useMemo, useState } from "react";

type Resource = "missions" | "agencies" | "spacecraft" | "launches";
type ApiRecord = Record<string, unknown>;

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

export default function ExplorePage() {
  const [query, setQuery] = useState("");
  const [resource, setResource] = useState<Resource>("missions");
  const [results, setResults] = useState<ApiRecord[]>([]);
  const [total, setTotal] = useState<number | null>(null);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const endpoint = useMemo(
    () => `${apiBaseUrl.replace(/\/$/, "")}/${resource}`,
    [resource]
  );

  async function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSearched(true);
    setLoading(true);
    setError("");

    try {
      const params = new URLSearchParams({ limit: "100", offset: "0" });
      if (query.trim()) params.set("search", query.trim());
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
                    <article className="result-card" key={`${String(identifier || "record")}-${index}`}>
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
                    </article>
                  );
                })}
              </div>
            )}
          </>
        )}
      </section>
      <footer>CRKL · Space data for curious minds</footer>
    </main>
  );
}
