<template>
  <div class="page-container" v-loading="loading">
    <div class="page-header"><h2>补弱学习计划</h2><el-button @click="load">刷新</el-button></div>
    <ErrorState v-if="error" :message="error" @retry="load" />
    <el-empty v-else-if="!plans.length" description="完成知识诊断后，可生成补弱计划">
      <el-button type="primary" @click="router.push('/student/diagnosis')">开始诊断</el-button>
    </el-empty>
    <el-select v-if="plans.length" v-model="selected" @change="selectPlan">
      <el-option v-for="item in plans" :key="item.id" :value="item.id" :label="`${item.title} #${item.id}`" />
    </el-select>
    <template v-if="plan">
      <el-alert class="mt12" type="info" :closable="false"
                title="先读讲解，再练习和复测；复测达到 80 分后，按 1、3、7 天安排复习。" />
      <el-card v-for="step in plan.steps" :key="step.id" shadow="never" class="mt12">
        <template #header><b>{{ step.name }}</b> <el-tag>{{ labels[step.status] }}</el-tag></template>
        <QuestionContent :question="{ stem: step.explanation }" />
        <p>练习：{{ step.practice_score ?? '未完成' }} · 复测：{{ step.retest_score ?? '未完成' }}</p>
        <p v-if="step.review_due">下次复习：{{ step.review_due.slice(0, 16).replace('T', ' ') }}</p>
        <el-button type="primary" :disabled="Boolean(plan.quiz) || step.status === 'completed' || !reviewDue(step)"
                   @click="start(step)">{{ actionLabels[step.status] || '已完成' }}</el-button>
        <el-button @click="router.push({ path: '/student/graph', query: { kp: step.id } })">查看关系图</el-button>
      </el-card>
      <el-card v-if="plan.quiz" class="mt12">
        <template #header>本次{{ actionLabels[plan.quiz.stage] || plan.quiz.stage }} · {{ plan.quiz.questions.length }} 题</template>
        <el-alert v-if="plan.quiz.reused_questions" type="warning" :closable="false"
                  title="题库数量有限，本次包含做过的题目，请结合教师建议判断是否真正掌握。" />
        <div v-for="question in plan.quiz.questions" :key="question.id" class="quiz-item">
          <QuestionContent :question="question" />
          <el-checkbox-group v-if="question.type === 'multiple'" v-model="answers[question.id]">
            <el-checkbox v-for="option in question.options" :key="option.key" :value="option.key">{{ option.key }}. <QuestionContent :question="{ stem: option.text, figure: option.figure }" /></el-checkbox>
          </el-checkbox-group>
          <el-radio-group v-else-if="['single','judge'].includes(question.type)" v-model="answers[question.id]">
            <el-radio v-for="option in question.options" :key="option.key" :value="option.key">{{ option.key }}. <QuestionContent :question="{ stem: option.text, figure: option.figure }" /></el-radio>
          </el-radio-group>
          <el-input v-else v-model="answers[question.id]" placeholder="填写答案" />
        </div>
        <el-button type="primary" :loading="loading" @click="submit">提交测验</el-button>
      </el-card>
      <el-card v-if="result" class="mt12">
        <template #header>测验结果：{{ result.score }} 分</template>
        <p v-for="item in result.results" :key="item.question_id">{{ item.correct ? '正确' : '错误' }} · 参考答案：{{ item.answer }} · {{ item.analysis }}</p>
      </el-card>
      <el-collapse class="mt12"><el-collapse-item title="历史测验">
        <p v-for="entry in plan.history" :key="entry.quiz_id">{{ entry.at.slice(0,16) }} · {{ entry.stage }} · {{ entry.score }} 分</p>
      </el-collapse-item></el-collapse>
    </template>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { extensionApi } from '@/api/extensions'
import QuestionContent from '@/components/QuestionContent.vue'
import ErrorState from '@/components/ErrorState.vue'
import { parseServerDate } from '@/utils/date'

const route = useRoute()
const router = useRouter()
const plans = ref([])
const selected = ref(null)
const plan = ref(null)
const result = ref(null)
const loading = ref(false)
const error = ref('')
const answers = reactive({})
const labels = { learning: '讲解与练习', retest: '等待复测', review: '按计划复习', completed: '已完成' }
const actionLabels = { learning: '开始练习', practice: '专项练习', retest: '开始复测', review: '开始复习' }
function setPlan(value) {
  plan.value = value
  selected.value = value.id
  for (const question of value.quiz?.questions || []) answers[question.id] = question.type === 'multiple' ? [] : ''
}
async function load() {
  loading.value = true
  error.value = ''
  try {
    if (route.query.diagnosis) await extensionApi.createPlan(Number(route.query.diagnosis))
    plans.value = (await extensionApi.plans()).data.items
    const next = plans.value.find(item => item.id === selected.value) || plans.value[0]
    if (next) setPlan(next)
  } catch { error.value = '学习计划加载失败，请重试' }
  finally { loading.value = false }
}
function selectPlan() { const next = plans.value.find(item => item.id === selected.value); if (next) setPlan(next); result.value = null }
function reviewDue(step) { return step.status !== 'review' || (parseServerDate(step.review_due) && parseServerDate(step.review_due) <= new Date()) }
async function start(step) {
  loading.value = true
  try { setPlan((await extensionApi.quiz(plan.value.id, {
    step_id: step.id, stage: step.status === 'learning' ? 'practice' : step.status, version: plan.value.version
  })).data); result.value = null }
  finally { loading.value = false }
}
async function submit() {
  loading.value = true
  try {
    const response = await extensionApi.submitQuiz(plan.value.id, {
      quiz_id: plan.value.quiz.id, answers, version: plan.value.version
    })
    setPlan(response.data.plan); result.value = response.data.result
  } finally { loading.value = false }
}
onMounted(load)
</script>

<style scoped>
.mt12 { margin-top: 12px; }
.quiz-item { margin: 18px 0; }
</style>
