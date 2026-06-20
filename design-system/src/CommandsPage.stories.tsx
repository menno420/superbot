import type { Meta, StoryObj } from "@storybook/react";

import { CommandsPage } from "./CommandsPage";

const meta: Meta<typeof CommandsPage> = {
  title: "Pages/CommandsPage",
  component: CommandsPage,
  parameters: { layout: "fullscreen" },
};
export default meta;

type Story = StoryObj<typeof CommandsPage>;

export const Default: Story = {
  args: { build: { commit: "1f26d13", committedAt: "2026-06-20" } },
};
