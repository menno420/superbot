import type { Meta, StoryObj } from "@storybook/react";

import { FeaturesPage } from "./FeaturesPage";

const meta: Meta<typeof FeaturesPage> = {
  title: "Pages/FeaturesPage",
  component: FeaturesPage,
  parameters: { layout: "fullscreen" },
};
export default meta;

type Story = StoryObj<typeof FeaturesPage>;

export const Default: Story = {
  args: { build: { commit: "1f26d13", committedAt: "2026-06-20" } },
};
