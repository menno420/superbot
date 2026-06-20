import { defineConfig } from "tsup";

// esbuild-based build → dist/ (ESM + .d.ts). This compiled output is what
// /design-sync converts and uploads to Claude Design (it ships the built dist,
// never a reimplementation). React stays external (it's a peer dependency).
export default defineConfig({
  entry: ["src/index.ts"],
  format: ["esm"],
  dts: true,
  clean: true,
  sourcemap: true,
  external: ["react", "react-dom"],
  outDir: "dist",
});
