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

  it("opens a record overlay and navigates to a related record", async () => {
    const fetchMock = vi
      .spyOn(global, "fetch")
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            count: 1,
            results: [{ launch_id: 7, name: "Test Launch" }]
          }),
          { status: 200 }
        )
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            launch_id: 7,
            name: "Test Launch",
            missions: [{ mission_id: 3, name: "Test Mission" }]
          }),
          { status: 200 }
        )
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ mission_id: 3, name: "Test Mission", agencies: [] }),
          { status: 200 }
        )
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ launch_id: 7, name: "Test Launch", missions: [] }), {
          status: 200
        })
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ mission_id: 3, name: "Test Mission", agencies: [] }), {
          status: 200
        })
      );

    render(<ExplorePage />);
    fireEvent.click(screen.getByRole("button", { name: "Launches" }));
    fireEvent.click(screen.getByRole("button", { name: "Search" }));
    await waitFor(() => expect(screen.getByText("Test Launch")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /Test Launch/i }));
    await waitFor(() =>
      expect(screen.getByRole("dialog")).toHaveTextContent("Test Mission")
    );
    expect(fetchMock.mock.calls[1][0]).toContain("/launches/7");

    fireEvent.click(screen.getByRole("button", { name: /Test Mission/i }));
    await waitFor(() =>
      expect(screen.getByRole("dialog")).toHaveTextContent("mission detail")
    );
    expect(fetchMock.mock.calls[2][0]).toContain("/missions/3");

    fireEvent.click(screen.getByRole("button", { name: /Previous detail/i }));
    await waitFor(() =>
      expect(screen.getByRole("dialog")).toHaveTextContent("Test Launch")
    );
    expect(fetchMock.mock.calls[3][0]).toContain("/launches/7");
    expect(screen.getByRole("button", { name: /Next detail/i })).not.toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: /Next detail/i }));
    await waitFor(() =>
      expect(screen.getByRole("dialog")).toHaveTextContent("Test Mission")
    );
    expect(fetchMock.mock.calls[4][0]).toContain("/missions/3");
  });

  it("closes the detail overlay with Escape", async () => {
    vi.spyOn(global, "fetch")
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            count: 1,
            results: [{ launch_id: 7, name: "Test Launch" }]
          }),
          { status: 200 }
        )
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ launch_id: 7, name: "Test Launch", missions: [] }),
          { status: 200 }
        )
      );

    render(<ExplorePage />);
    fireEvent.click(screen.getByRole("button", { name: "Search" }));
    await waitFor(() => expect(screen.getByText("Test Launch")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: /Test Launch/i }));
    await waitFor(() => expect(screen.getByRole("dialog")).toBeInTheDocument());

    fireEvent.keyDown(window, { key: "Escape" });

    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument()
    );
  });

  it("links to the project website from the footer", () => {
    render(<ExplorePage />);

    expect(screen.getByRole("link", { name: "About Us" })).toHaveAttribute(
      "href",
      "https://crkl-sdsu.github.io/CRKL/"
    );
  });
});
