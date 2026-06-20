import * as React from "react";

import type { CommandRecord } from "./CommandDetail";
import { CommandEntry } from "./CommandEntry";
import { PageHeader } from "./PageHeader";
import { PageShell } from "./PageShell";
import { Pill } from "./Pill";
import { SearchBar } from "./SearchBar";
import { SiteFooter, type BuildMeta } from "./SiteFooter";
import { SiteHeader } from "./SiteHeader";

export interface CommandCategoryGroup {
  /** Category name (e.g. "games"). */
  category: string;
  /** Commands in this category. */
  commands: CommandRecord[];
}

export interface CommandsPageProps {
  /** The "Add to Discord" install URL. */
  addUrl?: string;
  /** Command categories to show. */
  groups?: CommandCategoryGroup[];
  /** Deployed-build metadata for the footer/header. */
  build?: BuildMeta;
}

// Sample defaults so the page renders standalone in Storybook / on the canvas.
const DEFAULT_GROUPS: CommandCategoryGroup[] = [
  {
    category: "games",
    commands: [
      {
        name: "blackjack",
        usage: "!blackjack <bet>",
        status: "finished",
        description: "Start a game of blackjack against the bot.",
        aliases: ["bj"],
        examples: ["!blackjack 100"],
      },
      {
        name: "rps",
        usage: "!rps @user",
        status: "finished",
        description: "Challenge a member to rock-paper-scissors.",
        examples: ["!rps @friend"],
      },
    ],
  },
  {
    category: "moderation",
    commands: [
      {
        name: "warn",
        usage: "!warn @user <reason>",
        status: "finished",
        description: "Issue a warning to a member.",
        permissions: "moderators",
        examples: ["!warn @user spamming"],
      },
      {
        name: "automod",
        usage: "!automod",
        status: "in-progress",
        description: "Configure automatic moderation rules.",
        permissions: "admins",
      },
    ],
  },
];

/**
 * The full `/commands` reference page — searchable, category filter pills, and a
 * list of expandable {@link CommandEntry} cards. Mirrors
 * `botsite/templates/commands.html`. Renders standalone with sample data.
 */
export function CommandsPage({
  addUrl = "#",
  groups = DEFAULT_GROUPS,
  build,
}: CommandsPageProps) {
  const all = groups.flatMap((g) => g.commands);
  return (
    <PageShell
      header={
        <SiteHeader
          active="commands"
          addUrl={addUrl}
          hasBuild={Boolean(build?.commit)}
        />
      }
      footer={<SiteFooter build={build} />}
    >
      <PageHeader
        title="Commands"
        subtitle={`${all.length} commands across ${groups.length} categories. Click any command for details — search or filter to find one fast.`}
      />
      <div className="mb-6 space-y-3">
        <SearchBar placeholder="Search commands, aliases, descriptions…" />
        <div className="flex flex-wrap gap-2">
          <Pill active>All</Pill>
          {groups.map((g) => (
            <Pill key={g.category}>{g.category}</Pill>
          ))}
        </div>
      </div>
      <div className="space-y-2">
        {all.map((cmd) => (
          <CommandEntry key={cmd.name} command={cmd} />
        ))}
      </div>
    </PageShell>
  );
}
