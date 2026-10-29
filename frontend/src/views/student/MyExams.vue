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
              <span v-if="attemptInfo(t).total > 1" class="attempt-info">
                第 {{ attemptInfo(t).used }} / {{ attemptInfo(t).total }} 次
              </span>
              <el-button link type="primary" @click="viewResult(t)">查看解析</el-button>
              <!-- 重考按钮的显示条件是「还有剩余次数」，不是「allow_retake 为真」。
                   allow_retake 是**总允许次数**（最小 1），直接 v-if 恒为真，
                   导致 1 次机会用完的卷子也显示「重考」，点进去被立刻弹回列表。 -->
              <el-button v-if="attemptInfo(t).left > 0" link type="warning"
                         @click="goExam(t)">重考（剩 {{ attemptInfo(t).left }} 次）</el-button>
              <span v-else class="tip">已用完 {{ attemptInfo(t).total }} 次作答机会</span>
            </template>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 答题解析弹窗：逐题展示我的答案 / 正确答案 / 解析 -->
    <el-dialog v-model="detailDlg" title="答题解析" width="760px" top="5vh">
      <div v-loading="detailLoading" class="detail-body">
        <el-descriptions v-if="detailInfo" :column="4" border size="small" class="mb12">
          <el-descriptions-item label="任务">{{ detailInfo.title }}</el-descriptions-item>
          <el-descriptions-item label="得分">
            <b class="hl">{{ detailInfo.score ?? '-' }}</b> / {{ detailInfo.total_score }}
          </el-descriptions-item>
          <el-descriptions-item label="答对">
            {{ detailInfo.right }} / {{ detailInfo.count }} 题
          </el-descriptions-item>
          <el-descriptions-item label="结果">
            <el-tag size="small" :type="detailInfo.is_passed ? 'success' : 'danger'">
              {{ detailInfo.is_passed ? '及格' : '不及格' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <div v-for="(r, idx) in detailItems" :key="idx" class="p-item"
             :class="r.is_correct ? 'ok' : 'ng'">
          <div class="p-head">
            <span class="p-no">第 {{ idx + 1 }} 题</span>
            <el-tag size="small" :type="r.is_correct ? 'success' : 'danger'">
              {{ r.is_correct ? '正确' : '错误' }}
            </el-tag>
            <span class="p-score">{{ r.score ?? 0 }} / {{ r.full_score ?? '-' }} 分</span>
          </div>
          <div class="p-stem">{{ r.stem }}</div>
          <div v-if="parseOptions(r.options).length" class="p-opts">
            <span v-for="o in parseOptions(r.options)" :key="o.key" class="p-opt">
              {{ o.key }}. {{ o.text }}
            </span>
          </div>
          <div class="p-answers">
            <div><b>我的答案：</b><span class="mine">{{ fmtAnswer(r.my_answer) }}</span></div>
            <div><b>正确答案：</b><span class="correct">{{ fmtAnswer(r.correct_answer) }}</span></div>
          </div>
          <div v-if="r.analysis" class="p-analysis"><b>解析：</b>{{ r.analysis }}</div>
          <div v-if="r.comment" class="p-comment"><b>教师评语：</b>{{ r.comment }}</div>
        </div>

        <el-empty v-if="!detailLoading && !detailItems.length"
                  description="暂无答题明细（可能未作答或成绩尚未生成）" />
      </div>
      <template #footer>
        <el-button @click="detailDlg = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, EditPen } from '@element-plus/icons-vue'
import { taskApi } from '@/api'

const router = useRouter()
const tab = ref('pending')
const list = ref([])
const loading = ref(false)

const detailDlg = ref(false)
const detailLoading = ref(false)
const detailInfo = ref(null)
const detailItems = ref([])

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
    const res = await taskApi.myTasks({ page: 1, page_size: 50 })
    list.value = res.data?.items || []
  } finally {
    loading.value = false
  }
}

/**
 * 作答次数信息（用于「还剩几次」与重考按钮）。
 *
 * `allow_retake` 是**总允许次数**（后端 `max(int(allow_retake or 1), 1)`），
 * 不是布尔开关。已用次数取 `attempt_count`（后端按 Submission 实际条数统计），
 * 缺失时回落到 `my_submission.attempt`，再缺就按「已交卷则用掉 1 次」兜底——
 * 否则算不出剩余次数，只能退化成永远显示重考。
 */
function attemptInfo(t) {
  const total = Math.max(Number(t.allow_retake) || 1, 1)
  let used = Number(t.attempt_count)
  if (!Number.isFinite(used) || used <= 0) {
    used = Number(t.my_submission?.attempt) || (t.my_submission?.submit_time ? 1 : 0)
  }
  return { total, used, left: Math.max(total - used, 0) }
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

  // 原先这里只弹一个 6 秒自动消失的 toast，学生根本看不到逐题解析，
  // 而且接口报错时 await 抛异常无人捕获 —— 表现就是「点了没反应」。
  // 改为真正的解析弹窗：逐题显示我的答案 / 正确答案 / 解析。
  detailDlg.value = true
  detailLoading.value = true
  detailInfo.value = null
  detailItems.value = []
  try {
    const res = await taskApi.submissionDetail(sid)
    const d = res.data || {}
    detailInfo.value = {
      title: d.task_title || t.title,
      score: d.score,
      total_score: t.my_submission?.total_score ?? t.total_score,
      is_passed: d.is_passed,
      class_rank: d.class_rank,
      right: (d.answers || []).filter(a => a.is_correct).length,
      count: (d.answers || []).length,
    }
    detailItems.value = (d.answers || []).map(a => ({
      ...a,
      my_answer: a.content,
      correct_answer: a.answer,
      // 解析可能被后端开关隐藏（show_answer=False），此时明确提示而不是留白
      analysis: a.analysis,
    }))
  } catch (e) {
    detailDlg.value = false
    ElMessage.error(`加载解析失败：${e.message || '未知错误'}`)
  } finally {
    detailLoading.value = false
  }
}

function fmtAnswer(v) {
  if (v === null || v === undefined || v === '') return '未作答'
  if (Array.isArray(v)) return v.join('') || '未作答'
  if (typeof v === 'object') return v.text || v.value || JSON.stringify(v)
  return String(v).replace(/^"|"$/g, '')
}

function parseOptions(v) {
  if (!v) return []
  if (Array.isArray(v)) return v
  try {
    const p = JSON.parse(v)
    return Array.isArray(p) ? p : []
  } catch { return [] }
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
.attempt-info {
  font-size: 12px; color: #909399; padding: 0 8px;
  border-left: 1px solid var(--el-border-color-light);
}

/* 解析弹窗 */
.detail-body { min-height: 120px; max-height: 68vh; overflow-y: auto; }
.hl { color: var(--el-color-primary); font-size: 16px; }
.p-item { padding: 12px 0; border-bottom: 1px dashed #ebeef5; }
.p-item:last-child { border-bottom: none; }
.p-head { display: flex; align-items: center; gap: 8px; }
.p-no { font-weight: 600; }
.p-score { font-size: 12px; color: #909399; margin-left: auto; }
.p-stem { margin: 8px 0; line-height: 1.8; white-space: pre-wrap; }
.p-opts { display: flex; flex-direction: column; gap: 2px; margin-bottom: 8px; }
.p-opt { font-size: 13px; color: #606266; }
.p-answers { font-size: 13px; line-height: 1.9; }
.mine { color: #f56c6c; }
.correct { color: #67c23a; }
.p-analysis {
  margin-top: 8px; padding: 8px 10px; background: #f5f7fa; border-radius: 4px;
  font-size: 13px; line-height: 1.7; color: #606266;
}
.p-comment { margin-top: 6px; font-size: 13px; color: #e6a23c; }
</style>
