<template>
  <div class="page-container" v-loading="loading">
    <div class="page-header"><h2>班级知识图谱</h2></div>
    <el-card shadow="never">
      <el-select v-model="classId" placeholder="班级" @change="changeClass">
        <el-option v-for="item in classes" :key="item.id" :value="item.id" :label="item.name" />
      </el-select>
      <el-select v-model="subjectId" placeholder="任教学科" @change="loadGraph">
        <el-option v-for="item in subjects" :key="item.id" :value="item.id" :label="item.name" />
      </el-select>
      <el-button @click="loadGraph">刷新</el-button>
    </el-card>
    <ErrorState v-if="error" :message="error" @retry="loadGraph" />
    <template v-else-if="graph">
      <p>班级 {{ graph.student_count }} 名学生 · 绿色为掌握较好、红色为薄弱；未采集数据的知识点按难度显示。</p>
      <el-alert v-if="graph.truncated" title="图谱已限制为 600 个节点，请按学科缩小范围" type="warning" :closable="false" />
      <el-card shadow="never">
        <EChart v-if="graph.nodes.length" :option="option" height="min(550px, 65vh)" @chart-click="selectNode" />
        <el-empty v-else description="暂无已发布知识点" />
      </el-card>
      <el-card v-if="current" shadow="never" class="mt12">
        <template #header>{{ current.name }}</template>
        <p>薄弱学生 {{ current.weak_students }} 人 · 已测 {{ current.tracked_students }} 人 · 未测 {{ current.unknown_students }} 人</p>
        <p>常见错因：{{ Object.entries(current.error_reasons).map(([reason, count]) => `${reason} ${count} 次`).join('、') || '暂无记录' }}</p>
        <el-button @click="toggle(current.id)">{{ selected.includes(current.id) ? '移出专项作业' : '加入专项作业' }}</el-button>
      </el-card>
      <el-card shadow="never" class="mt12">
        <template #header>专项作业 · 已选择 {{ selected.length }} 个知识点</template>
        <el-tag v-for="id in selected" :key="id" closable @close="toggle(id)">{{ graph.nodes.find(item => item.id === id)?.name }}</el-tag>
        <el-form :inline="true" class="mt12">
          <el-form-item label="题量"><el-input-number v-model="count" :min="1" :max="30" /></el-form-item>
          <el-form-item label="截止天数"><el-input-number v-model="days" :min="1" :max="30" /></el-form-item>
          <el-button type="primary" :loading="publishing" :disabled="!selected.length" @click="publish">发布到本班</el-button>
        </el-form>
        <p v-if="published">已发布任务 #{{ published.task_id }}，实际 {{ published.question_count }} 题。</p>
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { eduApi } from '@/api'
import { extensionApi } from '@/api/extensions'
import { buildGraphOption } from '@/utils/knowledgeGraph'
import EChart from '@/components/EChart.vue'
import ErrorState from '@/components/ErrorState.vue'
import { useUserStore } from '@/store/user'

const classes = ref([])
const subjects = ref([])
const classId = ref(null)
const subjectId = ref(null)
const graph = ref(null)
const current = ref(null)
const selected = ref([])
const count = ref(10)
const days = ref(7)
const loading = ref(false)
const publishing = ref(false)
const published = ref(null)
const error = ref('')
const store = useUserStore()
const assignments = ref([])
let graphRequest = 0
let classRequest = 0
onBeforeUnmount(() => { graphRequest++; classRequest++ })
const option = computed(() => buildGraphOption({ nodes: graph.value?.nodes || [], edges: graph.value?.edges || [], useMastery: true }))
async function changeClass() {
  const requestId = ++classRequest
  graphRequest++; graph.value = null; selected.value = []; current.value = null; published.value = null
  const klass = classes.value.find(item => item.id === classId.value)
  if (!klass) return
  const response = await eduApi.subjects({ grade_id: klass.grade_id })
  if (requestId !== classRequest) return
  const items = response.data.items || response.data
  subjects.value = store.permissions.roles?.includes('teacher') && !store.permissions.roles?.some(role => ['sys_admin', 'grade_admin'].includes(role))
    ? items.filter(subject => assignments.value.some(item => item.class_id === classId.value && item.subject_id === subject.id))
    : items
  subjectId.value = subjects.value[0]?.id
  selected.value = []; current.value = null
  await loadGraph()
}
async function loadGraph() {
  const requestId = ++graphRequest
  selected.value = []; current.value = null; published.value = null; graph.value = null
  if (!classId.value || !subjectId.value) { loading.value = false; return }
  loading.value = true; error.value = ''
  try {
    const response = await extensionApi.classGraph({ class_id: classId.value, subject_id: subjectId.value })
    if (requestId === graphRequest) graph.value = response.data
  } catch { if (requestId === graphRequest) error.value = '班级图谱加载失败，请检查任教关系后重试' }
  finally { if (requestId === graphRequest) loading.value = false }
}
function selectNode(params) { if (params.dataType === 'node') current.value = params.data.raw }
function toggle(id) { selected.value = selected.value.includes(id) ? selected.value.filter(item => item !== id) : [...selected.value, id] }
async function publish() {
  publishing.value = true
  try {
    published.value = (await extensionApi.assign({
      class_id: classId.value, subject_id: subjectId.value, knowledge_point_ids: selected.value, count: count.value, due_days: days.value
    })).data
    ElMessage.success(published.value.reused ? '已复用刚才发布的同一份作业' : '专项作业已发布')
  } finally { publishing.value = false }
}
onMounted(async () => {
  try {
    if (store.permissions.roles?.includes('teacher') && !store.permissions.roles?.some(role => ['sys_admin', 'grade_admin'].includes(role))) {
      const result = await eduApi.teachingAssignments({ teacher_id: store.userInfo.id })
      assignments.value = result.data.items || result.data
    }
    const response = await eduApi.classes({ page_size: 100 })
    classes.value = response.data.items || response.data
    classId.value = classes.value[0]?.id
    await changeClass()
  } catch { error.value = '班级信息加载失败，请重试' }
})
</script>

<style scoped>
.mt12 { margin-top: 12px; }
.el-select { margin-right: 10px; }
.el-tag { margin-right: 6px; }
</style>
