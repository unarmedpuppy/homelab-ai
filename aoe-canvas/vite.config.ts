import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    proxy: {
      '/api/harness': {
        target: 'http://localhost:8013',
        rewrite: (path) => path.replace(/^\/api\/harness/, ''),
        changeOrigin: true,
      },
      '/api/router': {
        target: 'http://localhost:8012',
        rewrite: (path) => path.replace(/^\/api\/router/, ''),
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom'],
          'vendor-phaser': ['phaser'],
          'vendor-query': ['@tanstack/react-query'],
        },
      },
    },
    chunkSizeWarningLimit: 2000,
  },
})
