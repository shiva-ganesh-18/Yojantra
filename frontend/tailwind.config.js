/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        gov: {
          navy: {
            50: '#F0F4F8',
            100: '#D9E2EC',
            200: '#BCCCDC',
            300: '#9FB3C8',
            400: '#829AB1',
            500: '#627D98',
            600: '#486581',
            700: '#334E68',
            800: '#1E3A5F',
            900: '#0F253E',
            950: '#0A192F',
          },
          saffron: {
            50: '#FFF7ED',
            100: '#FFEDD5',
            200: '#FED7AA',
            300: '#FDBA74',
            400: '#FB923C',
            500: '#F97316',
            600: '#EA580C',
            700: '#C2410C',
            800: '#9A3412',
            900: '#7C2D12',
          },
          emerald: {
            50: '#ECFDF5',
            100: '#D1FAE5',
            200: '#A7F3D0',
            300: '#6EE7B7',
            400: '#34D399',
            500: '#10B981',
            600: '#059669',
            700: '#047857',
            800: '#065F46',
            900: '#064E3B',
          },
          slate: {
            card: '#FFFFFF',
            bg: '#F8FAFC',
            subtle: '#F1F5F9',
            border: '#E2E8F0',
            muted: '#64748B',
            dark: '#1E293B',
          }
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      boxShadow: {
        'gov': '0 1px 3px 0 rgba(15, 37, 62, 0.06), 0 1px 2px -1px rgba(15, 37, 62, 0.04)',
        'gov-md': '0 4px 6px -1px rgba(15, 37, 62, 0.07), 0 2px 4px -2px rgba(15, 37, 62, 0.05)',
        'gov-lg': '0 10px 15px -3px rgba(15, 37, 62, 0.08), 0 4px 6px -4px rgba(15, 37, 62, 0.04)',
        'gov-hover': '0 12px 20px -3px rgba(15, 37, 62, 0.12), 0 4px 6px -4px rgba(15, 37, 62, 0.06)',
      }
    },
  },
  plugins: [],
}
