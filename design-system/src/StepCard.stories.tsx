import type { Meta, StoryObj } from "@storybook/react";

import { StepCard } from "./StepCard";

const meta: Meta<typeof StepCard> = {
  title: "Sections/StepCard",
  component: StepCard,
  args: { number: "1", title: "Invite", body: "Add SuperBot to your server." },
};
export default meta;

type Story = StoryObj<typeof StepCard>;

export const Default: Story = {};
