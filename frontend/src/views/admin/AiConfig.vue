<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">AI 大模型配置</h2>
      <el-button :icon="Refresh" @click="load">刷新</el-button>
    </div>

    <el-alert type="info" :closable="false" class="mb16"
              title="在此配置大模型后立即生效，无需重启服务。配置优先级高于 .env 环境变量。" />

    <!-- 当前状态 -->
    <el-card shadow="never" class="mb16" v-loading="loading">
      <template #header>
        <div class="card-header">
          <b>当前状态</b>
          <el-tag :type="config.LLM_ENABLED ? 'success' : 'warning'" size="small" effect="dark" round>
            <el-icon style="vertical-align:-2px"><Cpu /></el-icon>
            {{ config.LLM_ENABLED ? 'AI 已启用' : '规则引擎降级模式' }}
          </el-tag>
        </div>
      </template>
      <el-descriptions :column="4" border>
        <el-descriptions-item label="提供商">
          <el-tag size="small">{{ providerLabel(config.LLM_PROVIDER) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="模型">{{ config.LLM_MODEL || '-' }}</el-descriptions-item>
        <el-descriptions-item label="API 地址">{{ masked(config.LLM_BASE_URL) }}</el-descriptions-item>
        <el-descriptions-item label="API Key">
          <el-tag size="small" :type="keyConfigured ? 'success' : 'danger'">
            {{ keyConfigured ? '已配置' : '未配置' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="提供商来源">{{ providerSourceLabel }}</el-descriptions-item>
        <el-descriptions-item label="Key 来源">{{ keySourceLabel }}</el-descriptions-item>
        <el-descriptions-item label="温度">{{ config.LLM_TEMPERATURE ?? '-' }}</el-descriptions-item>
        <el-descriptions-item label="最大输出">{{ config.LLM_MAX_TOKENS ?? '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- max_tokens 被后端上限收敛提示 -->
    <el-alert v-if="cappedMaxTokens" type="warning" :closable="false" show-icon class="mb16"
              :title="`max_tokens 已按后端上限收敛为 ${cappedMaxTokens}（数据库中保存的值超过上限，保存后自动回写）`" />

    <!-- 配置表单 -->
    <el-card shadow="never" v-loading="saving">
      <template #header><b>模型配置</b></template>

      <el-form :model="form" label-width="120px" style="max-width: 720px">
        <el-form-item label="启用 AI">
          <el-switch v-model="form.llm_enabled" active-text="启用大模型" inactive-text="规则引擎降级" />
        </el-form-item>

        <el-form-item label="提供商">
          <el-select v-model="form.llm_provider" placeholder="选择提供商" style="width: 100%"
                     @change="onProviderChange">
            <el-option v-for="(p, key) in providers" :key="key" :label="p.label" :value="key" />
          </el-select>
        </el-form-item>

        <el-form-item label="API Key">
          <div class="api-key-block">
            <el-input v-model="form.llm_api_key" type="password" show-password
                      :placeholder="apiKeyPlaceholder" :disabled="clearKey" clearable />
            <div class="form-tip">
              <template v-if="keyConfigured">
                已保存（{{ keySourceLabel }}）；留空保存不会修改，输入新值才会覆盖。
              </template>
              <template v-else>当前未配置 API Key。</template>
              <template v-if="form.llm_provider === 'ollama'"> Ollama 本地部署无需 API Key。</template>
            </div>
          </div>
        </el-form-item>

        <el-form-item v-if="keyConfigured" label="清除 Key">
          <el-checkbox v-model="clearKey">清除已保存的 API Key（保存时提交空字符串）</el-checkbox>
        </el-form-item>

        <el-form-item label="API 地址">
          <el-input v-model="form.llm_base_url" placeholder="https://api.deepseek.com/v1" clearable />
          <div v-if="form.llm_provider === 'custom'" class="form-tip">
            自定义提供商必须填写兼容 OpenAI 协议的 API 地址
          </div>
        </el-form-item>

        <el-form-item label="模型名称">
          <el-input v-model="form.llm_model" placeholder="deepseek-chat / qwen-plus / gpt-4o-mini" clearable />
        </el-form-item>

        <el-form-item label="温度参数">
          <el-slider v-model="form.llm_temperature" :min="0" :max="2" :step="0.1"
                     show-input style="max-width: 500px" />
        </el-form-item>

        <el-form-item label="最大输出">
          <el-input-number v-model="form.llm_max_tokens" :min="256" :max="32768" :step="256" />
          <span class="form-tip">
            Token<template v-if="maxTokensCap">（后端上限 {{ maxTokensCap }}，超出会被收敛）</template>
          </span>
        </el-form-item>

        <el-form-item label="超时时间">
          <el-input-number v-model="form.llm_timeout" :min="10" :max="300" :step="5" />
          <span class="form-tip">秒</span>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :icon="Connection" @click="testConnection"
                     :loading="testing">测试连接</el-button>
          <el-button type="success" :icon="Check" @click="save">保存配置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 测试结果 -->
    <el-card v-if="testResult" shadow="never" class="mt16">
      <template #header><b>连接测试结果</b></template>
      <el-result :icon="testResult.success ? 'success' : 'error'"
                 :title="testResult.success ? '连接成功' : '连接失败'"
                 :sub-title="testResult.message">
        <template #extra v-if="testResult.success">
          <el-descriptions :column="3" border>
            <el-descriptions-item label="模型">{{ testResult.model }}</el-descriptions-item>
            <el-descriptions-item label="耗时">
              {{ testResult.duration_ms != null ? `${testResult.duration_ms} ms` : '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="输入 Token">
              {{ testResult.usage?.input_tokens ?? '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="输出 Token">
              {{ testResult.usage?.output_tokens ?? '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="Base URL" :span="2">
              {{ testResult.base_url || '-' }}
            </el-descriptions-item>
          </el-descriptions>
        </template>
      </el-result>
    </el-card>

    <!-- 场景路由：题目类走独立「快场景」模型 -->
    <el-card shadow="never" class="mt16">
      <template #header>
        <div class="card-header">
          <b>场景路由</b>
          <el-tag size="small" type="info">题目类任务用独立模型 / 低推理档</el-tag>
        </div>
      </template>
      <el-form label-width="150px" style="max-width: 720px">
        <el-form-item label="快场景业务类型">
          <el-select v-model="fastBizTypes" multiple filterable allow-create
                     default-first-option style="width: 100%"
                     placeholder="留空 = 关闭路由，全部走上面的全局模型">
            <el-option v-for="t in bizTypes" :key="t" :label="bizLabel(t)" :value="t" />
          </el-select>
          <div class="form-tip">
            只有列出的业务类型走下面这份独立配置；全部清空即恢复默认（生产回滚开关）。
          </div>
        </el-form-item>
        <el-form-item label="快场景模型">
          <el-input v-model="form.llm_model_fast" placeholder="留空 = 复用主模型" clearable />
        </el-form-item>
        <el-form-item label="快场景 API 地址">
          <el-input v-model="form.llm_base_url_fast"
                    placeholder="留空 = 复用主 API 地址；跨厂商时才需要填" clearable />
        </el-form-item>
        <el-form-item label="快场景推理档">
          <el-select v-model="form.llm_fast_reasoning_effort" clearable
                     placeholder="留空 = 不传该参数（兼容不认识的网关）" style="width: 100%">
            <el-option label="low（推荐：省推理 token，正文更不容易被挤空）" value="low" />
            <el-option label="medium" value="medium" />
            <el-option label="high" value="high" />
            <el-option label="minimal" value="minimal" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 按业务类型细化预算 -->
    <el-card shadow="never" class="mt16">
      <template #header>
        <div class="card-header">
          <b>按业务类型细化预算</b>
          <el-button size="small" :icon="Plus" @click="addBudgetRow">新增一行</el-button>
        </div>
      </template>
      <el-alert type="info" :closable="false" class="mb16"
                title="留空的字段表示沿用上面的全局配置；配了才生效，全部删掉即关闭该功能。" />
      <el-table :data="budgetRows" border size="small">
        <template #empty>
          <TableEmpty text="尚未配置，所有业务走全局预算" />
        </template>
        <el-table-column label="业务类型" width="200">
          <template #default="{ row }">
            <el-select v-model="row.biz_type" size="small" filterable allow-create
                       default-first-option placeholder="选择或输入">
              <el-option v-for="t in bizTypes" :key="t" :label="bizLabel(t)" :value="t" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="温度" width="150">
          <template #default="{ row }">
            <el-input-number v-model="row.temperature" :min="0" :max="2" :step="0.1"
                             size="small" controls-position="right" placeholder="沿用" />
          </template>
        </el-table-column>
        <el-table-column label="最大输出 Token" width="180">
          <template #default="{ row }">
            <el-input-number v-model="row.max_tokens" :min="64"
                             :max="maxTokensCap || 32768" :step="256"
                             size="small" controls-position="right" placeholder="沿用" />
          </template>
        </el-table-column>
        <el-table-column label="推理档" width="200">
          <template #default="{ row }">
            <el-select v-model="row.reasoning_effort" size="small" clearable
                       placeholder="沿用">
              <el-option label="沿用（场景默认）" :value="null" />
              <el-option label="low" value="low" />
              <el-option label="medium" value="medium" />
              <el-option label="high" value="high" />
              <el-option label="minimal" value="minimal" />
              <el-option label="显式不传（覆盖场景默认）" value="" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90" align="center">
          <template #default="{ $index }">
            <el-button link type="danger" @click="removeBudgetRow($index)">移除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="form-tip" style="margin-left: 0; margin-top: 8px;">
        典型用法：出题 <code>question_generate</code> 低温度 + 大预算；
        路由 <code>router</code> 只给几百 token；答疑 <code>tutor</code> 温度略高。
      </div>
    </el-card>

    <!-- 提供商说明 -->
    <el-card shadow="never" class="mt16">
      <template #header><b>提供商说明</b></template>
      <el-table :data="providerTable" border size="small">
        <template #empty><TableEmpty text="暂无模型提供商，点击「新增提供商」开始配置" /></template>
        <el-table-column prop="label" label="提供商" width="180" />
        <el-table-column prop="base_url" label="默认 API 地址" />
        <el-table-column prop="model" label="默认模型" width="180" />
        <el-table-column label="说明" min-width="200">
          <template #default="{ row }">
            {{ row.desc }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { Refresh, Connection, Check, Cpu, Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'
import { confirmAction } from '@/utils/confirm'
import { toastIfUnhandled } from '@/utils/notify'

const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const config = ref({})
const meta = ref({})
const providers = ref({})
const testResult = ref(null)
// 后端新接口可能把 key_configured 放在顶层或 config 内，这里统一兜底
const apiKeyConfigured = ref(null)
// 勾选后保存提交 llm_api_key:''（显式清除）；不勾选且未输入则不提交该字段
const clearKey = ref(false)
// 场景路由的业务类型是「多选 + 自由输入」，后端存逗号串，这里用数组编辑
const fastBizTypes = ref([])
// 按业务类型细化预算（F-06）：后端存 JSON 对象，这里用行表格编辑
const budgetRows = ref([])
const bizTypes = ref([])

const form = ref({
  llm_enabled: true,
  llm_provider: 'deepseek',
  llm_api_key: '',
  llm_base_url: '',
  llm_model: '',
  llm_temperature: 0.7,
  llm_max_tokens: 4096,
  llm_timeout: 60,
  llm_model_fast: '',
  llm_base_url_fast: '',
  llm_fast_reasoning_effort: ''
})

// Key 是否已配置：优先用后端 key_configured，旧后端则用掩码 Key 判断
const keyConfigured = computed(() => {
  if (typeof apiKeyConfigured.value === 'boolean') return apiKeyConfigured.value
  const c = config.value || {}
  if (typeof c.KEY_CONFIGURED === 'boolean') return c.KEY_CONFIGURED
  if (typeof c.key_configured === 'boolean') return c.key_configured
  const key = c.LLM_API_KEY
  return typeof key === 'string' && key.length > 0
})

function metaOf(key) { return meta.value?.[key] || {} }

// biz_type 的中文说明：只影响下拉里的显示，未列出的值照样可以手填
const BIZ_LABELS = {
  question_generate: '出题 / 组卷补题（question_generate）',
  question_variants: '变式题（question_variants）',
  grading: '智能批改（grading）',
  paper_parse: '试卷解析（paper_parse）',
  lesson_head: '教案·目标（lesson_head）',
  lesson_body: '教案·正文（lesson_body）',
  study_plan: '学习规划（study_plan）',
  tutor: '答疑助教（tutor）',
  router: '意图路由（router）',
  note: '笔记整理（note）'
}
function bizLabel(t) { return BIZ_LABELS[t] || t }

function addBudgetRow() {
  budgetRows.value.push({
    biz_type: '',
    temperature: null,
    max_tokens: null,
    reasoning_effort: null
  })
}
function removeBudgetRow(index) { budgetRows.value.splice(index, 1) }

/** 行表格 → 后端要的 `{biz_type: {字段}}`；留空字段直接不出现（= 沿用全局）。 */
function buildBudgets() {
  const out = {}
  for (const row of budgetRows.value) {
    const biz = String(row.biz_type || '').trim()
    if (!biz) continue
    const spec = {}
    if (row.temperature !== null && row.temperature !== undefined && row.temperature !== '') {
      spec.temperature = Number(row.temperature)
    }
    if (row.max_tokens !== null && row.max_tokens !== undefined && row.max_tokens !== '') {
      spec.max_tokens = Number(row.max_tokens)
    }
    // '' 是**有意义**的取值（显式不传推理档），不能用真值判断丢掉
    if (row.reasoning_effort !== null && row.reasoning_effort !== undefined) {
      spec.reasoning_effort = String(row.reasoning_effort)
    }
    if (Object.keys(spec).length) out[biz] = spec
  }
  return out
}

const providerSourceLabel = computed(() =>
  metaOf('llm_provider').has_db_value ? '数据库配置' : '环境变量/默认值')
const keySourceLabel = computed(() => {
  if (metaOf('llm_api_key').has_db_value) {
    return keyConfigured.value ? '数据库配置' : '数据库（已清除）'
  }
  return keyConfigured.value ? '环境变量' : '未配置'
})
const apiKeyPlaceholder = computed(() => {
  if (clearKey.value) return '保存时将清除已保存的 Key'
  return keyConfigured.value ? '已保存（留空不修改）' : '未配置，请输入 API Key'
})
const maxTokensCap = computed(() => {
  const m = metaOf('llm_max_tokens')
  return m.cap || null
})
const cappedMaxTokens = computed(() => {
  const m = metaOf('llm_max_tokens')
  return m.capped ? m.cap : null
})

const providerTable = computed(() => {
  return Object.entries(providers.value).map(([key, p]) => {
    const desc = {
      deepseek: '国产高性价比模型，支持中文场景优秀',
      qwen: '阿里云通义千问，DashScope 兼容模式',
      openai: 'GPT 系列模型，需海外网络环境',
      ollama: '本地部署的开源模型，无需联网',
      custom: '任何兼容 OpenAI 协议的服务端点'
    }[key] || ''
    return { label: p.label, base_url: p.base_url || '-', model: p.model || '-', desc }
  })
})

function providerLabel(key) {
  return providers.value[key]?.label || key || '未配置'
}

function masked(v) {
  if (!v) return '-'
  const s = String(v)
  if (s.length <= 12) return s
  return s.slice(0, 6) + '****' + s.slice(-4)
}

function onProviderChange(key) {
  const preset = providers.value[key]
  if (preset) {
    if (preset.base_url) form.value.llm_base_url = preset.base_url
    if (preset.model) form.value.llm_model = preset.model
  }
}

async function load() {
  loading.value = true
  try {
    const res = await request.get('/system/ai-config')
    const data = res.data
    config.value = data.config
    meta.value = data.meta || {}
    providers.value = data.providers
    apiKeyConfigured.value = typeof data.key_configured === 'boolean'
      ? data.key_configured
      : (typeof data.config?.key_configured === 'boolean'
        ? data.config.key_configured : null)
    // 填充表单：**不把掩码 Key 填进输入框**（避免管理员误保存掩码值）
    const c = data.config
    form.value = {
      llm_enabled: c.LLM_ENABLED ?? true,
      llm_provider: c.LLM_PROVIDER || 'deepseek',
      llm_api_key: '',
      llm_base_url: c.LLM_BASE_URL || '',
      llm_model: c.LLM_MODEL || '',
      llm_temperature: c.LLM_TEMPERATURE ?? 0.7,
      llm_max_tokens: c.LLM_MAX_TOKENS ?? 4096,
      llm_timeout: c.LLM_TIMEOUT ?? 60,
      llm_model_fast: c.LLM_MODEL_FAST || '',
      llm_base_url_fast: c.LLM_BASE_URL_FAST || '',
      llm_fast_reasoning_effort: c.LLM_FAST_REASONING_EFFORT || ''
    }
    fastBizTypes.value = String(c.LLM_FAST_BIZ_TYPES || '')
      .split(',').map(s => s.trim()).filter(Boolean)
    // 预算覆盖：后端已解析好（坏数据返回空表），前端不自己 JSON.parse
    budgetRows.value = Object.entries(data.biz_budgets || {}).map(([biz, spec]) => ({
      biz_type: biz,
      temperature: spec.temperature ?? null,
      max_tokens: spec.max_tokens ?? null,
      reasoning_effort: spec.reasoning_effort ?? null
    }))
    bizTypes.value = data.biz_types || []
    clearKey.value = false
  } finally {
    loading.value = false
  }
}

async function save() {
  if (form.value.llm_provider === 'custom' && !form.value.llm_base_url.trim()) {
    return ElMessage.warning('自定义提供商必须填写 API 地址')
  }
  // 启用但未配置 Key（非 Ollama）：仅确认提示，不阻止保存（可先保存再补 Key）
  if (form.value.llm_enabled && form.value.llm_provider !== 'ollama'
      && !keyConfigured.value && !form.value.llm_api_key.trim() && !clearKey.value) {
    try {
      if (!await confirmAction(
        '已启用 AI 但尚未配置 API Key（非 Ollama），AI 调用会失败并自动降级到规则引擎。确认继续保存？',
        '配置确认', { type: 'warning', confirmButtonText: '继续保存' })) return
    } catch { return }
  }
  // 勾选清除 Key 且仍启用 AI：明确告知保存后 AI 将不可用
  if (clearKey.value && form.value.llm_enabled && form.value.llm_provider !== 'ollama') {
    try {
      if (!await confirmAction(
        '将清除已保存的 API Key，但 AI 仍处于启用状态，保存后 AI 调用会失败并降级为规则引擎。确认继续保存？',
        '清除 Key 确认', { type: 'warning', confirmButtonText: '确认清除' })) return
    } catch { return }
  }

  // 组装 payload：未输入且未勾选清除 → 不带 llm_api_key（避免空值误清）
  const budgets = buildBudgets()
  // 同一 biz_type 配两行时，后一行会静默覆盖前一行 —— 与其让管理员
  // 对着"配了没生效"排查，不如保存前直接拦下。
  const seen = new Set()
  for (const row of budgetRows.value) {
    const biz = String(row.biz_type || '').trim()
    if (!biz) continue
    if (seen.has(biz)) {
      return ElMessage.warning(`业务类型 ${biz} 配了多行，请合并后再保存`)
    }
    seen.add(biz)
  }
  if (form.value.llm_max_tokens && maxTokensCap.value
      && Number(form.value.llm_max_tokens) > Number(maxTokensCap.value)) {
    // 后端会收敛，但这里先说清楚，避免"保存了却不是这个数"
    ElMessage.warning(`最大输出超过后端上限 ${maxTokensCap.value}，保存后会被收敛`)
  }

  const payload = { ...form.value }
  delete payload.llm_api_key
  const newKey = form.value.llm_api_key.trim()
  if (newKey) payload.llm_api_key = newKey
  else if (clearKey.value) payload.llm_api_key = ''
  payload.llm_fast_biz_types = fastBizTypes.value.join(',')
  payload.llm_biz_budgets = budgets

  saving.value = true
  try {
    const res = await request.put('/system/ai-config', payload)
    ElMessage.success(res.data?.message || 'AI 配置已保存')
    await load()
  } catch (e) {
    toastIfUnhandled(e, '保存失败')
  } finally {
    saving.value = false
  }
}

async function testConnection() {
  if (form.value.llm_provider === 'custom' && !form.value.llm_base_url.trim()) {
    return ElMessage.warning('自定义提供商必须填写 API 地址')
  }
  testing.value = true
  testResult.value = null
  try {
    const payload = {
      llm_provider: form.value.llm_provider,
      llm_base_url: form.value.llm_base_url,
      llm_model: form.value.llm_model
    }
    // 输入了新 Key 才发送；留空时由后端使用已保存的 Key
    const typedKey = form.value.llm_api_key.trim()
    if (typedKey) payload.llm_api_key = typedKey
    const res = await request.post('/system/ai-config/test', payload)
    testResult.value = res.data
    if (testResult.value.success) {
      const elapsed = testResult.value.duration_ms != null
        ? `（${testResult.value.duration_ms} ms）` : ''
      ElMessage.success(`连接测试成功${elapsed}`)
    } else {
      ElMessage.warning(testResult.value.message)
    }
  } catch (e) {
    testResult.value = {
      success: false,
      message: e.response?.data?.message || e.response?.data?.detail || e.message
    }
    ElMessage.error('连接测试失败')
  } finally {
    testing.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.mb16 { margin-bottom: 16px; }
.mt16 { margin-top: 16px; }
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.form-tip {
  margin-left: 8px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.api-key-block { width: 100%; }
</style>
