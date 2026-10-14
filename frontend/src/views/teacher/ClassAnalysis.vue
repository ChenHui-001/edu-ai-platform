<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">班级学情分析</h2>
      <el-select v-model="classId" placeholder="选择班级" style="width:200px" @change="loadAll">
        <el-option v-for="c in classes" :key="c.id" :label="`${c.grade_name} ${c.name}`" :value="c.id" />
      </el-select>
    </div>

    <el-empty v-if="!classId" description="请先选择要分析的班级" />

    <template v-else>
      <el-row :gutter="16" class="mb16" v-if="overview">
        <el-col :span="4" v-for="c in cards" :key="c.label">
          <div class="stat-card">
            <div class="stat-value">{{ c.value }}</div>
            <div class="stat-label">{{ c.label }}</div>
          </div>
        </el-col>
      </el-row>

      <el-row :gutter="16" class="mb16">
        <el-col :span="12">
          <el-card shadow="never">
            <template #header><b>成绩分布</b></template>
            <ReactEcharts v-if="overview" :option="distOption" style="height: 300px" />
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="never">
            <template #header><b>学生成绩排名</b></template>
            <ReactEcharts v-if="comparison.length" :option="rankOption" style="height: 300px" />
            <el-empty v-else description="暂无成绩数据" :image-size="60" />
          </el-card>
        </el-col>
      </el-row>

      <el-card shadow="never">
        <template #header><b>学生明细</b></template>
        <el-table v-loading="loading" :data="comparison" border stripe>
          <el-table-column type="index" label="#" width="50" align="center" />
          <el-table-column prop="student_name" label="学生" width="110" />
          <el-table-column prop="score" label="总分" width="90" align="center" />
          <el-table-column prop="avg_score" label="平均分" width="100" align="center" />
          <el-table-column prop="accuracy" label="正确率" width="100" align="center">
            <template #default="{ row }">
              <el-progress :percentage="Math.min(row.accuracy || 0, 100)"
                           :color="progressColor(row.accuracy)" style="width:90px" />
            </template>
          </el-table-column>
          <el-table-column prop="submission_count" label="提交次数" width="100" align="center" />
          <el-table-column prop="last_submit" label="最近提交" width="160" />
          <el-table-column label="评价" width="90">
            <template #default="{ row }">
              <el-tag :type="row.accuracy >= 80 ? 'success' : row.accuracy >= 60 ? 'warning' : 'danger'"
                      size="small">
                {{ row.accuracy >= 80 ? '优秀' : row.accuracy >= 60 ? '中等' : '待提升' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="110">
            <template #default="{ row }">
              <el-button link type="primary" @click="goStudent(row)">个体分析</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import ReactEcharts from 'echarts-for-react'
import { reportApi, eduApi } from '@/api'

const router = useRouter()
const classes = ref([])
const classId = ref(null)
const overview = ref(null)
const comparison = ref([])
const loading = ref(false)

const cards = computed(() => overview.value ? [
  { label: '班级人数', value: overview.value.student_count },
  { label: '参与人数', value: overview.value.active_students },
  { label: '平均分', value: overview.value.avg_score },
  { label: '最高分', value: overview.value.max_score },
  { label: '最低分', value: overview.value.min_score },
  { label: '及格率', value: `${overview.value.pass_rate}%` }
] : [])

const distOption = computed(() => {
  const bands = overview.value?.score_bands || {}
  return {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie', radius: ['40%', '68%'], center: ['50%', '45%'],
      data: Object.entries(bands).map(([name, value]) => ({ name, value })),
      label: { formatter: '{b}: {c} 人' }
    }]
  }
})

const rankOption = computed(() => {
  const sorted = [...comparison.value].sort((a, b) => (b.avg_score || 0) - (a.avg_score || 0))
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 90, right: 30, top: 20, bottom: 40 },
    xAxis: { type: 'value', name: '平均分' },
    yAxis: {
      type: 'category', data: sorted.map(s => s.student_name).reverse(),
      axisLabel: { fontSize: 11 }
    },
    series: [{
      type: 'bar', data: sorted.map(s => s.avg_score || 0).reverse(),
      itemStyle: { color: '#2f6fd0' }, barMaxWidth: 16,
      label: { show: true, position: 'right', fontSize: 11 }
    }]
  }
})

function progressColor(v) {
  if (v >= 80) return '#67c23a'
  if (v >= 60) return '#e6a23c'
  return '#f56c6c'
}

async function loadAll() {
  if (!classId.value) return
  loading.value = true
  try {
    const [o, c] = await Promise.all([
      reportApi.classOverview({ class_id: classId.value }),
      reportApi.studentComparison({ class_id: classId.value })
    ])
    overview.value = o.data.data
    comparison.value = c.data.data || []
  } finally {
    loading.value = false
  }
}

function goStudent(row) {
  router.push({ name: 'StudentAnalysis', query: { student_id: row.student_id, class_id: classId.value } })
}

onMounted(async () => {
  const res = await eduApi.classes({ page_size: 100 })
  classes.value = res.data.data?.items || []
  if (classes.value.length) {
    classId.value = classes.value[0].id
    loadAll()
  }
})
</script>

<style scoped>
.mb16 { margin-bottom: 16px; }
</style>
