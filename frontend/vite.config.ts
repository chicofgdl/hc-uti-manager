import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import tailwindcss from '@tailwindcss/vite'

const apiProxyTarget = process.env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8000'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue(), tailwindcss()],
  build: {
    // outDir: path.resolve(__dirname, '../src/static/dist'),
    outDir: "dist",
    emptyOutDir: true,
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    watch: {
      usePolling: true, // necessário para hot-reload dentro de containers no Windows
      interval: 500,
    },
    hmr: {
      host: 'localhost',
      port: 5173,
    },
    proxy: {
      '/api': {
        target: apiProxyTarget,
        changeOrigin: true,
      },
      '/leitos': {
        target: apiProxyTarget,
        changeOrigin: true,
      },
      '/solicitacoes-reserva': {
        target: apiProxyTarget,
        changeOrigin: true,
      },
      '/reservas': {
        target: apiProxyTarget,
        changeOrigin: true,
      },
      '/transferencias': {
        target: apiProxyTarget,
        changeOrigin: true,
      },
      '/notificacoes': {
        target: apiProxyTarget,
        changeOrigin: true,
      },
      '/users': {
        target: apiProxyTarget,
        changeOrigin: true,
      },
    }
  }
})
