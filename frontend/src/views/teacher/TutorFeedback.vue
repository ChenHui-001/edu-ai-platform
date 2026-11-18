<template>
  <div class="page-container" v-loading="loading">
    <div class="page-header"><h2>答疑纠错审核</h2><el-button @click="load">刷新</el-button></div>
    <ErrorState v-if="error" :message="error" @retry="load" />
    <el-empty v-else-if="!items.length" description="暂无需要核对的反馈" />
    <el-card v-for="item in items" :key="item.id" shadow="never" class="feedback-card">
      <template #header>题目 #{{ item.question_id }} · {{ stages[item.stage] }} · {{ item.status === 'resolved' ? '已核对' : '待核对' }}</template>
      <p>{{ item.content }}</p>
      <el-input v-model="corrections[item.id]" type="textarea" :rows="4" maxlength="4000" placeholder="填写核对后的讲解，保存后该阶段优先展示此内容" />
      <el-button class="mt12" type="primary" :disabled="!corrections[item.id]?.trim()" @click="save(item)">保存核对结果</el-button>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { extensionApi } from '@/api/extensions'
import ErrorState from '@/components/ErrorState.vue'
const items = ref([])
const corrections = reactive({})
const loading = ref(false)
const error = ref('')
const stages = { hint: '提示', steps: '步骤', answer: '答案' }
async function load() {
  loading.value = true; error.value = ''
  try { items.value = (await extensionApi.feedbackList()).data.items; for (const item of items.value) corrections[item.id] = item.correction || '' }
  catch { error.value = '反馈加载失败，请重试' }
  finally { loading.value = false }
}
async function save(item) {
  loading.value = true
  try { await extensionApi.reviewFeedback(item.id, corrections[item.id]); ElMessage.success('核对结果已保存'); await load() }
  finally { loading.value = false }
}
onMounted(load)
</script>

<style scoped>
.feedback-card { margin-top: 12px; }
.mt12 { margin-top: 12px; }
</style>
