/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      colors: {
        'poke-red': '#FF0000',
        'poke-blue': '#0558b1',
        'poke-blue-dark': '#0b4e95',
        'poke-yellow': '#FFDE00',
        'dark-bg': '#121212',
        'light-bg': '#FFFFFF',
      },
      fontFamily: {
        sans: ['CyGrotesk', 'sans-serif'],
      }
    },
  },
  plugins: [],
}

