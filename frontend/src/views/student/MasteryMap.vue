<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">掌握度图谱</h2>
      <div>
        <el-select v-model="subjectFilter" placeholder="选择学科" clearable style="width:140px"
                   @change="load">
          <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
        </el-select>
        <el-button :icon="Refresh" @click="load" class="ml8">刷新</el-button>
      </div>
    </div>

    <el-row :gutter="16" class="mb16" v-loading="loading">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-value" :style="{ color: avgColor }">{{ data.avg_mastery || 0 }}%</div>
          <div class="stat-label">平均掌握度</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-value" style="color:#f56c6c">{{ data.weak_points?.length || 0 }}</div>
          <div class="stat-label">薄弱知识点</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-value" style="color:#67c23a">{{ data.strong_points?.length || 0 }}</div>
          <div class="stat-label">已精通知识点</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-value">{{ data.items?.length || 0 }}</div>
          <div class="stat-label">学习知识点总数</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :span="12">
        <el-card shadow="never" v-loading="loading">
          <template #header><b>知识点掌握度雷达图</b></template>
          <div ref="radarChart" style="height: 360px"></div>
          <el-empty v-if="!loading && !data.items?.length" description="暂无掌握度数据，去练习几道题吧" :image-size="60" />
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card shadow="never" v-loading="loading">
          <template #header><b>知识点掌握度排行（热力色）</b></template>
          <div ref="barChart" style="height: 360px"></div>
          <el-empty v-if="!loading && !data.items?.length" description="暂无数据" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="mt16" v-if="data.weak_points?.length">
      <template #header>
        <div class="flex-between">
          <b>薄弱知识点（优先攻克）</b>
          <el-button type="warning" size="small" :icon="Edit" @click="practiceWeak">薄弱专项练习</el-button>
        </div>
      </template>
      <div class="weak-list">
        <div v-for="w in data.weak_points" :key="w.knowledge_point_id" class="weak-item"
             @click="practiceOne(w)">
          <div class="weak-info">
            <span class="weak-name">{{ w.name }}</span>
            <span class="weak-stat">做 {{ w.total_count }} 题 · 对 {{ w.correct_count }} · 错 {{ w.wrong_count }}</span>
          </div>
          <div class="weak-bar-wrap">
            <div class="weak-bar" :style="{ width: w.mastery + '%', background: masteryColor(w.mastery) }"></div>
          </div>
          <span class="weak-mastery" :style="{ color: masteryColor(w.mastery) }">{{ w.mastery }}%</span>
          <el-button size="small" type="primary" text>去练习</el-button>
        </div>
      </div>
    </el-card>

    <el-card shadow="never" class="mt16" v-if="data.strong_points?.length">
      <template #header><b>已精通知识点（继续保持）</b></template>
      <el-tag v-for="s in data.strong_points" :key="s.knowledge_point_id"
              type="success" effect="plain" class="strong-tag">
        {{ s.name }} {{ s.mastery }}%
      </el-tag>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, Edit } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { learningApi } from '@/api'
import { fetchSubjects, currentGradeId, resolveSubjectId } from '@/utils/subject'

const router = useRouter()
const loading = ref(false)
const data = ref({})
const subjects = ref([])
const subjectFilter = ref(null)

const radarChart = ref(null)
const barChart = ref(null)
let radarInst = null
let barInst = null

const avgColor = computed(() => {
  const v = data.value.avg_mastery || 0
  if (v >= 80) return '#67c23a'
  if (v >= 60) return '#e6a23c'
  return '#f56c6c'
})

function masteryColor(v) {
  if (v >= 80) return '#67c23a'
  if (v >= 60) return '#e6a23c'
  if (v >= 40) return '#f0a020'
  return '#f56c6c'
}

async function load() {
  loading.value = true
  try {
    // 去重代表 id 指向最低年级，直接查会得到本年级的空白掌握图谱
    const sid = resolveSubjectId(subjects.value, subjectFilter.value, currentGradeId())
    const res = await learningApi.masteryMap(sid ? { subject_id: sid } : {})
    data.value = res.data
    await nextTick()
    renderCharts()
  } finally {
    loading.value = false
  }
}

async function loadSubjects() {
  subjects.value = await fetchSubjects({ gradeId: currentGradeId() })
}

function renderCharts() {
  const items = data.value.items || []
  if (!items.length) return

  // 雷达图
  if (radarChart.value) {
    if (!radarInst) radarInst = echarts.init(radarChart.value)
    const top = items.slice(0, 10)
    radarInst.setOption({
      tooltip: { trigger: 'item' },
      radar: {
        indicator: top.map(i => ({ name: i.name.length > 6 ? i.name.slice(0, 6) + '...' : i.name, max: 100 })),
        radius: '65%',
        splitArea: { areaStyle: { color: ['#f5f7fa', '#fff'] } },
        axisLabel: { fontSize: 11 }
      },
      series: [{
        type: 'radar',
        data: [{ value: top.map(i => i.mastery), name: '掌握度', areaStyle: { color: 'rgba(64,158,255,0.2)' }, lineStyle: { color: '#409eff' }, itemStyle: { color: '#409eff' } }]
      }]
    })
  }

  // 横向条形图
  if (barChart.value) {
    if (!barInst) barInst = echarts.init(barChart.value)
    const sorted = [...items].sort((a, b) => b.mastery - a.mastery)
    barInst.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: 120, right: 40, top: 10, bottom: 10 },
      xAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
      yAxis: { type: 'category', data: sorted.map(i => i.name.length > 10 ? i.name.slice(0, 10) + '...' : i.name),
               axisLabel: { fontSize: 11 } },
      series: [{
        type: 'bar',
        data: sorted.map(i => ({
          value: i.mastery,
          itemStyle: { color: masteryColor(i.mastery) }
        })),
        label: { show: true, position: 'right', formatter: '{c}%', fontSize: 11 },
        barWidth: '60%'
      }]
    })
  }
}

function practiceOne(kp) {
  router.push({ path: '/student/practice', query: { kp: kp.knowledge_point_id, subject: kp.subject_id } })
}

function practiceWeak() {
  const weak = data.value.weak_points || []
  if (!weak.length) return ElMessage.info('暂无薄弱知识点')
  router.push({ path: '/student/practice', query: { kps: weak.map(w => w.knowledge_point_id).join(','), subject: weak[0].subject_id } })
}

function handleResize() {
  radarInst?.resize()
  barInst?.resize()
}

onMounted(async () => {
  await loadSubjects()
  await load()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  radarInst?.dispose()
  barInst?.dispose()
})
</script>

<style scoped>
.mb16 { margin-bottom: 16px; }
.mt16 { margin-top: 16px; }
.ml8 { margin-left: 8px; }
.stat-card {
  text-align: center;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}
.stat-value { font-size: 28px; font-weight: 700; color: #409eff; }
.stat-label { font-size: 12px; color: #909399; margin-top: 4px; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
.weak-list { display: flex; flex-direction: column; gap: 8px; }
.weak-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}
.weak-item:hover { background: #ecf5ff; }
.weak-info { flex: 1; min-width: 0; }
.weak-name { font-weight: 500; font-size: 14px; }
.weak-stat { font-size: 12px; color: #909399; margin-left: 8px; }
.weak-bar-wrap { width: 120px; height: 8px; background: #ebeef5; border-radius: 4px; overflow: hidden; }
.weak-bar { height: 100%; border-radius: 4px; transition: width 0.3s; }
.weak-mastery { font-size: 13px; font-weight: 600; width: 40px; text-align: right; }
.strong-tag { margin: 4px; }
</style>
