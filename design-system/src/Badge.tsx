import * as React from "react";

export type BadgeTone =
  | "finished"
  | "in-progress"
  | "game"
  | "new"
  | "improved"
  | "fixed";

const TONES: Record<BadgeTone, string> = {
  finished: "bg-emerald-900/50 text-emerald-300",
  "in-progress": "bg-amber-900/60 text-amber-300",
  game: "bg-fuchsia-900/50 text-fuchsia-300",
  new: "bg-emerald-500/15 text-emerald-300 ring-1 ring-emerald-500/30",
  improved: "bg-sky-500/15 text-sky-300 ring-1 ring-sky-500/30",
  fixed: "bg-amber-500/15 text-amber-300 ring-1 ring-amber-500/30",
};

export interface BadgeProps {
  /** Which status/category the pill represents. */
  tone?: BadgeTone;
  children: React.ReactNode;
}

/**
 * A small status / category pill — command maturity (`finished` vs
 * `in-progress`), a `game` marker, or a changelog kind (`new` / `improved` /
 * `fixed`).
 */
export function Badge({ tone = "finished", children }: BadgeProps) {
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${TONES[tone]}`}
    >
      {children}
    </span>
  );
}
