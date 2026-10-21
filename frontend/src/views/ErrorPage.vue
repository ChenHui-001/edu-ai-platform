<template>
  <div class="err-wrap">
    <div class="err-code">{{ code }}</div>
    <h2 class="err-title">{{ title }}</h2>
    <p class="err-desc">{{ desc }}</p>
    <p class="err-path" v-if="code === 404">请求地址：{{ route.fullPath }}</p>
    <div class="err-actions">
      <el-button type="primary" @click="goHome">返回首页</el-button>
      <el-button @click="$router.back()">返回上一页</el-button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

// 一个组件同时承担 404 与 403：两者的差异只有文案，
// 拆两个文件只会让后续改文案时漏改其中一个。
const code = computed(() => (route.name === 'Forbidden' ? 403 : 404))
const title = computed(() => (code.value === 403 ? '无权访问该页面' : '页面不存在'))
const desc = computed(() => (
  code.value === 403
    ? '当前账号的角色或权限不足以打开此页面。如确需访问，请联系管理员调整角色权限。'
    : '地址可能输入有误，或该功能已下线。'
))

function goHome() {
  router.replace('/dashboard')
}
</script>

<style scoped>
.err-wrap {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px;
  text-align: center;
}
.err-code { font-size: 72px; font-weight: 700; color: #c0c4cc; line-height: 1; }
.err-title { margin: 8px 0 0; font-size: 20px; color: #303133; }
.err-desc { margin: 0; color: #606266; font-size: 14px; max-width: 460px; }
.err-path { margin: 0; color: #909399; font-size: 12px; word-break: break-all; }
.err-actions { margin-top: 16px; display: flex; gap: 12px; }
</style>
