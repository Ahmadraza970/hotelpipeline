/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: "#0f172a",
        panel: "#1e293b",
        "panel-2": "#283548",
        brand: "#0d9488",
        "brand-hover": "#0d8577",
        critical: "#fca5a5",
        high: "#fb9225",
        medium: "#fcd34d",
        low: "#93c5fd",
        info: "#a7f3d0",
      },
      fontFamily: { mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"] },
    },
  },
  plugins: [],
};
