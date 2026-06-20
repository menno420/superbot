import * as React from "react";

import { ChangelogEntry, type ChangelogEntryProps } from "./ChangelogEntry";
import { PageHeader } from "./PageHeader";
import { PageShell } from "./PageShell";
import { SiteFooter, type BuildMeta } from "./SiteFooter";
import { SiteHeader } from "./SiteHeader";

export interface ChangelogItem extends ChangelogEntryProps {
  /** Date string — entries are grouped by date, newest first. */
  date: string;
}

export interface ChangelogPageProps {
  /** The "Add to Discord" install URL. */
  addUrl?: string;
  /** Changelog entries, newest first. */
  entries?: ChangelogItem[];
  /** Deployed-build metadata for the footer/header. */
  build?: BuildMeta;
}

// Sample defaults so the page renders standalone in Storybook / on the canvas.
const DEFAULT_ENTRIES: ChangelogItem[] = [
  {
    date: "2026-06-20",
    kind: "feature",
    title: "The whole site is now editable as real components",
    summary: "Every page is a source-backed component you can redesign visually.",
  },
  {
    date: "2026-06-20",
    kind: "improvement",
    title: "Faster command search",
    summary: "Client-side filtering on the commands page is now instant.",
  },
  {
    date: "2026-06-18",
    kind: "fix",
    title: "Fixed the broken feedback button",
    summary: "The submit form works again.",
  },
];

/**
 * The full `/changelog` page — a curated, newest-first timeline grouped by date,
 * each day listing {@link ChangelogEntry} items. Mirrors
 * `botsite/templates/changelog.html`. Renders standalone with sample data.
 */
export function ChangelogPage({
  addUrl = "#",
  entries = DEFAULT_ENTRIES,
  build,
}: ChangelogPageProps) {
  // Group consecutive entries by date, preserving order (newest first).
  const groups: { date: string; items: ChangelogItem[] }[] = [];
  for (const entry of entries) {
    const last = groups[groups.length - 1];
    if (last && last.date === entry.date) {
      last.items.push(entry);
    } else {
      groups.push({ date: entry.date, items: [entry] });
    }
  }
  return (
    <PageShell
      header={
        <SiteHeader
          active="changelog"
          addUrl={addUrl}
          hasBuild={Boolean(build?.commit)}
        />
      }
      footer={<SiteFooter build={build} />}
    >
      <PageHeader
        bordered
        title="What's new"
        badge={{
          label: "generated",
          title:
            "Curated from the bot's changelog as of the last deploy — not a live feed.",
        }}
        subtitle="New features, fixes and improvements you can feel — the changes that actually reach your server. Hand-curated, newest first."
      />
      {groups.length > 0 ? (
        <div className="space-y-10">
          {groups.map((group) => (
            <section key={group.date} className="relative">
              <div className="mb-4 flex items-center gap-3">
                <span className="h-2.5 w-2.5 rounded-full bg-indigo-500 ring-4 ring-indigo-500/15" />
                <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
                  <time dateTime={group.date}>{group.date}</time>
                </h2>
              </div>
              <div className="ml-[5px] space-y-4 border-l border-slate-800 pl-6">
                {group.items.map((item, i) => (
                  <ChangelogEntry
                    key={i}
                    kind={item.kind}
                    title={item.title}
                    summary={item.summary}
                    url={item.url}
                  />
                ))}
              </div>
            </section>
          ))}
        </div>
      ) : (
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-8 text-center">
          <p className="text-slate-300">No changelog entries yet.</p>
          <p className="mt-2 text-sm text-slate-500">
            Check back soon — new features and fixes will show up here as they
            ship.
          </p>
        </div>
      )}
    </PageShell>
  );
}
