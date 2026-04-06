/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'md-primary': 'var(--color-md-primary)',
        'md-on-primary': 'var(--color-md-on-primary)',
        'md-secondary-container': 'var(--color-md-secondary-container)',
        'md-on-secondary-container': 'var(--color-md-on-secondary-container)',
        'md-tertiary': 'var(--color-md-tertiary)',
        'md-on-tertiary': 'var(--color-md-on-tertiary)',
        'md-surface': 'var(--color-md-surface)',
        'md-surface-container': 'var(--color-md-surface-container)',
        'md-surface-container-low': 'var(--color-md-surface-container-low)',
        'md-on-background': 'var(--color-md-on-background)',
        'md-on-surface-variant': 'var(--color-md-on-surface-variant)',
        'md-outline': 'var(--color-md-outline)',
      },
      fontFamily: {
        sans: ['Roboto', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        'pill': '9999px',
        'card': '24px',
        'hero': '48px',
        'dialog': '28px',
      },
      transitionTimingFunction: {
        'md-emphasized': 'cubic-bezier(0.2, 0, 0, 1)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'shimmer': 'shimmer 2s linear infinite',
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        }
      }
    },
  },
  plugins: [],
}
