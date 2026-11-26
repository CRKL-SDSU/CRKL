import { describe, expect, it } from "vitest";

import { cardFields, detailFields, formatValue, sourceLine, timestampLine } from "./fields";

const launch = {
  launch_id: 1,
  source_provider: "ll2",
  source_id: "a1b2",
  name: "Artemis IV",
  net: "2028-09-12T04:30:00",
  status: "Scheduled",
  image_url: "https://example.com/a.jpg",
  thumbnail_url: null,
  window_start: "2028-09-12T04:00:00",
  window_end: null,
  created_at: "2026-11-26T18:29:13",
  updated_at: "2026-11-27T09:00:00",
  missions: [{ mission_id: 3 }]
};

describe("formatValue", () => {
  it("formats date-times as UTC and drops empty values", () => {
    expect(formatValue("2028-09-12T04:30:00")).toBe("2028-09-12 04:30 UTC");
    expect(formatValue("2028-09-12T04:30:00Z")).toBe("2028-09-12 04:30 UTC");
    expect(formatValue("Mars")).toBe("Mars");
    expect(formatValue("  ")).toBeNull();
    expect(formatValue(null)).toBeNull();
    expect(formatValue({ a: 1 })).toBeNull();
  });
});

describe("cardFields", () => {
  it("shows the resource's fixed fields, with a dash when empty", () => {
    expect(cardFields(launch, "launches")).toEqual([
      { key: "net", label: "Launch date (NET)", value: "2028-09-12 04:30 UTC" },
      { key: "status", label: "Status", value: "Scheduled" }
    ]);
    expect(cardFields({ status: null, target_body: "Moon" }, "missions")).toEqual([
      { key: "target_body", label: "Target", value: "Moon" },
      { key: "status", label: "Status", value: "—" }
    ]);
  });
});

describe("detailFields", () => {
  it("lists the same fields for every record, never internal columns", () => {
    expect(detailFields(launch, "launches")).toEqual([
      { key: "net", label: "Launch date (NET)", value: "2028-09-12 04:30 UTC" },
      { key: "status", label: "Status", value: "Scheduled" },
      { key: "window_start", label: "Window opens", value: "2028-09-12 04:00 UTC" },
      { key: "window_end", label: "Window closes", value: "—" }
    ]);
    expect(detailFields({}, "agencies").map((field) => field.label)).toEqual(["Abbreviation", "Country"]);
  });
});

describe("metadata lines", () => {
  it("names the source and the record's timestamps", () => {
    expect(sourceLine(launch)).toBe("Source: Launch Library 2 · a1b2");
    expect(timestampLine(launch)).toBe("Added 2026-11-26 18:29 UTC · Updated 2026-11-27 09:00 UTC");
    expect(sourceLine({})).toBeNull();
    expect(timestampLine({ updated_at: "2026-11-27T09:00:00" })).toBe("Updated 2026-11-27 09:00 UTC");
  });
});
