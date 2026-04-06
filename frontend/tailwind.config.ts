import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f172a",
        mist: "#f1f5f9",
        steel: "#1e293b",
        signal: "#0f766e",
        amber: "#b45309",
        danger: "#b91c1c",
      },
      boxShadow: {
        panel: "0 20px 60px -30px rgba(15, 23, 42, 0.35)",
      },
      backgroundImage: {
        "grid-fade":
          "linear-gradient(rgba(15,23,42,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(15,23,42,0.04) 1px, transparent 1px)",
      },
      fontFamily: {
        sans: ["IBM Plex Sans", "Avenir Next", "Segoe UI", "sans-serif"],
        mono: ["IBM Plex Mono", "SFMono-Regular", "monospace"],
      },
    },
  },
  plugins: [],
} satisfies Config;
