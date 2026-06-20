import * as React from "react";

export interface PillProps {
  /** Active (selected) styling — the highlighted filter. */
  active?: boolean;
  /** Render as a link to this href (a jump/anchor pill) instead of a button. */
  href?: string;
  /** Click handler when rendered as a button. */
  onClick?: () => void;
  children: React.ReactNode;
}

const BASE = "rounded-full px-3 py-1 text-xs font-medium";
const ACTIVE = "border border-sky-600 bg-sky-600/20 text-sky-300";
const INACTIVE =
  "border border-slate-700 text-slate-300 hover:border-slate-500";

/**
 * A rounded filter / jump chip. `/features` uses anchor pills (category jump
 * links); `/commands` uses button pills with an active state. Mirrors both.
 */
export function Pill({ active = false, href, onClick, children }: PillProps) {
  const cls = `${BASE} ${active ? ACTIVE : INACTIVE}`;
  return href ? (
    <a href={href} className={cls}>
      {children}
    </a>
  ) : (
    <button type="button" className={cls} onClick={onClick}>
      {children}
    </button>
  );
}
