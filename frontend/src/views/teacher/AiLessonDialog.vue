<template>
  <el-dialog v-model="visible" title="AI 生成教案" width="1080px" top="4vh"
             destroy-on-close @closed="onClosed">
    <!-- 步骤条：条件 → 生成中 → 预览编辑 → 保存 -->
    <el-steps :active="step" align-center finish-status="success" class="mb16">
      <el-step title="填写条件" />
      <el-step title="AI 生成" />
      <el-step title="预览与编辑" />
      <el-step title="存入教案库" />
    </el-steps>

    <!-- ---------------- 第一步：条件 ---------------- -->
    <div v-show="step === 0" class="cond-wrap">
      <el-form :model="cond" :rules="rules" ref="condRef" label-width="110px">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="年级" prop="grade_id">
              <el-select v-model="cond.grade_id" placeholder="请选择年级"
                         style="width:100%" @change="onGradeChange">
                <el-option v-for="g in options.grades" :key="g.id"
                           :label="g.name" :value="g.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="学科" prop="subject_id">
              <el-select v-model="cond.subject_id" placeholder="先选年级"
                         style="width:100%" :disabled="!cond.grade_id"
                         @change="onSubjectChange">
                <el-option v-for="s in options.subjects" :key="s.id"
                           :label="s.name" :value="s.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="教学主题" prop="topic">
          <el-input v-model="cond.topic" placeholder="如：一元一次方程的解法——移项"
                    maxlength="128" show-word-limit />
        </el-form-item>

        <el-form-item label="关联知识点">
          <el-select v-model="cond.knowledge_point_id" clearable filterable
                     placeholder="可选，选中后教案会围绕该知识点展开"
                     style="width:100%" :disabled="!options.knowledge_points.length">
            <el-option v-for="k in options.knowledge_points" :key="k.id"
                       :label="k.name" :value="k.id" />
          </el-select>
        </el-form-item>

        <el-row :gutter="12">
          <el-col :span="8">
            <el-form-item label="课时（分钟）" prop="duration_minutes">
              <el-input-number v-model="cond.duration_minutes" :min="15" :max="180"
                               :step="5" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="第几课时">
              <el-input v-model="cond.period" placeholder="如：第 1 课时" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="教材版本">
              <el-input v-model="cond.textbook_version" placeholder="如：人教版 2024" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="教学目标">
          <el-input v-model="cond.objectives" type="textarea" :rows="3"
                    placeholder="可选。留空由 AI 拟定；填写则 AI 会按你的要求优化表述并保留原意" />
        </el-form-item>
        <el-form-item label="补充要求">
          <el-input v-model="cond.extra_requirements" type="textarea" :rows="2"
                    placeholder="可选。如：需要小组合作环节 / 结合本校学情降低难度 / 融入信息技术" />
        </el-form-item>
      </el-form>
    </div>

    <!-- ---------------- 第二步：生成中 ---------------- -->
    <div v-show="step === 1" class="gen-wrap">
      <el-progress :percentage="job.progress" :stroke-width="14" :status="progressStatus"
                   striped striped-flow />
      <div class="gen-stage">{{ job.stage || '正在生成…' }}</div>
      <el-alert type="info" :closable="false" class="mt12"
                title="生成通常需要 20~60 秒，可关闭此窗口稍后在「生成记录」里查看结果" />
      <div class="gen-actions">
        <el-button @click="cancelPoll" :loading="polling">后台生成，稍后查看</el-button>
      </div>
    </div>

    <!-- ---------------- 第三步：预览与编辑 ---------------- -->
    <div v-show="step === 2" class="preview-wrap">
      <!-- 质量提示：AI 产物不可盲信，缺哪节就明说 -->
      <el-alert v-if="qualityWarn" :type="qualityType" :closable="false" class="mb12"
                show-icon>
        <template #title>
          <span v-if="result.generation?.mode === 'rule'">
            未配置大模型，本教案由规则引擎按模板生成 —— 题目与情境需教师补充具体内容
          </span>
          <span v-else-if="result.generation?.missing?.length">
            以下章节 AI 未能完整生成，已用模板补全，请重点核对：{{ result.generation.missing.join('、') }}
          </span>
          <span v-else>已生成，仍建议核对重难点与实际学情是否匹配</span>
        </template>
        <div v-if="result.generation?.warnings?.length" class="warn-list">
          <div v-for="(w, i) in result.generation.warnings" :key="i">· {{ w }}</div>
        </div>
      </el-alert>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="基本信息" name="base">
          <el-form :model="edit" label-width="110px">
            <el-form-item label="教案标题">
              <el-input v-model="edit.title" maxlength="128" />
            </el-form-item>
            <el-form-item label="课题">
              <el-input v-model="edit.topic" maxlength="128" />
            </el-form-item>
            <el-form-item label="教学目标">
              <el-input v-model="edit.objectives" type="textarea" :rows="4" />
            </el-form-item>
            <el-form-item label="教学重点">
              <el-input v-model="edit.key_points" type="textarea" :rows="3" />
            </el-form-item>
            <el-form-item label="教学难点">
              <el-input v-model="edit.difficulties" type="textarea" :rows="3" />
            </el-form-item>
            <el-form-item label="教学准备">
              <el-input v-model="edit.teaching_preparation" type="textarea" :rows="3" />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane name="stages">
          <template #label>
            教学过程（{{ timeTotal }} / {{ cond.duration_minutes }} 分钟）
          </template>
          <el-alert v-if="timeTotal !== cond.duration_minutes" type="warning"
                    :closable="false" class="mb8" show-icon
                    :title="`各环节合计 ${timeTotal} 分钟，与设定的 ${cond.duration_minutes} 分钟不一致`" />
          <div class="stage-table">
            <el-table :data="edit.stages" border size="small">
              <el-table-column label="环节" width="140">
                <template #default="{ row }">
                  <el-input v-model="row.name" size="small" maxlength="32" />
                </template>
              </el-table-column>
              <el-table-column label="时长" width="110" align="center">
                <template #default="{ row }">
                  <el-input-number v-model="row.duration_minutes" :min="1" :max="120"
                                   size="small" controls-position="right" style="width:90px" />
                </template>
              </el-table-column>
              <el-table-column label="教师活动" min-width="220">
                <template #default="{ row }">
                  <el-input v-model="row.teacher_activity" type="textarea" :rows="3" />
                </template>
              </el-table-column>
              <el-table-column label="学生活动" min-width="220">
                <template #default="{ row }">
                  <el-input v-model="row.student_activity" type="textarea" :rows="3" />
                </template>
              </el-table-column>
              <el-table-column label="设计意图" min-width="160">
                <template #default="{ row }">
                  <el-input v-model="row.content" type="textarea" :rows="3" />
                </template>
              </el-table-column>
            </el-table>
            <el-button :icon="Plus" plain size="small" class="mt8"
                       @click="edit.stages.push({ name: '新环节', duration_minutes: 5, content: '', teacher_activity: '', student_activity: '' })">
              添加环节
            </el-button>
          </div>
        </el-tab-pane>

        <el-tab-pane label="练习 · 作业 · 板书" name="rest">
          <el-form :model="edit" label-width="110px">
            <el-form-item label="课堂练习">
              <el-input v-model="edit.class_exercise" type="textarea" :rows="6" />
            </el-form-item>
            <el-form-item label="作业布置">
              <el-input v-model="edit.homework" type="textarea" :rows="4" />
            </el-form-item>
            <el-form-item label="板书设计">
              <el-input v-model="edit.board_design" type="textarea" :rows="8" />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="预览" name="md">
          <pre class="md-preview">{{ markdownPreview }}</pre>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- ---------------- 第四步：完成 ---------------- -->
    <div v-show="step === 3" class="done-wrap">
      <el-result icon="success" title="已存入教案库"
                 :sub-title="savedInfo">
        <template #extra>
          <el-button type="primary" @click="goManage">去教案管理查看</el-button>
          <el-button @click="restart">再生成一份</el-button>
        </template>
      </el-result>
    </div>

    <template #footer>
      <div class="footer-bar">
        <span class="footer-tip">
          <el-tag v-if="job.jobId" size="small" type="info">任务 #{{ job.jobId }}</el-tag>
          <span v-if="step === 2" class="ml8">
            生成方式：{{ result.generation?.mode === 'llm' ? '大模型' : '规则引擎' }}
          </span>
        </span>
        <span>
          <el-button v-if="step === 0" @click="visible = false">取消</el-button>
          <el-button v-if="step === 0" type="primary" :icon="MagicStick"
                     :loading="submitting" @click="doGenerate">开始生成</el-button>
          <el-button v-if="step === 2" @click="step = 1">重新生成</el-button>
          <el-button v-if="step === 2" :icon="Download" :disabled="!job.jobId"
                     @click="doExport">导出 Markdown</el-button>
          <el-button v-if="step === 2" type="primary" :icon="Check"
                     :loading="savingToLib" @click="doSave">保存到教案库</el-button>
          <el-button v-if="step === 3" type="primary" @click="visible = false">完成</el-button>
        </span>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, MagicStick, Download, Check } from '@element-plus/icons-vue'
import { lessonAiApi } from '@/api'
import { downloadBlob } from '@/utils/download'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  // 从筛选栏带入的默认年级/学科，避免用户再选一遍
  defaultGradeId: { type: [Number, String], default: null },
  defaultSubjectId: { type: [Number, String], default: null },
  // 从「生成记录」恢复：直接跳到预览步骤，不必重新生成
  resumeJobId: { type: [Number, String], default: null }
})
const emit = defineEmits(['update:modelValue', 'saved'])

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v)
})

const step = ref(0)
const activeTab = ref('base')
const submitting = ref(false)
const savingToLib = ref(false)
const savedInfo = ref('')
const condRef = ref()

const options = reactive({ grades: [], subjects: [], knowledge_points: [] })
const cond = reactive({
  grade_id: null, subject_id: null, topic: '', knowledge_point_id: null,
  duration_minutes: 45, period: '', textbook_version: '',
  objectives: '', extra_requirements: ''
})
const rules = {
  grade_id: [{ required: true, message: '请选择年级', trigger: 'change' }],
  subject_id: [{ required: true, message: '请选择学科', trigger: 'change' }],
  topic: [{ required: true, message: '请填写教学主题', trigger: 'blur' }],
  duration_minutes: [{ required: true, message: '请填写课时', trigger: 'blur' }]
}

const job = reactive({ jobId: null, status: '', progress: 0, stage: '', error: '' })
const result = ref({})
const edit = ref({ stages: [] })
const polling = ref(false)
let timer = null

const progressStatus = computed(() => {
  if (job.status === 'success') return 'success'
  if (job.status === 'failed') return 'exception'
  return ''
})

// 环节时长合计：与课时对比，实时提示
const timeTotal = computed(() =>
  (edit.value.stages || []).reduce((s, x) => s + (Number(x.duration_minutes) || 0), 0))

const qualityType = computed(() => {
  const q = result.value.generation?.quality
  if (q === 'low') return 'error'
  if (q === 'medium') return 'warning'
  return 'success'
})
const qualityWarn = computed(() => {
  const g = result.value.generation
  if (!g) return false
  return g.mode === 'rule' || q_hasIssue(g)
})
function q_hasIssue(g) {
  return !!(g.missing?.length || g.warnings?.length)
}

// 预览用 Markdown：只做最小渲染（标题/加粗/表格用等宽文本展示），
// 不引入 markdown 依赖 —— 教案正文是纯文本，等宽预排版足够阅读。
const markdownPreview = computed(() => {
  const e = edit.value
  const lines = [`# ${e.title || e.topic || '教案'}`, '']
  const secs = [
    ['一、教学目标', e.objectives], ['二、教学重点', e.key_points],
    ['三、教学难点', e.difficulties], ['四、教学准备', e.teaching_preparation]
  ]
  secs.forEach(([h, v]) => { lines.push(`## ${h}`, '', v || '（未填写）', '') })
  lines.push('## 五、教学过程', '')
  ;(e.stages || []).forEach((s, i) => {
    lines.push(`### 5.${i + 1} ${s.name}（${s.duration_minutes} 分钟）`)
    if (s.content) lines.push(`设计意图：${s.content}`)
    if (s.teacher_activity) lines.push('【教师活动】', s.teacher_activity)
    if (s.student_activity) lines.push('【学生活动】', s.student_activity)
    lines.push('')
  })
  const rest = [
    ['六、课堂练习', e.class_exercise], ['七、作业布置', e.homework],
    ['八、板书设计', e.board_design]
  ]
  rest.forEach(([h, v]) => { lines.push(`## ${h}`, '', v || '（未填写）', '') })
  return lines.join('\n')
})

// ------------------------------------------------------------ 条件联动
async function loadOptions(gradeId) {
  const r = await lessonAiApi.options(gradeId)
  const d = r.data || {}
  options.grades = d.grades || []
  options.subjects = d.subjects || []
  options.knowledge_points = d.knowledge_points || []
}

async function onGradeChange(gid) {
  // 年级变了必须重取学科：学科是按年级配置的，沿用旧年级的 subject_id
  // 会生成整份错年级的教案（后端也会 400，但这里先纠正体验更好）
  cond.subject_id = null
  cond.knowledge_point_id = null
  await loadOptions(gid)
}
function onSubjectChange() {
  cond.knowledge_point_id = null
}

// ------------------------------------------------------------ 生成
async function doGenerate() {
  try {
    await condRef.value.validate()
  } catch { return }

  submitting.value = true
  job.jobId = null
  job.progress = 0
  job.stage = '任务排队中'
  job.status = 'pending'
  job.error = ''
  step.value = 1

  try {
    const r = await lessonAiApi.generate({
      topic: cond.topic.trim(),
      grade_id: cond.grade_id,
      subject_id: cond.subject_id,
      knowledge_point_id: cond.knowledge_point_id || null,
      duration_minutes: cond.duration_minutes,
      period: cond.period || null,
      textbook_version: cond.textbook_version || null,
      objectives: cond.objectives || '',
      extra_requirements: cond.extra_requirements || ''
    })
    job.jobId = r.data?.job_id
    startPoll()
  } catch (e) {
    job.status = 'failed'
    job.error = e?.response?.data?.message || e?.message || '提交失败'
    step.value = 0
    ElMessage.error(job.error)
  } finally {
    submitting.value = false
  }
}

function startPoll() {
  stopPoll()
  polling.value = true
  // 2 秒一次；与后端 JOB_TIMEOUT_SECONDS(300s) 对齐留余量
  let ticks = 0
  timer = setInterval(async () => {
    ticks += 1
    if (ticks > 200) {           // 约 400s 兜底，避免无限轮询
      stopPoll()
      job.status = 'failed'
      job.error = '生成超时，请稍后在生成记录中查看或重试'
      return
    }
    try {
      const r = await lessonAiApi.job(job.jobId)
      const d = r.data || {}
      job.status = d.status
      job.progress = d.progress || 0
      job.stage = d.stage || ''
      if (d.status === 'success') {
        stopPoll()
        applyResult(d.result || {})
      } else if (d.status === 'failed') {
        stopPoll()
        job.error = d.error || '生成失败'
        ElMessage.error(job.error)
      }
    } catch (e) {
      // 单次轮询失败不终止：网络抖动很常见，交给 ticks 兜底
      if (e?.response?.status === 403 || e?.response?.status === 404) {
        stopPoll()
        job.status = 'failed'
        job.error = e?.response?.data?.message || '任务不可访问'
      }
    }
  }, 2000)
}

function stopPoll() {
  if (timer) { clearInterval(timer); timer = null }
  polling.value = false
}

function cancelPoll() {
  stopPoll()
  visible.value = false
  ElMessage.info(`任务 #${job.jobId} 在后台继续生成，可从「生成记录」查看`)
}

function applyResult(data) {
  result.value = data
  // 深拷贝到可编辑副本：直接绑定 result 会让「重新生成」时上一份的修改残留
  edit.value = {
    title: data.title || '',
    topic: data.topic || '',
    objectives: data.objectives || '',
    key_points: data.key_points || '',
    difficulties: data.difficulties || '',
    teaching_preparation: data.teaching_preparation || '',
    class_exercise: data.class_exercise || '',
    homework: data.homework || '',
    board_design: data.board_design || '',
    stages: (data.stages || []).map(s => ({
      name: s.name, duration_minutes: s.duration_minutes,
      content: s.content || '',
      teacher_activity: s.teacher_activity || '',
      student_activity: s.student_activity || ''
    }))
  }
  step.value = 2
  activeTab.value = 'base'
}

// ------------------------------------------------------------ 导出 / 保存
async function doExport() {
  if (!job.jobId) return
  // 此前用 fetch + localStorage.getItem('token') 手拼请求头：全站 token 键名
  // 是 access_token，取到的永远是空串 → 导出必 401。
  // 统一走 axios（拦截器注入 Authorization）+ blob 本地下载。
  await downloadBlob(lessonAiApi.exportBlob(job.jobId),
    `${edit.value.title || edit.value.topic || '教案'}.md`)
  ElMessage.success('已导出 Markdown')
}

async function doSave() {
  if (!edit.value.topic) {
    ElMessage.warning('课题不能为空')
    return
  }
  savingToLib.value = true
  try {
    // 提交编辑后的全部字段：用户可能改了任何一处，逐字段 diff 反而容易漏
    const r = await lessonAiApi.save(job.jobId, {
      ...edit.value,
      grade_id: result.value.grade_id ?? cond.grade_id,
      subject_id: result.value.subject_id ?? cond.subject_id,
      knowledge_point_id: result.value.knowledge_point_id ?? cond.knowledge_point_id,
      duration_minutes: cond.duration_minutes,
      period: result.value.period ?? cond.period,
      textbook_version: result.value.textbook_version ?? cond.textbook_version
    })
    savedInfo.value = `《${r.data?.title || edit.value.title}》已保存，可在教案管理中继续编辑或上传课件`
    step.value = 3
    emit('saved', r.data)
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || e?.message || '保存失败')
  } finally {
    savingToLib.value = false
  }
}

function goManage() {
  visible.value = false
  emit('saved')
}

function restart() {
  step.value = 0
  job.jobId = null
  result.value = {}
  edit.value = { stages: [] }
}

function onClosed() {
  stopPoll()
  step.value = 0
  job.jobId = null
  job.progress = 0
  job.stage = ''
  job.status = ''
  job.error = ''
  result.value = {}
  edit.value = { stages: [] }
}

// 打开时预取选项并带入筛选条件
watch(() => props.modelValue, async (open) => {
  if (!open) return
  await loadOptions(props.defaultGradeId)
  if (props.defaultGradeId) cond.grade_id = props.defaultGradeId
  if (props.defaultSubjectId) cond.subject_id = props.defaultSubjectId
  // 从生成记录恢复：拉完整结果直接进预览
  if (props.resumeJobId) {
    try {
      const r = await lessonAiApi.job(props.resumeJobId)
      const d = r.data || {}
      if (d.status === 'success' && d.result) {
        job.jobId = d.job_id
        job.status = 'success'
        job.progress = 100
        cond.topic = d.result.topic || cond.topic
        cond.duration_minutes = d.result.duration_minutes || cond.duration_minutes
        cond.period = d.result.period || ''
        if (d.result.grade_id) {
          cond.grade_id = d.result.grade_id
          await loadOptions(cond.grade_id)
          cond.subject_id = d.result.subject_id || null
        }
        applyResult(d.result)
      } else {
        ElMessage.warning(d.error || '该任务结果不可用')
      }
    } catch (e) {
      ElMessage.error(e?.response?.data?.message || '读取结果失败')
    }
  }
})

onBeforeUnmount(stopPoll)
</script>

<style scoped>
.mb8 { margin-bottom: 8px; }
.mb12 { margin-bottom: 12px; }
.mb16 { margin-bottom: 16px; }
.mt8 { margin-top: 8px; }
.mt12 { margin-top: 12px; }
.ml8 { margin-left: 8px; }
.gen-wrap { padding: 40px 60px; text-align: center; }
.gen-stage { margin-top: 16px; font-size: 15px; color: var(--el-text-color-primary); }
.gen-actions { margin-top: 24px; }
.warn-list { margin-top: 6px; font-size: 13px; line-height: 1.7; }
.md-preview {
  white-space: pre-wrap; word-break: break-word;
  background: var(--el-fill-color-light); padding: 16px; border-radius: 4px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 13px; line-height: 1.7; max-height: 52vh; overflow: auto;
  color: var(--el-text-color-primary);
}
.footer-bar { display: flex; align-items: center; justify-content: space-between; }
.footer-tip { color: var(--el-text-color-secondary); font-size: 13px; }
.cond-wrap { max-height: 62vh; overflow-y: auto; padding-right: 6px; }
.preview-wrap { max-height: 64vh; overflow-y: auto; padding-right: 6px; }
</style>
