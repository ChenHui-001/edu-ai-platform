<template>
  <div class="page-container">
    <div class="welcome-card">
      <div>
        <h2>{{ greeting }}，{{ userStore.realName }}！</h2>
        <p>{{ userStore.roleLabel }} · {{ today }}</p>
      </div>
      <el-button type="primary" @click="$router.push('/agent/chat')">
        <el-icon><MagicStick /></el-icon> 问 AI 助手
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col v-for="s in stats" :key="s.label" :xs="12" :sm="12" :md="6">
        <div class="stat-card" style="margin-bottom: 16px">
          <div class="stat-value" :style="{ color: s.color }">{{ s.value }}</div>
          <div class="stat-label">{{ s.label }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <!-- 学生端：待办 -->
      <el-col v-if="userStore.isStudent && !userStore.isTeacher" :xs="24" :md="14">
        <el-card shadow="never" class="mb">
          <template #header>
            <div class="card-header">
              <span>今日待办</span>
              <el-link type="primary" :underline="false" @click="$router.push('/student/review')">
                全部复习计划
              </el-link>
            </div>
          </template>
          <el-empty v-if="reviewData.today_count === 0" description="今日暂无复习任务，保持学习节奏" :image-size="70" />
          <el-timeline v-else>
            <el-timeline-item
              v-for="p in reviewData.items.filter(i => i.scheduled_date === reviewData.today).slice(0, 6)"
              :key="p.id" :timestamp="p.knowledge_point_name" placement="top"
            >
              {{ p.stage > 1 ? `第 ${p.stage} 轮复习` : '首次复习' }}
              <el-button link type="primary" @click="$router.push('/student/review')">去复习</el-button>
            </el-timeline-item>
          </el-timeline>
        </el-card>

        <el-card shadow="never">
          <template #header><span>我的作业考试</span></template>
          <el-table :data="tasks" size="small" empty-text="暂无任务">
            <el-table-column prop="title" label="名称" />
            <el-table-column prop="type_label" label="类型" width="80" />
            <el-table-column label="截止时间" width="150">
              <template #default="{ row }">
                <span v-if="row.remaining_seconds > 0">
                  剩 {{ formatRemain(row.remaining_seconds) }}
                </span>
                <span v-else style="color:#f56c6c">已截止</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag v-if="row.my_submission" type="success" size="small">已交</el-tag>
                <el-tag v-else type="warning" size="small">待完成</el-tag>
              </template>
            </el-table-column>
            <el-table-column width="80">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="$router.push(`/student/exam/${row.id}`)">
                  进入
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 学生端：学习报表 -->
      <el-col v-if="userStore.isStudent && !userStore.isTeacher" :xs="24" :md="10">
        <el-card shadow="never" class="mb">
          <template #header>
            <div class="card-header">
              <span>成绩趋势</span>
              <el-link type="primary" :underline="false" @click="$router.push('/student/report')">详细报表</el-link>
            </div>
          </template>
          <ReactECharts v-if="trend.length" :option="trendOption" style="height: 260px" />
          <el-empty v-else description="暂无成绩数据" :image-size="70" />
        </el-card>

        <el-card shadow="never">
          <template #header><span>知识点掌握雷达</span></template>
          <ReactECharts v-if="radar.length" :option="radarOption" style="height: 280px" />
          <el-empty v-else description="暂无掌握度数据" :image-size="70" />
        </el-card>
      </el-col>

      <!-- 教师端 -->
      <el-col v-if="userStore.isTeacher" :xs="24" :md="14">
        <el-card shadow="never" class="mb">
          <template #header>
            <div class="card-header">
              <span>待批改</span>
              <el-link type="primary" :underline="false" @click="$router.push('/teacher/grading')">批改中心</el-link>
            </div>
          </template>
          <el-table :data="pending" size="small" empty-text="暂无待批改">
            <el-table-column prop="student_name" label="学生" width="100" />
            <el-table-column prop="task_title" label="任务" show-overflow-tooltip />
            <el-table-column prop="score" label="得分" width="80" />
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="$router.push('/teacher/grading')">批改</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>我发布的任务</span>
              <el-link type="primary" :underline="false" @click="$router.push('/teacher/tasks')">任务管理</el-link>
            </div>
          </template>
          <el-table :data="tasks" size="small" empty-text="暂无任务">
            <el-table-column prop="title" label="名称" show-overflow-tooltip />
            <el-table-column prop="submission_count" label="提交" width="70" />
            <el-table-column label="完成率" width="100">
              <template #default="{ row }">{{ row.completion_rate }}%</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 管理员端 -->
      <el-col v-if="userStore.isAdmin" :xs="24" :md="14">
        <el-card shadow="never">
          <template #header><span>系统运行概览</span></template>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="用户总数">{{ sysStats.user?.total ?? '-' }}</el-descriptions-item>
            <el-descriptions-item label="学生数">{{ sysStats.user?.student ?? '-' }}</el-descriptions-item>
            <el-descriptions-item label="教师数">{{ sysStats.user?.teacher ?? '-' }}</el-descriptions-item>
            <el-descriptions-item label="待审批">{{ sysStats.user?.pending ?? '-' }}</el-descriptions-item>
            <el-descriptions-item label="题库总量">{{ sysStats.content?.question ?? '-' }}</el-descriptions-item>
            <el-descriptions-item label="试卷数">{{ sysStats.content?.paper ?? '-' }}</el-descriptions-item>
            <el-descriptions-item label="AI 调用">{{ sysStats.ai?.calls ?? '-' }}</el-descriptions-item>
            <el-descriptions-item label="AI 失败">{{ sysStats.ai?.failed ?? '-' }}</el-descriptions-item>
          </el-descriptions>
          <el-button type="primary" plain style="margin-top:12px;width:100%"
                     @click="$router.push('/admin/reports')">
            查看完整报表
          </el-button>
        </el-card>
      </el-col>

      <!-- 右侧：AI 助手快捷入口 + 知识点雷达（教师） -->
      <el-col v-if="userStore.isTeacher" :xs="24" :md="10">
        <el-card shadow="never" class="mb">
          <template #header><span>AI 能力快捷入口</span></template>
          <div class="ai-grid">
            <div v-for="a in aiEntries" :key="a.name" class="ai-card" @click="$router.push(a.path)">
              <el-icon :size="24"><component :is="a.icon" /></el-icon>
              <div class="ai-name">{{ a.name }}</div>
            </div>
          </div>
        </el-card>

        <el-card shadow="never">
          <template #header><span>成绩趋势（近 10 次）</span></template>
          <ReactECharts v-if="trend.length" :option="trendOption" style="height: 260px" />
          <el-empty v-else description="暂无数据" :image-size="70" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import ReactECharts from 'echarts-for-react'
import { gradingApi, reportApi, taskApi } from '@/api'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()

const tasks = ref([])
const pending = ref([])
const reviewData = ref({ today_count: 0, items: [] })
const trend = ref([])
const radar = ref([])
const sysStats = ref({})

const today = computed(() => new Date().toLocaleDateString('zh-CN', {
  year: 'numeric', month: 'long', day: 'numeric', weekday: 'long'
}))

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '凌晨好'
  if (h < 12) return '早上好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})

const aiEntries = [
  { name: '智能出题', icon: 'Cpu', path: '/agent/generate' },
  { name: 'AI 组卷', icon: 'Tickets', path: '/agent/generate' },
  { name: '答疑助教', icon: 'ChatLineRound', path: '/agent/chat' },
  { name: '学习规划', icon: 'Compass', path: '/agent/chat' }
]

const stats = computed(() => {
  if (userStore.isStudent && !userStore.isTeacher) {
    return [
      { label: '待复习任务', value: reviewData.value.today_count ?? 0, color: '#2f6fd0' },
      { label: '待完成任务', value: tasks.value.filter(t => !t.my_submission).length, color: '#e6a23c' },
      { label: '已完成任务', value: tasks.value.filter(t => t.my_submission).length, color: '#67c23a' },
      { label: '作业考试', value: tasks.value.length, color: '#909399' }
    ]
  }
  if (userStore.isTeacher) {
    return [
      { label: '发布任务', value: tasks.value.length, color: '#2f6fd0' },
      { label: '待批改', value: pending.value.length, color: '#e6a23c' },
      { label: '学生人数', value: sysStats.value.user?.student ?? 0, color: '#67c23a' },
      { label: '题库总量', value: sysStats.value.content?.question ?? 0, color: '#909399' }
    ]
  }
  return [
    { label: '用户总数', value: sysStats.value.user?.total ?? 0, color: '#2f6fd0' },
    { label: '待审批', value: sysStats.value.user?.pending ?? 0, color: '#e6a23c' },
    { label: '题库总量', value: sysStats.value.content?.question ?? 0, color: '#67c23a' },
    { label: 'AI 调用', value: sysStats.value.ai?.calls ?? 0, color: '#909399' }
  ]
})

const trendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 40, right: 20, top: 30, bottom: 40 },
  xAxis: { type: 'category', data: trend.value.map(t => t.name.slice(0, 8)), axisLabel: { rotate: 30 } },
  yAxis: { type: 'value', max: 100, name: '得分率(%)' },
  series: [{
    type: 'line', smooth: true, data: trend.value.map(t => t.rate),
    itemStyle: { color: '#2f6fd0' }, areaStyle: { opacity: 0.15 }
  }]
}))

const radarOption = computed(() => ({
  tooltip: {},
  radar: {
    indicator: radar.value.slice(0, 8).map(r => ({ name: r.name.slice(0, 8), max: 100 })),
    radius: '65%'
  },
  series: [{
    type: 'radar',
    data: [{ value: radar.value.slice(0, 8).map(r => r.mastery), name: '掌握度' }],
    areaStyle: { opacity: 0.25 }
  }]
}))

function formatRemain(sec) {
  const d = Math.floor(sec / 86400)
  const h = Math.floor((sec % 86400) / 3600)
  const m = Math.floor((sec % 3600) / 60)
  if (d > 0) return `${d} 天 ${h} 小时`
  if (h > 0) return `${h} 小时 ${m} 分`
  return `${m} 分钟`
}

onMounted(async () => {
  try {
    if (userStore.isStudent) {
      const t = await taskApi.myTasks({ page: 1, page_size: 8 })
      tasks.value = t.data.items || []
      const r = await import('@/api').then(m => m.learningApi.reviewPlans({}))
      reviewData.value = r.data
      const tr = await reportApi.scoreTrend()
      trend.value = tr.data || []
      const rd = await reportApi.knowledgeRadar()
      radar.value = rd.data || []
    }
    if (userStore.isTeacher) {
      const t = await taskApi.list({ page: 1, page_size: 8 })
      tasks.value = t.data.items || []
      const p = await gradingApi.pending({ page: 1, page_size: 8 })
      pending.value = p.data.items || []
    }
    if (userStore.isAdmin) {
      const s = await reportApi.adminOverview()
      sysStats.value = s.data
    }
    if (userStore.isTeacher && !userStore.isAdmin) {
      const s = await reportApi.studentOverview()
      sysStats.value = { user: { student: 0 }, content: { question: 0 } }
    }
  } catch (e) { /* 忽略加载错误 */ }
})
</script>

<style scoped>
.welcome-card {
  background: linear-gradient(135deg, #2f6fd0, #5a8fd6);
  color: #fff;
  border-radius: 10px;
  padding: 24px 28px;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
}

.welcome-card h2 { margin: 0 0 6px; font-size: 22px; }
.welcome-card p { margin: 0; opacity: 0.9; font-size: 13px; }

.mb { margin-bottom: 16px; }

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.ai-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.ai-card {
  text-align: center;
  padding: 16px 8px;
  border-radius: 8px;
  background: #f5f7fa;
  cursor: pointer;
  transition: all 0.2s;
  color: #2f6fd0;
}

.ai-card:hover {
  background: #ecf5ff;
  transform: translateY(-2px);
}

.ai-name { margin-top: 8px; font-size: 13px; color: #606266; }
</style>
