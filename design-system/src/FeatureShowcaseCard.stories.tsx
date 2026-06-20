import type { Meta, StoryObj } from "@storybook/react";

import { FeatureShowcaseCard } from "./FeatureShowcaseCard";

const meta: Meta<typeof FeatureShowcaseCard> = {
  title: "Sections/FeatureShowcaseCard",
  component: FeatureShowcaseCard,
};
export default meta;

type Story = StoryObj<typeof FeatureShowcaseCard>;

export const Game: Story = {
  args: {
    emoji: "🃏",
    name: "Blackjack",
    description: "Play blackjack against the bot.",
    tags: ["cards", "casino"],
    isGame: true,
  },
};
export const Plain: Story = {
  args: {
    emoji: "🛡️",
    name: "Auto-moderation",
    description: "Filter spam and unwanted content automatically.",
    tags: ["safety"],
  },
};
