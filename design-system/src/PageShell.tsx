import * as React from "react";

export interface PageShellProps {
  /** The sticky site header (typically `<SiteHeader />`). */
  header?: React.ReactNode;
  /** The site footer (typically `<SiteFooter />`). */
  footer?: React.ReactNode;
  /** Page body, rendered inside the centered `<main>` column. */
  children: React.ReactNode;
}

/**
 * The page chrome that wraps every bot-site page — the dark canvas, the centered
 * max-width column, and the header/footer slots. Mirrors `botsite/base.html`'s
 * `<body>` + `<main>` layout so a page composed here ports straight to Jinja.
 */
export function PageShell({ header, footer, children }: PageShellProps) {
  return (
    <div className="flex min-h-screen flex-col bg-slate-950 text-slate-100">
      {header}
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">
        {children}
      </main>
      {footer}
    </div>
  );
}
