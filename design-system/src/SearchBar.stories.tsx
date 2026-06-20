import type { Meta, StoryObj } from "@storybook/react";

import { SearchBar } from "./SearchBar";

const meta: Meta<typeof SearchBar> = {
  title: "Components/SearchBar",
  component: SearchBar,
  args: { placeholder: "Search features…" },
};
export default meta;

type Story = StoryObj<typeof SearchBar>;

export const Default: Story = {};
