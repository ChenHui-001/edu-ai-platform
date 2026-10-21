<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">模拟考试</h2>
      <el-button :icon="Refresh" @click="load">刷新</el-button>
    </div>

    <el-tabs v-model="tab" @tab-change="onTabChange">
      <el-tab-pane label="待完成" name="pending" />
      <el-tab-pane label="已完成" name="done" />
    </el-tabs>

    <el-empty v-if="!loading && !shown.length" description="暂无考试任务" />

    <el-row :gutter="16">
      <el-col :span="12" v-for="t in shown" :key="t.id">
        <el-card shadow="never" class="task-card">
          <div class="task-head">
            <div>
              <h3 class="task-title">{{ t.title }}</h3>
              <p class="task-sub">
                <el-tag size="small" :type="t.type === 'exam' ? 'danger' : 'primary'">{{ t.type_label }}</el-tag>
                <el-tag size="small" type="info" effect="plain" class="ml4">{{ t.subject_name }}</el-tag>
                <el-tag size="small" type="info" effect="plain" class="ml4">{{ t.grade_name }}</el-tag>
              </p>
            </div>
            <el-tag :type="taskStatus(t).type" size="small">{{ taskStatus(t).label }}</el-tag>
          </div>

          <el-descriptions :column="2" border size="small" class="mt12">
            <el-descriptions-item label="开始时间">{{ t.start_at || '不限' }}</el-descriptions-item>
            <el-descriptions-item label="截止时间">{{ t.end_at || '不限' }}</el-descriptions-item>
            <el-descriptions-item label="时长">{{ t.duration || '不限' }} 分钟</el-descriptions-item>
            <el-descriptions-item label="满分">{{ t.total_score }} 分</el-descriptions-item>
          </el-descriptions>

          <p v-if="t.description" class="task-desc">{{ t.description }}</p>

          <div class="task-actions">
            <template v-if="tab === 'pending'">
              <el-button type="primary" :icon="EditPen" :disabled="!canStart(t)"
                         @click="goExam(t)">开始答题</el-button>
              <span v-if="!canStart(t)" class="tip">{{ disabledReason(t) }}</span>
            </template>
            <template v-else>
              <span class="score-badge">
                <!-- 得分挂在 my_submission 上，任务对象本身没有 score 字段。
                     只读 t.score 会让「已完成」永远显示「得分 -」。 -->
                得分 <b>{{ t.my_submission?.score ?? t.score ?? '-' }}</b>
                / {{ t.my_submission?.total_score ?? t.total_score }}</span>
              <el-button link type="primary" @click="viewResult(t)">查看解析</el-button>
              <el-button v-if="t.allow_retake" link type="warning" @click="goExam(t)">重考</el-button>
            </template>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, EditPen } from '@element-plus/icons-vue'
import { taskApi, learningApi } from '@/api'

const router = useRouter()
const tab = ref('pending')
const list = ref([])
const loading = ref(false)

function parseDate(s) { return s ? new Date(String(s).replace(/-/g, '/')) : null }

function taskStatus(t) {
  if (t.status === 'finished' || t.submission_status === 'graded') {
    return { label: '已完成', type: 'success' }
  }
  const now = new Date()
  const end = parseDate(t.end_at)
  if (end && end < now) return { label: '已截止', type: 'info' }
  const start = parseDate(t.start_at)
  if (start && start > now) return { label: '未开始', type: 'warning' }
  return { label: '进行中', type: 'primary' }
}

function canStart(t) {
  const s = taskStatus(t)
  return s.label === '进行中' || s.label === '已截止' || s.label === '未开始'
}

function disabledReason(t) {
  const s = taskStatus(t)
  if (s.label === '已截止') return '已过截止时间'
  return ''
}

async function load() {
  loading.value = true
  try {
    const res = await taskApi.myTasks({
      page: 1, page_size: 50, status: tab.value === 'pending' ? 'published' : ''
    })
    list.value = res.data?.items || []
  } finally {
    loading.value = false
  }
}

// 两个 tab 必须按「是否已交卷」真正分流：后端 status=published 只是任务状态，
// 已交卷的任务同样满足。仅靠接口过滤会让「待完成」里堆满已做完的考试，
// 点「开始答题」才被告知不能重复作答；「已完成」里也会混入没做过的任务。
const shown = computed(() => list.value.filter((t) => {
  const done = !!(t.my_submission && t.my_submission.submit_time)
  return tab.value === 'done' ? done : !done
}))

function onTabChange() { load() }

function goExam(t) { router.push({ name: 'ExamPaper', params: { taskId: t.id } }) }

async function viewResult(t) {
  // my/tasks 返回的提交挂在 my_submission 上（无顶层 submission_id）；
  // 详情接口返回 answers（无 results/total_score/summary）
  const sid = t.my_submission?.id
  if (!sid) return ElMessage.warning('尚未生成成绩')
  const res = await taskApi.submissionDetail(sid)
  const d = res.data
  const answers = d.answers || []
  const right = answers.filter(a => a.is_correct).length
  ElMessageBoxAlert(
    `任务：${d.task_title || t.title}\n得分：${d.score ?? '-'}\n` +
    `答对：${right}/${answers.length} 题\n` +
    (d.is_passed == null ? '' : `结果：${d.is_passed ? '及格' : '不及格'}`)
  )
}

function ElMessageBoxAlert(text) {
  ElMessage({ message: text.replace(/\n/g, '；'), type: 'info', duration: 6000, showClose: true })
}

onMounted(load)
</script>

<style scoped>
.ml4 { margin-left: 4px; }
.mt12 { margin-top: 12px; }
.task-card { margin-bottom: 16px; }
.task-head { display: flex; justify-content: space-between; align-items: flex-start; }
.task-title { margin: 0 0 6px; font-size: 16px; }
.task-sub { margin: 0; }
.task-desc { color: #909399; font-size: 13px; margin: 10px 0 0; }
.task-actions {
  margin-top: 14px; display: flex; align-items: center; gap: 12px;
}
.score-badge { font-size: 14px; color: #606266; }
.score-badge b { color: var(--el-color-primary); font-size: 18px; }
.tip { font-size: 12px; color: #f56c6c; }
</style>
