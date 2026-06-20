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

export { PageHeader } from "./PageHeader";
export type { PageHeaderProps, PageHeaderBadge } from "./PageHeader";

export { SearchBar } from "./SearchBar";
export type { SearchBarProps } from "./SearchBar";

export { Pill } from "./Pill";
export type { PillProps } from "./Pill";

export { FeatureShowcaseCard } from "./FeatureShowcaseCard";
export type { FeatureShowcaseCardProps } from "./FeatureShowcaseCard";

export { CommandDetail } from "./CommandDetail";
export type { CommandRecord, PlannedIdea } from "./CommandDetail";

export { CommandEntry } from "./CommandEntry";
export type { CommandEntryProps } from "./CommandEntry";

export { ChangelogEntry } from "./ChangelogEntry";
export type { ChangelogEntryProps, ChangelogKind } from "./ChangelogEntry";

export { StatusCard } from "./StatusCard";
export type { StatusCardProps, StatusBuild } from "./StatusCard";

// ── Page compositions (the per-route surfaces Claude Design edits) ───────────
export { LandingPage } from "./LandingPage";
export type {
  LandingPageProps,
  FeatureCategory,
  HowItWorksStep,
} from "./LandingPage";

export { FeaturesPage } from "./FeaturesPage";
export type { FeaturesPageProps, FeatureCategoryGroup } from "./FeaturesPage";

export { CommandsPage } from "./CommandsPage";
export type { CommandsPageProps, CommandCategoryGroup } from "./CommandsPage";

export { ChangelogPage } from "./ChangelogPage";
export type { ChangelogPageProps, ChangelogItem } from "./ChangelogPage";

export { StatusPage } from "./StatusPage";
export type { StatusPageProps, StatusCounts } from "./StatusPage";
