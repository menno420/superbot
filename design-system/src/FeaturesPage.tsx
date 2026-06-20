import * as React from "react";

import {
  FeatureShowcaseCard,
  type FeatureShowcaseCardProps,
} from "./FeatureShowcaseCard";
import { PageHeader } from "./PageHeader";
import { PageShell } from "./PageShell";
import { Pill } from "./Pill";
import { SearchBar } from "./SearchBar";
import { SiteFooter, type BuildMeta } from "./SiteFooter";
import { SiteHeader } from "./SiteHeader";

export interface FeatureCategoryGroup {
  /** Category name (e.g. "games"). */
  category: string;
  /** Features in this category. */
  features: FeatureShowcaseCardProps[];
}

export interface FeaturesPageProps {
  /** The "Add to Discord" install URL. */
  addUrl?: string;
  /** Feature categories to show. */
  groups?: FeatureCategoryGroup[];
  /** Deployed-build metadata for the footer/header. */
  build?: BuildMeta;
}

// Sample defaults so the page renders standalone in Storybook / on the canvas.
const DEFAULT_GROUPS: FeatureCategoryGroup[] = [
  {
    category: "games",
    features: [
      {
        emoji: "🃏",
        name: "Blackjack",
        description: "Play blackjack against the bot.",
        tags: ["cards", "casino"],
        isGame: true,
      },
      {
        emoji: "✊",
        name: "Rock Paper Scissors",
        description: "Challenge another member to a duel.",
        tags: ["duel"],
        isGame: true,
      },
    ],
  },
  {
    category: "moderation",
    features: [
      {
        emoji: "🛡️",
        name: "Auto-moderation",
        description: "Filter spam and unwanted content automatically.",
        tags: ["safety"],
      },
      {
        emoji: "⚠️",
        name: "Warnings",
        description: "Track and escalate member warnings.",
        tags: ["audit"],
      },
    ],
  },
];

/**
 * The full `/features` showcase page — searchable, category-jump pills, and a
 * grid of {@link FeatureShowcaseCard}s per category. Mirrors
 * `botsite/templates/features.html`. Renders standalone with sample data.
 */
export function FeaturesPage({
  addUrl = "#",
  groups = DEFAULT_GROUPS,
  build,
}: FeaturesPageProps) {
  const total = groups.reduce((n, g) => n + g.features.length, 0);
  return (
    <PageShell
      header={
        <SiteHeader
          active="features"
          addUrl={addUrl}
          hasBuild={Boolean(build?.commit)}
        />
      }
      footer={<SiteFooter build={build} />}
    >
      <PageHeader
        title="Features"
        subtitle={`${total} feature areas across ${groups.length} categories — games, moderation, AI, economy and more. Search or jump to a category.`}
      />
      <div className="mb-6 space-y-3">
        <SearchBar placeholder="Search features…" />
        <div className="flex flex-wrap gap-2">
          {groups.map((g) => (
            <Pill key={g.category} href={`#cat-${g.category}`}>
              {g.category}
            </Pill>
          ))}
        </div>
      </div>
      <div className="space-y-10">
        {groups.map((g) => (
          <section
            key={g.category}
            id={`cat-${g.category}`}
            className="scroll-mt-24"
          >
            <h2 className="mb-4 text-lg font-semibold capitalize">
              {g.category}
            </h2>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {g.features.map((f) => (
                <FeatureShowcaseCard key={f.name} {...f} />
              ))}
            </div>
          </section>
        ))}
      </div>
    </PageShell>
  );
}
