<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">学习报表</h2>
      <div>
        <el-button :icon="Download" @click="exportExcel">导出 Excel</el-button>
        <el-button :icon="Refresh" @click="loadAll">刷新</el-button>
      </div>
    </div>

    <el-row :gutter="16" class="mb16" v-if="overview">
      <el-col :span="5" v-for="c in cards" :key="c.label">
        <div class="stat-card">
          <div class="stat-value" :style="{ color: c.color }">{{ c.value }}</div>
          <div class="stat-label">{{ c.label }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="mb16">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>
            <div class="flex-between">
              <b>成绩趋势</b>
              <el-select v-model="subjectId" placeholder="全部学科" clearable size="small"
                         style="width:130px" @change="loadTrend">
                <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
              </el-select>
            </div>
          </template>
          <ReactEcharts v-if="trend.length" :option="trendOption" style="height: 300px" />
          <el-empty v-else description="暂无成绩数据" :image-size="60" />
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card shadow="never">
          <template #header><b>知识点掌握雷达</b></template>
          <ReactEcharts v-if="radar.length >= 3" :option="radarOption" style="height: 300px" />
          <el-empty v-else description="知识点数据不足（需答题关联知识点）" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="mb16">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><b>错题分析</b></template>
          <ReactEcharts v-if="wrong.total > 0" :option="wrongOption" style="height: 300px" />
          <el-empty v-else description="暂无错题，继续保持！" :image-size="60" />
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card shadow="never">
          <template #header>
            <div class="flex-between">
              <b>AI 个性化学习建议</b>
              <el-button size="small" type="primary" plain :loading="sugLoading" @click="loadSuggestion">
                重新生成
              </el-button>
            </div>
          </template>
          <div v-loading="sugLoading">
            <div v-if="suggestion?.summary" class="advice-summary">{{ suggestion.summary }}</div>

            <template v-if="suggestion?.weak_points?.length">
              <el-divider content-position="left">薄弱知识点</el-divider>
              <div class="tag-wrap">
                <el-tag v-for="w in suggestion.weak_points" :key="w" type="danger" size="small" class="mr4">
                  {{ w }}
                </el-tag>
              </div>
            </template>

            <template v-if="suggestion?.advice?.length">
              <el-divider content-position="left">提升建议</el-divider>
              <ul class="advice-list">
                <li v-for="(a, i) in suggestion.advice" :key="i">{{ a }}</li>
              </ul>
            </template>

            <template v-if="suggestion?.daily_plan?.length">
              <el-divider content-position="left">近期计划</el-divider>
              <div v-for="(d, i) in suggestion.daily_plan" :key="i" class="day-item">
                <b>Day {{ i + 1 }}</b>
                <ul>
                  <li v-for="(t, j) in (d.tasks || d.items || [])" :key="j">{{ t }}</li>
                </ul>
              </div>
            </template>

            <el-empty v-if="!sugLoading && !suggestion?.summary" description="点击「重新生成」获取 AI 建议" :image-size="60" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never">
      <template #header><b>错题高频知识点 Top10</b></template>
      <el-table :data="wrong.knowledge_rank || []" border stripe max-height="320">
        <el-table-column type="index" label="排名" width="80" align="center">
          <template #default="{ $index }">
            <el-tag :type="$index < 3 ? 'danger' : 'info'" size="small">No.{{ $index + 1 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="知识点" min-width="200" />
        <el-table-column prop="count" label="错题数" width="110" align="center" />
        <el-table-column label="占比" width="180">
          <template #default="{ row }">
            <el-progress :percentage="pct(row.count)" status="exception" />
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!(wrong.knowledge_rank || []).length" description="暂无数据" :image-size="60" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import ReactEcharts from 'echarts-for-react'
import { Refresh, Download } from '@element-plus/icons-vue'
import { reportApi, eduApi } from '@/api'

const overview = ref(null)
const trend = ref([])
const radar = ref([])
const wrong = ref({})
const suggestion = ref(null)
const subjects = ref([])
const subjectId = ref(null)
const sugLoading = ref(false)

const cards = computed(() => overview.value ? [
  { label: '累计做题', value: overview.value.question_total, color: '#2f6fd0' },
  { label: '总体正确率', value: `${overview.value.accuracy}%`, color: '#67c23a' },
  { label: '未掌握错题', value: overview.value.wrong_unmastered, color: '#f56c6c' },
  { label: '今日学习(分)', value: overview.value.study_minutes_today, color: '#e6a23c' },
  { label: '7日学习(分)', value: overview.value.study_minutes_7d, color: '#67c23a' }
] : [])

const trendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 45, right: 20, top: 30, bottom: 50 },
  xAxis: { type: 'category', data: trend.value.map(t => (t.name || t.task_title || '').slice(0, 8)),
           axisLabel: { rotate: 30, fontSize: 10 } },
  yAxis: { type: 'value', name: '分数' },
  series: [{ type: 'line', smooth: true, data: trend.value.map(t => t.score),
             itemStyle: { color: '#2f6fd0' }, areaStyle: { opacity: 0.12 } }]
}))

const radarOption = computed(() => {
  const items = radar.value.slice(0, 8)
  return {
    tooltip: {},
    radar: { indicator: items.map(i => ({ name: (i.name || i.subject_name || '').slice(0, 7), max: 100 })), radius: '62%' },
    series: [{ type: 'radar', data: [{ value: items.map(i => i.mastery ?? i.value), name: '掌握度' }],
               areaStyle: { opacity: 0.25, color: '#2f6fd0' } }]
  }
})

const wrongOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0 },
  series: [{
    type: 'pie', radius: ['38%', '66%'], center: ['50%', '44%'],
    data: (wrong.value.reason_distribution || []).map(r => ({ name: r.reason, value: r.count })),
    label: { formatter: '{b}: {c}' }
  }]
}))

function pct(count) {
  const max = Math.max(...(wrong.value.knowledge_rank || []).map(k => k.count), 1)
  return Math.round((count / max) * 100)
}

async function loadOverview() {
  const res = await reportApi.studentOverview()
  overview.value = res.data
}

async function loadTrend() {
  const res = await reportApi.scoreTrend(subjectId.value ? { subject_id: subjectId.value } : {})
  trend.value = res.data || []
}

async function loadRadar() {
  const res = await reportApi.knowledgeRadar(subjectId.value ? { subject_id: subjectId.value } : {})
  radar.value = res.data || []
}

async function loadWrong() {
  const res = await reportApi.wrongAnalysis(subjectId.value ? { subject_id: subjectId.value } : {})
  wrong.value = res.data || {}
}

async function loadSuggestion() {
  sugLoading.value = true
  try {
    const res = await reportApi.learningSuggestion()
    suggestion.value = res.data
    ElMessage.success('AI 建议已更新')
  } finally {
    sugLoading.value = false
  }
}

async function loadAll() {
  await Promise.all([loadOverview(), loadTrend(), loadRadar(), loadWrong(), loadSuggestion()])
}

async function exportExcel() {
  // 同 ScoreCenter：blob 下载 + report_type 必填
  const res = await reportApi.exportExcel({ report_type: 'student_overview' })
  const url = URL.createObjectURL(res.data)
  const a = document.createElement('a')
  a.href = url
  a.download = `学习总览报表.xlsx`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(async () => {
  await loadAll()
  const s = await eduApi.subjects()
  subjects.value = s.data.data || []
})
</script>

<style scoped>
.flex-between { display: flex; align-items: center; justify-content: space-between; }
.mb16 { margin-bottom: 16px; }
.mt8 { margin-top: 8px; }
.mr4 { margin-right: 4px; }
.tag-wrap { line-height: 2.2; }
.advice-summary {
  background: #f0f6ff; padding: 12px; border-radius: 8px; line-height: 1.9;
  border-left: 3px solid var(--el-color-primary);
}
.advice-list { margin: 0; padding-left: 20px; line-height: 2; }
.day-item { margin-top: 8px; }
.day-item ul { margin: 4px 0 0; padding-left: 20px; line-height: 1.9; }
</style>
