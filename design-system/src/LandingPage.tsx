import * as React from "react";

import { ButtonLink } from "./ButtonLink";
import { CapabilityBand } from "./CapabilityBand";
import { FeatureCard, type FeatureItem } from "./FeatureCard";
import { Hero } from "./Hero";
import { PageShell } from "./PageShell";
import { Section } from "./Section";
import { SiteFooter, type BuildMeta } from "./SiteFooter";
import { SiteHeader } from "./SiteHeader";
import { StepCard } from "./StepCard";

export interface FeatureCategory {
  /** Category heading (e.g. "games"). */
  category: string;
  /** Features listed under it. */
  items: FeatureItem[];
}

export interface HowItWorksStep {
  /** Step marker shown in the circle. */
  number: React.ReactNode;
  /** Step title. */
  title: string;
  /** Step description. */
  body: string;
}

export interface LandingPageProps {
  /** The "Add to Discord" install URL. */
  addUrl?: string;
  /** Honest catalogue counts for the capability band. */
  counts?: { commands: number; features: number; games: number };
  /** Feature categories for the "What it does" grid. */
  features?: FeatureCategory[];
  /** The "How it works" steps. */
  steps?: HowItWorksStep[];
  /** Deployed-build metadata for the footer freshness badge. */
  build?: BuildMeta;
}

// Sample defaults so the page renders fully standalone in Storybook and on the
// Claude Design canvas. The live site overrides these from botsite/data/site.json.
const DEFAULT_COUNTS = { commands: 308, features: 36, games: 8 };

const DEFAULT_FEATURES: FeatureCategory[] = [
  {
    category: "games",
    items: [
      { emoji: "🃏", name: "Blackjack" },
      { emoji: "✊", name: "Rock Paper Scissors" },
      { emoji: "🎲", name: "Dice" },
    ],
  },
  {
    category: "moderation",
    items: [
      { emoji: "🛡️", name: "Auto-moderation" },
      { emoji: "⚠️", name: "Warnings" },
      { emoji: "⏳", name: "Timeouts" },
    ],
  },
  {
    category: "ai tools",
    items: [
      { emoji: "🤖", name: "AI gateway" },
      { emoji: "📝", name: "Summaries" },
      { emoji: "🌐", name: "Translations" },
    ],
  },
];

const DEFAULT_STEPS: HowItWorksStep[] = [
  { number: "1", title: "Invite", body: "Add SuperBot to your server." },
  { number: "2", title: "Configure", body: "Pick the features you want." },
  {
    number: "3",
    title: "Enjoy",
    body: "Your members start playing and using it.",
  },
];

/**
 * The full marketing landing page composed from the design-system parts — the
 * canonical "page" Claude Design edits, mapping 1:1 onto `botsite/index.html`
 * (plus the `base.html` chrome). Every region is a real, source-backed
 * component, so edits on the canvas always have somewhere in source to save to.
 * Renders standalone with sample defaults; the live site passes real data.
 */
export function LandingPage({
  addUrl = "#",
  counts = DEFAULT_COUNTS,
  features = DEFAULT_FEATURES,
  steps = DEFAULT_STEPS,
  build,
}: LandingPageProps) {
  return (
    <PageShell
      header={<SiteHeader addUrl={addUrl} hasBuild={Boolean(build?.commit)} />}
      footer={<SiteFooter build={build} />}
    >
      <Hero
        primary={{ label: "Add to Discord", href: addUrl }}
        secondary={{ label: "Explore features", href: "/features" }}
      />

      <CapabilityBand
        stats={[
          { value: counts.commands, label: "commands", href: "/commands" },
          { value: counts.features, label: "feature areas", href: "/features" },
          { value: counts.games, label: "games", href: "/features" },
        ]}
      />

      <Section
        title="What it does"
        action={{ label: "All features →", href: "/features" }}
      >
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((f) => (
            <FeatureCard
              key={f.category}
              category={f.category}
              items={f.items}
            />
          ))}
        </div>
      </Section>

      <Section title="How it works" centered>
        <div className="mx-auto grid max-w-3xl grid-cols-1 gap-4 sm:grid-cols-3">
          {steps.map((s, i) => (
            <StepCard key={i} number={s.number} title={s.title} body={s.body} />
          ))}
        </div>
      </Section>

      <section className="mt-14 text-center">
        <ButtonLink
          href={addUrl}
          target="_blank"
          rel="noopener"
          variant="primary"
        >
          Add SuperBot to your server
        </ButtonLink>
      </section>
    </PageShell>
  );
}
