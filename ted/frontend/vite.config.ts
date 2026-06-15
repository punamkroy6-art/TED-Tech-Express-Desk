import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // Dev server: proxy /api to local FastAPI
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
  // Preview server (Vite preview): same proxy
  preview: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
  // Production build: /api is served from same origin (Vercel routes it)
  // No base URL needed — relative paths work on Vercel
})
