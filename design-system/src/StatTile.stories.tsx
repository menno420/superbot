import type { Meta, StoryObj } from "@storybook/react";

import { StatTile } from "./StatTile";

const meta: Meta<typeof StatTile> = {
  title: "Components/StatTile",
  component: StatTile,
};
export default meta;

type Story = StoryObj<typeof StatTile>;

export const Commands: Story = { args: { value: 120, label: "commands" } };
export const Band: Story = {
  render: () => (
    <div className="grid max-w-2xl grid-cols-3 gap-4">
      <StatTile value={120} label="commands" href="#" />
      <StatTile value={18} label="feature areas" href="#" />
      <StatTile value={9} label="games" href="#" />
    </div>
  ),
};
