// Builds a ready-to-paste LLM prompt for a record, so visitors can dig into primary sources.

import { PROVIDERS, Resource, detailFields, EMPTY_VALUE } from "./fields";

type ApiRecord = Record<string, unknown>;

const LL2_API = "https://ll.thespacedevs.com/2.3.0";

// Launch Library 2 endpoints for each resource; LL2 has no missions endpoint,
// because its missions live inside launches
const LL2_PATHS: Partial<Record<Resource, string>> = {
  agencies: "agencies",
  spacecraft: "spacecraft",
  launches: "launches"
};

const SINGULAR: Record<Resource, string> = {
  missions: "mission",
  agencies: "space agency",
  spacecraft: "spacecraft",
  launches: "launch"
};

// what "more detail" means for each kind of record
const DETAIL_TOPICS: Record<Resource, string> = {
  missions: "its objectives, spacecraft, timeline, and results",
  agencies: "its history, main programs, and notable missions",
  spacecraft: "its design, operator, missions, and current status",
  launches: "the vehicle, payload, launch site, and outcome"
};

const RELATED_LISTS: { key: string; label: string }[] = [
  { key: "missions", label: "Related missions" },
  { key: "agencies", label: "Related agencies" },
  { key: "spacecraft", label: "Related spacecraft" },
  { key: "launches", label: "Related launches" }
];

const MAX_RELATED = 5;

function text(value: unknown) {
  return typeof value === "string" ? value.trim() : "";
}

// the record's own page in the Launch Library 2 API, only for records imported from LL2
export function ll2Url(record: ApiRecord, resource: Resource): string | null {
  const path = LL2_PATHS[resource];
  const id = text(record.source_id);
  if (!path || text(record.source_provider) !== "ll2" || !/^[\w-]+$/.test(id)) return null;
  return `${LL2_API}/${path}/${id}/`;
}

function relatedNames(record: ApiRecord, key: string): string[] {
  const items = record[key];
  if (!Array.isArray(items)) return [];
  return items
    .map((item) => (typeof item === "object" && item !== null ? text((item as ApiRecord).name) : ""))
    .filter(Boolean);
}

function primaryDataLinks(record: ApiRecord, resource: Resource): string[] {
  const own = ll2Url(record, resource);
  if (own) return [own];
  // a mission's primary data is in the launches that carried it
  if (resource === "missions" && Array.isArray(record.launches)) {
    return record.launches
      .map((launch) => (typeof launch === "object" && launch !== null ? ll2Url(launch as ApiRecord, "launches") : null))
      .filter((url): url is string => url !== null)
      .slice(0, MAX_RELATED);
  }
  return [];
}

export function buildPrompt(record: ApiRecord, resource: Resource): string {
  const kind = SINGULAR[resource];
  const lines = [`I'm looking at this ${kind} in CRKL-Space, a space data catalog.`, ""];

  lines.push(`Name: ${text(record.name) || EMPTY_VALUE}`);
  for (const field of detailFields(record, resource)) {
    if (field.value !== EMPTY_VALUE) lines.push(`${field.label}: ${field.value}`);
  }
  for (const { key, label } of RELATED_LISTS) {
    const names = relatedNames(record, key);
    if (names.length === 0) continue;
    const more = names.length > MAX_RELATED ? `, and ${names.length - MAX_RELATED} more` : "";
    lines.push(`${label}: ${names.slice(0, MAX_RELATED).join(", ")}${more}`);
  }

  const provider = text(record.source_provider);
  const sourceId = text(record.source_id);
  if (provider === "ll2") {
    lines.push(`Source: Launch Library 2 by The Space Devs${sourceId ? `, ID ${sourceId}` : ""}`);
  } else if (provider) {
    lines.push(`Source: ${PROVIDERS[provider] ?? provider}${sourceId ? `, ID ${sourceId}` : ""}`);
  }

  const links = primaryDataLinks(record, resource);
  if (links.length > 0) {
    lines.push("", "Primary data (Launch Library 2 API, JSON):", ...links.map((url) => `- ${url}`));
  }

  lines.push(
    "",
    "Please:",
    `1. Point me to primary sources for this ${kind} (official agency pages, press kits, mission documents)${
      links.length > 0 ? ", starting from the primary data above" : ""
    }.`,
    `2. Give me more detail about this ${kind}: ${DETAIL_TOPICS[resource]}.`,
    "3. Say clearly when you're unsure, and when facts may have changed since your training data."
  );
  return lines.join("\n");
}
