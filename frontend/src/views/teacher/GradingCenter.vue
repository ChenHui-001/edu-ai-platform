<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">批改中心</h2>
      <div>
        <el-button :icon="Refresh" @click="load">刷新待批</el-button>
      </div>
    </div>

    <el-row :gutter="16">
      <!-- 待批改列表 -->
      <el-col :span="10">
        <el-card shadow="never">
          <template #header>
            <div class="flex-between">
              <b>待批改队列</b>
              <el-tag type="warning" size="small">{{ list.length }} 份</el-tag>
            </div>
          </template>
          <el-input v-model="filter" placeholder="搜索学生 / 任务" clearable
                    :prefix-icon="Search" class="mb12" />
          <el-list v-loading="loading" class="sub-list">
            <el-list-item v-for="item in filtered" :key="item.id" class="sub-item"
                          :class="{ active: current?.id === item.id }"
                          @click="select(item)">
              <div class="row-between">
                <span class="name">{{ item.student_name }}</span>
                <el-tag size="small" :type="item.needs_manual ? 'warning' : 'info'">
                  {{ item.needs_manual ? '需人工' : 'AI 已批' }}
                </el-tag>
              </div>
              <p class="task">{{ item.task_title }}</p>
              <div class="row-between">
                <span class="tip">{{ item.submit_time }}</span>
                <span class="score">{{ item.score ?? '-' }} / {{ item.total_score }}</span>
              </div>
            </el-list-item>
            <el-empty v-if="!loading && !filtered.length" description="暂无待批改作业" :image-size="70" />
          </el-list>
        </el-card>
      </el-col>

      <!-- 批改区 -->
      <el-col :span="14">
        <el-card shadow="never" v-loading="detailLoading">
          <template #header>
            <div class="flex-between" v-if="detail">
              <b>{{ detail.student?.name }} · {{ detail.task_title }}</b>
              <div>
                <el-tag size="small" class="mr8">客观 {{ detail.objective_score ?? 0 }} 分</el-tag>
                <el-tag size="small" type="warning">主观 {{ detail.subjective_score ?? 0 }} 分</el-tag>
                <el-button size="small" type="primary" class="ml8" @click="publish"
                           :disabled="detail.status !== 'graded'">发布成绩</el-button>
                <el-button size="small" type="danger" plain @click="reject">打回重做</el-button>
              </div>
            </div>
          </template>

          <el-empty v-if="!detail" description="请从左侧选择一份答卷" />

          <template v-else>
            <div v-for="(it, idx) in detail.items" :key="idx" class="q-item">
              <div class="q-head">
                <b>第 {{ idx + 1 }} 题</b>
                <el-tag size="small" :type="it.is_correct ? 'success' : 'danger'" class="ml8">
                  {{ it.is_correct ? '正确' : '错误' }}
                </el-tag>
                <el-tag v-if="it.grader_type" size="small" effect="plain" class="ml8">
                  {{ it.grader_type === 'ai' ? 'AI 批改' : '人工批改' }}
                </el-tag>
                <span class="score-input">
                  得分
                  <el-input-number v-model="scores[it.id]" :min="0" :max="it.full_score"
                                   :step="0.5" size="small" style="width:100px" />
                  / {{ it.full_score }}
                </span>
              </div>
              <p class="content"><b>学生答案：</b>{{ it.content || '（未作答）' }}</p>
              <p class="correct"><b>正确答案：</b>{{ formatAnswer(it.correct_answer) }}</p>
              <p v-if="it.ai_comment" class="ai-comment">
                <b>AI 评语：</b>{{ it.ai_comment }}
              </p>
              <p v-if="it.ai_error_points?.length" class="err-points">
                <b>失分点：</b>
                <el-tag v-for="(p, i) in it.ai_error_points" :key="i" size="small" type="danger"
                        effect="plain" class="ml4">{{ p }}</el-tag>
              </p>
              <el-input v-model="comments[it.id]" placeholder="教师评语（可选）"
                        type="textarea" :rows="1" class="mt4" />
            </div>

            <div class="footer-bar">
              <span>总分：<b class="total">{{ totalScore }}</b> / {{ detail.total_score }}</span>
              <el-button type="primary" :loading="saving" @click="saveGrade">保存批改结果</el-button>
            </div>
          </template>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import { gradingApi } from '@/api'

const list = ref([])
const detail = ref(null)
const scores = reactive({})
const comments = reactive({})
const filter = ref('')
const loading = ref(false)
const detailLoading = ref(false)
const saving = ref(false)

const filtered = computed(() => {
  const k = filter.value.trim().toLowerCase()
  if (!k) return list.value
  return list.value.filter(i =>
    (i.student_name || '').toLowerCase().includes(k) ||
    (i.task_title || '').toLowerCase().includes(k))
})

const totalScore = computed(() => {
  if (!detail.value) return 0
  const s = detail.value.items.reduce((sum, it) => sum + (scores[it.id] ?? it.score ?? 0), 0)
  return Number(s.toFixed(1))
})

function formatAnswer(a) {
  if (a === null || a === undefined) return '-'
  if (typeof a === 'object') return JSON.stringify(a)
  return String(a)
}

async function load() {
  loading.value = true
  try {
    const res = await gradingApi.pending({ page: 1, page_size: 100 })
    list.value = res.data.data?.items || []
  } finally {
    loading.value = false
  }
}

async function select(item) {
  detailLoading.value = true
  detail.value = null
  try {
    const res = await gradingApi.detail(item.id)
    const d = res.data.data
    detail.value = d
    ;(d.items || []).forEach(it => {
      scores[it.id] = it.score ?? 0
      comments[it.id] = it.teacher_comment || ''
    })
  } finally {
    detailLoading.value = false
  }
}

async function saveGrade() {
  saving.value = true
  try {
    const answers = (detail.value.items || []).map(it => ({
      answer_id: it.id,
      score: scores[it.id] ?? 0,
      is_correct: (scores[it.id] ?? 0) >= (it.full_score ?? 0),
      teacher_comment: comments[it.id] || ''
    }))
    await gradingApi.grade(detail.value.submission_id, { answers })
    ElMessage.success('批改结果已保存')
    load()
  } finally {
    saving.value = false
  }
}

async function reject() {
  const { value } = await ElMessageBox.prompt('请输入打回原因', '打回重做', {
    inputPlaceholder: '如：第 3 题计算过程缺失，请重新作答'
  })
  await gradingApi.reject(detail.value.submission_id, { reason: value })
  ElMessage.success('已打回，学生可重新提交')
  detail.value = null
  load()
}

async function publish() {
  await ElMessageBox.confirm('发布后学生即可看到最终成绩，确认发布？', '提示', { type: 'info' })
  await gradingApi.publish(detail.value.submission_id)
  ElMessage.success('成绩已发布')
  detail.value = null
  load()
}

onMounted(load)
</script>

<style scoped>
.flex-between, .row-between {
  display: flex; align-items: center; justify-content: space-between;
}
.mb12 { margin-bottom: 12px; }
.mr8 { margin-right: 8px; }
.ml4 { margin-left: 4px; }
.ml8 { margin-left: 8px; }
.mt4 { margin-top: 4px; }
.sub-list { max-height: 620px; overflow-y: auto; }
.sub-item {
  cursor: pointer; border: 1px solid #ebeef5; border-radius: 8px;
  margin-bottom: 8px; padding: 10px; transition: all .2s;
}
.sub-item:hover { border-color: #a5c4f0; background: #f7fafd; }
.sub-item.active { border-color: var(--el-color-primary); background: var(--el-color-primary-light-9); }
.name { font-weight: 600; }
.task { margin: 4px 0; color: #606266; font-size: 13px; }
.tip { color: #909399; font-size: 12px; }
.score { color: var(--el-color-primary); font-weight: 600; }
.q-item {
  padding: 14px; border: 1px solid #ebeef5; border-radius: 8px; margin-bottom: 12px;
}
.q-head { display: flex; align-items: center; margin-bottom: 8px; }
.score-input { margin-left: auto; display: flex; align-items: center; gap: 6px; font-size: 13px; }
.content, .correct, .ai-comment, .err-points { margin: 6px 0; line-height: 1.6; }
.correct { color: #67c23a; }
.ai-comment { color: #2f6fd0; background: #f0f6ff; padding: 6px 10px; border-radius: 6px; }
.err-points { color: #f56c6c; }
.footer-bar {
  position: sticky; bottom: 0; background: #fff; padding: 12px 0 4px;
  border-top: 1px solid #ebeef5; display: flex; align-items: center; justify-content: space-between;
}
.total { color: var(--el-color-primary); font-size: 18px; }
</style>
