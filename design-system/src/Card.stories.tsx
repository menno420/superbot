import type { Meta, StoryObj } from "@storybook/react";

import { Card } from "./Card";

const meta: Meta<typeof Card> = {
  title: "Components/Card",
  component: Card,
};
export default meta;

type Story = StoryObj<typeof Card>;

export const Default: Story = {
  args: {
    children: (
      <div>
        <h3 className="font-semibold text-slate-100">A surface</h3>
        <p className="mt-2 text-sm text-slate-400">
          The standard bordered card used across the site.
        </p>
      </div>
    ),
  },
};
