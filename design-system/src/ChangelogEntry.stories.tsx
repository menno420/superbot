import type { Meta, StoryObj } from "@storybook/react";

import { ChangelogEntry } from "./ChangelogEntry";

const meta: Meta<typeof ChangelogEntry> = {
  title: "Sections/ChangelogEntry",
  component: ChangelogEntry,
};
export default meta;

type Story = StoryObj<typeof ChangelogEntry>;

export const New: Story = {
  args: {
    kind: "feature",
    title: "New games hub",
    summary: "All the games in one place.",
  },
};
export const Fixed: Story = {
  args: { kind: "fix", title: "Fixed the submit button", url: "#" },
};
