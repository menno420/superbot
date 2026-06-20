import * as React from "react";

export interface PageHeaderBadge {
  /** Badge text (e.g. "generated"). */
  label: string;
  /** Tooltip explaining the badge. */
  title?: string;
}

export interface PageHeaderProps {
  /** The page title (h1). */
  title: string;
  /** Supporting copy beneath the title. */
  subtitle?: React.ReactNode;
  /**
   * Bordered header style (Changelog / Status): a bottom rule + larger subtitle.
   * Plain style (Features / Commands) when false.
   */
  bordered?: boolean;
  /** Optional "generated"-style badge shown next to the title. */
  badge?: PageHeaderBadge;
}

/**
 * A page header mirroring the two `botsite/` styles: the plain title + muted
 * subtitle used by `/features` and `/commands`, and the bordered variant (with
 * an optional "generated" freshness badge) used by `/changelog` and `/status`.
 */
export function PageHeader({
  title,
  subtitle,
  bordered = false,
  badge,
}: PageHeaderProps) {
  if (bordered) {
    return (
      <section className="mb-8 border-b border-slate-800 pb-6">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
          {badge ? (
            <span
              className="rounded bg-slate-800 px-2 py-0.5 text-xs text-slate-400"
              title={badge.title}
            >
              {badge.label}
            </span>
          ) : null}
        </div>
        {subtitle ? (
          <p className="mt-3 max-w-2xl text-slate-300">{subtitle}</p>
        ) : null}
      </section>
    );
  }
  return (
    <section className="mb-8">
      <h1 className="text-3xl font-bold">{title}</h1>
      {subtitle ? <p className="mt-2 text-slate-400">{subtitle}</p> : null}
    </section>
  );
}
