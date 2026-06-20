import * as React from "react";

import { Badge } from "./Badge";

export interface CommandCardProps {
  /** The command name, rendered as `!name`. */
  name: string;
  /** One-line usage/summary. */
  usage?: string;
  /** Maturity — drives the status badge. */
  status?: "finished" | "in-progress";
}

/**
 * The signature command-reference row from /commands: the command name, a
 * maturity badge, and its one-line usage.
 */
export function CommandCard({
  name,
  usage,
  status = "finished",
}: CommandCardProps) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 px-4 py-3">
      <div className="flex items-center gap-3">
        <code className="font-semibold text-sky-300">!{name}</code>
        <Badge tone={status}>{status}</Badge>
        {usage ? (
          <span className="hidden truncate text-sm text-slate-400 sm:inline">
            {usage}
          </span>
        ) : null}
      </div>
    </div>
  );
}
