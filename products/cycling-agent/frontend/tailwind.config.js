/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#f4efe3",
        parchment: "#fbf7ee",
        ink: "#243126",
        muted: "#5f665f",
        line: "#d8d1c4",
        moss: "#6a8a68",
        river: "#5a7d8c",
        amber: "#c96b3c",
      },
      fontFamily: {
        display: ["Iowan Old Style", "Songti SC", "Noto Serif CJK SC", "Georgia", "serif"],
        body: ["Avenir Next", "PingFang SC", "Hiragino Sans GB", "Arial", "sans-serif"],
      },
      boxShadow: {
        paper: "0 20px 50px rgba(28, 37, 29, 0.08)",
      },
    },
  },
  plugins: [],
};
