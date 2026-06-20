import type { Meta, StoryObj } from "@storybook/react";

import { StatusPage } from "./StatusPage";

const meta: Meta<typeof StatusPage> = {
  title: "Pages/StatusPage",
  component: StatusPage,
  parameters: { layout: "fullscreen" },
};
export default meta;

type Story = StoryObj<typeof StatusPage>;

export const Default: Story = {};
