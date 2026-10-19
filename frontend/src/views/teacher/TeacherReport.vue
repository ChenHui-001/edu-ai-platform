<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">教学报表</h2>
      <div>
        <el-button :icon="Download" @click="exportExcel">导出 Excel</el-button>
        <el-button :icon="Refresh" @click="loadAll">刷新</el-button>
      </div>
    </div>

    <el-card shadow="never" class="filter-card">
      <el-form :inline="true">
        <el-form-item label="班级">
          <el-select v-model="classId" placeholder="选择班级" clearable style="width:200px" @change="loadAll">
            <el-option v-for="c in classes" :key="c.id" :label="`${c.grade_name} ${c.name}`" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="任务">
          <el-select v-model="taskId" placeholder="选择作业/考试" clearable filterable style="width:240px"
                     @change="loadEffect">
            <el-option v-for="t in tasks" :key="t.id" :label="t.title" :value="t.id" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <el-row :gutter="16" class="mb16" v-if="overview">
      <el-col :span="6" v-for="c in cards" :key="c.label">
        <div class="stat-card">
          <div class="stat-value">{{ c.value }}</div>
          <div class="stat-label">{{ c.label }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="mb16">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>
            <div class="flex-between">
              <b>知识点教学效果评估</b>
              <el-tag size="small" type="info">正确率越高说明该知识点教学越有效</el-tag>
            </div>
          </template>
          <el-table v-loading="loadingEffect" :data="effect" border stripe max-height="400">
            <el-table-column prop="name" label="知识点" min-width="150" show-overflow-tooltip />
            <el-table-column prop="total_count" label="答题数" width="90" align="center" />
            <el-table-column prop="correct_count" label="答对数" width="90" align="center" />
            <el-table-column label="正确率" width="160">
              <template #default="{ row }">
                <el-progress :percentage="Math.min(row.accuracy || 0, 100)"
                             :color="effectColor(row.accuracy)" />
              </template>
            </el-table-column>
            <el-table-column label="评价" width="100">
              <template #default="{ row }">
                <el-tag :type="effectTag(row.accuracy)" size="small">
                  {{ effectText(row.accuracy) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!loadingEffect && !effect.length" description="请选择任务后查看" :image-size="60" />
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card shadow="never">
          <template #header><b>知识点正确率分布</b></template>
          <EChart v-if="effect.length" :option="effectOption" style="height: 400px" />
          <el-empty v-else description="暂无数据" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never">
      <template #header><b>班级横向对比</b></template>
      <el-table v-loading="loading" :data="comparison" border stripe>
        <el-table-column type="index" label="排名" width="70" align="center">
          <template #default="{ $index }">
            <el-tag :type="$index < 3 ? 'success' : 'info'" size="small">第 {{ $index + 1 }} 名</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="学生" width="120" />
        <el-table-column prop="submission_count" label="提交次数" width="110" align="center" />
        <el-table-column prop="avg_score" label="平均分" width="110" align="center" />
        <el-table-column prop="accuracy" label="正确率" width="170">
          <template #default="{ row }">
            <el-progress :percentage="Math.min(row.accuracy || 0, 100)"
                         :color="effectColor(row.accuracy)" />
          </template>
        </el-table-column>
        <el-table-column prop="last_submit" label="最近提交" width="170" />
        <el-table-column label="综合评价" width="110">
          <template #default="{ row }">
            <el-tag :type="effectTag(row.accuracy)" size="small">{{ effectText(row.accuracy) }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import EChart from '@/components/EChart.vue'
import { Download, Refresh } from '@element-plus/icons-vue'
import { reportApi, eduApi, taskApi } from '@/api'

const classes = ref([])
const tasks = ref([])
const classId = ref(null)
const taskId = ref(null)
const overview = ref(null)
const comparison = ref([])
const effect = ref([])
const loading = ref(false)
const loadingEffect = ref(false)

const cards = computed(() => overview.value ? [
  { label: '班级人数', value: overview.value.student_count },
  { label: '参与人数', value: overview.value.active_students },
  { label: '班级平均分', value: overview.value.avg_score },
  { label: '及格率', value: `${overview.value.pass_rate}%` }
] : [])

const effectOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 50, right: 20, top: 30, bottom: 80 },
  xAxis: { type: 'category', data: effect.value.map(e => e.name.slice(0, 8)),
           axisLabel: { rotate: 45, fontSize: 11 } },
  yAxis: { type: 'value', name: '正确率 %', max: 100 },
  series: [{
    type: 'bar', data: effect.value.map(e => e.accuracy),
    itemStyle: { color: (p) => ['#67c23a', '#e6a23c', '#f56c6c'][effectColorIdx(effect.value[p.dataIndex]?.accuracy)] },
    barMaxWidth: 24,
    label: { show: true, position: 'top', fontSize: 10 }
  }]
}))

function effectColorIdx(v) { return v >= 80 ? 0 : v >= 60 ? 1 : 2 }
function effectColor(v) { return ['#67c23a', '#e6a23c', '#f56c6c'][effectColorIdx(v)] }
function effectTag(v) { return ['success', 'warning', 'danger'][effectColorIdx(v)] }
function effectText(v) { return ['优秀', '合格', '需强化'][effectColorIdx(v)] }

async function loadAll() {
  if (!classId.value) return
  loading.value = true
  try {
    const [o, c] = await Promise.all([
      reportApi.classOverview({ class_id: classId.value, task_id: taskId.value }),
      reportApi.studentComparison({ class_id: classId.value, task_id: taskId.value })
    ])
    overview.value = o.data
    comparison.value = c.data || []
  } finally {
    loading.value = false
  }
}

async function loadEffect() {
  if (!taskId.value) { effect.value = []; return }
  loadingEffect.value = true
  try {
    const res = await reportApi.knowledgeEffect({ class_id: classId.value, task_id: taskId.value })
    // knowledge-effect 返回对象 {items, weak, good, avg_accuracy}，表格用 items。
    // 之前误取整个对象塞给 el-table 导致「data.reduce is not a function」崩溃。
    const d = res.data
    effect.value = Array.isArray(d) ? d : (d?.items || [])
  } finally {
    loadingEffect.value = false
  }
}

function exportExcel() {
  window.open(reportApi.exportUrl({ scope: 'teacher', class_id: classId.value || '' }), '_blank')
}

onMounted(async () => {
  const [c, t] = await Promise.all([
    eduApi.classes({ page_size: 100, mine: true }),
    taskApi.list({ page: 1, page_size: 100 })
  ])
  // /edu/classes 返回数组（非分页 items），两种结构都兼容
  const _cd = c.data
  classes.value = Array.isArray(_cd) ? _cd : (_cd?.items || [])
  tasks.value = t.data?.items || []
  if (classes.value.length) {
    classId.value = classes.value[0].id
    loadAll()
  }
})
</script>

<style scoped>
.flex-between { display: flex; align-items: center; justify-content: space-between; }
.mb16 { margin-bottom: 16px; }
.filter-card :deep(.el-form-item) { margin-bottom: 12px; }
</style>
