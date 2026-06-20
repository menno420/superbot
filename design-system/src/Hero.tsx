import * as React from "react";

import { ButtonLink } from "./ButtonLink";

export interface HeroCta {
  /** Button label. */
  label: string;
  /** Destination href. */
  href: string;
}

export interface HeroProps {
  /** The big product wordmark/headline. */
  title?: string;
  /** Supporting tagline beneath the title. */
  tagline?: React.ReactNode;
  /** Primary CTA (the brand "Add to Discord" action). */
  primary?: HeroCta;
  /** Optional secondary CTA. */
  secondary?: HeroCta;
}

/**
 * The homepage hero — product wordmark, tagline, and the primary/secondary
 * calls-to-action. Mirrors the hero `<section>` in `botsite/index.html`.
 */
export function Hero({
  title = "SuperBot",
  tagline = "One Discord bot for games, moderation, AI tools and more — built by a self-improving, AI-assisted development workflow.",
  primary,
  secondary,
}: HeroProps) {
  return (
    <section className="py-12 text-center sm:py-16">
      <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">{title}</h1>
      <p className="mx-auto mt-4 max-w-2xl text-lg text-slate-300">{tagline}</p>
      {(primary || secondary) && (
        <div className="mt-7 flex items-center justify-center gap-3">
          {primary && (
            <ButtonLink
              href={primary.href}
              target="_blank"
              rel="noopener"
              variant="primary"
            >
              {primary.label}
            </ButtonLink>
          )}
          {secondary && (
            <ButtonLink href={secondary.href} variant="secondary">
              {secondary.label}
            </ButtonLink>
          )}
        </div>
      )}
    </section>
  );
}
