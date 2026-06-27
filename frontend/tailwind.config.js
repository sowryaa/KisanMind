/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        darkBg: "#0d0d0d",
        darkSurface: "#1a1a1a",
        farmGreen: "#22c55e",
        farmGreenDark: "#16a34a",
      },
    },
  },
  plugins: [],
}
