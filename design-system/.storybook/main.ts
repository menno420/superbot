import type { StorybookConfig } from "@storybook/react-vite";

const config: StorybookConfig = {
  stories: ["../src/**/*.stories.@(ts|tsx)"],
  // Storybook 9+ folds the former addon-essentials (controls, actions, backgrounds,
  // viewport, …) into core, so no separate essentials package is installed.
  addons: [],
  framework: { name: "@storybook/react-vite", options: {} },
};

export default config;
