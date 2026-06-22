/// <reference types="vitest/config" />
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// Vite config for the runnable SPA (`build:app` → dist-app/). This is SEPARATE from
// the tsup library build (`build` → dist/, the component artifacts /design-sync ships):
// here we bundle src/app/main.tsx into a static HTML+JS+CSS site botsite can serve
// (PR 2). Relative base so the bundle works from any path under botsite/site/.
//
// `vitest/config`'s defineConfig is a superset of vite's, so it also carries the
// `test` block for the data-adapter smoke test (pure mappers → Node env, no DOM).
export default defineConfig({
  plugins: [react()],
  base: "./",
  build: {
    outDir: "dist-app",
    emptyOutDir: true,
  },
  test: {
    environment: "node",
    include: ["src/app/**/*.test.ts"],
  },
});
