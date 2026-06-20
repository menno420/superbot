import type { Meta, StoryObj } from "@storybook/react";

import { ChangelogPage } from "./ChangelogPage";

const meta: Meta<typeof ChangelogPage> = {
  title: "Pages/ChangelogPage",
  component: ChangelogPage,
  parameters: { layout: "fullscreen" },
};
export default meta;

type Story = StoryObj<typeof ChangelogPage>;

export const Default: Story = {
  args: { build: { commit: "1f26d13", committedAt: "2026-06-20" } },
};
