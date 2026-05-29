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
        // 赛博东方配色 (引用设计token)
        gold: {
          50: '#fff9e6',
          100: '#fff0b3',
          200: '#ffe680',
          300: '#ffdc4d',
          400: '#ffd21a',
          500: '#d4a017',
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
          700: '#1a1a1a',
          800: '#121212',
          900: '#0a0a0a',
        },
        // 使用 CSS 变量的语义色
        yi: {
          void: 'var(--yi-black-void)',
          deep: 'var(--yi-black-deep)',
          surface: 'var(--yi-black-surface)',
          elevated: 'var(--yi-black-elevated)',
          gold: {
            bright: 'var(--yi-gold-bright)',
            DEFAULT: 'var(--yi-gold-primary)',
            muted: 'var(--yi-gold-muted)',
            ghost: 'var(--yi-gold-ghost)',
          },
          ink: {
            DEFAULT: 'var(--yi-ink-white)',
            light: 'var(--yi-ink-light)',
            medium: 'var(--yi-ink-medium)',
          },
        },
        // 五行配色
        element: {
          metal: '#c0c0c0',
          wood: '#228b22',
          water: '#1e90ff',
          fire: '#dc143c',
          earth: '#daa520',
        },
      },
      fontFamily: {
        chinese: ['"Noto Serif SC"', '"Source Han Serif SC"', 'serif'],
        display: ['"LXGW WenKai"', '"Noto Serif SC"', 'serif'],
        body: ['"Noto Sans SC"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
      },
      spacing: {
        'yi-1': 'var(--yi-space-1)',
        'yi-2': 'var(--yi-space-2)',
        'yi-3': 'var(--yi-space-3)',
        'yi-4': 'var(--yi-space-4)',
        'yi-6': 'var(--yi-space-6)',
        'yi-8': 'var(--yi-space-8)',
        'yi-12': 'var(--yi-space-12)',
      },
      borderRadius: {
        yi: 'var(--yi-radius-md)',
      },
      boxShadow: {
        yi: 'var(--yi-shadow-md)',
        'yi-lg': 'var(--yi-shadow-lg)',
        'yi-glow': 'var(--yi-shadow-glow)',
        'yi-cyber': 'var(--yi-shadow-cyber)',
      },
      transitionDuration: {
        yi: 'var(--yi-duration-normal)',
        'yi-fast': 'var(--yi-duration-fast)',
        'yi-slow': 'var(--yi-duration-slow)',
      },
      transitionTimingFunction: {
        'yi-expo': 'var(--yi-ease-out-expo)',
        'yi-back': 'var(--yi-ease-out-back)',
      },
      animation: {
        'spin-slow': 'spin 20s linear infinite',
        'pulse-gold': 'pulse-gold 2s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'ink-spread': 'ink-spread 1.5s var(--yi-ease-out-expo) forwards',
        'cyber-scan': 'cyber-scan 4s linear infinite',
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
        'ink-spread': {
          '0%': { transform: 'scale(0)', opacity: '0.8' },
          '100%': { transform: 'scale(1)', opacity: '0' },
        },
        'cyber-scan': {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
      },
    },
  },
  plugins: [],
} satisfies Config
