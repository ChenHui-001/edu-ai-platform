<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">系统报表</h2>
      <div>
        <el-button :icon="Download" @click="exportExcel">导出 Excel</el-button>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
      </div>
    </div>

    <template v-if="overview">
      <el-row :gutter="16" class="mb16">
        <el-col :span="6" v-for="c in userCards" :key="c.label">
          <div class="stat-card">
            <div class="stat-value">{{ c.value }}</div>
            <div class="stat-label">{{ c.label }}</div>
          </div>
        </el-col>
      </el-row>

      <el-row :gutter="16" class="mb16">
        <el-col :span="6" v-for="c in contentCards" :key="c.label">
          <div class="stat-card">
            <div class="stat-value">{{ c.value }}</div>
            <div class="stat-label">{{ c.label }}</div>
          </div>
        </el-col>
      </el-row>

      <el-row :gutter="16" class="mb16">
        <el-col :span="6" v-for="c in examCards" :key="c.label">
          <div class="stat-card">
            <div class="stat-value">{{ c.value }}</div>
            <div class="stat-label">{{ c.label }}</div>
          </div>
        </el-col>
      </el-row>
    </template>

    <el-row :gutter="16">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><b>各年级教学数据对比</b></template>
          <el-table v-loading="loadingGrade" :data="grades" border stripe>
            <el-table-column prop="grade_name" label="年级" width="110" />
            <el-table-column prop="user_count" label="用户数" width="90" align="center" />
            <el-table-column prop="question_count" label="题量" width="90" align="center" />
            <el-table-column prop="submission_count" label="提交数" width="90" align="center" />
            <el-table-column prop="avg_score_rate" label="平均得分率" width="110" align="center">
              <template #default="{ row }">{{ row.avg_score_rate ?? 0 }}%</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card shadow="never">
          <template #header><b>各学科题量分布</b></template>
          <EChart :option="subjectOption" style="height: 320px" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="mt16">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><b>AI 引擎运行统计</b></template>
          <el-table :data="aiRows" border>
            <el-table-column prop="label" label="指标" />
            <el-table-column prop="value" label="数量" width="120" align="center" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><b>系统运行状况</b></template>
          <el-descriptions :column="1" border v-if="runtime">
            <el-descriptions-item label="服务器时间">{{ runtime.server_time }}</el-descriptions-item>
            <el-descriptions-item label="运行时长">{{ runtime.uptime }}</el-descriptions-item>
            <el-descriptions-item label="在线用户">{{ runtime.online_users }}</el-descriptions-item>
            <el-descriptions-item label="数据库">{{ runtime.database }}</el-descriptions-item>
            <el-descriptions-item label="向量库">{{ runtime.vector_db }}</el-descriptions-item>
            <el-descriptions-item label="编排模式">{{ runtime.orchestrator }}</el-descriptions-item>
            <el-descriptions-item label="大模型">{{ runtime.llm }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import EChart from '@/components/EChart.vue'
import { Refresh, Download } from '@element-plus/icons-vue'
import { reportApi } from '@/api'

const overview = ref(null)
const grades = ref([])
const subjects = ref([])
const runtime = ref(null)
const loadingGrade = ref(false)

const userCards = computed(() => !overview.value ? [] : [
  { label: '用户总数', value: overview.value.user.total },
  { label: '学生数', value: overview.value.user.student },
  { label: '教师数', value: overview.value.user.teacher },
  { label: '7日活跃', value: overview.value.user.active_7d }
])
const contentCards = computed(() => !overview.value ? [] : [
  { label: '题目总数', value: overview.value.content.question },
  { label: '已上架题目', value: overview.value.content.published_question },
  { label: '试卷数', value: overview.value.content.paper },
  { label: '知识点数', value: overview.value.content.knowledge_point }
])
const examCards = computed(() => !overview.value ? [] : [
  { label: '作业考试数', value: overview.value.exam.task },
  { label: '提交总数', value: overview.value.exam.submission },
  { label: '全局平均分', value: overview.value.exam.avg_score },
  { label: '待审批用户', value: overview.value.user.pending }
])
const aiRows = computed(() => !overview.value ? [] : [
  { label: 'AI 调用总数', value: overview.value.ai.calls },
  { label: '失败次数', value: overview.value.ai.failed },
  { label: '规则降级次数', value: overview.value.ai.fallback },
  { label: '成功率', value: overview.value.ai.calls
      ? `${((overview.value.ai.calls - overview.value.ai.failed) / overview.value.ai.calls * 100).toFixed(2)}%`
      : '0%' }
])

const subjectOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 50, right: 20, top: 30, bottom: 40 },
  xAxis: { type: 'category', data: subjects.value.map(s => s.subject), axisLabel: { rotate: 30 } },
  yAxis: { type: 'value', name: '题目数' },
  series: [
    { name: '题目数', type: 'bar', data: subjects.value.map(s => s.question_count),
      itemStyle: { color: '#2f6fd0' }, barMaxWidth: 28 },
    { name: '笔记数', type: 'line', data: subjects.value.map(s => s.note_count),
      itemStyle: { color: '#e6a23c' } }
  ]
}))

async function load() {
  loadingGrade.value = true
  try {
    const [o, g, s, r] = await Promise.all([
      reportApi.adminOverview(), reportApi.gradeComparison(),
      reportApi.subjectComparison(), reportApi.systemRuntime()
    ])
    overview.value = o.data
    grades.value = g.data || []
    subjects.value = s.data || []
    runtime.value = r.data
  } finally {
    loadingGrade.value = false
  }
}

function exportExcel() {
  window.open(reportApi.exportUrl({ scope: 'admin' }), '_blank')
}

onMounted(load)
</script>

<style scoped>
.mb16 { margin-bottom: 16px; }
.mt16 { margin-top: 16px; }
</style>
