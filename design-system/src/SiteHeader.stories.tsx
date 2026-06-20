import type { Meta, StoryObj } from "@storybook/react";

import { SiteHeader } from "./SiteHeader";

const meta: Meta<typeof SiteHeader> = {
  title: "Layout/SiteHeader",
  component: SiteHeader,
  parameters: { layout: "fullscreen" },
  args: { addUrl: "#" },
};
export default meta;

type Story = StoryObj<typeof SiteHeader>;

export const Default: Story = {};
export const ActiveFeatures: Story = { args: { active: "features" } };
export const NoBuild: Story = { args: { hasBuild: false } };
