import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'Yojantra',
        short_name: 'Yojantra',
        description: 'Your intelligent path to government schemes',
        theme_color: '#0b192c',
        background_color: '#ffffff',
        display: 'standalone',
        scope: '/',
        start_url: '/',
        icons: [
          { src: '/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icon-512.png', sizes: '512x512', type: 'image/png' }
        ]
      },
      workbox: {
        runtimeCaching: [
          {
            urlPattern: ({ url }) => url.pathname.startsWith('/schemes') || url.pathname.startsWith('/csc'),
            handler: 'NetworkFirst',
            options: {
              cacheName: 'schemes-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 60 * 24 * 3, // 3 days
              },
              cacheableResponse: {
                statuses: [0, 200],
              },
            },
          },
        ],
      },
      devOptions: {
        enabled: false,
      },
    })
  ],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-ui': ['lucide-react'],
          'vendor-firebase': ['firebase/app', 'firebase/auth'],
          'vendor-query': ['react-query', 'axios', 'zustand'],
        }
      }
    },
    chunkSizeWarningLimit: 600
  },
  server: {
    port: process.env.PORT ? parseInt(process.env.PORT, 10) : 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      }
    }
  }
});
