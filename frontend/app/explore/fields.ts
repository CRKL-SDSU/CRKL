// Which fields a record shows, with readable labels and values.
// Each resource shows a fixed list of fields, so every record has the same layout;
// internal columns (keys, import bookkeeping, image columns) are never listed.

export type Resource = "missions" | "agencies" | "spacecraft" | "launches";
type ApiRecord = Record<string, unknown>;
export type Field = { key: string; label: string; value: string };

const LABELS: Record<string, string> = {
  abbrev: "Abbreviation",
  country_code: "Country",
  description: "Description",
  launch_service_provider: "Launch provider",
  net: "Launch date (NET)",
  role: "Role",
  spacecraft_type: "Type",
  status: "Status",
  target_body: "Target",
  window_end: "Window closes",
  window_start: "Window opens"
};

// the few fields worth a glance on a result card; the rest are in the detail panel
const CARD_KEYS: Record<Resource, string[]> = {
  missions: ["target_body", "status"],
  agencies: ["abbrev", "country_code"],
  spacecraft: ["spacecraft_type"],
  launches: ["net", "status", "launch_service_provider"]
};

// the fields in the detail panel, in order; empty ones still show as "—"
const DETAIL_KEYS: Record<Resource, string[]> = {
  missions: ["description", "target_body", "status"],
  agencies: ["abbrev", "country_code"],
  spacecraft: ["spacecraft_type"],
  launches: ["net", "status", "launch_service_provider", "window_start", "window_end"]
};

export const EMPTY_VALUE = "—";

// display names for source_provider; "dummy" marks the fictional sample data in specs/db/dummy_data.sql
export const PROVIDERS: Record<string, string> = { ll2: "Launch Library 2", dummy: "Dummy" };

const DATE_TIME = /^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})(?::\d{2}(?:\.\d+)?)?(Z|[+-]00:?00)?$/;

export function labelFor(key: string) {
  return LABELS[key] ?? key.replaceAll("_", " ");
}

// "2026-09-12T04:30:00" -> "2026-09-12 04:30 UTC" (Launch Library 2 times are in UTC)
export function formatValue(value: unknown): string | null {
  if (value === null || value === undefined) return null;
  if (typeof value === "string") {
    const text = value.trim();
    if (!text) return null;
    const match = DATE_TIME.exec(text);
    return match ? `${match[1]} ${match[2]} UTC` : text;
  }
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return null;
}

function toField(record: ApiRecord, key: string): Field {
  return { key, label: labelFor(key), value: formatValue(record[key]) ?? EMPTY_VALUE };
}

export function cardFields(record: ApiRecord, resource: Resource): Field[] {
  return CARD_KEYS[resource].map((key) => toField(record, key));
}

export function detailFields(record: ApiRecord, resource: Resource): Field[] {
  return DETAIL_KEYS[resource].map((key) => toField(record, key));
}

// "Source: Launch Library 2 · 7a1b..." for the bottom of the detail panel
export function sourceLine(record: ApiRecord): string | null {
  const provider = formatValue(record.source_provider);
  const id = formatValue(record.source_id);
  if (!provider && !id) return null;
  const name = provider ? (PROVIDERS[provider] ?? provider) : null;
  return `Source: ${[name, id].filter(Boolean).join(" · ")}`;
}

// "Added 2026-11-26 18:29 UTC · Updated 2026-11-27 09:00 UTC", shown small under the source line
export function timestampLine(record: ApiRecord): string | null {
  const parts = [
    formatValue(record.created_at) && `Added ${formatValue(record.created_at)}`,
    formatValue(record.updated_at) && `Updated ${formatValue(record.updated_at)}`
  ].filter(Boolean);
  return parts.length > 0 ? parts.join(" · ") : null;
}
