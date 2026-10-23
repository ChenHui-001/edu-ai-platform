import { defineConfig } from 'vitest/config'

// 单元测试只覆盖纯工具函数；sanitize 依赖 DOMParser，用轻量 DOM 实现提供环境。
// 不用 jsdom：当前 Node（22.3）下 jsdom 30 的 html-encoding-sniffer 会 require ESM 报错。
export default defineConfig({
  test: {
    environment: 'happy-dom',
    include: ['src/**/__tests__/**/*.test.js']
  }
})
