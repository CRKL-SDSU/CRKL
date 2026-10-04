import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import ExplorePage from "./page";

describe("ExplorePage", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("enables related search by default and sends the selected mode", async () => {
    const fetchMock = vi
      .spyOn(global, "fetch")
      .mockResolvedValue(
        new Response(JSON.stringify({ count: 0, results: [] }), { status: 200 })
      );

    render(<ExplorePage />);

    const toggle = screen.getByRole("checkbox", {
      name: /include related records/i
    });
    expect(toggle).toBeChecked();

    fireEvent.change(screen.getByRole("searchbox"), {
      target: { value: "Mars" }
    });
    fireEvent.click(screen.getByRole("button", { name: "Search" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    expect(fetchMock.mock.calls[0][0]).toContain("related=true");
  });

  it("supports exact-table-only searches when related search is disabled", async () => {
    const fetchMock = vi
      .spyOn(global, "fetch")
      .mockResolvedValue(
        new Response(JSON.stringify({ count: 0, results: [] }), { status: 200 })
      );

    render(<ExplorePage />);
    fireEvent.click(
      screen.getByRole("checkbox", { name: /include related records/i })
    );
    fireEvent.click(screen.getByRole("button", { name: "Search" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    expect(fetchMock.mock.calls[0][0]).toContain("related=false");
  });
});
