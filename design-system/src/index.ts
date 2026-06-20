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
