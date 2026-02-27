/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        mono: ['"Courier New"', 'Courier', 'monospace'],
      },
      colors: {
        aoe: {
          gold: '#c8a84b',
          dark: '#1a1208',
          panel: '#2a1f0a',
          border: '#6b5320',
          text: '#d4c06a',
        },
      },
    },
  },
  plugins: [],
}
