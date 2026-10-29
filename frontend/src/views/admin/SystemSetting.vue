<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">系统配置</h2>
      <el-button :icon="Refresh" @click="load">刷新</el-button>
    </div>

    <el-alert type="info" :closable="false" class="mb16"
              title="敏感配置（API Key、数据库口令）已脱敏展示；修改后需重启服务生效" />

    <!-- el-col 用响应式断点：手机上两张卡片各占满一行，不再被压成半边 -->
    <el-row :gutter="16">
      <el-col :xs="24" :sm="24" :md="12" :lg="12">
        <el-card shadow="never" v-loading="loading">
          <template #header><b>基础配置</b></template>
          <el-descriptions :column="1" border v-if="config">
            <el-descriptions-item label="应用名称">{{ config.app_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="版本">
              <el-tag size="small" type="success" effect="plain">v{{ config.version || '-' }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="运行模式">
              <el-tag size="small" :type="config.debug ? 'warning' : 'success'">
                {{ config.debug ? '调试模式' : '生产模式' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="数据库">
              {{ config.database_url || config.database || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="每页条数">{{ config.default_page_size ?? '-' }}</el-descriptions-item>
            <el-descriptions-item label="最大上传(MB)">{{ config.max_upload_size ?? '-' }}</el-descriptions-item>
            <el-descriptions-item label="及格分">{{ config.pass_score ?? '-' }}</el-descriptions-item>
            <el-descriptions-item label="登录有效期">
              {{ config.access_token_expire_minutes ?? '-' }} 分钟
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="24" :md="12" :lg="12" class="col-stack">
        <el-card shadow="never" v-loading="loading">
          <template #header><b>AI 与检索配置</b></template>
          <el-descriptions :column="1" border v-if="config">
            <el-descriptions-item label="大模型提供商">
              <el-tag :type="config.llm_enabled ? 'success' : 'info'" size="small">
                {{ config.llm_provider || '未配置' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="模型名称">{{ config.llm_model || '-' }}</el-descriptions-item>
            <el-descriptions-item label="API 地址">{{ config.llm_base_url || '-' }}</el-descriptions-item>
            <el-descriptions-item label="API Key">
              {{ config.llm_api_key || '未配置' }}
            </el-descriptions-item>
            <el-descriptions-item label="向量库">
              {{ config.chroma_persist_dir ? `ChromaDB（${config.chroma_persist_dir}）` : '未配置（SQL 降级）' }}
            </el-descriptions-item>
            <el-descriptions-item label="RAG 召回数量">{{ config.rag_top_k ?? '-' }}</el-descriptions-item>
            <el-descriptions-item label="复习间隔">
              {{ (config.review_intervals || []).join(' / ') }} 天
            </el-descriptions-item>
            <el-descriptions-item label="调度器">{{ config.scheduler_enabled ? '已启用' : '已停用' }}</el-descriptions-item>
            <el-descriptions-item label="日志保留">{{ config.log_retention_days ?? '-' }} 天</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="mt16" v-loading="loading">
      <template #header>
        <div class="card-head">
          <b>可在线修改的配置项</b>
          <span class="hint">共 {{ editable.length }} 项 · 密钥类已脱敏</span>
        </div>
      </template>
      <el-table v-if="editable.length" :data="editable" size="small" stripe max-height="380">
        <el-table-column prop="label" label="配置项" min-width="130" show-overflow-tooltip />
        <el-table-column prop="key" label="键名" min-width="150" show-overflow-tooltip>
          <template #default="{ row }"><code>{{ row.key }}</code></template>
        </el-table-column>
        <el-table-column prop="value" label="当前值" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">{{ row.value === '' || row.value === null ? '（空）' : row.value }}</template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="90" />
        <el-table-column prop="updated_at" label="更新时间" width="160" />
      </el-table>
      <el-empty v-else description="暂无可在线修改的配置项" :image-size="60" />
    </el-card>

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

    <!-- 版本号 / 构建号 / 最后更新时间（时间戳由后端在版本变化时自动记录） -->
    <VersionInfo class="mt16" />
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { systemApi } from '@/api'
import VersionInfo from '@/components/VersionInfo.vue'

const config = ref(null)
const loading = ref(false)
// 可在线编辑项来自后端 editable 数组（此前接口有返回、页面从未渲染）
const editable = computed(() => config.value?.editable || [])

const envKeys = [
  'APP_NAME', 'APP_VERSION', 'DEBUG', 'SECRET_KEY', 'DATABASE_URL',
  'DEFAULT_PAGE_SIZE', 'MAX_PAGE_SIZE', 'MAX_UPLOAD_SIZE', 'PASS_SCORE',
  'ACCESS_TOKEN_EXPIRE_MINUTES', 'REFRESH_TOKEN_EXPIRE_DAYS', 'LOGIN_MAX_FAILED',
  'LOGIN_LOCK_MINUTES', 'LLM_ENABLED', 'LLM_PROVIDER', 'LLM_API_KEY', 'LLM_BASE_URL',
  'LLM_MODEL', 'LLM_TEMPERATURE', 'LLM_MAX_TOKENS', 'RAG_TOP_K', 'RAG_CHUNK_SIZE',
  'CHROMA_PERSIST_DIR', 'REVIEW_INTERVALS', 'SCHEDULER_ENABLED', 'LOG_LEVEL', 'CORS_ORIGINS'
]

async function load() {
  loading.value = true
  try {
    const res = await systemApi.config()
    // 后端返回小写键（app_name/version/...）。此页曾按大写键（APP_NAME/...）渲染，
    // 与接口契约漂移，导致所有字段显示为空 —— 绑定必须与 /system/config 实际返回一致。
    config.value = res.data
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
.card-head {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.hint { font-size: 12px; color: #909399; }

/* 卡片在 <md 断点堆叠时补上纵向间距（el-row 的 gutter 只管横向） */
@media (max-width: 991px) {
  .col-stack { margin-top: 16px; }
}

/* 手机上标签列只有 ~100px，「大模型提供商」会被拆成三行。
   标签不换行、值允许断词，避免整列变成竖排汉字。 */
@media (max-width: 768px) {
  :deep(.el-descriptions__label) {
    white-space: nowrap;
    font-size: 13px;
  }
  :deep(.el-descriptions__content) {
    word-break: break-word;
  }
}
</style>
