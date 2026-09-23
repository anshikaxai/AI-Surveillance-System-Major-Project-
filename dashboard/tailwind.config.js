/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        base: {
          900: '#0B1220',
          800: '#111A2E',
          700: '#1A2440',
          600: '#253053',
          500: '#3A4879',
        },
        accent: {
          green: '#10B981',
          amber: '#F59E0B',
          red: '#EF4444',
          cyan: '#06B6D4',
          violet: '#8B5CF6',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'monospace'],
      },
      boxShadow: {
        glow: '0 0 30px rgba(16,185,129,0.15)',
        card: '0 4px 20px rgba(0,0,0,0.4)',
      },
      keyframes: {
        pulse_slow: {
          '0%,100%': { opacity: 1 },
          '50%': { opacity: 0.5 },
        },
        slide_in: {
          from: { transform: 'translateY(8px)', opacity: 0 },
          to: { transform: 'translateY(0)', opacity: 1 },
        },
      },
      animation: {
        pulse_slow: 'pulse_slow 2s ease-in-out infinite',
        slide_in: 'slide_in 0.3s ease-out both',
      },
    },
  },
  plugins: [],
};
