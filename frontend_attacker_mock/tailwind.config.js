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
          orange: '#FF6600', // BOB primary
          blue: '#004A8F', // BOB secondary
        }
      }
    },
  },
  plugins: [],
}
