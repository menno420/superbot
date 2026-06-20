import * as React from "react";

export interface BuildMeta {
  /** Short commit SHA of the deployed build. */
  commit?: string;
  /** Human-readable commit timestamp. */
  committedAt?: string;
}

export interface SiteFooterProps {
  /** Deployed-build metadata for the freshness badge. */
  build?: BuildMeta;
  /** Link to the public source repository. */
  sourceUrl?: string;
}

/**
 * The site footer — the honest "generated / as of last deploy" freshness badge,
 * the build SHA, and a source link. Mirrors the `<footer>` in
 * `botsite/base.html`. The public site never claims live state here.
 */
export function SiteFooter({
  build,
  sourceUrl = "https://github.com/menno420/superbot",
}: SiteFooterProps) {
  return (
    <footer className="mx-auto w-full max-w-6xl border-t border-slate-800 px-4 py-6 text-xs text-slate-500">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <span className="rounded bg-slate-800 px-2 py-0.5 text-slate-400">
          generated
        </span>
        <span>
          {build?.commit ? (
            <>
              as of last deploy · build <code>{build.commit}</code>
              {build.committedAt ? ` · ${build.committedAt}` : null}
            </>
          ) : (
            "build info unavailable"
          )}
        </span>
        <span className="ml-auto">
          <a className="underline hover:text-slate-300" href={sourceUrl}>
            source
          </a>
        </span>
      </div>
    </footer>
  );
}
