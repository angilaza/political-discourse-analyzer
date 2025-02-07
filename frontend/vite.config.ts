import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 3000,
    proxy: {
      '/search': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})