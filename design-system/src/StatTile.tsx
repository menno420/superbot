import * as React from "react";

export interface StatTileProps {
  /** The headline number (e.g. a command count). */
  value: React.ReactNode;
  /** What the number counts (e.g. "commands"). */
  label: string;
  /** Optional deep-link; renders the tile as an anchor when provided. */
  href?: string;
}

/**
 * A single capability-count tile from the homepage "capability band" — e.g.
 * "120 / commands". Honest catalogue counts only (never server/user totals).
 */
export function StatTile({ value, label, href }: StatTileProps) {
  const inner = (
    <>
      <div className="text-3xl font-bold">{value}</div>
      <div className="text-sm text-slate-400">{label}</div>
    </>
  );
  const cls =
    "block rounded-xl border border-slate-800 bg-slate-900/50 p-5 text-center transition-colors hover:border-sky-600";
  return href ? (
    <a href={href} className={cls}>
      {inner}
    </a>
  ) : (
    <div className={cls}>{inner}</div>
  );
}
