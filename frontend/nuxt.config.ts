export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',
  devtools: { enabled: true },
  components: [
    { path: '~/components/ui', pathPrefix: false },
    { path: '~/components/hexagram', pathPrefix: false },
    { path: '~/components', pathPrefix: false },
  ],
  modules: [
    '@nuxtjs/tailwindcss',
    '@nuxtjs/color-mode',
    '@pinia/nuxt',
    '@vite-pwa/nuxt',
  ],
  css: [
    '~/assets/styles/tokens.css',
  ],
  colorMode: {
    classSuffix: '',
    preference: 'dark',
    fallback: 'dark',
    storageKey: 'nuxt-color-mode',
  },
  app: {
    head: {
      title: 'YI-AI 易学AI系统',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: '东方变化学AI操作系统 - 易学推演与变化分析' },
        { name: 'theme-color', content: '#0a0a14' },
        { name: 'apple-mobile-web-app-capable', content: 'yes' },
        { name: 'apple-mobile-web-app-status-bar-style', content: 'black-translucent' },
      ],
      link: [
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
        { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&display=swap' },
        { rel: 'manifest', href: '/manifest.json' },
        { rel: 'icon', type: 'image/svg+xml', href: '/icon.svg' },
        { rel: 'apple-touch-icon', href: '/apple-touch-icon.png' },
      ],
    },
    pageTransition: {
      name: 'fade',
      mode: 'out-in',
    },
  },
  pwa: {
    registerType: 'autoUpdate',
    manifest: {
      name: 'YI-AI 易学AI系统',
      short_name: 'YI-AI',
      description: '东方变化学AI操作系统',
      theme_color: '#0a0a14',
      background_color: '#0a0a14',
      display: 'standalone',
      orientation: 'portrait',
      categories: ['lifestyle', 'education'],
      icons: [
        { src: '/icon-192.png', sizes: '192x192', type: 'image/png' },
        { src: '/icon-512.png', sizes: '512x512', type: 'image/png' },
        { src: '/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
      ],
    },
    workbox: {
      navigateFallback: '/',
      globPatterns: ['**/*.{js,css,html,png,svg,ico,woff2}'],
      runtimeCaching: [
        {
          urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
          handler: 'CacheFirst',
          options: {
            cacheName: 'google-fonts-cache',
            expiration: { maxEntries: 10, maxAgeSeconds: 60 * 60 * 24 * 365 },
            cacheableResponse: { statuses: [0, 200] },
          },
        },
        {
          urlPattern: /\/api\/.*$/i,
          handler: 'NetworkFirst',
          options: {
            cacheName: 'api-cache',
            expiration: { maxEntries: 100, maxAgeSeconds: 60 * 60 },
            cacheableResponse: { statuses: [0, 200] },
          },
        },
      ],
    },
    client: {
      installPrompt: true,
    },
    devOptions: {
      enabled: false,
    },
  },
  runtimeConfig: {
    public: {
      apiBase: (globalThis as any).process?.env?.API_BASE || 'http://localhost:8000',
    },
  },
  // 性能优化
  experimental: {
    payloadExtraction: true,
    renderJsonPayloads: true,
  },
  routeRules: {
    '/': { prerender: true },
    '/hexagram/**': { swr: 3600 },
    '/history': { isr: 60 },
  },
})
