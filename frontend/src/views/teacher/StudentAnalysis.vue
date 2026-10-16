<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">学生个体分析</h2>
      <div>
        <el-select v-model="classId" placeholder="选择班级" style="width:190px" @change="onClassChange">
          <el-option v-for="c in classes" :key="c.id" :label="`${c.grade_name} ${c.name}`" :value="c.id" />
        </el-select>
        <el-select v-model="studentId" placeholder="选择学生" filterable style="width:190px"
                   @change="loadDetail">
          <el-option v-for="s in students" :key="s.id" :label="`${s.real_name}（${s.username}）`" :value="s.id" />
        </el-select>
      </div>
    </div>

    <el-empty v-if="!studentId" description="请先选择班级与学生" />

    <template v-else-if="detail">
      <el-row :gutter="16" class="mb16">
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
            <template #header><b>{{ detail.student?.name }} 成绩趋势</b></template>
            <ReactEcharts :option="trendOption" style="height: 300px" />
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="never">
            <template #header><b>知识点掌握情况</b></template>
            <ReactEcharts v-if="radar.length >= 3" :option="radarOption" style="height: 300px" />
            <el-empty v-else description="知识点数据不足（需答题关联知识点）" :image-size="60" />
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-card shadow="never">
            <template #header><b>薄弱知识点 Top10</b></template>
            <el-table :data="weakTable" border size="small" max-height="330">
              <el-table-column prop="name" label="知识点" min-width="150" />
              <el-table-column prop="mastery" label="掌握度" width="110">
                <template #default="{ row }">
                  <el-progress :percentage="Math.min(row.mastery, 100)"
                               :color="row.mastery >= 60 ? '#67c23a' : '#f56c6c'" />
                </template>
              </el-table-column>
              <el-table-column prop="wrong_count" label="错题数" width="80" align="center" />
            </el-table>
            <el-empty v-if="!weakTable.length" description="暂无薄弱点记录" :image-size="60" />
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="never">
            <template #header><b>历次成绩</b></template>
            <el-table :data="detail.score_trend || []" border size="small" max-height="330">
              <el-table-column prop="name" label="任务" min-width="180" show-overflow-tooltip />
              <el-table-column prop="score" label="得分" width="80" align="center" />
              <el-table-column prop="rank" label="排名" width="70" align="center" />
              <el-table-column prop="date" label="提交时间" width="160" />
            </el-table>
            <el-empty v-if="!(detail.score_trend || []).length" description="暂无成绩记录" :image-size="60" />
          </el-card>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import ReactEcharts from 'echarts-for-react'
import { reportApi, eduApi, systemApi, learningApi } from '@/api'

const route = useRoute()
const classes = ref([])
const students = ref([])
const classId = ref(null)
const studentId = ref(null)
const detail = ref(null)
const mastery = ref(null)

const cards = computed(() => {
  if (!detail.value) return []
  const trend = detail.value.score_trend || []
  const scores = trend.map(t => t.score || 0)
  const ranks = trend.map(t => t.rank).filter(Boolean)
  const total = trend.length
  return [
    { label: '参加次数', value: total },
    { label: '平均分', value: scores.length ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1) : 0 },
    { label: '最高分', value: scores.length ? Math.max(...scores) : 0 },
    { label: '最低分', value: scores.length ? Math.min(...scores) : 0 },
    { label: '最佳排名', value: ranks.length ? Math.min(...ranks) : '-' },
    { label: '平均掌握度', value: mastery.value ? `${mastery.value.avg_mastery}%` : '-' }
  ]
})

const radar = computed(() => mastery.value?.items || [])

const trendOption = computed(() => {
  const trend = detail.value?.score_trend || []
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 30, top: 30, bottom: 50 },
    xAxis: { type: 'category', data: trend.map(t => t.name?.slice(0, 8) || ''), axisLabel: { rotate: 30 } },
    yAxis: { type: 'value', name: '分数' },
    series: [{
      type: 'line', smooth: true, data: trend.map(t => t.score),
      itemStyle: { color: '#2f6fd0' }, areaStyle: { opacity: 0.12 }
    }]
  }
})

const radarOption = computed(() => {
  const items = radar.value.slice(0, 10)
  return {
    tooltip: {},
    radar: {
      indicator: items.map(i => ({ name: i.name.slice(0, 8), max: 100 })),
      radius: '65%'
    },
    series: [{
      type: 'radar', data: [{ value: items.map(i => i.mastery), name: '掌握度' }],
      areaStyle: { opacity: 0.25, color: '#2f6fd0' }
    }]
  }
})

const weakTable = computed(() => mastery.value?.weak_points || [])

async function loadStudents() {
  if (!classId.value) return
  // 学生下拉：人员简表（后端按任教班级校验；/system/users 教师必 403）
  const res = await eduApi.peopleBrief({ identity: 'student', class_id: classId.value })
  students.value = res.data.data?.items || []
}

function onClassChange() {
  loadStudents()
  studentId.value = null
  detail.value = null
}

async function loadDetail() {
  if (!studentId.value) return
  const res = await reportApi.studentDetail({ student_id: studentId.value })
  detail.value = res.data.data
  const m = await learningApi.masteryMap()
  mastery.value = m.data.data
}

onMounted(async () => {
  const res = await eduApi.classes({ page_size: 100 })
  classes.value = res.data.data?.items || []
  if (route.query.class_id) {
    classId.value = Number(route.query.class_id)
  } else if (classes.value.length) {
    classId.value = classes.value[0].id
  }
  if (classId.value) {
    await loadStudents()
    if (route.query.student_id) {
      studentId.value = Number(route.query.student_id)
      await loadDetail()
    }
  }
})
</script>

<style scoped>
.mb16 { margin-bottom: 16px; }
</style>
