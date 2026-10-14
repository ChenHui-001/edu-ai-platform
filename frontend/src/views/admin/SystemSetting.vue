<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">系统配置</h2>
      <el-button :icon="Refresh" @click="load">刷新</el-button>
    </div>

    <el-alert type="info" :closable="false" class="mb16"
              title="敏感配置（数据库连接、密钥）已脱敏展示；修改后需重启服务生效" />

    <el-row :gutter="16">
      <el-col :span="12">
        <el-card shadow="never" v-loading="loading">
          <template #header><b>基础配置</b></template>
          <el-descriptions :column="1" border v-if="config">
            <el-descriptions-item label="应用名称">{{ config.APP_NAME }}</el-descriptions-item>
            <el-descriptions-item label="版本">{{ config.APP_VERSION }}</el-descriptions-item>
            <el-descriptions-item label="运行环境">{{ config.ENVIRONMENT }}</el-descriptions-item>
            <el-descriptions-item label="数据库">{{ masked(config.DATABASE_URL) }}</el-descriptions-item>
            <el-descriptions-item label="每页条数">{{ config.DEFAULT_PAGE_SIZE }}</el-descriptions-item>
            <el-descriptions-item label="最大上传(MB)">{{ config.MAX_UPLOAD_SIZE }}</el-descriptions-item>
            <el-descriptions-item label="及格分">{{ config.PASS_SCORE }}</el-descriptions-item>
            <el-descriptions-item label="JWT 有效期">{{ config.ACCESS_TOKEN_EXPIRE_MINUTES }} 分钟</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card shadow="never" v-loading="loading">
          <template #header><b>AI 与检索配置</b></template>
          <el-descriptions :column="1" border v-if="config">
            <el-descriptions-item label="大模型提供商">
              <el-tag :type="config.LLM_ENABLED ? 'success' : 'info'" size="small">
                {{ config.LLM_PROVIDER || '未配置' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="模型名称">{{ config.LLM_MODEL || '-' }}</el-descriptions-item>
            <el-descriptions-item label="API 地址">{{ masked(config.LLM_BASE_URL) }}</el-descriptions-item>
            <el-descriptions-item label="API Key">{{ masked(config.LLM_API_KEY) }}</el-descriptions-item>
            <el-descriptions-item label="向量库">
              {{ config.CHROMA_PERSIST_DIR ? 'ChromaDB（已配置）' : '未配置（SQL 降级）' }}
            </el-descriptions-item>
            <el-descriptions-item label="RAG 召回数量">{{ config.RAG_TOP_K }}</el-descriptions-item>
            <el-descriptions-item label="复习间隔">
              {{ (config.REVIEW_INTERVALS || []).join(' / ') }} 天
            </el-descriptions-item>
            <el-descriptions-item label="调度器">{{ config.SCHEDULER_ENABLED ? '已启用' : '已停用' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="mt16">
      <template #header><b>配置修改指引</b></template>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="修改方式">
          编辑项目根目录 <code>.env</code> 文件（或 <code>backend/.env</code>），修改对应变量后重启容器
        </el-descriptions-item>
        <el-descriptions-item label="启用真实大模型">
          设置 <code>LLM_ENABLED=true</code>、<code>LLM_API_KEY=...</code>、<code>LLM_BASE_URL=...</code>、<code>LLM_MODEL=...</code>
        </el-descriptions-item>
        <el-descriptions-item label="切换到 PostgreSQL">
          将 <code>DATABASE_URL</code> 改为 <code>postgresql+psycopg://user:pass@host:5432/db</code>
        </el-descriptions-item>
        <el-descriptions-item label="完整变量清单">
          参考项目中的 <code>.env.example</code> 文件，共 {{ envKeys.length }} 项
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { systemApi } from '@/api'

const config = ref(null)
const loading = ref(false)
const envKeys = [
  'APP_NAME', 'APP_VERSION', 'ENVIRONMENT', 'DEBUG', 'SECRET_KEY', 'DATABASE_URL',
  'DEFAULT_PAGE_SIZE', 'MAX_PAGE_SIZE', 'MAX_UPLOAD_SIZE', 'PASS_SCORE',
  'ACCESS_TOKEN_EXPIRE_MINUTES', 'REFRESH_TOKEN_EXPIRE_DAYS', 'LOGIN_MAX_FAILED',
  'LOGIN_LOCK_MINUTES', 'LLM_ENABLED', 'LLM_PROVIDER', 'LLM_API_KEY', 'LLM_BASE_URL',
  'LLM_MODEL', 'LLM_TEMPERATURE', 'LLM_MAX_TOKENS', 'RAG_TOP_K', 'RAG_CHUNK_SIZE',
  'CHROMA_PERSIST_DIR', 'REVIEW_INTERVALS', 'SCHEDULER_ENABLED', 'LOG_LEVEL', 'CORS_ORIGINS'
]

function masked(v) {
  if (!v) return '-'
  const s = String(v)
  if (s.length <= 12) return s
  return s.slice(0, 6) + '****' + s.slice(-4)
}

async function load() {
  loading.value = true
  try {
    const res = await systemApi.config()
    config.value = res.data.data
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.mb16 { margin-bottom: 16px; }
.mt16 { margin-top: 16px; }
code {
  background: #f2f4f7; padding: 2px 6px; border-radius: 4px;
  font-family: Consolas, Monaco, monospace; font-size: 12px; color: #2f6fd0;
}
</style>
