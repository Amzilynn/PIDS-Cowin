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
          navy: '#0B1B2B',
          teal: '#4E8C8A',
          aqua: '#5CA3A1',
          slate: '#1E293B',
          accent: '#3B82F6',
        }
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        '3xl': '1.5rem',
        '4xl': '2rem',
      },
      backgroundImage: {
        'brand-gradient': 'linear-gradient(135deg, #0B1B2B 0%, #1E293B 100%)',
        'medical-gradient': 'linear-gradient(135deg, #4E8C8A 0%, #5CA3A1 100%)',
      }
    },
  },
  plugins: [],
}
