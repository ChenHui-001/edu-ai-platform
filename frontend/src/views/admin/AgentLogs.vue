<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">AI 调用日志</h2>
      <div>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
        <el-button :icon="Cpu" @click="statusDrawer = true">引擎状态</el-button>
      </div>
    </div>

    <el-row :gutter="16" class="mb12" v-if="engine">
      <el-col :span="6" v-for="c in cards" :key="c.label">
        <div class="stat-card">
          <div class="stat-value" :style="{ color: c.color }">{{ c.value }}</div>
          <div class="stat-label">{{ c.label }}</div>
        </div>
      </el-col>
    </el-row>

    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="query">
        <el-form-item label="Agent">
          <el-select v-model="query.agent_name" placeholder="全部" clearable style="width:180px">
            <el-option v-for="a in agents" :key="a.name"
                       :label="a.display_name || a.name" :value="a.name" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" placeholder="全部" clearable style="width:110px">
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>
        <el-form-item label="降级">
          <el-select v-model="query.is_fallback" placeholder="全部" clearable style="width:110px">
            <el-option label="是" :value="true" />
            <el-option label="否" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker v-model="dateRange" type="daterange" value-format="YYYY-MM-DD"
                          start-placeholder="开始" end-placeholder="结束" style="width:240px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="load">查询</el-button>
          <el-button :icon="Refresh" @click="reset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="list" border stripe>
        <el-table-column label="Agent" width="140">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ row.agent_name || row.agent_code }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="intent" label="意图" width="120" />
        <el-table-column prop="input_text" label="输入摘要" min-width="220" show-overflow-tooltip />
        <el-table-column prop="output_preview" label="输出摘要" min-width="240" show-overflow-tooltip />
        <el-table-column prop="duration_ms" label="耗时(ms)" width="100" />
        <el-table-column prop="token_usage" label="Token" width="100" />
        <el-table-column label="结果" width="110">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
              {{ row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
            <el-tag v-if="row.is_fallback" type="warning" size="small" class="ml4">降级</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="170" />
        <el-table-column label="操作" width="90">
          <template #default="{ row }">
            <el-button link type="primary" @click="detail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination class="mt16" background layout="total, sizes, prev, pager, next"
                     :total="total" v-model:current-page="query.page"
                     v-model:page-size="query.page_size"
                     @current-change="load" @size-change="load" />
    </el-card>

    <el-dialog v-model="detailDlg" title="调用详情" width="720px">
      <el-descriptions :column="2" border v-if="current">
        <el-descriptions-item label="Agent">{{ current.agent_name || current.agent_code }}</el-descriptions-item>
        <el-descriptions-item label="意图">{{ current.intent || '-' }}</el-descriptions-item>
        <el-descriptions-item label="耗时">{{ current.duration_ms }} ms</el-descriptions-item>
        <el-descriptions-item label="Token">
          <!-- 后端给的是 input_tokens / output_tokens，没有 token_usage 字段 -->
          {{ (current.input_tokens ?? 0) + (current.output_tokens ?? 0) || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="时间">{{ current.created_at }}</el-descriptions-item>
        <el-descriptions-item label="模型">{{ current.model || '-' }}</el-descriptions-item>
      </el-descriptions>
      <el-divider content-position="left">输入</el-divider>
      <pre class="code-box">{{ current?.input_text || '-' }}</pre>
      <el-divider content-position="left">输出</el-divider>
      <!-- 明细字段是 output_text（完整输出），output_preview 只在列表里 -->
      <pre class="code-box">{{ current?.output_text || current?.output_preview || '-' }}</pre>
      <el-divider v-if="current?.error_msg" content-position="left">错误</el-divider>
      <pre v-if="current?.error_msg" class="code-box error">{{ current.error_msg }}</pre>
    </el-dialog>

    <el-drawer v-model="statusDrawer" title="AI 引擎状态" size="420px">
      <el-descriptions :column="1" border v-if="engine">
        <el-descriptions-item label="编排模式">
          <el-tag :type="engine.orchestrator_mode === 'langgraph' ? 'success' : 'warning'" size="small">
            {{ engine.orchestrator_mode === 'langgraph' ? 'LangGraph 状态图' : '顺序编排（降级）' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="大模型">
          <el-tag :type="engine.llm_enabled ? 'success' : 'info'" size="small">
            {{ engine.llm_enabled ? `${engine.llm_provider} / ${engine.llm_model}` : '未配置（规则引擎）' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="向量数据库">
          <el-tag :type="engine.vector_db === 'chroma' ? 'success' : 'warning'" size="small">
            {{ engine.vector_db === 'chroma' ? 'ChromaDB' : 'SQL 检索（降级）' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="调度器">
          {{ engine.scheduler_running ? '运行中' : '已停止' }}
        </el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">已注册 Agent（{{ agents.length }}）</el-divider>
      <el-table :data="agents" border size="small">
        <!-- 后端字段是 name（标识）/ display_name（中文名），没有 code -->
        <el-table-column prop="display_name" label="名称" width="150" />
        <el-table-column prop="name" label="标识" width="150" />
        <el-table-column prop="description" label="说明" show-overflow-tooltip />
      </el-table>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { Search, Refresh, Cpu } from '@element-plus/icons-vue'
import { agentApi } from '@/api'

const list = ref([])
const agents = ref([])
const engine = ref(null)
const total = ref(0)
const loading = ref(false)
const detailDlg = ref(false)
const statusDrawer = ref(false)
const current = ref(null)
const dateRange = ref([])

const query = reactive({ page: 1, page_size: 20, agent_name: '', status: '', is_fallback: null })

const cards = computed(() => {
  if (!list.value.length) return []
  return [
    { label: '本页调用数', value: list.value.length, color: '#2f6fd0' },
    { label: '成功数', value: list.value.filter(r => r.status === 'success').length, color: '#67c23a' },
    { label: '失败数', value: list.value.filter(r => r.status !== 'success').length, color: '#f56c6c' },
    { label: '规则降级', value: list.value.filter(r => r.is_fallback).length, color: '#e6a23c' }
  ]
})

async function load() {
  loading.value = true
  try {
    const params = { ...query }
    if (dateRange.value?.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    const res = await agentApi.logs(params)
    const d = res.data || {}
    list.value = d.items || []
    total.value = d.total || 0
  } finally {
    loading.value = false
  }
}

function reset() {
  Object.assign(query, { page: 1, agent_name: '', status: '', is_fallback: null })
  dateRange.value = []
  load()
}

function detail(row) {
  current.value = row
  detailDlg.value = true
}

onMounted(async () => {
  await load()
  const [l, s] = await Promise.all([agentApi.list(), agentApi.status()])
  // /agent/list 返回的是对象 {agents: [...], orchestrator_mode, llm_enabled}，
  // 不是数组。原先直接 `l.data || []` 拿到对象，el-select 的 v-for 遍历对象值，
  // 下拉选项全空、抽屉里的 Agent 表格也是空的。
  agents.value = l.data?.agents || (Array.isArray(l.data) ? l.data : [])
  engine.value = s.data
})
</script>

<style scoped>
.mb12 { margin-bottom: 16px; }
.mt16 { margin-top: 16px; justify-content: flex-end; }
.ml4 { margin-left: 4px; }
.filter-card :deep(.el-form-item) { margin-bottom: 12px; }
.code-box {
  background: #f7f8fa; padding: 12px; border-radius: 6px;
  font-size: 12px; max-height: 220px; overflow: auto; white-space: pre-wrap;
  word-break: break-all; margin: 0;
}
.code-box.error { background: #fef0f0; color: #f56c6c; }
</style>
