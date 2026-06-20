import * as React from "react";

export interface PlannedIdea {
  /** Short status label (e.g. "planned"). */
  status: string;
  /** The idea title. */
  title: string;
}

export interface CommandRecord {
  /** Command name, rendered as `!name`. */
  name: string;
  /** One-line usage/summary. */
  usage?: string;
  /** Maturity — drives the status badge. */
  status?: "finished" | "in-progress";
  /** Full description (first paragraph). */
  description?: string;
  /** What the command is good for. */
  useCases?: string[];
  /** Alternate invocations. */
  aliases?: string[];
  /** Who may run it (defaults to "anyone"). */
  permissions?: string;
  /** Cooldown text, or null/undefined when none. */
  cooldown?: string | null;
  /** Real `!command …` example invocations. */
  examples?: string[];
  /** Curated note. */
  notes?: string;
  /** "What's planned" teasers. */
  plannedIdeas?: PlannedIdea[];
}

function DetailSection({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <div className="mb-1 text-xs uppercase tracking-wide text-slate-500">
        {label}
      </div>
      {children}
    </div>
  );
}

/**
 * The expanded body of a command on `/commands` — description, use-cases, the
 * aliases / permissions / cooldown grid, examples, notes, and "what's planned".
 * Mirrors `botsite/templates/_command_detail.html`; every field degrades to a
 * friendly omission. Pair with {@link CommandEntry} for the clickable card.
 */
export function CommandDetail({ command }: { command: CommandRecord }) {
  const {
    description,
    usage,
    useCases,
    aliases,
    permissions,
    cooldown,
    examples,
    notes,
    plannedIdeas,
  } = command;
  return (
    <div className="mt-3 space-y-3 text-sm">
      {description ? (
        <p className="text-slate-300">{description}</p>
      ) : usage ? (
        <p className="text-slate-300">{usage}</p>
      ) : null}

      {useCases && useCases.length > 0 ? (
        <DetailSection label="Use cases">
          <ul className="list-inside list-disc space-y-0.5 text-slate-300">
            {useCases.map((uc, i) => (
              <li key={i}>{uc}</li>
            ))}
          </ul>
        </DetailSection>
      ) : null}

      <dl className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-500">
            Aliases
          </dt>
          <dd className="mt-0.5">
            {aliases && aliases.length > 0 ? (
              <span className="flex flex-wrap gap-1">
                {aliases.map((alias) => (
                  <code
                    key={alias}
                    className="rounded bg-slate-800 px-1.5 py-0.5 text-xs text-sky-300"
                  >
                    !{alias}
                  </code>
                ))}
              </span>
            ) : (
              <span className="text-slate-500">none</span>
            )}
          </dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-500">
            Permissions
          </dt>
          <dd className="mt-0.5 text-slate-300">{permissions ?? "anyone"}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-500">
            Cooldown
          </dt>
          <dd className="mt-0.5 text-slate-300">{cooldown ?? "—"}</dd>
        </div>
      </dl>

      {examples && examples.length > 0 ? (
        <DetailSection label="Examples">
          <ul className="space-y-1">
            {examples.map((example, i) => (
              <li key={i}>
                <code className="rounded bg-slate-800 px-2 py-1 text-xs text-emerald-300">
                  {example}
                </code>
              </li>
            ))}
          </ul>
        </DetailSection>
      ) : null}

      {notes ? (
        <DetailSection label="Notes">
          <p className="text-slate-300">{notes}</p>
        </DetailSection>
      ) : null}

      {plannedIdeas && plannedIdeas.length > 0 ? (
        <DetailSection label="What's planned">
          <ul className="space-y-1">
            {plannedIdeas.map((idea, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="mt-0.5 shrink-0 rounded bg-violet-900/60 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-violet-300">
                  {idea.status}
                </span>
                <span className="text-slate-300">{idea.title}</span>
              </li>
            ))}
          </ul>
        </DetailSection>
      ) : null}
    </div>
  );
}
