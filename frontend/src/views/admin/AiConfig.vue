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
      <el-descriptions :column="3" border>
        <el-descriptions-item label="提供商">
          <el-tag size="small">{{ providerLabel(config.LLM_PROVIDER) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="模型">{{ config.LLM_MODEL || '-' }}</el-descriptions-item>
        <el-descriptions-item label="API 地址">{{ masked(config.LLM_BASE_URL) }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

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
          <el-input v-model="form.llm_api_key" type="password" show-password
                    placeholder="输入大模型服务的 API Key" clearable />
          <div class="form-tip" v-if="form.llm_provider === 'ollama'">
            Ollama 本地部署无需 API Key，留空即可
          </div>
        </el-form-item>

        <el-form-item label="API 地址">
          <el-input v-model="form.llm_base_url" placeholder="https://api.deepseek.com/v1" clearable />
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
          <span class="form-tip">Token</span>
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
          <el-descriptions :column="2" border>
            <el-descriptions-item label="模型">{{ testResult.model }}</el-descriptions-item>
            <el-descriptions-item label="输入 Token">{{ testResult.usage?.input_tokens }}</el-descriptions-item>
            <el-descriptions-item label="输出 Token">{{ testResult.usage?.output_tokens }}</el-descriptions-item>
          </el-descriptions>
        </template>
      </el-result>
    </el-card>

    <!-- 提供商说明 -->
    <el-card shadow="never" class="mt16">
      <template #header><b>提供商说明</b></template>
      <el-table :data="providerTable" border size="small">
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
import { Refresh, Connection, Check, Cpu } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const config = ref({})
const providers = ref({})
const testResult = ref(null)

const form = ref({
  llm_enabled: true,
  llm_provider: 'deepseek',
  llm_api_key: '',
  llm_base_url: '',
  llm_model: '',
  llm_temperature: 0.7,
  llm_max_tokens: 4096,
  llm_timeout: 60
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
    providers.value = data.providers
    // 填充表单
    const c = data.config
    form.value = {
      llm_enabled: c.LLM_ENABLED ?? true,
      llm_provider: c.LLM_PROVIDER || 'deepseek',
      llm_api_key: c.LLM_API_KEY || '',
      llm_base_url: c.LLM_BASE_URL || '',
      llm_model: c.LLM_MODEL || '',
      llm_temperature: c.LLM_TEMPERATURE ?? 0.7,
      llm_max_tokens: c.LLM_MAX_TOKENS ?? 4096,
      llm_timeout: c.LLM_TIMEOUT ?? 60
    }
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  try {
    const res = await request.put('/system/ai-config', form.value)
    ElMessage.success(res.data.message || 'AI 配置已保存')
    await load()
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function testConnection() {
  testing.value = true
  testResult.value = null
  try {
    const res = await request.post('/system/ai-config/test', {
      llm_provider: form.value.llm_provider,
      llm_api_key: form.value.llm_api_key,
      llm_base_url: form.value.llm_base_url,
      llm_model: form.value.llm_model
    })
    testResult.value = res.data
    if (testResult.value.success) {
      ElMessage.success('连接测试成功')
    } else {
      ElMessage.warning(testResult.value.message)
    }
  } catch (e) {
    testResult.value = { success: false, message: e.response?.data?.detail || e.message }
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
  color: #909399;
}
</style>
