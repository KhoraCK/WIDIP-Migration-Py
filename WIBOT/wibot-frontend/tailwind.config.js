/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'bg-primary': 'var(--bg-primary)',
        'bg-secondary': 'var(--bg-secondary)',
        'bg-user-msg': 'var(--bg-user-msg)',
        'bg-assistant-msg': 'var(--bg-assistant-msg)',
        'bg-code': 'var(--bg-code)',
        'text-primary': 'var(--text-primary)',
        'text-secondary': 'var(--text-secondary)',
        'accent': 'var(--accent)',
        'accent-hover': 'var(--accent-hover)',
        'border': 'var(--border)',
      },
      width: {
        'sidebar': 'var(--sidebar-width)',
      },
      height: {
        'header': 'var(--header-height)',
        'input-bar': 'var(--input-bar-height)',
      },
      animation: {
        'in': 'animate-in 0.2s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        'animate-in': {
          '0%': { opacity: '0', transform: 'translateY(-10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
