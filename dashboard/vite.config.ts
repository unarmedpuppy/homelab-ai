import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
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
        },
      },
    },
    // Adjust warning limit since recharts is inherently large
    chunkSizeWarningLimit: 300,
  },
})
