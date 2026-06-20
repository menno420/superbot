import type { Meta, StoryObj } from "@storybook/react";

import { LandingPage } from "./LandingPage";

const meta: Meta<typeof LandingPage> = {
  title: "Pages/LandingPage",
  component: LandingPage,
  parameters: { layout: "fullscreen" },
};
export default meta;

type Story = StoryObj<typeof LandingPage>;

// The whole marketing landing page composed from real components — the canonical
// surface Claude Design edits (maps 1:1 onto botsite/index.html + base.html chrome).
export const Default: Story = {
  args: {
    addUrl: "#",
    build: { commit: "1f26d13", committedAt: "2026-06-20" },
  },
};
