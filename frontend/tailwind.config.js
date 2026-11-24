/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        paper: '#f7f5f0',
        ink: {
          900: '#22231f',
          800: '#34352e',
        },
        clay: {
          50: '#fff7ed',
          100: '#ffedd5',
          200: '#fed7aa',
          500: '#c65d2e',
          600: '#ad4c25',
          700: '#913d20',
          800: '#78331f',
        },
        leaf: {
          50: '#f0fdf4',
          100: '#dcfce7',
          600: '#27834b',
          800: '#166534',
        },
        brand: {
          50: '#f0f7ff',
          100: '#e0effe',
          200: '#b9ddfd',
          500: '#0284c7',
          600: '#0369a1',
          700: '#075985',
          800: '#0c4a6e',
          900: '#082f49',
        },
      },
      boxShadow: {
        card: '0 2px 10px rgba(37, 35, 29, 0.04)',
        soft: '0 16px 40px rgba(37, 35, 29, 0.08)',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
