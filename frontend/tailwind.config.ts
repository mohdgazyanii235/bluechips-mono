import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Bluechips London design system
        black: {
          DEFAULT: '#0A0A0A',
          50: '#1A1A1A',
          100: '#141414',
          200: '#0F0F0F',
        },
        gold: {
          DEFAULT: '#C9A84C',
          50: '#F7F0DC',
          100: '#EFE0B9',
          200: '#E0C882',
          300: '#D4B562',
          400: '#C9A84C',
          500: '#B8943A',
          600: '#9A7B2E',
          700: '#7C6224',
          800: '#5E4A1B',
          900: '#3F3112',
        },
        ivory: {
          DEFAULT: '#F5F0E8',
          50: '#FDFCFA',
          100: '#FAF7F2',
          200: '#F5F0E8',
          300: '#EDE4D4',
          400: '#E0D4BC',
        },
        surface: {
          DEFAULT: '#111111',
          card: '#161616',
          border: '#2A2A2A',
          hover: '#1E1E1E',
        },
      },
      fontFamily: {
        serif: ['"Playfair Display"', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      backgroundImage: {
        'gold-gradient': 'linear-gradient(135deg, #C9A84C 0%, #E0C882 50%, #C9A84C 100%)',
        'dark-gradient': 'linear-gradient(180deg, #0A0A0A 0%, #141414 100%)',
        'card-gradient': 'linear-gradient(180deg, transparent 40%, rgba(10,10,10,0.95) 100%)',
        'hero-gradient': 'linear-gradient(180deg, rgba(10,10,10,0.3) 0%, rgba(10,10,10,0.7) 60%, #0A0A0A 100%)',
      },
      boxShadow: {
        'gold': '0 0 20px rgba(201,168,76,0.15)',
        'gold-strong': '0 0 40px rgba(201,168,76,0.3)',
        'card': '0 4px 24px rgba(0,0,0,0.4)',
        'card-hover': '0 8px 40px rgba(0,0,0,0.6)',
      },
      animation: {
        'shimmer': 'shimmer 2s infinite',
        'pulse-gold': 'pulse-gold 2s infinite',
        'fade-in': 'fade-in 0.4s ease-out',
        'slide-up': 'slide-up 0.4s ease-out',
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        'pulse-gold': {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(201,168,76,0.4)' },
          '50%': { boxShadow: '0 0 0 8px rgba(201,168,76,0)' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'slide-up': {
          '0%': { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      borderRadius: {
        'xl': '12px',
        '2xl': '16px',
      },
    },
  },
  plugins: [],
}

export default config
