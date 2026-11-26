import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CopyPromptButton } from "./copy-prompt-button";

const record = { name: "Dragon XL Cargo", source_provider: "ll2", source_id: "104", spacecraft_type: "Cargo" };

function stubClipboard(writeText: (value: string) => Promise<void>) {
  vi.stubGlobal("isSecureContext", true);
  Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText } });
}

describe("CopyPromptButton", () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("copies the prompt and confirms it", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    stubClipboard(writeText);

    render(<CopyPromptButton record={record} resource="spacecraft" />);
    fireEvent.click(screen.getByRole("button", { name: "Copy AI prompt" }));

    expect(await screen.findByRole("button", { name: "Copied" })).toHaveTextContent("Copied");
    const prompt = writeText.mock.calls[0][0] as string;
    expect(prompt).toContain("Name: Dragon XL Cargo");
    expect(prompt).toContain("https://ll.thespacedevs.com/2.3.0/spacecraft/104/");
  });

  it("says so when copying fails", async () => {
    stubClipboard(vi.fn().mockRejectedValue(new Error("denied")));

    render(<CopyPromptButton record={record} resource="spacecraft" />);
    fireEvent.click(screen.getByRole("button", { name: "Copy AI prompt" }));

    expect(await screen.findByRole("button", { name: "Copy failed" })).toBeInTheDocument();
  });
});
