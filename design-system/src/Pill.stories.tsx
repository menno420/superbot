import type { Meta, StoryObj } from "@storybook/react";

import { Pill } from "./Pill";

const meta: Meta<typeof Pill> = {
  title: "Components/Pill",
  component: Pill,
  args: { children: "games" },
};
export default meta;

type Story = StoryObj<typeof Pill>;

export const Inactive: Story = {};
export const Active: Story = { args: { active: true, children: "All" } };
export const AsLink: Story = { args: { href: "#cat-games", children: "games" } };
