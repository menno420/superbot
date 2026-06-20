// CommonJS config in an ESM package ("type": "module") → must be .cjs.
/** @type {import('tailwindcss').Config} */
module.exports = {
  // Scan the component sources so the compiled styles.css carries exactly the
  // utilities the components use. Mirrors the live botsite's Tailwind palette
  // (slate / indigo / sky / emerald / amber) so the design system reflects what
  // actually ships today.
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {},
  },
  plugins: [],
};
