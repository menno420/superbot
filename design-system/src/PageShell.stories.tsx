import type { Meta, StoryObj } from "@storybook/react";

import { PageShell } from "./PageShell";
import { SiteFooter } from "./SiteFooter";
import { SiteHeader } from "./SiteHeader";

const meta: Meta<typeof PageShell> = {
  title: "Layout/PageShell",
  component: PageShell,
  parameters: { layout: "fullscreen" },
};
export default meta;

type Story = StoryObj<typeof PageShell>;

export const WithChrome: Story = {
  render: () => (
    <PageShell
      header={<SiteHeader active="features" />}
      footer={
        <SiteFooter build={{ commit: "1f26d13", committedAt: "2026-06-20" }} />
      }
    >
      <p className="text-slate-300">Page content goes here.</p>
    </PageShell>
  ),
};
