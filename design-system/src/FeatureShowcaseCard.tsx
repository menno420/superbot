import * as React from "react";

import { Badge } from "./Badge";

export interface FeatureShowcaseCardProps {
  /** Leading emoji/icon. */
  emoji?: string;
  /** Feature display name. */
  name: string;
  /** One/two-line description. */
  description?: string;
  /** Short tag chips (first 4 shown). */
  tags?: string[];
  /** Show the fuchsia "game" badge. */
  isGame?: boolean;
  /** Deep-link to the related commands. */
  commandsHref?: string;
}

/**
 * A single feature card from the `/features` showcase — emoji, name, an optional
 * "game" badge, description, tag chips, and a "See commands" link. Distinct from
 * the homepage `FeatureCard`, which groups several features under one category.
 * Mirrors the feature `<article>` in `botsite/templates/features.html`.
 */
export function FeatureShowcaseCard({
  emoji = "•",
  name,
  description,
  tags = [],
  isGame = false,
  commandsHref = "/commands#",
}: FeatureShowcaseCardProps) {
  return (
    <article className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 transition-colors hover:border-sky-700">
      <div className="flex items-center gap-2">
        <span className="text-2xl">{emoji}</span>
        <h3 className="font-semibold">{name}</h3>
        {isGame ? (
          <span className="ml-auto">
            <Badge tone="game">game</Badge>
          </span>
        ) : null}
      </div>
      {description ? (
        <p className="mt-2 text-sm text-slate-400">{description}</p>
      ) : null}
      {tags.length > 0 ? (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {tags.slice(0, 4).map((tag) => (
            <span
              key={tag}
              className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-slate-400"
            >
              {tag}
            </span>
          ))}
        </div>
      ) : null}
      <a
        href={commandsHref}
        className="mt-3 inline-block text-xs text-sky-400 hover:text-sky-300"
      >
        See commands →
      </a>
    </article>
  );
}
