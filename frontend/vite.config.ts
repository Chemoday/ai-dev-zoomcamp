import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Dev runs same-origin: /api is proxied to Django, so no CORS setup is needed
// here or there. In production Django serves the built index.html and /api
// from the same host, so the app never needs an absolute API URL.
export default defineConfig({
  plugins: [vue()],
  resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } },
  server: {
    port: 5173,
    proxy: { '/api': { target: process.env.DJANGO_ORIGIN ?? 'http://localhost:8000', changeOrigin: true } },
  },
  build: { outDir: 'dist', emptyOutDir: true },
})
