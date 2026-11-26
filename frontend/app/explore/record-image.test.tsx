import { cleanup, fireEvent, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { RecordImage, imageCandidates, imageCreditOf, imageUrlOf } from "./record-image";

describe("imageUrlOf", () => {
  it("accepts only http and https URLs", () => {
    expect(imageUrlOf({ image_url: "https://example.com/logo.png" })).toBe("https://example.com/logo.png");
    expect(imageUrlOf({ image_url: "javascript:alert(1)" })).toBeNull();
    expect(imageUrlOf({ image_url: "data:image/png;base64,AAAA" })).toBeNull();
    expect(imageUrlOf({ image_url: "/relative.png" })).toBeNull();
    expect(imageUrlOf({ image_url: null })).toBeNull();
  });
});

describe("imageCandidates", () => {
  const record = { image_url: "https://example.com/full.jpg", thumbnail_url: "https://example.com/small.jpg" };

  it("prefers the thumbnail on cards and the full image in details", () => {
    expect(imageCandidates(record, "card")).toEqual(["https://example.com/small.jpg", "https://example.com/full.jpg"]);
    expect(imageCandidates(record, "detail")).toEqual(["https://example.com/full.jpg", "https://example.com/small.jpg"]);
  });

  it("uses whichever one exists", () => {
    expect(imageCandidates({ image_url: "https://example.com/full.jpg" }, "card")).toEqual(["https://example.com/full.jpg"]);
  });
});

describe("imageCreditOf", () => {
  it("joins the parts that exist", () => {
    expect(imageCreditOf({ image_credit: "CCTV", image_license: "Unknown" })).toBe("Image: CCTV · License: Unknown");
    expect(imageCreditOf({ image_credit: " ", image_license: "Unknown" })).toBe("License: Unknown");
    expect(imageCreditOf({})).toBeNull();
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

  it("falls back to the full image when the thumbnail fails", () => {
    const { container } = render(
      <RecordImage
        record={{ image_url: "https://example.com/full.jpg", thumbnail_url: "https://example.com/small.jpg" }}
        resource="launches"
        variant="card"
      />
    );
    fireEvent.error(container.querySelector("img")!);
    expect(container.querySelector("img")).toHaveAttribute("src", "https://example.com/full.jpg");
  });

  it("credits the image in the detail panel", () => {
    const { getByText } = render(
      <RecordImage
        record={{ image_url: "https://example.com/full.jpg", image_credit: "SAST/CASC", image_license: "Unknown" }}
        resource="launches"
        variant="detail"
      />
    );
    expect(getByText("Image: SAST/CASC · License: Unknown")).toBeInTheDocument();
  });

  it("leaves the image out of the detail panel when there is none", () => {
    const { container } = render(<RecordImage record={{}} resource="missions" variant="detail" />);
    expect(container).toBeEmptyDOMElement();
  });
});
