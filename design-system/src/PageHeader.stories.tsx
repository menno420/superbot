import type { Meta, StoryObj } from "@storybook/react";

import { PageHeader } from "./PageHeader";

const meta: Meta<typeof PageHeader> = {
  title: "Layout/PageHeader",
  component: PageHeader,
};
export default meta;

type Story = StoryObj<typeof PageHeader>;

export const Plain: Story = {
  args: {
    title: "Features",
    subtitle: "36 feature areas across 8 categories — search or jump to one.",
  },
};
export const Bordered: Story = {
  args: {
    bordered: true,
    title: "What's new",
    badge: { label: "generated", title: "As of the last deploy." },
    subtitle: "New features, fixes and improvements. Hand-curated, newest first.",
  },
};
