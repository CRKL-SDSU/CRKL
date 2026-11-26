import { cleanup, fireEvent, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { RecordImage, imageUrlOf } from "./record-image";

describe("imageUrlOf", () => {
  it("accepts only http and https URLs", () => {
    expect(imageUrlOf({ image_url: "https://example.com/logo.png" })).toBe("https://example.com/logo.png");
    expect(imageUrlOf({ image_url: "javascript:alert(1)" })).toBeNull();
    expect(imageUrlOf({ image_url: "data:image/png;base64,AAAA" })).toBeNull();
    expect(imageUrlOf({ image_url: "/relative.png" })).toBeNull();
    expect(imageUrlOf({ image_url: null })).toBeNull();
  });
});

describe("RecordImage", () => {
  afterEach(cleanup);

  it("shows the image, then an icon if the image fails to load", () => {
    const { container } = render(
      <RecordImage record={{ image_url: "https://example.com/a.png" }} resource="agencies" variant="card" />
    );
    const image = container.querySelector("img");
    expect(image).toHaveAttribute("src", "https://example.com/a.png");
    expect(image).toHaveAttribute("loading", "lazy");

    fireEvent.error(image!);
    expect(container.querySelector("img")).toBeNull();
    expect(container.querySelector(".record-image-empty svg")).not.toBeNull();
  });

  it("leaves the image out of the detail panel when there is none", () => {
    const { container } = render(<RecordImage record={{}} resource="missions" variant="detail" />);
    expect(container).toBeEmptyDOMElement();
  });
});
