import type { Preview } from "@storybook/react";

// Tailwind utilities for the rendered components (processed via postcss).
import "../src/styles.css";

const preview: Preview = {
  parameters: {
    backgrounds: {
      default: "superbot-dark",
      values: [{ name: "superbot-dark", value: "#020617" }],
    },
    controls: { matchers: { color: /(background|color)$/i, date: /Date$/i } },
  },
};

export default preview;
