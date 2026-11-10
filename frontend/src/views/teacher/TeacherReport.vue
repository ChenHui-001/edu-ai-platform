<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">教学报表</h2>
      <div>
        <el-button :icon="Download" :loading="exporting" @click="onExport">导出 Excel</el-button>
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
            <template #empty><TableEmpty text="暂无知识点数据" /></template>
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

    <el-card shadow="never" class="mb16">
      <template #header>
        <div class="flex-between">
          <b>班级薄弱知识点（按正确率升序）</b>
          <div>
            <el-tag v-if="weakSummary.below_60" size="small" type="danger">
              低于 60%：{{ weakSummary.below_60 }} 个
            </el-tag>
            <el-tag v-if="weakSummary.point_count" size="small" type="info">
              覆盖 {{ weakSummary.point_count }} 个知识点 / {{ weakSummary.student_count }} 名学生
            </el-tag>
          </div>
        </div>
      </template>
      <el-table v-loading="loadingWeak" :data="weakPoints" border stripe max-height="360">
        <template #empty><TableEmpty text="暂无掌握度数据（学生做过题后才会产生）" /></template>
        <el-table-column type="index" label="#" width="56" align="center" />
        <el-table-column prop="name" label="知识点" min-width="160" show-overflow-tooltip />
        <el-table-column prop="subject_name" label="学科" width="90" />
        <el-table-column label="正确率" width="170">
          <template #default="{ row }">
            <el-progress :percentage="Math.min(row.accuracy || 0, 100)"
                         :color="effectColor(row.accuracy)" />
          </template>
        </el-table-column>
        <el-table-column prop="weak_students" label="未掌握人数" width="110" align="center" />
        <el-table-column prop="answer_count" label="作答数" width="90" align="center" />
        <el-table-column prop="suggestion" label="讲评建议" min-width="220" show-overflow-tooltip />
      </el-table>
    </el-card>

    <el-card shadow="never">
      <template #header><b>班级横向对比</b></template>
      <el-table v-loading="loading" :data="comparison" border stripe>
        <template #empty><TableEmpty text="暂无提交记录" /></template>
        <el-table-column type="index" label="排名" width="70" align="center">
          <template #default="{ $index }">
            <el-tag :type="$index < 3 ? 'success' : 'info'" size="small">第 {{ $index + 1 }} 名</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="学生" width="120" />
        <el-table-column prop="submission_count" label="提交次数" width="110" align="center" />
        <el-table-column prop="avg_score_rate" label="得分率" width="100" align="center">
          <template #default="{ row }">{{ row.avg_score_rate ?? 0 }}%</template>
        </el-table-column>
        <el-table-column prop="avg_score" label="均分" width="90" align="center" />
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
import { ElMessage } from 'element-plus'
import { reportApi, eduApi, taskApi } from '@/api'
import { downloadBlob } from '@/utils/download'

const classes = ref([])
const tasks = ref([])
const classId = ref(null)
const taskId = ref(null)
const overview = ref(null)
const comparison = ref([])
const effect = ref([])
const weakPoints = ref([])
const weakSummary = ref({})
const loading = ref(false)
const loadingEffect = ref(false)
const loadingWeak = ref(false)

const cards = computed(() => overview.value ? [
  { label: '班级人数', value: overview.value.student_count },
  { label: '参与人数', value: overview.value.active_students },
  // 得分率口径（score/total_score）：不同试卷满分不同，原始分不可横向比较
  { label: '平均得分率', value: `${overview.value.avg_score_rate ?? 0}%` },
  { label: '及格率', value: `${overview.value.pass_rate ?? 0}%` },
  { label: '完成率', value: `${overview.value.completion_rate ?? 0}%` }
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
  // 薄弱知识点与任务无关（按班级聚合掌握度），单独加载、失败不影响上面两块
  loadWeak()
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

/**
 * 班级薄弱知识点。
 *
 * 与「知识点教学效果评估」并列但**不等价**：那个按任务看（要有 task_id），
 * 这个直接按班级聚合 `edu_knowledge_mastery`，选完班级就能看，
 * 备课场景用得上（"这个班二次函数只有 41%"）。不依赖 taskId，所以独立加载。
 */
async function loadWeak() {
  if (!classId.value) { weakPoints.value = []; weakSummary.value = {}; return }
  loadingWeak.value = true
  try {
    const res = await reportApi.classWeakPoints({ class_id: classId.value, limit: 10 })
    const d = res.data || {}
    weakPoints.value = d.items || []
    weakSummary.value = d.summary || {}
  } catch {
    // 掌握度表为空（新班级还没做过题）时后端正常返回空数组，
    // 走到这里说明真出错，保留空态即可，不打断整页
    weakPoints.value = []
    weakSummary.value = {}
  } finally {
    loadingWeak.value = false
  }
}

// 导出按钮 loading（P2-11）：导出是纯等待动作（拼 xlsx / 拉 blob），
// 没有 loading 时按钮毫无反馈，用户会连点造成重复下载。
const exporting = ref(false)

async function onExport() {
  if (exporting.value) return
  exporting.value = true
  try {
    await exportExcel()
  } finally {
    exporting.value = false
  }
}

async function exportExcel() {
  // 教学报表按班级导出：report_type=class_overview 必须配 class_id，
  // 否则后端会落到全站总览分支（教师无权查看）；裸 URL 还带不上 token。
  if (!classId.value) return ElMessage.warning('请先选择班级再导出')
  await downloadBlob(
    reportApi.exportExcel({ report_type: 'class_overview', class_id: classId.value }),
    '教学报表.xlsx')
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
