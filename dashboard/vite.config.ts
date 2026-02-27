import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api/harness': {
        target: 'https://agent-harness.server.unarmedpuppy.com',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api\/harness/, ''),
      },
      '/api/router': {
        target: 'https://llm-router.server.unarmedpuppy.com',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api\/router/, ''),
      },
      '/api/tasks': {
        target: 'https://tasks-api.server.unarmedpuppy.com',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api\/tasks/, ''),
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        // Manual chunking to optimize bundle sizes
        manualChunks: {
          // Split vendor dependencies
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-charts': ['recharts'],
          'vendor-query': ['@tanstack/react-query'],
          'vendor-markdown': ['react-markdown', 'remark-gfm'],
          'vendor-phaser': ['phaser'],
        },
      },
    },
    // Adjust warning limit since recharts is inherently large
    chunkSizeWarningLimit: 300,
  },
})
