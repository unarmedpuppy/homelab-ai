import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    proxy: {
      '/api/harness': {
        target: 'https://agent-harness.server.unarmedpuppy.com',
        rewrite: (path) => path.replace(/^\/api\/harness/, ''),
        changeOrigin: true,
        secure: false,
      },
      '/api/router': {
        target: 'https://llm-router.server.unarmedpuppy.com',
        rewrite: (path) => path.replace(/^\/api\/router/, ''),
        changeOrigin: true,
        secure: false,
      },
      '/api/tasks': {
        target: 'https://tasks-api.server.unarmedpuppy.com',
        rewrite: (path) => path.replace(/^\/api\/tasks/, ''),
        changeOrigin: true,
        secure: false,
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
