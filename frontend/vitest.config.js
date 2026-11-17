import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// 组件测试与纯函数测试共用同一套 Vitest 环境。
// sanitize 依赖 DOMParser，用轻量 DOM 实现提供环境。
// 不用 jsdom：当前 Node（22.3）下 jsdom 30 的 html-encoding-sniffer 会 require ESM 报错。
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  test: {
    environment: 'happy-dom',
    include: ['src/**/__tests__/**/*.test.js']
  }
})
