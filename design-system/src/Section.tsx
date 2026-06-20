import * as React from "react";

export interface SectionAction {
  /** Link label (e.g. "All features →"). */
  label: string;
  /** Link destination. */
  href: string;
}

export interface SectionProps {
  /** Section heading. */
  title?: string;
  /** Optional right-aligned action link (renders the title row as space-between). */
  action?: SectionAction;
  /** Center a plain title (used by "How it works"). */
  centered?: boolean;
  children: React.ReactNode;
}

/**
 * A content section with the site's two heading styles: a left title with an
 * optional right-aligned action link ("What it does" / "All features →"), or a
 * centered title ("How it works"). Mirrors the section headers in
 * `botsite/index.html`. Carries the `mt-14` rhythm between sections.
 */
export function Section({
  title,
  action,
  centered = false,
  children,
}: SectionProps) {
  return (
    <section className="mt-14">
      {title &&
        (action ? (
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-semibold">{title}</h2>
            <a
              href={action.href}
              className="text-sm text-sky-400 hover:text-sky-300"
            >
              {action.label}
            </a>
          </div>
        ) : (
          <h2
            className={`mb-4 text-xl font-semibold ${centered ? "text-center" : ""}`}
          >
            {title}
          </h2>
        ))}
      {children}
    </section>
  );
}
