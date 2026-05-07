/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
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
        },
        ivory: {
          DEFAULT: '#F5F0E8',
          100: '#FAF7F2',
          200: '#F5F0E8',
          300: '#EDE4D4',
        },
        stone: {
          400: '#A8A29E',
          500: '#78716C',
          600: '#57534E',
          700: '#44403C',
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
      typography: ({ theme }) => ({
        invert: {
          css: {
            '--tw-prose-body': theme('colors.stone.400'),
            '--tw-prose-headings': theme('colors.ivory.200'),
            '--tw-prose-links': theme('colors.gold.400'),
            '--tw-prose-bold': theme('colors.ivory.100'),
            '--tw-prose-quotes': theme('colors.stone.400'),
            '--tw-prose-quote-borders': theme('colors.gold.400'),
            '--tw-prose-bullets': theme('colors.gold.400'),
            '--tw-prose-counters': theme('colors.gold.400'),
            '--tw-prose-hr': theme('colors.surface.border'),
            '--tw-prose-th-borders': theme('colors.surface.border'),
            '--tw-prose-td-borders': theme('colors.surface.border'),
          },
        },
      }),
    },
  },
  plugins: [],
};
