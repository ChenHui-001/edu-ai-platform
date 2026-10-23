import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [
    vue(),
    // Element Plus 按需引入：模板里的 el-* 组件 / v-loading 指令在编译阶段
    // 自动补上 import 与对应组件样式；函数式 API（ElMessage/ElMessageBox）
    // 仍由各页面显式 import（main.js 里显式引入它们所需的两个样式文件）。
    AutoImport({
      imports: ['vue', 'vue-router', 'pinia'],
      resolvers: [ElementPlusResolver()],
      // 纯 JS 项目，不生成 auto-imports.d.ts / components.d.ts，避免多余文件
      dts: false
    }),
    Components({
      resolvers: [ElementPlusResolver()],
      // 本地组件（EChart / PomodoroTimer 等）均已显式 import，
      // 关闭目录自动扫描，避免隐式注册带来的行为差异
      dirs: [],
      dts: false
    })
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.VITE_API_TARGET || 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    // Element Plus 按需 + 去掉 element 手动分包后，最大分包已降到 600KB 以下；
    // 阈值从 800 收紧到 600，超出即告警。
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined
          const p = id.replace(/\\/g, '/')
          // ECharts 按需模块单独分包；zrender 拆出后 charts 分包可压到 600KB 以内，
          // 也让两者的缓存失效互不影响。
          if (p.includes('/node_modules/zrender/')) return 'zrender'
          if (p.includes('/node_modules/echarts/')) return 'charts'
          // 只固定分组「一定全量用到」的基础运行时库。
          // 注意：不要把 element-plus 放进 manualChunks —— Rollup 会把包入口的
          // 静态依赖树当成 chunk 入口，未使用的组件会被整体打回（实测 element
          // 手动分包反而一直保持 0.84MB，按需引入失效）。element-plus 组件交给
          // Vite 按路由动态分包，未使用组件才会真正被 tree-shake 掉。
          if (p.includes('/node_modules/vue/') || p.includes('/node_modules/vue-router/')
            || p.includes('/node_modules/pinia/') || p.includes('/node_modules/axios/')
            || p.includes('/node_modules/@vue/')) {
            return 'vendor'
          }
          return undefined
        }
      }
    }
  }
})
