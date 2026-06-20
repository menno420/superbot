import * as React from "react";

export interface NavItem {
  /** Route key (e.g. "features") — also the active-state match key. */
  key: string;
  /** Visible label (e.g. "Features"). */
  label: string;
  /** Destination href. Defaults to `/{key}`. */
  href?: string;
}

export interface SiteHeaderProps {
  /** Primary nav links. Defaults to the live site's nav. */
  navItems?: NavItem[];
  /** The currently-active route key, highlighted in the nav. */
  active?: string;
  /** The "Add to Discord" install URL. */
  addUrl?: string;
  /**
   * Whether a build is known — drives the status dot (emerald when a deploy is
   * known, slate otherwise). Honest "as of last deploy" posture; never a live
   * claim.
   */
  hasBuild?: boolean;
}

const DEFAULT_NAV: NavItem[] = [
  { key: "features", label: "Features" },
  { key: "commands", label: "Commands" },
  { key: "changelog", label: "Changelog" },
  { key: "status", label: "Status" },
];

/**
 * The sticky top navigation — logo, primary links, the "as of last deploy"
 * status dot, and the persistent "Add to Discord" CTA. Mirrors the `<header>`
 * in `botsite/base.html`.
 */
export function SiteHeader({
  navItems = DEFAULT_NAV,
  active,
  addUrl = "#",
  hasBuild = true,
}: SiteHeaderProps) {
  return (
    <header className="sticky top-0 z-10 border-b border-slate-800 bg-slate-900/70 backdrop-blur">
      <nav className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-5 gap-y-2 px-4 py-3">
        <a href="/" className="mr-2 text-lg font-bold">
          🤖 SuperBot
        </a>
        {navItems.map((item) => {
          const isActive = item.key === active;
          return (
            <a
              key={item.key}
              href={item.href ?? `/${item.key}`}
              className={`text-sm hover:text-sky-300 ${
                isActive ? "font-semibold text-sky-400" : "text-slate-300"
              }`}
            >
              {item.label}
            </a>
          );
        })}
        <div className="ml-auto flex items-center gap-3">
          <a
            href="/status"
            title="Status (as of last deploy)"
            className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200"
          >
            <span
              className={`inline-block h-2.5 w-2.5 rounded-full ${
                hasBuild ? "bg-emerald-500" : "bg-slate-500"
              }`}
            />
            <span className="hidden sm:inline">Status</span>
          </a>
          <a
            href={addUrl}
            target="_blank"
            rel="noopener"
            className="rounded-lg bg-indigo-600 px-4 py-1.5 text-sm font-semibold shadow hover:bg-indigo-500"
          >
            Add to Discord
          </a>
        </div>
      </nav>
    </header>
  );
}
