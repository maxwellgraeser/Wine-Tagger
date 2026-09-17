import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// Ports come from the same env vars run.sh uses, so a second checkout (e.g. a
// git worktree) can run beside the main one:
//   CELLAR_PORT  the FastAPI backend that /api is proxied to (default 8000)
//   VITE_PORT    this dev server's port (default 5173)
const apiPort = process.env.CELLAR_PORT || '8000'
const vitePort = Number(process.env.VITE_PORT || 5173)

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: vitePort,
    strictPort: true,
    proxy: {
      '/api': `http://localhost:${apiPort}`,
    },
  },
  build: {
    outDir: 'dist',
  },
})
