import type { Meta, StoryObj } from "@storybook/react";

import { CapabilityBand } from "./CapabilityBand";

const meta: Meta<typeof CapabilityBand> = {
  title: "Sections/CapabilityBand",
  component: CapabilityBand,
};
export default meta;

type Story = StoryObj<typeof CapabilityBand>;

export const Default: Story = {
  args: {
    stats: [
      { value: 308, label: "commands", href: "/commands" },
      { value: 36, label: "feature areas", href: "/features" },
      { value: 8, label: "games", href: "/features" },
    ],
  },
};
