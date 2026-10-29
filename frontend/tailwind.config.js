/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f5fa',
          100: '#e1ecf5',
          200: '#c3d9ea',
          500: '#1e4b7a',
          700: '#112d4e',
          800: '#0c223c',
          900: '#071628',
        }
      }
    },
  },
  plugins: [],
}
