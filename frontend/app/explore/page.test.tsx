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

  it("searches by tag when a tag on a result card is clicked", async () => {
    const fetchMock = vi
      .spyOn(global, "fetch")
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            count: 1,
            results: [
              { mission_id: 1, name: "Lunar Scout", tags: [{ tag_id: 4, name: "ocean worlds" }] }
            ]
          }),
          { status: 200 }
        )
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ count: 0, results: [] }), { status: 200 })
      );

    render(<ExplorePage />);
    fireEvent.click(screen.getByRole("button", { name: "Search" }));
    fireEvent.click(await screen.findByRole("button", { name: "#ocean worlds" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    const url = new URL(String(fetchMock.mock.calls[1][0]), "http://localhost");
    expect(url.pathname).toBe("/api/v1/missions");
    expect(url.searchParams.get("search")).toBe('tag:"ocean worlds"');
    expect(screen.getByRole("searchbox")).toHaveValue('tag:"ocean worlds"');
  });

  it("shows a card's thumbnail without listing the image fields as details", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          count: 1,
          results: [
            {
              launch_id: 7,
              name: "Night Owls",
              image_url: "https://example.com/full.jpg",
              thumbnail_url: "https://example.com/small.jpg",
              image_credit: "Rocket Lab",
              image_license: "Unknown",
              source_provider: "ll2",
              source_id: "e3df2ecd"
            }
          ]
        }),
        { status: 200 }
      )
    );

    const { container } = render(<ExplorePage />);
    fireEvent.click(screen.getByRole("button", { name: "Search" }));
    await screen.findByText("Night Owls");

    expect(container.querySelector(".result-card img")).toHaveAttribute("src", "https://example.com/small.jpg");
    const card = container.querySelector(".result-card")!;
    expect(card.textContent).not.toContain("example.com");
    expect(card.textContent).not.toContain("Rocket Lab");
    expect(card.querySelector(".result-source")).toHaveTextContent("Source: Launch Library 2 · e3df2ecd");
  });

  it("shows the API's message for a malformed query", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "A parenthesis is missing a closing ')'." }), {
        status: 400
      })
    );

    render(<ExplorePage />);
    fireEvent.change(screen.getByRole("searchbox"), { target: { value: "(mars" } });
    fireEvent.click(screen.getByRole("button", { name: "Search" }));

    expect(await screen.findByText("A parenthesis is missing a closing ')'.")).toBeInTheDocument();
  });

  it("adds a tag from the mission detail view", async () => {
    const fetchMock = vi
      .spyOn(global, "fetch")
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ count: 1, results: [{ mission_id: 1, name: "Lunar Scout", tags: [] }] }),
          { status: 200 }
        )
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ mission_id: 1, name: "Lunar Scout", tags: [] }), {
          status: 200
        })
      )
      .mockResolvedValue(
        new Response(JSON.stringify({ tags: [{ tag_id: 9, name: "moon" }], results: [] }), {
          status: 201
        })
      );

    render(<ExplorePage />);
    fireEvent.click(screen.getByRole("button", { name: "Search" }));
    fireEvent.click(await screen.findByRole("button", { name: /Lunar Scout/i }));
    await waitFor(() => expect(screen.getByRole("dialog")).toHaveTextContent("No tags yet."));

    fireEvent.change(screen.getByRole("combobox", { name: "New tag" }), {
      target: { value: "Moon" }
    });
    fireEvent.click(screen.getByRole("button", { name: "Add tag" }));

    await waitFor(() =>
      expect(screen.getByRole("dialog")).toHaveTextContent("#moon")
    );
    const post = fetchMock.mock.calls.find(([, init]) => init?.method === "POST");
    expect(String(post?.[0])).toBe("/api/v1/missions/1/tags");
    expect(post?.[1]?.body).toBe(JSON.stringify({ name: "Moon" }));
  });

  it("shows a dash for a mission without a status", async () => {
    vi.spyOn(global, "fetch")
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            count: 1,
            results: [{ mission_id: 1, name: "Real Mission", status: null }]
          }),
          { status: 200 }
        )
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ mission_id: 1, name: "Real Mission", status: null, agencies: [] }),
          { status: 200 }
        )
      );

    render(<ExplorePage />);
    fireEvent.click(screen.getByRole("button", { name: "Missions" }));
    fireEvent.click(screen.getByRole("button", { name: "Search" }));
    fireEvent.click(await screen.findByRole("button", { name: /Real Mission/i }));

    const dialog = await screen.findByRole("dialog");
    await waitFor(() => expect(dialog).toHaveTextContent("Status—"));
    expect(dialog).not.toHaveTextContent("mission id");
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
