import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  server: {
    host: true,
    port: Number(process.env.PORT) || 3000,
    ...(mode === 'development' 
      ? {
          proxy: {
            '/search': {
              target: 'http://localhost:8000',
              changeOrigin: true
            }
          }
        }
      : {})
  },
  preview: {
    port: Number(process.env.PORT) || 3000,
    host: true,
    ...(mode === 'production' 
      ? {
          allowedHosts: [
            'healthcheck.railway.app',
            'political-discourse-analyzer-production.up.railway.app',
            'agoradigital.up.railway.app'
          ]
        }
      : {})
  }
}))