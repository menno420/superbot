import type { Meta, StoryObj } from "@storybook/react";

import { ButtonLink } from "./ButtonLink";

const meta: Meta<typeof ButtonLink> = {
  title: "Components/ButtonLink",
  component: ButtonLink,
  args: { children: "Add to Discord", href: "#" },
};
export default meta;

type Story = StoryObj<typeof ButtonLink>;

export const Primary: Story = { args: { variant: "primary" } };
export const Secondary: Story = {
  args: { variant: "secondary", children: "Explore features" },
};
