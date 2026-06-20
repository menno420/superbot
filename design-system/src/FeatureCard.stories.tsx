import type { Meta, StoryObj } from "@storybook/react";

import { FeatureCard } from "./FeatureCard";

const meta: Meta<typeof FeatureCard> = {
  title: "Components/FeatureCard",
  component: FeatureCard,
};
export default meta;

type Story = StoryObj<typeof FeatureCard>;

export const Games: Story = {
  args: {
    category: "games",
    items: [
      { emoji: "🃏", name: "Blackjack" },
      { emoji: "✊", name: "Rock Paper Scissors" },
      { emoji: "🎲", name: "Dice" },
    ],
  },
};
