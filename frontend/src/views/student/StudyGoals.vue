<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">学习打卡</h2>
      <el-button type="primary" :icon="Plus" @click="openDialog">新建目标</el-button>
    </div>

    <el-row :gutter="16" class="mb16">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-value">{{ goals.length }}</div>
          <div class="stat-label">进行中目标</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-value" style="color:#f56c6c">{{ maxStreak }}</div>
          <div class="stat-label">最长连续打卡</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-value" style="color:#67c23a">{{ todayCheckedCount }}</div>
          <div class="stat-label">今日已打卡</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-value">{{ totalCheckinDays }}</div>
          <div class="stat-label">累计打卡天数</div>
        </div>
      </el-col>
    </el-row>

    <el-card shadow="never" class="mb16">
      <template #header><b>最近 30 天打卡日历</b></template>
      <div class="calendar-grid">
        <div v-for="day in calendarDays" :key="day.date"
             class="calendar-cell" :class="{ checked: day.value > 0, today: day.isToday }">
          <span class="cal-day">{{ day.label }}</span>
          <span v-if="day.value > 0" class="cal-val">{{ day.value }}</span>
        </div>
      </div>
    </el-card>

    <el-empty v-if="!goals.length" description="还没有学习目标，点击右上角创建一个吧！" />

    <el-card v-for="g in goals" :key="g.id" shadow="never" class="goal-card">
      <div class="goal-head">
        <div>
          <el-tag size="small" :type="g.target_type === 'daily' ? 'primary' : g.target_type === 'weekly' ? 'warning' : 'success'">
            {{ typeLabel(g.target_type) }}
          </el-tag>
          <b class="goal-title">{{ g.title }}</b>
          <span class="goal-target">目标：{{ g.target_value }} {{ unitLabel(g.unit) }}</span>
        </div>
        <div>
          <el-button v-if="!g.today_checked" type="primary" size="small" :icon="Check"
                     @click="openCheckin(g)">今日打卡</el-button>
          <el-tag v-else type="success" size="small" effect="dark">已完成 {{ g.today_value }}</el-tag>
          <el-button size="small" :icon="Edit" @click="editGoal(g)" text>编辑</el-button>
          <el-button size="small" type="danger" :icon="Delete" @click="removeGoal(g)" text>删除</el-button>
        </div>
      </div>
      <div class="goal-progress">
        <div class="streak-info">
          <span class="flame">{{ g.streak > 0 ? '🔥' : '○' }}</span>
          <span>连续 {{ g.streak }} 天</span>
        </div>
        <el-progress v-if="g.today_checked" :percentage="Math.min(100, Math.round(g.today_value / g.target_value * 100))"
                     :stroke-width="8" :format="() => `${g.today_value}/${g.target_value}`" />
      </div>
    </el-card>

    <!-- 新建/编辑目标对话框 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑目标' : '新建学习目标'" width="480px">
      <el-form :model="goalForm" label-width="100px">
        <el-form-item label="目标名称">
          <el-input v-model="goalForm.title" placeholder="如：每日数学 20 题" />
        </el-form-item>
        <el-form-item label="目标周期">
          <el-radio-group v-model="goalForm.target_type">
            <el-radio-button value="daily">每日</el-radio-button>
            <el-radio-button value="weekly">每周</el-radio-button>
            <el-radio-button value="longterm">长期</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="目标值">
          <el-input-number v-model="goalForm.target_value" :min="1" :max="200" />
          <el-radio-group v-model="goalForm.unit" style="margin-left:12px">
            <el-radio-button value="questions">题数</el-radio-button>
            <el-radio-button value="minutes">分钟</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveGoal">保存</el-button>
      </template>
    </el-dialog>

    <!-- 打卡对话框 -->
    <el-dialog v-model="checkinVisible" title="今日打卡" width="400px">
      <p style="text-align:center;font-size:14px;margin-bottom:16px">
        <span style="font-size:24px">{{ currentGoal?.streak > 0 ? '🔥' : '○' }}</span>
        <br>连续 {{ currentGoal?.streak || 0 }} 天
      </p>
      <el-form label-width="100px">
        <el-form-item :label="`今日完成（目标${currentGoal?.target_value}${unitLabel(currentGoal?.unit)}）`">
          <el-input-number v-model="checkinValue" :min="0" :max="500" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="checkinVisible = false">取消</el-button>
        <el-button type="primary" @click="doCheckin">打卡</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatLocalDate } from '@/utils/date'
import { Plus, Check, Edit, Delete } from '@element-plus/icons-vue'
import { learningApi } from '@/api'

const goals = ref([])
const calendar = ref({})
const maxStreak = ref(0)
const dialogVisible = ref(false)
const checkinVisible = ref(false)
const editing = ref(null)
const currentGoal = ref(null)
const checkinValue = ref(0)

const goalForm = ref({ title: '', target_type: 'daily', target_value: 10, unit: 'questions' })

const todayCheckedCount = computed(() => goals.value.filter(g => g.today_checked).length)
const totalCheckinDays = computed(() => Object.keys(calendar.value).length)

const calendarDays = computed(() => {
  const days = []
  const now = new Date()
  for (let i = 29; i >= 0; i--) {
    const d = new Date(now)
    d.setDate(d.getDate() - i)
    // 必须按本地时区取日期：toISOString() 是 UTC，东八区 0:00-8:00 会错一天，
    // 打卡日历 key 与后端 calendar（本地日期）对不上。
    const dateStr = formatLocalDate(d)
    days.push({
      date: dateStr,
      label: String(d.getDate()),
      value: calendar.value[dateStr] || 0,
      isToday: i === 0,
    })
  }
  return days
})

function typeLabel(t) { return { daily: '每日', weekly: '每周', longterm: '长期' }[t] || t }
function unitLabel(u) { return { questions: '题', minutes: '分' }[u] || u }

async function load() {
  const res = await learningApi.goals()
  goals.value = res.data.items || []
  calendar.value = res.data.calendar || {}
  maxStreak.value = res.data.max_streak || 0
}

function openDialog() {
  editing.value = null
  goalForm.value = { title: '', target_type: 'daily', target_value: 10, unit: 'questions' }
  dialogVisible.value = true
}

function editGoal(g) {
  editing.value = g.id
  goalForm.value = { title: g.title, target_type: g.target_type, target_value: g.target_value, unit: g.unit }
  dialogVisible.value = true
}

const saving = ref(false)
async function saveGoal() {
  if (saving.value) return
  if (!goalForm.value.title) { saving.value = false; return ElMessage.warning('请输入目标名称') }
  try {
    if (editing.value) {
      await learningApi.updateGoal(editing.value, goalForm.value)
      ElMessage.success('目标已更新')
    } else {
      await learningApi.createGoal(goalForm.value)
      ElMessage.success('目标已创建')
    }
    dialogVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function removeGoal(g) {
  await ElMessageBox.confirm('确定删除该目标？', '提示', { type: 'warning' })
  await learningApi.deleteGoal(g.id)
  ElMessage.success('已删除')
  load()
}

function openCheckin(g) {
  currentGoal.value = g
  checkinValue.value = g.target_value
  checkinVisible.value = true
}

const checking = ref(false)
async function doCheckin() {
  if (checking.value) return
  try {
    const res = await learningApi.checkin(currentGoal.value.id, { actual_value: checkinValue.value })
    ElMessage.success(res.message)
    checkinVisible.value = false
    load()
  } finally {
    checking.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.mb16 { margin-bottom: 16px; }
.stat-card { text-align: center; padding: 16px; background: #f5f7fa; border-radius: 8px; }
.stat-value { font-size: 28px; font-weight: 700; color: #409eff; }
.stat-label { font-size: 12px; color: #909399; margin-top: 4px; }
.calendar-grid { display: grid; grid-template-columns: repeat(10, 1fr); gap: 4px; }
.calendar-cell { aspect-ratio: 1; border-radius: 4px; background: #f5f7fa; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 11px; color: #c0c4cc; }
.calendar-cell.checked { background: #67c23a; color: #fff; }
.calendar-cell.today { border: 2px solid #409eff; }
.cal-day { font-weight: 500; }
.cal-val { font-size: 10px; }
.goal-card { margin-bottom: 12px; }
.goal-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.goal-title { margin: 0 8px; font-size: 15px; }
.goal-target { color: #909399; font-size: 13px; }
.goal-progress { display: flex; align-items: center; gap: 16px; }
.streak-info { display: flex; align-items: center; gap: 4px; font-size: 14px; font-weight: 500; white-space: nowrap; }
.flame { font-size: 20px; }
</style>
