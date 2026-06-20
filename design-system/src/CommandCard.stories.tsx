import type { Meta, StoryObj } from "@storybook/react";

import { CommandCard } from "./CommandCard";

const meta: Meta<typeof CommandCard> = {
  title: "Components/CommandCard",
  component: CommandCard,
};
export default meta;

type Story = StoryObj<typeof CommandCard>;

export const Finished: Story = {
  args: { name: "ping", usage: "Check the bot is alive", status: "finished" },
};
export const InProgress: Story = {
  args: { name: "tournament", usage: "Run a bracket", status: "in-progress" },
};
