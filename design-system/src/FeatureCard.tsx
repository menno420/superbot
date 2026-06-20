import * as React from "react";

import { Card } from "./Card";

export interface FeatureItem {
  /** Optional leading emoji/icon. */
  emoji?: string;
  /** The feature's display name. */
  name: string;
}

export interface FeatureCardProps {
  /** Category heading (e.g. "games", "moderation"). */
  category: string;
  /** The features listed under this category. */
  items: FeatureItem[];
}

/**
 * A category card listing a few features — the homepage "what it does" grid and
 * the /features showcase.
 */
export function FeatureCard({ category, items }: FeatureCardProps) {
  return (
    <Card>
      <div className="mb-2 text-xs uppercase tracking-wide text-slate-500">
        {category}
      </div>
      <ul className="space-y-2">
        {items.map((item, i) => (
          <li key={i} className="flex items-start gap-2">
            <span className="shrink-0">{item.emoji ?? "•"}</span>
            <span className="text-sm text-slate-200">{item.name}</span>
          </li>
        ))}
      </ul>
    </Card>
  );
}
