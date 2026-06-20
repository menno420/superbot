import type { Meta, StoryObj } from "@storybook/react";

import { CommandEntry } from "./CommandEntry";

const meta: Meta<typeof CommandEntry> = {
  title: "Sections/CommandEntry",
  component: CommandEntry,
};
export default meta;

type Story = StoryObj<typeof CommandEntry>;

export const Collapsed: Story = {
  args: {
    command: {
      name: "blackjack",
      usage: "!blackjack <bet>",
      status: "finished",
      description: "Play blackjack against the bot.",
      aliases: ["bj"],
      examples: ["!blackjack 100"],
    },
  },
};
export const Expanded: Story = {
  args: {
    defaultOpen: true,
    command: {
      name: "automod",
      usage: "!automod",
      status: "in-progress",
      description: "Configure automatic moderation rules.",
      permissions: "admins",
    },
  },
};
