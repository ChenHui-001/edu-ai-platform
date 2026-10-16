<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">错题本</h2>
      <div>
        <el-button :icon="Download" @click="exportWrong">导出</el-button>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
      </div>
    </div>

    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="query">
        <el-form-item label="学科">
          <el-select v-model="query.subject_id" placeholder="全部" clearable style="width:130px">
            <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="错因">
          <el-select v-model="query.error_reason" placeholder="全部" clearable style="width:130px">
            <el-option v-for="r in REASONS" :key="r" :label="r" :value="r" />
          </el-select>
        </el-form-item>
        <el-form-item label="掌握状态">
          <el-select v-model="query.is_mastered" placeholder="全部" clearable style="width:120px">
            <el-option label="未掌握" :value="false" />
            <el-option label="已掌握" :value="true" />
          </el-select>
        </el-form-item>
        <el-form-item label="题干">
          <el-input v-model="query.keyword" placeholder="关键词" clearable style="width:160px"
                    @keyup.enter="load" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="load">查询</el-button>
          <el-button :icon="Refresh" @click="reset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-row :gutter="16" class="mb12">
      <el-col :span="6" v-for="c in cards" :key="c.label">
        <div class="stat-card">
          <div class="stat-value">{{ c.value }}</div>
          <div class="stat-label">{{ c.label }}</div>
        </div>
      </el-col>
    </el-row>

    <el-empty v-if="!loading && !list.length" description="错题本是空的，继续保持！" />

    <el-card v-for="w in list" :key="w.id" shadow="never" class="wrong-card">
      <div class="wrong-head">
        <div>
          <el-tag size="small" :type="diffTag(w.difficulty)">{{ DIFF[w.difficulty] }}</el-tag>
          <el-tag size="small" effect="plain" class="ml4">{{ TYPES[w.type] || w.type }}</el-tag>
          <el-tag v-if="w.knowledge_point_name" size="small" type="info" class="ml4">
            {{ w.knowledge_point_name }}
          </el-tag>
        </div>
        <div>
          <el-tag v-if="w.is_mastered" type="success" size="small">已掌握</el-tag>
          <el-tag v-else type="danger" size="small">未掌握 · 错 {{ w.error_count }} 次</el-tag>
        </div>
      </div>

      <p class="stem" v-html="w.stem"></p>
      <p v-if="parse(w.options)?.length" class="opts">
        <span v-for="o in parse(w.options)" :key="o.key"
              :class="{ wrong: isMyWrong(o.key, w.wrong_answer), right: isRight(o.key, w.answer) }">
          {{ o.key }}. {{ o.text }}
        </span>
      </p>

      <el-descriptions :column="2" border size="small" class="mt12">
        <el-descriptions-item label="我的答案">
          <span class="text-danger">{{ format(w.wrong_answer) }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="正确答案">
          <span class="text-success">{{ format(w.answer) }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="题目解析" :span="2">{{ w.analysis || '-' }}</el-descriptions-item>
        <el-descriptions-item v-if="w.error_reason" label="错因标注">
          <el-tag size="small" type="warning">{{ w.error_reason }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item v-if="w.source_name" label="来源">{{ w.source_name }}</el-descriptions-item>
        <el-descriptions-item v-if="w.ai_reason" label="AI 错因分析" :span="2">
          {{ w.ai_reason }}
        </el-descriptions-item>
      </el-descriptions>

      <div class="wrong-actions">
        <el-button size="small" :icon="MagicStick" @click="analyze(w)">AI 分析错因</el-button>
        <el-button size="small" :icon="RefreshRight" @click="redo(w)">重做同类题</el-button>
        <el-button size="small" type="warning" :icon="MagicStick" :loading="variantLoading===w.id"
                   @click="variant(w)">变式练习</el-button>
        <el-dropdown @command="(c) => markReason(w, c)" trigger="click">
          <el-button size="small">标注错因<el-icon class="el-icon--right"><ArrowDown /></el-icon></el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item v-for="r in REASONS" :key="r" :command="r">{{ r }}</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button size="small" type="success" plain @click="markMastered(w)">
          {{ w.is_mastered ? '取消掌握' : '标记已掌握' }}
        </el-button>
      </div>
    </el-card>

    <el-pagination v-if="total > query.page_size" class="mt16" background
                   layout="total, prev, pager, next" :total="total"
                   v-model:current-page="query.page" @current-change="load" />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, MagicStick, RefreshRight, ArrowDown, Download } from '@element-plus/icons-vue'
import TYPES, { questionTypeLabel } from '@/constants/question'
import { learningApi, eduApi } from '@/api'

const DIFF = { easy: '简单', medium: '中等', hard: '困难' }
const REASONS = ['概念不清', '审题错误', '计算失误', '公式记错', '知识遗忘', '方法不会', '粗心大意']
const router = useRouter()

const list = ref([])
const subjects = ref([])
const total = ref(0)
const loading = ref(false)
const variantLoading = ref(null)
const query = reactive({ page: 1, page_size: 20, subject_id: null, error_reason: '', is_mastered: null, keyword: '' })

const cards = computed(() => [
  { label: '错题总数', value: total.value },
  { label: '本页未掌握', value: list.value.filter(w => !w.is_mastered).length },
  { label: '本页已掌握', value: list.value.filter(w => w.is_mastered).length },
  { label: '高频错题(≥3次)', value: list.value.filter(w => w.error_count >= 3).length }
])

function diffTag(d) { return { easy: 'success', medium: 'warning', hard: 'danger' }[d] || '' }
function parse(v) { if (!v) return null; try { return typeof v === 'string' ? JSON.parse(v) : v } catch { return null } }
function format(v) {
  if (v === null || v === undefined || v === '') return '未作答'
  if (typeof v === 'object') return Array.isArray(v) ? v.join(',') : JSON.stringify(v)
  return String(v)
}
function isMyWrong(key, wrong) {
  const arr = Array.isArray(wrong) ? wrong : String(wrong || '').split(/[,，\s]+/)
  return arr.includes(key)
}
function isRight(key, answer) {
  const a = parse(answer)
  if (a && typeof a === 'object') return (a.correct || a.answer || []).includes?.(key)
  const arr = Array.isArray(answer) ? answer : String(answer || '').split(/[,，\s]+/)
  return arr.includes(key)
}

async function load() {
  loading.value = true
  try {
    const res = await learningApi.wrongQuestions(query)
    const d = res.data || {}
    list.value = d.items || []
    total.value = d.total || 0
  } finally {
    loading.value = false
  }
}

function reset() {
  Object.assign(query, { page: 1, subject_id: null, error_reason: '', is_mastered: null, keyword: '' })
  load()
}

const analyzing = ref(false)
async function analyze(w) {
  if (analyzing.value) return
  analyzing.value = true
  try {
    const res = await learningApi.analyzeWrong(w.id)
    const d = res.data
    // AI 输出（可能回显题目/作答原文）先转义再进 HTML 弹窗，防注入
    const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => (
      { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    ))
    ElMessageBox.alert(
      `<b>AI 错因分析</b><br/>${esc(d.analysis) || '-'}` +
      (d.error_points?.length ? `<br/><br/><b>失分点：</b>${esc(d.error_points.join('、'))}` : ''),
      'AI 分析', { dangerouslyUseHTMLString: true }
    )
    w.ai_reason = d.analysis
  } finally {
    analyzing.value = false
  }
}

const redoing = ref(false)
async function redo(w) {
  if (redoing.value) return
  redoing.value = true
  try {
    const res = await learningApi.redoWrong(w.id)
    const d = res.data
    ElMessage.success(`已生成 ${d.count || d.items?.length || 0} 道同类练习题`)
  } finally {
    redoing.value = false
  }
}

const varianting = ref(false)
async function variant(w) {
  if (varianting.value) return
  varianting.value = true
  variantLoading.value = w.id
  try {
    const res = await learningApi.wrongVariant(w.id)
    ElMessage.success(res.message)
    router.push(`/student/exam/${res.data.task_id}`)
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '变式练习生成失败')
  } finally {
    variantLoading.value = null
  }
}

async function markReason(w, reason) {
  await learningApi.updateWrong(w.id, { error_reason: reason })
  ElMessage.success('错因已标注')
  w.error_reason = reason
}

async function markMastered(w) {
  await learningApi.updateWrong(w.id, { is_mastered: !w.is_mastered })
  ElMessage.success(w.is_mastered ? '已取消掌握标记' : '已标记为掌握')
  load()
}

async function exportWrong() {
  const res = await fetch(`/api/v1/learning/wrong-questions/export?${new URLSearchParams(query)}`, {
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  })
  if (!res.ok) return ElMessage.error('导出失败')
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `错题本_${new Date().toISOString().slice(0, 10)}.md`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(async () => {
  await load()
  const s = await eduApi.subjects()
  subjects.value = s.data.data || []
})
</script>

<style scoped>
.mb12 { margin-bottom: 16px; }
.mt12 { margin-top: 12px; }
.mt16 { margin-top: 16px; justify-content: flex-end; }
.ml4 { margin-left: 4px; }
.wrong-card { margin-bottom: 16px; }
.wrong-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.stem { line-height: 1.8; margin: 8px 0; font-size: 15px; }
.opts { margin: 8px 0; line-height: 2; }
.opts span { display: inline-block; margin-right: 20px; padding: 2px 6px; border-radius: 4px; }
.opts .wrong { background: #fef0f0; color: #f56c6c; text-decoration: line-through; }
.opts .right { background: #f0f9eb; color: #67c23a; font-weight: 600; }
.text-danger { color: #f56c6c; }
.text-success { color: #67c23a; }
.wrong-actions { margin-top: 12px; display: flex; gap: 8px; flex-wrap: wrap; }
.filter-card :deep(.el-form-item) { margin-bottom: 12px; }
</style>
