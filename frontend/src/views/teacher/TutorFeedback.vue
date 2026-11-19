<template>
  <div class="page-container" v-loading="loading">
    <div class="page-header">
      <h2>答疑纠错审核</h2>
      <div>
        <el-select v-model="statusFilter" style="width: 130px">
          <el-option label="全部反馈" value="" />
          <el-option label="待核对" value="pending" />
          <el-option label="已核对" value="resolved" />
        </el-select>
        <el-button @click="load">刷新</el-button>
      </div>
    </div>
    <p>共 {{ total }} 条反馈 · 核对结果只对反馈学生所在班级生效</p>
    <ErrorState v-if="error" :message="error" @retry="load" />
    <el-empty v-else-if="!items.length" description="暂无符合条件的反馈" />
    <el-card v-for="item in items" :key="item.id" shadow="never" class="feedback-card">
      <template #header>
        题目 #{{ item.question_id }} · {{ stages[item.stage] }} · {{ item.status === 'resolved' ? '已核对' : '待核对' }}
        <span class="muted"> · {{ item.student_name || '学生' }} · {{ item.class_name || '未分班' }}</span>
      </template>
      <p class="question-stem">{{ item.question_stem }}</p>
      <p>{{ item.content }}</p>
      <el-input v-model="corrections[item.id]" type="textarea" :rows="4" maxlength="4000"
                placeholder="填写核对后的讲解，保存后仅对该班学生的这一阶段答疑优先展示" />
      <el-button class="mt12" type="primary" :disabled="!corrections[item.id]?.trim()" @click="save(item)">
        保存核对结果
      </el-button>
    </el-card>
    <el-pagination v-if="total > pageSize" v-model:current-page="page" :total="total"
                   :page-size="pageSize" layout="total, prev, pager, next" @current-change="load" />
  </div>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { extensionApi } from '@/api/extensions'
import ErrorState from '@/components/ErrorState.vue'
import { confirmAction } from '@/utils/confirm'

const items = ref([])
const corrections = reactive({})
const loading = ref(false)
const error = ref('')
const total = ref(0)
const page = ref(1)
const pageSize = 20
const statusFilter = ref('')
const stages = { hint: '提示', steps: '步骤', answer: '答案' }

async function load() {
  loading.value = true; error.value = ''
  try {
    const response = await extensionApi.feedbackList({
      page: page.value, page_size: pageSize, status: statusFilter.value || undefined
    })
    items.value = response.data.items
    total.value = response.data.total
    for (const item of items.value) corrections[item.id] = item.correction || ''
  } catch { error.value = '反馈加载失败，请重试' }
  finally { loading.value = false }
}

function reload() {
  page.value = 1
  load()
}

async function save(item) {
  const scope = item.class_name || '该学生所在班级'
  if (!await confirmAction(`核对结果只对「${scope}」的学生生效，不会扩散到其他班级。确认保存？`, '确认纠错范围')) return
  loading.value = true
  try {
    await extensionApi.reviewFeedback(item.id, corrections[item.id], true)
    ElMessage.success('核对结果已保存')
    await load()
  } finally { loading.value = false }
}

watch(statusFilter, reload)
onMounted(load)
</script>

<style scoped>
.feedback-card { margin-top: 12px; }
.mt12 { margin-top: 12px; }
.muted { color: var(--el-text-color-secondary); font-weight: normal; }
.question-stem { color: var(--el-text-color-secondary); font-size: 13px; }
</style>
