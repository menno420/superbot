import * as React from "react";

import { PageHeader } from "./PageHeader";
import { PageShell } from "./PageShell";
import { SiteFooter } from "./SiteFooter";
import { SiteHeader } from "./SiteHeader";
import { StatusCard, type StatusBuild } from "./StatusCard";

export interface StatusCounts {
  commands: number;
  features: number;
  games: number;
}

export interface StatusPageProps {
  /** The "Add to Discord" install URL. */
  addUrl?: string;
  /** Deployed-build metadata. */
  build?: StatusBuild;
  /** Honest catalogue counts for the "what's in the box" band. */
  counts?: StatusCounts;
}

// Sample defaults so the page renders standalone in Storybook / on the canvas.
const DEFAULT_BUILD: StatusBuild = {
  commit: "1f26d13",
  committedAt: "2026-06-20",
  subject: "design-system: compose the full site",
};

const DEFAULT_COUNTS: StatusCounts = { commands: 308, features: 36, games: 8 };

/**
 * The full `/status` page — the honest "online as of last deploy" build card
 * ({@link StatusCard}) plus a "what's in the box" catalogue-counts band. Mirrors
 * `botsite/templates/status.html` (a build-time snapshot, never a live claim).
 */
export function StatusPage({
  addUrl = "#",
  build = DEFAULT_BUILD,
  counts = DEFAULT_COUNTS,
}: StatusPageProps) {
  const bands: [number, string][] = [
    [counts.commands, "commands"],
    [counts.features, "feature areas"],
    [counts.games, "games"],
  ];
  return (
    <PageShell
      header={
        <SiteHeader
          active="status"
          addUrl={addUrl}
          hasBuild={Boolean(build?.commit)}
        />
      }
      footer={<SiteFooter build={build} />}
    >
      <PageHeader
        bordered
        title="Status"
        badge={{
          label: "generated",
          title: "Reflects the last deploy, not a live health check.",
        }}
        subtitle="What's running right now, as of the last deploy. This page is a build-time snapshot — it doesn't poll the bot live."
      />
      <StatusCard build={build} />
      <section className="mt-8">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">
          What's in the box
        </h2>
        <div className="grid max-w-2xl grid-cols-3 gap-4">
          {bands.map(([value, label]) => (
            <div
              key={label}
              className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 text-center"
            >
              <div className="text-3xl font-bold">{value}</div>
              <div className="text-sm text-slate-400">{label}</div>
            </div>
          ))}
        </div>
      </section>
    </PageShell>
  );
}
