<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">自主组卷</h2>
      <el-button :icon="Refresh" @click="loadData">刷新</el-button>
    </div>

    <el-alert type="success" :closable="false" class="mb16"
              title="按你的需求自定义练习卷：选知识点、定难度、挑题型，生成专属自测卷" />

    <el-card shadow="never">
      <el-form :model="form" label-width="100px" style="max-width: 720px">
        <el-form-item label="试卷名称">
          <el-input v-model="form.name" placeholder="给我的自测卷起个名字" clearable />
        </el-form-item>

        <el-form-item label="学科">
          <el-select v-model="form.subject_id" placeholder="选择学科" style="width:100%"
                     @change="onSubjectChange">
            <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="年级">
          <el-select v-model="form.grade_id" placeholder="全部年级" clearable style="width:100%">
            <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="题目数量">
          <el-slider v-model="form.count" :min="5" :max="30" show-input style="max-width:400px" />
        </el-form-item>

        <el-form-item label="题型">
          <el-checkbox-group v-model="form.question_types">
            <el-checkbox v-for="(l, v) in TYPES" :key="v" :value="v">{{ l }}</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-form-item label="难度">
          <el-radio-group v-model="form.difficulty">
            <el-radio-button value="">不限</el-radio-button>
            <el-radio-button value="easy">简单</el-radio-button>
            <el-radio-button value="medium">中等</el-radio-button>
            <el-radio-button value="hard">困难</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="限定知识点">
          <el-select v-model="form.knowledge_point_ids" multiple filterable collapse-tags
                     placeholder="不选则全学科范围" style="width:100%">
            <el-option v-for="k in kps" :key="k.id" :label="k.name" :value="k.id" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :icon="MagicStick" :loading="generating" @click="generate">
            生成自测卷
          </el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" class="mt16" v-if="result">
      <template #header><b>组卷结果</b></template>
      <el-result icon="success" :title="`组卷成功：${result.total} 题`"
                 :sub-title="`满分 ${result.total_score} 分`">
        <template #extra>
          <el-button type="primary" size="large" @click="startPractice">
            立即开始答题
          </el-button>
        </template>
      </el-result>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, MagicStick } from '@element-plus/icons-vue'
import { learningApi, eduApi, taskApi } from '@/api'

const router = useRouter()
const subjects = ref([])
const grades = ref([])
const kps = ref([])
const generating = ref(false)
const result = ref(null)

const TYPES = { single: '单选题', multiple: '多选题', judge: '判断题', fill: '填空题', short: '简答题', calculate: '计算题' }

const form = reactive({
  name: '', subject_id: null, grade_id: null, count: 10,
  question_types: ['single', 'multiple', 'judge', 'fill'],
  difficulty: '', knowledge_point_ids: []
})

async function loadData() {
  const [s, g] = await Promise.all([eduApi.subjects(), eduApi.grades()])
  subjects.value = s.data || []
  grades.value = g.data || []
}

async function onSubjectChange() {
  if (!form.subject_id) { kps.value = []; return }
  const res = await eduApi.knowledgeList({ subject_id: form.subject_id, page_size: 200 })
  kps.value = res.data?.items || res.data || []
}

function resetForm() {
  Object.assign(form, {
    name: '', subject_id: null, grade_id: null, count: 10,
    question_types: ['single', 'multiple', 'judge', 'fill'], difficulty: '', knowledge_point_ids: []
  })
  kps.value = []
  result.value = null
}

async function generate() {
  if (!form.subject_id) return ElMessage.warning('请选择学科')
  generating.value = true
  result.value = null
  try {
    const res = await learningApi.customPaper(form)
    result.value = res.data
    ElMessage.success(res.message)
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '组卷失败')
  } finally {
    generating.value = false
  }
}

function startPractice() {
  if (result.value?.task_id) {
    router.push(`/student/exam/${result.value.task_id}`)
  }
}

onMounted(loadData)
</script>

<style scoped>
.mb16 { margin-bottom: 16px; }
.mt16 { margin-top: 16px; }
</style>
