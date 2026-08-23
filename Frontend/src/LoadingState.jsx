"use client";

import { useEffect, useState } from "react";

/* ─────────────────────────────────────────────────────────
 * LOADING STATE — pixel-grid loader for long-running work
 *
 * Variants:
 *   Drive  — square cells, chevron wavefront driving right;
 *            the 650ms cycle is shorter than the sweep, so
 *            two fronts are always in flight
 *   Dots   — same wavefront, circular cells
 *   Orbit  — a comet lapping the grid perimeter
 *   Surfer — the Drive loader paired with a meme video below
 *
 * Paired with a shimmering label and a live elapsed timer
 * in mono tabular figures. Reduced motion freezes the grid
 * to its dim state; the timer still ticks.
 * ───────────────────────────────────────────────────────── */

const chevron = Array.from({ length: 9 }, (_, i) => {
  const r = Math.floor(i / 3), c = i % 3;
  return (c + Math.abs(r - 1)) * 90;
});

const ORBIT_ORDER = [0, 1, 2, 5, 8, 7, 6, 3];
const orbit = Array.from({ length: 9 }, (_, i) => {
  const k = ORBIT_ORDER.indexOf(i);
  return k === -1 ? null : k * 110;
});

const PATTERNS = {
  Drive: { delays: chevron, dur: 650, round: false },
  Dots: { delays: chevron, dur: 650, round: true },
  Orbit: { delays: orbit, dur: 950, round: false },
};

function LoaderGrid({
  delays,
  dur,
  round,
}) {
  return (
    <span aria-hidden className="grid shrink-0 grid-cols-[repeat(3,4px)] gap-[1.5px]" style={{ display: "inline-grid", gridTemplateColumns: "repeat(3, 4px)", gap: "2px", width: "18px" }}>
      {delays.map((delay, index) => (
        <span
          key={index}
          className={`size-[4px] bg-ink ${round ? "rounded-full" : "rounded-[1px]"}`}
          style={{
            width: "4px",
            height: "4px",
            backgroundColor: "var(--ink-primary)",
            borderRadius: round ? "50%" : "1px",
            opacity: delay === null ? 0.07 : 0.15,
            animation: delay === null ? "none" : `pixel-on ${dur}ms ease-in-out ${delay}ms infinite`,
          }}
        />
      ))}
    </span>
  );
}

function useElapsed() {
  const [ds, setDs] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setDs((d) => d + 1), 100);
    return () => clearInterval(t);
  }, []);
  const total = ds / 10;
  if (total < 60) return `${total.toFixed(1)}s`;
  return `${Math.floor(total / 60)}m ${(total % 60).toFixed(1)}s`;
}

export default function LoadingState({
  label,
  variant = "Drive",
  videoSrc = "/subway-surfers.mp4",
}) {
  const elapsed = useElapsed();
  const surfer = variant === "Surfer";
  const resolvedLabel = label ?? (surfer ? "Subway surfing" : "Verifying Book Listings Across Marketplaces");
  const [videoOk, setVideoOk] = useState(true);
  const { delays, dur, round } = PATTERNS[variant] ?? PATTERNS.Drive;

  const loadingBarEl = (
    <div
      style={{
        width: "220px",
        height: "8px",
        backgroundColor: "rgba(43, 30, 22, 0.08)",
        borderRadius: "4px",
        border: "1px solid var(--border-aged)",
        overflow: "hidden",
        position: "relative",
      }}
    >
      <div
        style={{
          width: "100%",
          height: "100%",
          background: "linear-gradient(90deg, transparent 0%, var(--ink-primary) 50%, transparent 100%)",
          animation: "loading-bar-sweep 1.2s cubic-bezier(0.4, 0, 0.2, 1) infinite",
        }}
      />
    </div>
  );
  const elapsedEl = <span className="font-mono text-[12px] text-ink-3 tabular-nums" style={{ fontFamily: "monospace", fontSize: "0.9rem", color: "var(--ink-dim)" }}>[{elapsed}]</span>;

  if (surfer) {
    return (
      <div role="status" className="flex w-fit flex-col items-start" style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
        <div className="flex items-center gap-2.5" style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <LoaderGrid {...PATTERNS.Drive} />
          {loadingBarEl}
          {elapsedEl}
        </div>

        <div
          className="mt-2 w-56 overflow-hidden rounded-[10px] shadow-overlay"
          style={{ animation: "pop-in 200ms cubic-bezier(0.16,1,0.3,1) both", transformOrigin: "top left", marginTop: "12px" }}
        >
          <div className="relative aspect-video w-full" style={{ background: "var(--tooltip-bg)", padding: "8px", borderRadius: "6px" }}>
            {videoOk ? (
              <video
                src={videoSrc}
                autoPlay
                muted
                loop
                playsInline
                onError={() => setVideoOk(false)}
                className="h-full w-full object-cover"
                style={{ width: "200px", borderRadius: "4px" }}
              />
            ) : (
              <div className="flex h-full w-full flex-col items-center justify-center gap-1.5" style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                <LoaderGrid {...PATTERNS.Drive} />
                <span className="px-3 text-center font-mono text-[10px]" style={{ color: "var(--tooltip-muted)", fontSize: "0.8rem" }}>
                  Video unavailable
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div role="status" className="flex w-fit items-center gap-2.5" style={{ display: "flex", alignItems: "center", gap: "12px", background: "var(--paper-card)", padding: "16px 24px", borderRadius: "8px", border: "1px solid var(--border-aged)", boxShadow: "var(--shadow-vintage)" }}>
      <LoaderGrid delays={delays} dur={dur} round={round} />
      {loadingBarEl}
      {elapsedEl}
    </div>
  );
}
