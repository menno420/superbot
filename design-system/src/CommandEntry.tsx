import * as React from "react";

import { Badge } from "./Badge";
import { CommandDetail, type CommandRecord } from "./CommandDetail";

export interface CommandEntryProps {
  /** The command to render. */
  command: CommandRecord;
  /** Start expanded (defaults to collapsed). */
  defaultOpen?: boolean;
}

/**
 * A clickable command on `/commands`: a native `<details>` whose summary shows
 * `!name`, a maturity badge and the one-line usage, expanding to the full
 * {@link CommandDetail}. Uses `<details>` so it works without JavaScript, exactly
 * like `botsite/templates/commands.html`.
 */
export function CommandEntry({
  command,
  defaultOpen = false,
}: CommandEntryProps) {
  const status = command.status ?? "finished";
  return (
    <details
      open={defaultOpen}
      className="group rounded-xl border border-slate-800 bg-slate-900/40 px-4 py-3 open:bg-slate-900/70"
    >
      <summary className="flex cursor-pointer list-none items-center gap-3">
        <code className="font-semibold text-sky-300">!{command.name}</code>
        <Badge tone={status}>{status}</Badge>
        {command.usage ? (
          <span className="hidden truncate text-sm text-slate-400 sm:inline">
            {command.usage}
          </span>
        ) : null}
        <span className="ml-auto text-xs text-slate-600 transition-transform group-open:rotate-90">
          ▸
        </span>
      </summary>
      <CommandDetail command={command} />
    </details>
  );
}
