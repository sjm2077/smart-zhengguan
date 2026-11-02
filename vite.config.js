import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 3000,
    open: true,
    proxy: {
      '/api-grad': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api-grad/, '/api'),
      },
      '/api-research': {
        target: 'http://127.0.0.1:8888',
        changeOrigin: true,
        // 科研系统路由挂在 /api/ 下，需去掉 /api-research 前缀
        rewrite: (path) => path.replace(/^\/api-research/, ''),
      },
      // 知识库/智能体服务（独立进程，不依赖任何子系统）
      '/kb': {
        target: 'http://127.0.0.1:8900',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/kb/, ''),
      },
    },
  }
})
