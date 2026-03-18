import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    // Dev server proxy — used only when running `npm run dev` locally
    port: 5173,
    proxy: {
      '/api': {
        target:       'http://localhost:8000',
        changeOrigin: true,
        timeout:      0,
        proxyTimeout: 0,
      },
      '/media': {
        target:       'http://localhost:8000',
        changeOrigin: true,
        timeout:      0,
        proxyTimeout: 0,
      },
    },
  },
  build: {
    outDir:   'dist',
    sourcemap: false,
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks: {
          vue:      ['vue', 'vue-router', 'pinia'],
          primevue: ['primevue'],
          hlsjs:    ['hls.js'],
        },
      },
    },
  },
})
