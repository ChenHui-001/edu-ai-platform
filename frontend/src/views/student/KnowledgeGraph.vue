<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">知识图谱</h2>
      <div class="header-actions">
        <el-button :icon="Refresh" :loading="loading" @click="loadGraph">刷新</el-button>
      </div>
    </div>

    <el-card shadow="never" class="filter-card">
      <div class="filters">
        <el-select v-model="form.grade_id" class="f-select" placeholder="年级"
                   :disabled="isStudent" @change="onGradeChange">
          <el-option v-for="g in grades" :key="g.id" :value="g.id" :label="g.name" />
        </el-select>
        <el-select v-model="form.subject_id" class="f-select" placeholder="学科"
                   @change="onSubjectChange">
          <el-option v-for="s in subjects" :key="s.id" :value="s.id" :label="s.name" />
        </el-select>
        <el-select v-model="form.root_id" class="f-center" filterable clearable remote
                   :remote-method="searchNodes" :loading="searching"
                   placeholder="定位知识点（输入名称搜索）" @change="onCenterChange">
          <el-option v-for="n in centerOptions" :key="n.id" :value="n.id" :label="n.name" />
        </el-select>
        <el-radio-group v-model="form.depth" :disabled="!form.root_id" @change="loadGraph">
          <el-radio-button :value="1">1 层</el-radio-button>
          <el-radio-button :value="2">2 层</el-radio-button>
          <el-radio-button :value="3">3 层</el-radio-button>
        </el-radio-group>
        <el-switch v-model="form.showHierarchy" active-text="层级连线"
                   @change="loadGraph" />
        <el-button v-if="form.root_id" text @click="clearCenter">取消定位</el-button>
      </div>
      <div class="legend-tip">
        <span class="dot dot-hard" /> 硬先修
        <span class="dot dot-soft" /> 软先修
        <span class="dot dot-hier" /> 教材层级
        <span class="muted">· 点击节点查看详情，双击以该知识点为中心展开</span>
      </div>
    </el-card>

    <el-row :gutter="16" class="mt12">
      <el-col :xs="24" :lg="17">
        <el-card shadow="never" v-loading="loading" class="chart-card">
          <template #header>
            <div class="flex-between">
              <b>关系网络</b>
              <span class="muted">
                {{ graph.counts.nodes }} 节点 · {{ graph.counts.prereq_edges }} 先修边
                <template v-if="graph.counts.hierarchy_edges">
                  · {{ graph.counts.hierarchy_edges }} 层级边
                </template>
              </span>
            </div>
          </template>

          <el-alert v-if="graph.truncated" class="mb10" type="warning" :closable="false"
                    show-icon
                    title="节点过多已截断"
                    :description="`当前范围超过 ${limit} 个知识点，只显示前 ${limit} 个。可缩小到单个单元或用「定位知识点」展开局部。`" />

          <EChart v-if="graph.nodes.length" :option="option" height="620px"
                  @chart-click="onChartClick" />
          <el-empty v-else description="当前年级/学科暂无已发布知识点" :image-size="80" />
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="7">
        <el-card shadow="never" class="detail-card">
          <template #header><b>节点详情</b></template>
          <template v-if="current">
            <h3 class="node-title">{{ current.name }}</h3>
            <div class="meta">
              <el-tag size="small" effect="plain">{{ current.grade_name || '—' }}</el-tag>
              <el-tag v-if="current.difficulty" size="small" effect="plain">
                {{ difficultyLabel(current.difficulty) }}
              </el-tag>
              <el-tag size="small" type="info" effect="plain">
                {{ current.question_count || 0 }} 题
              </el-tag>
              <el-tag v-if="hasMastery" size="small"
                      :type="current.mastery >= 80 ? 'success' : (current.mastery >= 60 ? 'warning' : 'danger')"
                      effect="plain">
                掌握度 {{ current.mastery }}
              </el-tag>
            </div>
            <div v-if="current.path" class="muted path-line">{{ current.path }}</div>

            <el-divider content-position="left">
              先修（{{ prereqOfCurrent.length }}）
            </el-divider>
            <div v-if="prereqOfCurrent.length" class="rel-list">
              <div v-for="item in prereqOfCurrent" :key="`p-${item.id}`" class="rel-item"
                   @click="focusNode(item.id)">
                <el-tag size="small" :type="item.strength === 'hard' ? 'danger' : 'info'"
                        effect="plain">
                  {{ item.strength === 'hard' ? '硬' : '软' }}
                </el-tag>
                <span class="rel-name">{{ item.name }}</span>
              </div>
            </div>
            <div v-else class="muted mb10">无先修要求</div>

            <el-divider content-position="left">
              后继（{{ dependentsOfCurrent.length }}）
            </el-divider>
            <div v-if="dependentsOfCurrent.length" class="rel-list">
              <div v-for="item in dependentsOfCurrent" :key="`d-${item.id}`" class="rel-item"
                   @click="focusNode(item.id)">
                <el-tag size="small" type="info" effect="plain">后</el-tag>
                <span class="rel-name">{{ item.name }}</span>
              </div>
            </div>
            <div v-else class="muted mb10">暂无后继知识点</div>

            <div class="detail-actions">
              <el-button type="primary" size="small" @click="focusNode(current.id)">
                以它为中心
              </el-button>
              <el-button size="small" @click="goPractice(current)">
                去练习
              </el-button>
            </div>
          </template>
          <el-empty v-else description="点击左侧任意节点查看详情" :image-size="70" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import EChart from '@/components/EChart.vue'
import { eduApi, knowledgeApi } from '@/api'
import { useUserStore } from '@/store/user'
import { buildGraphOption } from '@/utils/knowledgeGraph'

const LIMIT = 600
const router = useRouter()
const userStore = useUserStore()
const isStudent = computed(() => userStore.isStudent)

const loading = ref(false)
const searching = ref(false)
const grades = ref([])
const subjects = ref([])
const centerOptions = ref([])
const selectedId = ref(null)
const limit = LIMIT

const form = reactive({
  grade_id: null,
  subject_id: null,
  root_id: null,
  depth: 2,
  showHierarchy: true
})

const graph = reactive({
  nodes: [],
  edges: [],
  counts: { nodes: 0, edges: 0, prereq_edges: 0, hierarchy_edges: 0 },
  truncated: false
})

const current = computed(
  () => graph.nodes.find(node => Number(node.id) === Number(selectedId.value)) || null
)
const hasMastery = computed(
  () => current.value && current.value.mastery !== null
    && current.value.mastery !== undefined
)

function neighbors(kind) {
  const id = Number(current.value?.id)
  const byId = new Map(graph.nodes.map(node => [Number(node.id), node]))
  return graph.edges
    .filter(edge => edge.kind === 'prereq')
    .filter(edge => (kind === 'prereq'
      ? Number(edge.target) === id
      : Number(edge.source) === id))
    .map(edge => {
      const otherId = kind === 'prereq' ? Number(edge.source) : Number(edge.target)
      const node = byId.get(otherId)
      return node ? { ...node, strength: edge.strength } : null
    })
    .filter(Boolean)
}

const prereqOfCurrent = computed(() => (current.value ? neighbors('prereq') : []))
const dependentsOfCurrent = computed(() => (current.value ? neighbors('dependents') : []))

const option = computed(() => buildGraphOption({
  nodes: graph.nodes,
  edges: graph.edges,
  selectedId: selectedId.value,
  useMastery: isStudent.value,
  showHierarchy: form.showHierarchy
}))

function difficultyLabel(value) {
  return { easy: '简单', medium: '中等', hard: '较难', challenge: '挑战' }[value] || value
}

async function loadGrades() {
  const res = await eduApi.grades()
  const items = res.data?.items || res.data || []
  grades.value = isStudent.value && userStore.userInfo?.grade_id
    ? items.filter(g => Number(g.id) === Number(userStore.userInfo.grade_id))
    : items
  form.grade_id = grades.value[0]?.id ?? userStore.userInfo?.grade_id ?? null
}

async function loadSubjects() {
  const res = await eduApi.subjects({ grade_id: form.grade_id })
  const items = res.data?.items || res.data || []
  subjects.value = items
  if (!items.some(item => Number(item.id) === Number(form.subject_id))) {
    const math = items.find(item => item.name === '数学')
    form.subject_id = math?.id ?? items[0]?.id ?? null
  }
}

async function onGradeChange() {
  form.root_id = null
  selectedId.value = null
  await loadSubjects()
  await loadGraph()
}

async function onSubjectChange() {
  form.root_id = null
  selectedId.value = null
  centerOptions.value = []
  await loadGraph()
}

async function loadGraph() {
  if (!form.subject_id) return
  loading.value = true
  try {
    const res = await knowledgeApi.graph({
      grade_id: form.grade_id || undefined,
      subject_id: form.subject_id,
      root_id: form.root_id || undefined,
      depth: form.depth,
      include_hierarchy: form.showHierarchy
    })
    const data = res.data || {}
    graph.nodes = data.nodes || []
    graph.edges = data.edges || []
    graph.counts = data.counts || { nodes: 0, edges: 0, prereq_edges: 0, hierarchy_edges: 0 }
    graph.truncated = Boolean(data.truncated)
    if (form.root_id && graph.nodes.some(n => Number(n.id) === Number(form.root_id))) {
      selectedId.value = Number(form.root_id)
    } else if (!graph.nodes.some(n => Number(n.id) === Number(selectedId.value))) {
      selectedId.value = null
    }
  } catch {
    graph.nodes = []
    graph.edges = []
    graph.counts = { nodes: 0, edges: 0, prereq_edges: 0, hierarchy_edges: 0 }
  } finally {
    loading.value = false
  }
}

async function searchNodes(keyword) {
  const text = String(keyword || '').trim()
  if (!text) return
  searching.value = true
  try {
    const res = await knowledgeApi.list({
      grade_id: form.grade_id || undefined,
      subject_id: form.subject_id,
      keyword: text,
      status: 'published'
    })
    const items = res.data?.items || res.data || []
    centerOptions.value = items.slice(0, 30)
  } catch {
    centerOptions.value = []
  } finally {
    searching.value = false
  }
}

function onCenterChange(value) {
  if (!value) {
    clearCenter()
    return
  }
  loadGraph()
}

function clearCenter() {
  form.root_id = null
  selectedId.value = null
  loadGraph()
}

function onChartClick(params) {
  if (params.dataType !== 'node') return
  selectedId.value = Number(params.data.id)
}

function focusNode(id) {
  form.root_id = Number(id)
  if (!centerOptions.value.some(n => Number(n.id) === Number(id))) {
    centerOptions.value = [...centerOptions.value, { id: Number(id), name: current.value?.name || `#${id}` }]
  }
  loadGraph()
}

function goPractice(node) {
  if (!node) return
  router.push({
    path: '/student/practice',
    query: { subject: form.subject_id, kp: node.id }
  })
}

onMounted(async () => {
  try {
    await loadGrades()
    await loadSubjects()
    await loadGraph()
  } catch {
    ElMessage.error('图谱加载失败，请稍后重试')
  }
})
</script>

<style scoped>
.filter-card { margin-bottom: 12px; }
.filters { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
.f-select { width: 120px; }
.f-center { width: 280px; }
.legend-tip {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--el-text-color-regular);
  flex-wrap: wrap;
}
.dot { width: 14px; height: 3px; border-radius: 2px; display: inline-block; }
.dot-hard { background: #f56c6c; }
.dot-soft { background: #909399; }
.dot-hier { background: #c0c4cc; }
.mt12 { margin-top: 12px; }
.mb10 { margin-bottom: 10px; }
.flex-between { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.muted { color: var(--el-text-color-secondary); font-size: 12px; }
.path-line { margin: 6px 0 4px; word-break: break-all; }
.node-title { margin: 0 0 8px; font-size: 16px; }
.meta { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 6px; }
.rel-list { display: flex; flex-direction: column; gap: 6px; max-height: 220px; overflow: auto; }
.rel-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 6px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  cursor: pointer;
}
.rel-item:hover { background: var(--el-fill-color-light); }
.rel-name { font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.detail-actions { margin-top: 12px; display: flex; gap: 8px; }
</style>
