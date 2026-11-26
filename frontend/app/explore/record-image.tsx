"use client";

import { useState } from "react";

type Resource = "missions" | "agencies" | "spacecraft" | "launches";

// only show images from plain web URLs (never data:, javascript:, or relative URLs)
export function imageUrlOf(record: Record<string, unknown>, key = "image_url"): string | null {
  const value = record[key];
  if (typeof value !== "string") return null;
  try {
    const url = new URL(value);
    return url.protocol === "https:" || url.protocol === "http:" ? url.href : null;
  } catch {
    return null;
  }
}

// cards prefer the small thumbnail; the detail panel prefers the full image.
// Either one is used when the other is missing or fails to load.
export function imageCandidates(record: Record<string, unknown>, variant: "card" | "detail") {
  const keys = variant === "card" ? ["thumbnail_url", "image_url"] : ["image_url", "thumbnail_url"];
  const urls = keys.map((key) => imageUrlOf(record, key)).filter((url): url is string => url !== null);
  return urls.filter((url, index) => urls.indexOf(url) === index);
}

// simple line icons, shown when a record has no image or its image fails to load
const fallbackIcons: Record<Resource, string[]> = {
  // a planet with an orbit
  missions: ["M12 8a4 4 0 1 0 0 8a4 4 0 1 0 0-8", "M3 15c2 3 16-2 18-6"],
  // a building with columns
  agencies: ["M3 20h18", "M4 9h16", "M12 4l8 5H4z", "M6 9v11M10 9v11M14 9v11M18 9v11"],
  // a satellite with solar panels
  spacecraft: ["M9 9h6v6H9z", "M2 10h5v4H2zM17 10h5v4h-5z", "M7 12h2M15 12h2", "M12 9V5"],
  // a rocket lifting off
  launches: ["M12 3c3 3 4 7 3 12H9C8 10 9 6 12 3z", "M9 15l-3 3h3M15 15l3 3h-3", "M11 18h2v3h-2z"]
};

export function RecordImage({
  record,
  resource,
  variant
}: {
  record: Record<string, unknown>;
  resource: Resource;
  variant: "card" | "detail";
}) {
  // remember which URLs failed, so the next candidate (or a different record's image) gets a try
  const [failed, setFailed] = useState<string[]>([]);
  const src = imageCandidates(record, variant).find((url) => !failed.includes(url));

  if (src === undefined) {
    // the detail panel just leaves the image out; cards keep their shape with an icon
    if (variant === "detail") return null;
    return (
      <div className={`record-image record-image-${variant} record-image-empty`} aria-hidden="true">
        <svg fill="none" stroke="currentColor" strokeLinejoin="round" strokeWidth="1.2" viewBox="0 0 24 24">
          {fallbackIcons[resource].map((d) => (
            <path d={d} key={d} />
          ))}
        </svg>
      </div>
    );
  }

  const image = (
    <div className={`record-image record-image-${variant}`}>
      {/* eslint-disable-next-line @next/next/no-img-element -- images come from many outside hosts */}
      <img
        alt=""
        decoding="async"
        loading="lazy"
        onError={() => setFailed((urls) => [...urls, src])}
        referrerPolicy="no-referrer"
        src={src}
      />
    </div>
  );
  if (variant === "card") return image;

  // the detail panel credits the image's source (images belong to their owners, not to LL2)
  const credit = imageCreditOf(record);
  return (
    <figure className="record-figure">
      {image}
      {credit && <figcaption className="record-image-credit">{credit}</figcaption>}
    </figure>
  );
}

// "Image: CCTV · License: Unknown", leaving out whichever part is missing
export function imageCreditOf(record: Record<string, unknown>): string | null {
  const text = (value: unknown) => (typeof value === "string" ? value.trim() : "");
  const parts = [
    text(record.image_credit) && `Image: ${text(record.image_credit)}`,
    text(record.image_license) && `License: ${text(record.image_license)}`
  ].filter(Boolean);
  return parts.length > 0 ? parts.join(" · ") : null;
}
