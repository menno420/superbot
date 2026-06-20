import type { Meta, StoryObj } from "@storybook/react";

import { Hero } from "./Hero";

const meta: Meta<typeof Hero> = {
  title: "Sections/Hero",
  component: Hero,
  parameters: { layout: "fullscreen" },
};
export default meta;

type Story = StoryObj<typeof Hero>;

export const Default: Story = {
  args: {
    primary: { label: "Add to Discord", href: "#" },
    secondary: { label: "Explore features", href: "/features" },
  },
};
