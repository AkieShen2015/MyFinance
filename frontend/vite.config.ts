import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  cacheDir: process.env.VITE_CACHE_DIR ?? 'node_modules/.vite',
  plugins: [react(), tailwindcss()],
  server: {
    hmr: {
      clientPort: Number(process.env.VITE_HMR_CLIENT_PORT ?? 5173),
    },
    watch: {
      usePolling: true,
      interval: 300,
    },
    proxy: {
      '/api': process.env.VITE_API_TARGET ?? 'http://localhost:8000',
    },
  },
})
