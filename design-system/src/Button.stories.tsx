import type { Meta, StoryObj } from "@storybook/react";

import { Button } from "./Button";

const meta: Meta<typeof Button> = {
  title: "Components/Button",
  component: Button,
  args: { children: "Add to Discord" },
};
export default meta;

type Story = StoryObj<typeof Button>;

export const Primary: Story = { args: { variant: "primary" } };
export const Secondary: Story = {
  args: { variant: "secondary", children: "Explore features" },
};
