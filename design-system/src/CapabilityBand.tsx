import * as React from "react";

import { StatTile } from "./StatTile";

export interface CapabilityStat {
  /** The headline number. */
  value: React.ReactNode;
  /** What the number counts. */
  label: string;
  /** Optional deep-link. */
  href?: string;
}

export interface CapabilityBandProps {
  /** The capability tiles (honest catalogue counts only). */
  stats: CapabilityStat[];
}

/**
 * The homepage capability band — a centered row of {@link StatTile}s showing
 * honest catalogue counts (commands / feature areas / games). Mirrors the
 * capability `<section>` in `botsite/index.html`.
 */
export function CapabilityBand({ stats }: CapabilityBandProps) {
  return (
    <section className="mx-auto grid max-w-2xl grid-cols-3 gap-4">
      {stats.map((stat, i) => (
        <StatTile
          key={i}
          value={stat.value}
          label={stat.label}
          href={stat.href}
        />
      ))}
    </section>
  );
}
