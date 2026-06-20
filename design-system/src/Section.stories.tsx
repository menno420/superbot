import type { Meta, StoryObj } from "@storybook/react";

import { Section } from "./Section";

const meta: Meta<typeof Section> = {
  title: "Sections/Section",
  component: Section,
};
export default meta;

type Story = StoryObj<typeof Section>;

export const WithAction: Story = {
  args: {
    title: "What it does",
    action: { label: "All features →", href: "/features" },
    children: <p className="text-slate-300">Section content.</p>,
  },
};
export const Centered: Story = {
  args: {
    title: "How it works",
    centered: true,
    children: <p className="text-center text-slate-300">Centered content.</p>,
  },
};
