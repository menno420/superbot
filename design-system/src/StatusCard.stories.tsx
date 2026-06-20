import type { Meta, StoryObj } from "@storybook/react";

import { StatusCard } from "./StatusCard";

const meta: Meta<typeof StatusCard> = {
  title: "Sections/StatusCard",
  component: StatusCard,
};
export default meta;

type Story = StoryObj<typeof StatusCard>;

export const Online: Story = {
  args: {
    build: {
      commit: "1f26d13",
      committedAt: "2026-06-20",
      subject: "compose the full site",
    },
  },
};
export const Unavailable: Story = { args: { build: undefined } };
