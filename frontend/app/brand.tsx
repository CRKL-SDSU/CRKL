// The CRKL-Space logo: a targeting mark and the "CRKL /SPACE" wordmark.
// Colors come from the theme variables, so the logo follows light and dark mode.

// "SPACE" is drawn with straight strokes on a 12 x 20 grid, like a pen plotter
const spaceGlyphs = [
  ["M12 0H3L0 3V8L3 10H9L12 12V17L9 20H0"], // S
  ["M0 20V0H9L12 3V8L9 11H0"], // P
  ["M0 20V5L5 0H7L12 5V20", "M0 12H12"], // A
  ["M12 0H4L0 4V16L4 20H12"], // C
  ["M12 0H0V20H12", "M0 10H9"] // E
];

// Layout in wordmark units: the cap height of every glyph is 20
const CRKL_WIDTH = 79.2; // Barlow Semi Condensed 600 at cap height 20, with .22em tracking
const SLASH_X = CRKL_WIDTH + 12; // a word space before the slash
const SPACE_X = SLASH_X + 7 + 8; // the slash, then the same gap as between letters
const LETTER_STEP = 12 + 8;
const WORDMARK_WIDTH = SPACE_X + 4 * LETTER_STEP + 12;

export function BrandMark({ size = 28 }: { size?: number }) {
  return (
    <svg aria-hidden="true" className="brand-mark" height={size} viewBox="0 0 32 32" width={size}>
      <path d="M24 7.5H11l-5 5v7l5 5h13" fill="none" stroke="currentColor" strokeWidth="3" />
      <rect fill="var(--accent)" height="5" width="5" x="21.5" y="13.5" />
      <path d="M1 16h3M28 16h3M16 1v3M16 28v3" stroke="var(--muted)" strokeWidth="1.2" />
    </svg>
  );
}

export function BrandWordmark({ height = 18 }: { height?: number }) {
  const viewHeight = 23;
  return (
    <svg
      aria-label="CRKL-Space"
      className="brand-wordmark"
      height={height}
      role="img"
      viewBox={`0 -1.5 ${WORDMARK_WIDTH + 1} ${viewHeight}`}
      width={(height * (WORDMARK_WIDTH + 1)) / viewHeight}
    >
      <text
        fill="currentColor"
        fontFamily="'Barlow Semi Condensed', sans-serif"
        fontSize={20 / 0.7}
        fontWeight={600}
        lengthAdjust="spacing"
        textLength={CRKL_WIDTH}
        x="0"
        y="20"
      >
        CRKL
      </text>
      <path
        d={`M${SLASH_X} 20L${SLASH_X + 7} 0`}
        fill="none"
        stroke="var(--accent)"
        strokeLinecap="round"
        strokeWidth="1.8"
      />
      <g
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1"
      >
        {spaceGlyphs.map((paths, index) =>
          paths.map((d) => (
            <path d={d} key={`${index}-${d}`} transform={`translate(${SPACE_X + index * LETTER_STEP} 0)`} />
          ))
        )}
      </g>
    </svg>
  );
}

export function BrandLogo() {
  return (
    <>
      <BrandMark />
      <BrandWordmark />
    </>
  );
}
