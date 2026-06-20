// CommonJS config in an ESM package ("type": "module"), so it must be .cjs —
// Vite's PostCSS loader reads .js here as ESM and `module.exports` would throw.
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
