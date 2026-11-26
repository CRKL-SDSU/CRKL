"use client";

import { useEffect, useState } from "react";

import { Resource } from "./fields";
import { buildPrompt } from "./prompt";

type CopyState = "idle" | "copied" | "failed";

// navigator.clipboard needs a secure context (https or localhost); fall back to a hidden textarea
async function copyText(value: string) {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(value);
    return;
  }
  const area = document.createElement("textarea");
  area.value = value;
  area.setAttribute("readonly", "");
  area.style.position = "fixed";
  area.style.opacity = "0";
  document.body.appendChild(area);
  area.select();
  const copied = document.execCommand("copy");
  area.remove();
  if (!copied) throw new Error("Copy failed");
}

// two stacked sheets (copy) with a sparkle (AI) on the front one
function PromptIcon() {
  return (
    <svg aria-hidden="true" fill="none" height="16" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" viewBox="0 0 24 24" width="16">
      <path d="M8 8V4h12v12h-4" />
      <path d="M4 8h12v12H4z" />
      <path className="copy-prompt-spark" d="M10 10.5l.9 2.1 2.1.9-2.1.9-.9 2.1-.9-2.1-2.1-.9 2.1-.9z" strokeWidth="1" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg aria-hidden="true" fill="none" height="16" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" viewBox="0 0 24 24" width="16">
      <path d="M5 12.5l4.5 4.5L19 7.5" />
    </svg>
  );
}

export function CopyPromptButton({ record, resource }: { record: Record<string, unknown>; resource: Resource }) {
  const [state, setState] = useState<CopyState>("idle");

  // go back to the normal look a moment after copying
  useEffect(() => {
    if (state === "idle") return;
    const timer = window.setTimeout(() => setState("idle"), 2000);
    return () => window.clearTimeout(timer);
  }, [state]);

  async function copy() {
    try {
      await copyText(buildPrompt(record, resource));
      setState("copied");
    } catch {
      setState("failed");
    }
  }

  const label = state === "copied" ? "Copied" : state === "failed" ? "Copy failed" : "Copy AI prompt";
  return (
    <button
      aria-label={label}
      className={`copy-prompt copy-prompt-${state}`}
      onClick={() => void copy()}
      title="Copy a prompt for an AI assistant, with this record's details and links to its primary data"
      type="button"
    >
      {state === "copied" ? <CheckIcon /> : <PromptIcon />}
      {/* the icon alone in normal use; a word only to confirm the result */}
      {state !== "idle" && <span>{label}</span>}
    </button>
  );
}
