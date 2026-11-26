import { describe, expect, it } from "vitest";

import { buildPrompt, ll2Url } from "./prompt";

const launch = {
  launch_id: 2,
  source_provider: "ll2",
  source_id: "e3df2ecd-c239-472f-95e4-2b89b4f75800",
  name: "Ariane 6 Heavy Maiden",
  net: "2027-05-20T18:15:00",
  status: "Success",
  window_start: null,
  window_end: null,
  missions: [{ name: "Mercury Mapper" }, { name: "Venus Profiler" }]
};

describe("ll2Url", () => {
  it("links LL2 records to their API page", () => {
    expect(ll2Url(launch, "launches")).toBe(
      "https://ll.thespacedevs.com/2.3.0/launches/e3df2ecd-c239-472f-95e4-2b89b4f75800/"
    );
    expect(ll2Url({ source_provider: "ll2", source_id: "44" }, "agencies")).toBe(
      "https://ll.thespacedevs.com/2.3.0/agencies/44/"
    );
  });

  it("gives no link for missions, other sources, or odd IDs", () => {
    expect(ll2Url({ source_provider: "ll2", source_id: "12" }, "missions")).toBeNull();
    expect(ll2Url({ source_provider: "sample", source_id: "ag-101" }, "agencies")).toBeNull();
    expect(ll2Url({ source_provider: "ll2", source_id: "../x" }, "agencies")).toBeNull();
  });
});

describe("buildPrompt", () => {
  it("includes the record's details, related names, source, and primary data link", () => {
    const prompt = buildPrompt(launch, "launches");
    expect(prompt).toContain("I'm looking at this launch in CRKL-Space");
    expect(prompt).toContain("Name: Ariane 6 Heavy Maiden");
    expect(prompt).toContain("Launch date (NET): 2027-05-20 18:15 UTC");
    expect(prompt).not.toContain("Window opens");
    expect(prompt).toContain("Related missions: Mercury Mapper, Venus Profiler");
    expect(prompt).toContain("Source: Launch Library 2 by The Space Devs, ID e3df2ecd");
    expect(prompt).toContain("- https://ll.thespacedevs.com/2.3.0/launches/e3df2ecd-c239-472f-95e4-2b89b4f75800/");
    expect(prompt).toContain("starting from the primary data above");
    expect(prompt).toContain("the vehicle, payload, launch site, and outcome");
  });

  it("links a mission to the launches that carried it", () => {
    const prompt = buildPrompt(
      {
        name: "Lunar Scout",
        source_provider: "ll2",
        source_id: "12",
        launches: [{ name: "Ariane 6", source_provider: "ll2", source_id: "e3df2ecd" }]
      },
      "missions"
    );
    expect(prompt).toContain("- https://ll.thespacedevs.com/2.3.0/launches/e3df2ecd/");
  });

  it("leaves out the primary data section when there is no LL2 link", () => {
    const prompt = buildPrompt({ name: "Test", source_provider: "sample", source_id: "x" }, "agencies");
    expect(prompt).not.toContain("Primary data");
    expect(prompt).toContain("Source: sample, ID x");
  });
});
