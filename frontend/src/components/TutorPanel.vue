<template>
  <el-card shadow="never" class="tutor-panel">
    <template #header>分步答疑</template>
    <div class="tutor-actions">
      <el-button :loading="loading" @click="ask('hint')">给我一个提示</el-button>
      <el-button :loading="loading" @click="ask('steps')">讲解步骤</el-button>
      <el-button :loading="loading" @click="ask('answer')">查看答案</el-button>
    </div>
    <AiFallbackNotice :show="Boolean(reply?.is_fallback)" reason="当前使用知识资料规则提示，非模型生成讲解" />
    <template v-if="reply">
      <QuestionContent :question="{ stem: reply.answer }" />
      <el-tag v-if="reply.teacher_reviewed" type="success">教师已核对</el-tag>
      <p>引用资料：</p>
      <ul><li v-for="reference in reply.references" :key="`${reference.type}-${reference.id}`">
        <el-link v-if="reference.type === '知识点'" @click="openKnowledge(reference)">
          {{ reference.type }}：{{ reference.name }}
        </el-link>
        <span v-else>{{ reference.type }}：{{ reference.name }}</span>
        <span v-if="reference.textbook_version"> · {{ reference.textbook_version }}</span>
      </li></ul>
      <el-input v-model="feedback" type="textarea" :rows="2" maxlength="2000" placeholder="发现问题？请描述需要教师核对的内容" />
      <el-button class="mt12" :loading="sending" :disabled="!feedback.trim()" @click="sendFeedback">提交纠错</el-button>
    </template>
  </el-card>
</template>

<script setup>
import { onBeforeUnmount, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { extensionApi } from '@/api/extensions'
import QuestionContent from './QuestionContent.vue'
import AiFallbackNotice from './AiFallbackNotice.vue'

const props = defineProps({ questionId: { type: Number, required: true } })
const router = useRouter()
const loading = ref(false)
const sending = ref(false)
const reply = ref(null)
const feedback = ref('')
let requestId = 0
watch(() => props.questionId, () => { requestId++; loading.value = false; reply.value = null; feedback.value = '' })
onBeforeUnmount(() => { requestId++ })
async function ask(stage) {
  const current = ++requestId
  loading.value = true
  try {
    const response = await extensionApi.tutor(props.questionId, stage)
    if (current === requestId) reply.value = response.data
  } finally { if (current === requestId) loading.value = false }
}
async function sendFeedback() {
  sending.value = true
  try {
    await extensionApi.feedback({ question_id: props.questionId, stage: reply.value.stage, content: feedback.value })
    feedback.value = ''
    ElMessage.success('已提交，等待教师核对')
  } finally { sending.value = false }
}
function openKnowledge(reference) {
  router.push({ path: '/student/graph', query: { kp: reference.id } })
}
</script>

<style scoped>
.tutor-panel { margin: 12px 0; }
.tutor-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
.mt12 { margin-top: 12px; }
</style>
