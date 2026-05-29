import type { Config } from 'tailwindcss'

export default {
  darkMode: 'class',
  content: [
    './components/**/*.{vue,js,ts}',
    './layouts/**/*.vue',
    './pages/**/*.vue',
    './app.vue',
  ],
  theme: {
    extend: {
      colors: {
        // 赛博东方配色
        gold: {
          50: '#fff9e6',
          100: '#fff0b3',
          200: '#ffe680',
          300: '#ffdc4d',
          400: '#ffd21a',
          500: '#d4a017',  // 主金色
          600: '#b8860b',
          700: '#8b6914',
          800: '#5f4b1d',
          900: '#332b0f',
        },
        ink: {
          50: '#f5f5f5',
          100: '#e8e8e8',
          200: '#d1d1d1',
          300: '#a3a3a3',
          400: '#757575',
          500: '#4a4a4a',
          600: '#2d2d2d',
          700: '#1a1a1a',  // 主背景
          800: '#121212',
          900: '#0a0a0a',
        },
        // 五行配色
        element: {
          metal: '#c0c0c0',  // 金 - 白银
          wood: '#228b22',   // 木 - 绿
          water: '#1e90ff',  // 水 - 蓝
          fire: '#dc143c',   // 火 - 红
          earth: '#daa520',  // 土 - 黄
        },
      },
      fontFamily: {
        chinese: ['"Noto Serif SC"', '"Source Han Serif SC"', 'serif'],
      },
      animation: {
        'spin-slow': 'spin 20s linear infinite',
        'pulse-gold': 'pulse-gold 2s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        'pulse-gold': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.6' },
        },
        'glow': {
          '0%': { boxShadow: '0 0 5px rgba(212, 160, 23, 0.5)' },
          '100%': { boxShadow: '0 0 20px rgba(212, 160, 23, 0.8)' },
        },
      },
    },
  },
  plugins: [],
} satisfies Config
