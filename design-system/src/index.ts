// Public API of @superbot/design-system. tsup builds this entry into
// dist/index.js + dist/index.d.ts — the artifacts /design-sync consumes.
export { Button } from "./Button";
export type { ButtonProps, ButtonVariant } from "./Button";

export { Badge } from "./Badge";
export type { BadgeProps, BadgeTone } from "./Badge";

export { Card } from "./Card";
export type { CardProps } from "./Card";

export { StatTile } from "./StatTile";
export type { StatTileProps } from "./StatTile";

export { FeatureCard } from "./FeatureCard";
export type { FeatureCardProps, FeatureItem } from "./FeatureCard";

export { CommandCard } from "./CommandCard";
export type { CommandCardProps } from "./CommandCard";

// ── Layout / chrome ─────────────────────────────────────────────────────────
export { ButtonLink } from "./ButtonLink";
export type { ButtonLinkProps } from "./ButtonLink";

export { PageShell } from "./PageShell";
export type { PageShellProps } from "./PageShell";

export { SiteHeader } from "./SiteHeader";
export type { SiteHeaderProps, NavItem } from "./SiteHeader";

export { SiteFooter } from "./SiteFooter";
export type { SiteFooterProps, BuildMeta } from "./SiteFooter";

// ── Sections ────────────────────────────────────────────────────────────────
export { Hero } from "./Hero";
export type { HeroProps, HeroCta } from "./Hero";

export { Section } from "./Section";
export type { SectionProps, SectionAction } from "./Section";

export { StepCard } from "./StepCard";
export type { StepCardProps } from "./StepCard";

export { CapabilityBand } from "./CapabilityBand";
export type { CapabilityBandProps, CapabilityStat } from "./CapabilityBand";

// ── Page composition (the canonical surface Claude Design edits) ─────────────
export { LandingPage } from "./LandingPage";
export type {
  LandingPageProps,
  FeatureCategory,
  HowItWorksStep,
} from "./LandingPage";
