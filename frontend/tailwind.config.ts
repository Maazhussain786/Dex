import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0e1116",
        panel: "#171b22",
        line: "#2a303a",
        mint: "#4fd1b8",
        brass: "#d6a84f",
        coral: "#ee6f6f",
        violet: "#9b87f5"
      }
    }
  },
  plugins: []
};

export default config;
