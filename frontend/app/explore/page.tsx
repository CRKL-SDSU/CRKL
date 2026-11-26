"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { BrandLogo } from "../brand";
import { aboutUrl } from "../site";
import { CopyPromptButton } from "./copy-prompt-button";
import { cardFields, detailFields, sourceLine, timestampLine } from "./fields";
import { RecordImage } from "./record-image";

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
type TagRecord = { tag_id: number; name: string };

const resources: { value: Resource; label: string }[] = [
  { value: "missions", label: "Missions" },
  { value: "agencies", label: "Agencies" },
  { value: "spacecraft", label: "Spacecraft" },
  { value: "launches", label: "Launches" }
];

const apiBaseUrl = "/api/v1";

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

const singularLabels: Record<Resource, string> = {
  missions: "mission",
  agencies: "agency",
  spacecraft: "spacecraft",
  launches: "launch"
};

function resourceLabel(resource: Resource) {
  return singularLabels[resource];
}

function tagsOf(record: ApiRecord): TagRecord[] {
  return Array.isArray(record.tags)
    ? record.tags.filter(
        (tag): tag is TagRecord =>
          typeof tag === "object" && tag !== null && "tag_id" in tag && "name" in tag
      )
    : [];
}

// tag:moon, or tag:"ocean worlds" for a multi-word tag
function tagQuery(name: string) {
  return name.includes(" ") ? `tag:"${name}"` : `tag:${name}`;
}

async function errorMessage(response: Response) {
  try {
    const body: unknown = await response.json();
    if (typeof body === "object" && body !== null) {
      const detail = (body as { detail?: unknown }).detail;
      if (typeof detail === "string") return detail;
    }
  } catch {
    // fall through to the status text
  }
  return `API returned ${response.status} ${response.statusText}`;
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
  const [searchedQuery, setSearchedQuery] = useState("");
  const [tagInput, setTagInput] = useState("");
  const [tagSuggestions, setTagSuggestions] = useState<TagRecord[]>([]);
  const [tagError, setTagError] = useState("");
  const [tagSaving, setTagSaving] = useState(false);

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
    setTagInput("");
    setTagError("");
  }

  useEffect(() => {
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") closeDetail();
    }
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, []);

  async function runSearch(searchQuery: string, searchResource: Resource) {
    setSearched(true);
    setLoading(true);
    setError("");
    setSearchedQuery(searchQuery.trim());

    try {
      const params = new URLSearchParams({ limit: "100", offset: "0" });
      if (searchQuery.trim()) params.set("search", searchQuery.trim());
      params.set("related", String(includeRelated));
      const response = await fetch(
        `${apiBaseUrl.replace(/\/$/, "")}/${searchResource}?${params.toString()}`,
        { headers: { Accept: "application/json" } }
      );
      if (!response.ok) {
        throw new Error(await errorMessage(response));
      }
      const body: unknown = await response.json();

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

  function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void runSearch(query, resource);
  }

  // clicking a tag searches missions with that tag
  function searchTag(name: string) {
    const nextQuery = tagQuery(name);
    closeDetail();
    setQuery(nextQuery);
    setResource("missions");
    void runSearch(nextQuery, "missions");
  }

  function updateDetailTags(tags: TagRecord[]) {
    const missionId = detail?.record?.mission_id;
    setDetail((current) =>
      current?.record ? { ...current, record: { ...current.record, tags } } : current
    );
    setResults((current) =>
      current.map((record) =>
        missionId !== undefined && record.mission_id === missionId ? { ...record, tags } : record
      )
    );
  }

  async function addTag(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!detail?.record || !tagInput.trim()) return;
    setTagSaving(true);
    setTagError("");
    try {
      const response = await fetch(
        `${apiBaseUrl}/missions/${encodeURIComponent(String(detail.id))}/tags`,
        {
          method: "POST",
          headers: { Accept: "application/json", "Content-Type": "application/json" },
          body: JSON.stringify({ name: tagInput })
        }
      );
      if (!response.ok) throw new Error(await errorMessage(response));
      const body = (await response.json()) as { tags: TagRecord[] };
      updateDetailTags(body.tags);
      setTagInput("");
    } catch (requestError) {
      setTagError(requestError instanceof Error ? requestError.message : "Unable to add the tag.");
    } finally {
      setTagSaving(false);
    }
  }

  async function removeTag(tag: TagRecord) {
    if (!detail?.record) return;
    setTagError("");
    try {
      const response = await fetch(
        `${apiBaseUrl}/missions/${encodeURIComponent(String(detail.id))}/tags/${tag.tag_id}`,
        { method: "DELETE", headers: { Accept: "application/json" } }
      );
      if (!response.ok) throw new Error(await errorMessage(response));
      const body = (await response.json()) as { tags: TagRecord[] };
      updateDetailTags(body.tags);
    } catch (requestError) {
      setTagError(
        requestError instanceof Error ? requestError.message : "Unable to remove the tag."
      );
    }
  }

  // suggest existing tags while typing, so people reuse them instead of creating variants
  useEffect(() => {
    if (!tagInput.trim()) {
      setTagSuggestions([]);
      return;
    }
    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      try {
        const params = new URLSearchParams({ search: tagInput.trim(), limit: "8" });
        const response = await fetch(`${apiBaseUrl}/tags?${params.toString()}`, {
          headers: { Accept: "application/json" },
          signal: controller.signal
        });
        if (!response.ok) return;
        const body = (await response.json()) as { results?: TagRecord[] };
        setTagSuggestions(Array.isArray(body.results) ? body.results : []);
      } catch {
        // suggestions are optional
      }
    }, 200);
    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [tagInput]);

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
          <BrandLogo />
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
            placeholder="Search the space catalog... e.g. tag:moon OR mars"
            type="search"
            value={query}
          />
          <button disabled={loading} type="submit">
            {loading ? "Searching..." : "Search"}
          </button>
        </form>
        <p className="search-syntax">
          <code>tag:moon</code> tag · <code>mars OR venus</code> either · <code>-radar</code> exclude ·{" "}
          <code>&quot;south pole&quot;</code> phrase · <code>( )</code> group
        </p>
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
                <h2>{results.length} results for {searchedQuery ? `“${searchedQuery}”` : "all records"}</h2>
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
                  const fields = cardFields(record, resource);
                  const description = typeof record.description === "string" ? record.description.trim() : "";
                  const tags = tagsOf(record);
                  return (
                    <article className="result-card" key={`${String(identifier || "record")}-${index}`}>
                      <button
                        className="result-card-main"
                        onClick={() => identifier && openDetail(resource, identifier)}
                        type="button"
                      >
                        <RecordImage record={record} resource={resource} variant="card" />
                        <div className="result-card-top">
                          <span className="result-type">{resourceLabel(resource)}</span>
                        </div>
                        <h3>{titleFor(record)}</h3>
                        {description && <p className="result-description">{description}</p>}
                        <div className="result-details">
                          {fields.map((field) => (
                            <span key={field.key}><b>{field.label}</b>{field.value}</span>
                          ))}
                        </div>
                        {sourceLine(record) && <small className="result-source">{sourceLine(record)}</small>}
                      </button>
                      {tags.length > 0 && (
                        <div className="tag-list" aria-label="Tags">
                          {tags.slice(0, 4).map((tag) => (
                            <button
                              className="tag-chip"
                              key={tag.tag_id}
                              onClick={() => searchTag(tag.name)}
                              title={`Search ${tagQuery(tag.name)}`}
                              type="button"
                            >
                              #{tag.name}
                            </button>
                          ))}
                          {tags.length > 4 && <span className="tag-more">+{tags.length - 4}</span>}
                        </div>
                      )}
                    </article>
                  );
                })}
              </div>
            )}
          </>
        )}
      </section>
      <footer>
        CRKL-Space · Space data for curious minds · <a href={aboutUrl}>About Us</a>
      </footer>
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
                <RecordImage record={detail.record} resource={detail.resource} variant="detail" />
                <div className="detail-fields">
                  {detailFields(detail.record, detail.resource).map((field) => (
                    <div className={field.key === "description" ? "detail-field-wide" : undefined} key={field.key}>
                      <b>{field.label}</b>
                      <span>{field.value}</span>
                    </div>
                  ))}
                </div>
                {detail.resource === "missions" && (
                  <section className="related-section tag-editor" aria-label="Mission tags">
                    <h3>tags</h3>
                    <div className="tag-list">
                      {tagsOf(detail.record).length === 0 && (
                        <span className="tag-empty">No tags yet.</span>
                      )}
                      {tagsOf(detail.record).map((tag) => (
                        <span className="tag-chip-group" key={tag.tag_id}>
                          <button
                            className="tag-chip"
                            onClick={() => searchTag(tag.name)}
                            title={`Search ${tagQuery(tag.name)}`}
                            type="button"
                          >
                            #{tag.name}
                          </button>
                          <button
                            aria-label={`Remove tag ${tag.name}`}
                            className="tag-remove"
                            onClick={() => void removeTag(tag)}
                            type="button"
                          >
                            ×
                          </button>
                        </span>
                      ))}
                    </div>
                    <form className="tag-form" onSubmit={addTag}>
                      <input
                        aria-label="New tag"
                        list="tag-suggestions"
                        maxLength={30}
                        onChange={(event) => setTagInput(event.target.value)}
                        placeholder="Add a tag (letters, digits, spaces, hyphens)"
                        value={tagInput}
                      />
                      <datalist id="tag-suggestions">
                        {tagSuggestions.map((tag) => (
                          <option key={tag.tag_id} value={tag.name} />
                        ))}
                      </datalist>
                      <button disabled={tagSaving || !tagInput.trim()} type="submit">
                        {tagSaving ? "Adding..." : "Add tag"}
                      </button>
                    </form>
                    {tagError && <div className="error-message">{tagError}</div>}
                  </section>
                )}
                {Object.entries(detail.record)
                  .filter(([field, value]) => field !== "tags" && Array.isArray(value))
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
                              {typeof relatedRecord.role === "string" && relatedRecord.role && (
                                <small>{relatedRecord.role}</small>
                              )}
                            </button>
                          );
                        })}
                      </div>
                    </section>
                  ))}
                <div className="detail-meta">
                  <div className="detail-meta-lines">
                    {sourceLine(detail.record) && <span>{sourceLine(detail.record)}</span>}
                    {timestampLine(detail.record) && <span>{timestampLine(detail.record)}</span>}
                  </div>
                  <CopyPromptButton record={detail.record} resource={detail.resource} />
                </div>
              </>
            )}
          </section>
        </div>
      )}
    </main>
  );
}
