import type { Meta, StoryObj } from "@storybook/react";

import { Badge } from "./Badge";

const meta: Meta<typeof Badge> = {
  title: "Components/Badge",
  component: Badge,
};
export default meta;

type Story = StoryObj<typeof Badge>;

export const Finished: Story = { args: { tone: "finished", children: "finished" } };
export const InProgress: Story = {
  args: { tone: "in-progress", children: "in-progress" },
};
export const Game: Story = { args: { tone: "game", children: "game" } };
export const ChangelogKinds: Story = {
  render: () => (
    <div className="flex gap-2">
      <Badge tone="new">New</Badge>
      <Badge tone="improved">Improved</Badge>
      <Badge tone="fixed">Fixed</Badge>
    </div>
  ),
};
