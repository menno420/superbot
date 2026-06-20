import type { Meta, StoryObj } from "@storybook/react";

import { SiteFooter } from "./SiteFooter";

const meta: Meta<typeof SiteFooter> = {
  title: "Layout/SiteFooter",
  component: SiteFooter,
  parameters: { layout: "fullscreen" },
};
export default meta;

type Story = StoryObj<typeof SiteFooter>;

export const WithBuild: Story = {
  args: { build: { commit: "1f26d13", committedAt: "2026-06-20" } },
};
export const NoBuild: Story = {};
