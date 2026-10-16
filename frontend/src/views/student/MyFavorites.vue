<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">题目收藏</h2>
      <div>
        <el-button type="primary" :icon="Promotion" @click="generatePractice"
                   :disabled="!list.length">收藏专项练习</el-button>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
      </div>
    </div>

    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="query">
        <el-form-item label="标签">
          <el-select v-model="query.tag" placeholder="全部" clearable style="width:140px">
            <el-option v-for="t in tags" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="题干">
          <el-input v-model="query.keyword" placeholder="关键词" clearable style="width:180px"
                    @keyup.enter="load" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="load">查询</el-button>
          <el-button :icon="Refresh" @click="reset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-row :gutter="12" class="mb12">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-value">{{ total }}</div>
          <div class="stat-label">收藏总数</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-value">{{ tags.length }}</div>
          <div class="stat-label">标签数</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-value">{{ typeCount }}</div>
          <div class="stat-label">题型种类</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-value" style="color:#67c23a">{{ recentCount }}</div>
          <div class="stat-label">近 7 天新增</div>
        </div>
      </el-col>
    </el-row>

    <el-empty v-if="!loading && !list.length" description="收藏夹是空的，做题时点击星标收藏好题！" />

    <div v-loading="loading">
      <el-card v-for="(item, idx) in list" :key="item.id" shadow="never" class="fav-card">
        <div class="fav-head">
          <b>第 {{ idx + 1 }} 题</b>
          <el-tag size="small" class="ml4">{{ TYPES[item.type] || item.type }}</el-tag>
          <el-tag v-if="item.difficulty" size="small" :type="diffType(item.difficulty)" class="ml4">
            {{ diffLabel(item.difficulty) }}
          </el-tag>
          <span v-if="item.subject_name" class="ml8 text-muted">{{ item.subject_name }}</span>
          <span v-if="item.knowledge_point_name" class="ml8 text-muted">{{ item.knowledge_point_name }}</span>
          <el-tag v-if="item.tag" size="small" type="warning" effect="plain" class="ml8">{{ item.tag }}</el-tag>
          <span class="fav-date">{{ formatDate(item.created_at) }}</span>
        </div>

        <p class="stem" v-html="item.stem"></p>

        <div v-if="item.options" class="options">
          <div v-for="o in parseOptions(item.options)" :key="o.key" class="opt-line">
            <b>{{ o.key }}.</b> {{ o.text }}
          </div>
        </div>

        <div class="fav-footer">
          <el-input v-if="editingId === item.id" v-model="editTag" placeholder="标签（如：考前必看）"
                    size="small" style="width:200px" />
          <el-button v-if="editingId === item.id" type="primary" size="small"
                     @click="saveTag(item)">保存</el-button>
          <el-button v-if="editingId === item.id" size="small" @click="editingId = null">取消</el-button>
          <el-button v-else size="small" :icon="Edit" @click="startEdit(item)">改标签</el-button>
          <el-button type="danger" size="small" :icon="Delete" @click="remove(item)">取消收藏</el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Promotion, Refresh, Search, Edit, Delete } from '@element-plus/icons-vue'
import TYPES, { questionTypeLabel } from '@/constants/question'
import { learningApi } from '@/api'

const router = useRouter()
const loading = ref(false)
const list = ref([])
const total = ref(0)
const tags = ref([])
const editingId = ref(null)
const editTag = ref('')

const query = ref({ tag: '', keyword: '' })


const typeCount = computed(() => new Set(list.value.map(i => i.type)).size)
const recentCount = computed(() => {
  const now = new Date()
  const week = 7 * 24 * 60 * 60 * 1000
  return list.value.filter(i => {
    if (!i.created_at) return false
    const d = typeof i.created_at === 'string' ? new Date(i.created_at) : i.created_at
    return now - d < week
  }).length
})

function diffLabel(d) {
  return { easy: '简单', medium: '中等', hard: '困难' }[d] || d
}
function diffType(d) {
  return { easy: 'success', medium: 'warning', hard: 'danger' }[d] || 'info'
}
function parseOptions(opts) {
  if (!opts) return []
  if (Array.isArray(opts)) return opts
  try { return JSON.parse(opts) } catch { return [] }
}
function formatDate(d) {
  if (!d) return ''
  const s = typeof d === 'string' ? d : String(d)
  return s.slice(0, 10)
}

async function load() {
  loading.value = true
  try {
    const res = await learningApi.favorites({
      page: 1, page_size: 100,
      tag: query.value.tag || undefined,
      keyword: query.value.keyword || undefined
    })
    list.value = res.data.items
    total.value = res.data.total
    tags.value = res.data.tags || []
  } finally {
    loading.value = false
  }
}

function reset() {
  query.value = { tag: '', keyword: '' }
  load()
}

function startEdit(item) {
  editingId.value = item.id
  editTag.value = item.tag || ''
}

async function saveTag(item) {
  await learningApi.addFavorite({ question_id: item.question_id, tag: editTag.value })
  item.tag = editTag.value
  editingId.value = null
  ElMessage.success('标签已更新')
  load()
}

async function remove(item) {
  await ElMessageBox.confirm('确定取消收藏该题？', '提示', { type: 'warning' })
  await learningApi.removeFavorite(item.id)
  ElMessage.success('已取消收藏')
  load()
}

const generating = ref(false)
async function generatePractice() {
  if (generating.value) return
  try {
    const res = await learningApi.favoritesPractice({})
    ElMessage.success(res.message)
    router.push(`/student/exam/${res.data.task_id}`)
  } finally {
    generating.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.filter-card { margin-bottom: 16px; }
.mb12 { margin-bottom: 12px; }
.stat-card {
  text-align: center;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}
.stat-value { font-size: 24px; font-weight: 700; color: #409eff; }
.stat-label { font-size: 12px; color: #909399; margin-top: 4px; }
.fav-card { margin-bottom: 12px; }
.fav-head { display: flex; align-items: center; flex-wrap: wrap; gap: 4px; margin-bottom: 8px; }
.ml4 { margin-left: 4px; }
.ml8 { margin-left: 8px; }
.text-muted { color: #909399; font-size: 12px; }
.fav-date { margin-left: auto; font-size: 12px; color: #c0c4cc; }
.stem { font-size: 14px; line-height: 1.8; margin: 8px 0; }
.options { margin: 8px 0; }
.opt-line { padding: 4px 0; font-size: 13px; }
.fav-footer { display: flex; gap: 8px; align-items: center; margin-top: 8px; }
</style>
