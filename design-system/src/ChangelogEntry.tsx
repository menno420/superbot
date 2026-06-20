import * as React from "react";

export type ChangelogKind = "feature" | "improvement" | "fix" | "update";

export interface ChangelogEntryProps {
  /** Change kind — drives the colored label. Unknown/empty → "Update". */
  kind?: ChangelogKind;
  /** Entry title. */
  title: string;
  /** Optional one/two-line summary. */
  summary?: string;
  /** Optional outbound link (e.g. a release) — renders a "Details →" link. */
  url?: string;
}

const KIND_STYLES: Record<ChangelogKind, { label: string; ring: string }> = {
  feature: {
    label: "New",
    ring: "bg-emerald-500/15 text-emerald-300 ring-emerald-500/30",
  },
  improvement: {
    label: "Improved",
    ring: "bg-sky-500/15 text-sky-300 ring-sky-500/30",
  },
  fix: {
    label: "Fixed",
    ring: "bg-amber-500/15 text-amber-300 ring-amber-500/30",
  },
  update: {
    label: "Update",
    ring: "bg-slate-700/40 text-slate-300 ring-slate-600/40",
  },
};

/**
 * One entry in the `/changelog` timeline — a colored kind label ("New" /
 * "Improved" / "Fixed" / "Update"), a title, an optional summary, and an
 * optional "Details" link. Mirrors `botsite/templates/changelog.html`.
 */
export function ChangelogEntry({
  kind = "update",
  title,
  summary,
  url,
}: ChangelogEntryProps) {
  const style = KIND_STYLES[kind] ?? KIND_STYLES.update;
  return (
    <article className="rounded-xl border border-slate-800 bg-slate-900/40 p-5">
      <div className="flex flex-wrap items-center gap-3">
        <span
          className={`rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ${style.ring}`}
        >
          {style.label}
        </span>
        <h3 className="font-semibold text-slate-100">{title}</h3>
      </div>
      {summary ? (
        <p className="mt-2 text-sm text-slate-300">{summary}</p>
      ) : null}
      {url ? (
        <a
          href={url}
          rel="noopener"
          className="mt-3 inline-flex items-center gap-1 text-sm text-sky-400 hover:text-sky-300"
        >
          Details →
        </a>
      ) : null}
    </article>
  );
}
