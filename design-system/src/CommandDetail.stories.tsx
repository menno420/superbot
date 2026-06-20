import type { Meta, StoryObj } from "@storybook/react";

import { CommandDetail } from "./CommandDetail";

const meta: Meta<typeof CommandDetail> = {
  title: "Sections/CommandDetail",
  component: CommandDetail,
};
export default meta;

type Story = StoryObj<typeof CommandDetail>;

export const Default: Story = {
  args: {
    command: {
      name: "blackjack",
      description: "Start a game of blackjack against the bot.",
      useCases: ["Have fun", "Wager points"],
      aliases: ["bj"],
      permissions: "anyone",
      examples: ["!blackjack 100"],
      plannedIdeas: [{ status: "planned", title: "Multiplayer tables" }],
    },
  },
};
