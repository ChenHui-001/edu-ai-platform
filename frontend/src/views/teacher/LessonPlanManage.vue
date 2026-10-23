<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">教案管理</h2>
      <div>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
        <el-button :icon="CopyDocument" @click="onlyMine = !onlyMine; load()">
          {{ onlyMine ? '看共享' : '只看我的' }}
        </el-button>
        <el-button :icon="Clock" @click="openHistory">生成记录</el-button>
        <el-button v-if="can('lesson:plan:write')" type="primary" :icon="MagicStick"
                   @click="aiVisible = true">AI 生成教案</el-button>
        <el-button v-if="can('lesson:plan:write')" :icon="Plus"
                   @click="openDialog()">新建教案</el-button>
      </div>
    </div>

    <!-- 筛选 -->
    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="query">
        <el-form-item label="学科">
          <el-select v-model="query.subject_id" placeholder="全部" clearable style="width:160px">
            <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="年级">
          <el-select v-model="query.grade_id" placeholder="全部" clearable style="width:130px">
            <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="query.keyword" placeholder="标题/课题" clearable
                    style="width:200px" @keyup.enter="load" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="load">查询</el-button>
          <el-button :icon="RefreshLeft" @click="reset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 列表 -->
    <el-card shadow="never">
      <el-table v-loading="loading" :data="list" border stripe>
        <el-table-column prop="title" label="教案标题" min-width="220" show-overflow-tooltip />
        <el-table-column prop="topic" label="课题" min-width="160" show-overflow-tooltip />
        <el-table-column label="学科/年级" width="160">
          <template #default="{ row }">
            <el-tag size="small" class="mr4">{{ row.subject_name || '-' }}</el-tag>
            <el-tag size="small" type="info">{{ row.grade_name || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="课时" width="80" align="center">
          <template #default="{ row }">
            {{ row.duration_minutes || 45 }} 分钟
          </template>
        </el-table-column>
        <el-table-column prop="period" label="第几课时" width="100" show-overflow-tooltip />
        <el-table-column label="使用次数" width="90" align="center" prop="use_count" />
        <el-table-column label="共享" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_shared" type="success" size="small">已共享</el-tag>
            <el-tag v-else type="info" size="small">私有</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="来源" width="86" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.ai_generated" type="warning" size="small">AI</el-tag>
            <el-tag v-else type="info" size="small" effect="plain">人工</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="更新时间" width="160" prop="updated_at" />
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDialog(row)">查看/编辑</el-button>
            <el-button link type="primary" v-if="can('lesson:plan:copy')"
                       @click="copyPlan(row)">复制</el-button>
            <el-button link type="warning" v-if="can('lesson:plan:share') && row.creator_id === meId"
                       @click="toggleShare(row)">
              {{ row.is_shared ? '取消共享' : '共享' }}
            </el-button>
            <el-button link type="danger" v-if="can('lesson:plan:write') && row.creator_id === meId"
                       @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination class="mt16" background layout="total, prev, pager, next, jumper"
                     :total="total" v-model:current-page="query.page"
                     :page-size="query.page_size" @current-change="load" />
    </el-card>

    <!-- 编辑/新建 弹窗 -->
    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑教案' : '新建教案'" width="920px"
               destroy-on-close>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-row :gutter="10">
          <el-col :span="12">
            <el-form-item label="标题" prop="title">
              <el-input v-model="form.title" placeholder="如：解一元一次方程——移项" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="课题" prop="topic">
              <el-input v-model="form.topic" placeholder="如：解一元一次方程" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="10">
          <el-col :span="8">
            <el-form-item label="学科" prop="subject_id">
              <el-select v-model="form.subject_id" style="width:100%" @change="onFormSubjectChange">
                <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="年级" prop="grade_id">
              <el-select v-model="form.grade_id" style="width:100%" @change="onFormGradeChange">
                <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="4">
            <el-form-item label="课时（分）">
              <el-input-number v-model="form.duration_minutes" :min="5" :max="180" :step="5" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="4">
            <el-form-item label="第几课时">
              <el-input v-model="form.period" placeholder="如：第 1 课时" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="关联知识点">
          <el-select v-model="form.knowledge_point_id" clearable filterable
                     style="width:100%" :disabled="!formKnowledge.length">
            <el-option v-for="k in formKnowledge" :key="k.id" :label="k.name" :value="k.id" />
          </el-select>
        </el-form-item>
        <el-row :gutter="10">
          <el-col :span="12">
            <el-form-item label="教学目标">
              <el-input v-model="form.objectives" type="textarea" :rows="4"
                        placeholder="知识与技能 / 过程与方法 / 情感态度价值观" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="教学准备">
              <el-input v-model="form.teaching_preparation" type="textarea" :rows="4"
                        placeholder="教师准备（课件/教具）与学生准备（学具/预习）" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="10">
          <el-col :span="12">
            <el-form-item label="教学重点">
              <el-input v-model="form.key_points" type="textarea" :rows="4" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="教学难点">
              <el-input v-model="form.difficulties" type="textarea" :rows="4" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="板书设计">
          <el-input v-model="form.board_design" type="textarea" :rows="3" />
        </el-form-item>
        <el-divider content-position="left">教学过程</el-divider>
        <div v-for="(stage, i) in form.stages" :key="i" class="stage-block">
          <div class="stage-head">
            <el-input v-model="stage.name" placeholder="阶段名（导入/新授/练习/小结/作业）"
                      style="width:200px" size="small" />
            <el-input-number v-model="stage.duration_minutes" :min="1" :max="120" :step="1"
                             size="small" style="width:110px" />
            <span class="stage-unit">分钟</span>
            <span class="stage-spacer" />
            <el-button :icon="Delete" link type="danger"
                       @click="form.stages.splice(i, 1)">删除</el-button>
          </div>
          <el-row :gutter="8">
            <el-col :span="12">
              <el-input v-model="stage.teacher_activity" type="textarea" :rows="3"
                        placeholder="教师活动：具体动作与关键提问" />
            </el-col>
            <el-col :span="12">
              <el-input v-model="stage.student_activity" type="textarea" :rows="3"
                        placeholder="学生活动：具体任务与预期表现" />
            </el-col>
          </el-row>
          <el-input v-model="stage.content" type="textarea" :rows="2" class="mt4"
                    placeholder="设计意图（可选）" />
        </div>
        <el-button :icon="Plus" plain size="small" @click="addStage" class="mt8">添加阶段</el-button>

        <el-form-item label="课堂练习" class="mt12">
          <el-input v-model="form.class_exercise" type="textarea" :rows="3"
                    placeholder="随堂检测题，建议附参考答案" />
        </el-form-item>
        <el-form-item label="作业布置">
          <el-input v-model="form.homework" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="教学反思">
          <el-input v-model="form.reflection" type="textarea" :rows="2" placeholder="课后可填写" />
        </el-form-item>
        <el-form-item label="教学附件">
          <div class="att-block w-full">
            <!-- 新建态：先保存拿到 id 才能挂附件 -->
            <el-upload v-if="form.id" drag multiple
                       :show-file-list="false"
                       :http-request="doUploadAttachment"
                       accept=".jpg,.jpeg,.png,.gif,.webp,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.csv,.md"
                       class="w-full">
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text">拖拽文件到此处，或 <em>点击上传</em></div>
              <template #tip>
                <div class="el-upload__tip">支持图片 / PPT / Word / Excel / PDF，单个 ≤ 50MB</div>
              </template>
            </el-upload>
            <el-alert v-else type="info" :closable="false"
                      title="保存教案后即可上传课件附件（图片 / PPT / 文档）" />
            <!-- 附件列表 -->
            <div v-if="attachments.length" class="att-list mt8">
              <div v-for="a in attachments" :key="a.id" class="att-item">
                <el-icon class="mr4"><Document /></el-icon>
                <span class="att-name" :title="a.filename">{{ a.filename }}</span>
                <el-tag size="small" type="info" class="mr4">{{ (a.file_size / 1024).toFixed(0) }} KB</el-tag>
                <el-button link type="primary" size="small"
                           @click="previewAtt(a)">预览</el-button>
                <el-button link type="primary" size="small"
                           @click="downloadAtt(a)">下载</el-button>
                <el-button link type="danger" size="small"
                           v-if="a.uploader_id === meId"
                           @click="removeAtt(a)">删除</el-button>
              </div>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="共享给同科">
          <el-switch v-model="form.is_shared" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">关闭</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存教案</el-button>
      </template>
    </el-dialog>

    <!-- AI 生成教案（条件 → 进度 → 预览编辑 → 入库） -->
    <AiLessonDialog v-model="aiVisible" :default-grade-id="query.grade_id"
                    :default-subject-id="query.subject_id"
                    :resume-job-id="aiResumeJobId" @saved="onAiSaved" />

    <!-- 生成记录：后台跑的、失败的任务都能在这里找回 -->
    <el-drawer v-model="historyVisible" title="AI 生成记录" size="620px">
      <el-table v-loading="historyLoading" :data="history" size="small" border>
        <el-table-column prop="topic" label="教学主题" min-width="160" show-overflow-tooltip />
        <el-table-column label="状态" width="92" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'success'" type="success" size="small">已完成</el-tag>
            <el-tag v-else-if="row.status === 'failed'" type="danger" size="small">失败</el-tag>
            <el-tag v-else type="warning" size="small">{{ row.progress }}%</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration_minutes" label="课时" width="70" align="center" />
        <el-table-column prop="created_at" label="提交时间" width="150" />
        <el-table-column label="操作" width="110" align="center">
          <template #default="{ row }">
            <el-button link type="primary" size="small"
                       :disabled="row.status !== 'success'"
                       @click="viewHistoryJob(row)">查看</el-button>
            <el-button link type="danger" size="small" v-if="row.error"
                       @click="showJobError(row)">原因</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!historyLoading && !history.length"
                description="还没有生成记录，点右上角「AI 生成教案」开始" />
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Refresh, RefreshLeft, Search, Delete, CopyDocument, UploadFilled,
  MagicStick, Clock, Document
} from '@element-plus/icons-vue'
import { lessonApi, lessonAiApi, attachmentApi, eduApi } from '@/api'
import { useUserStore } from '@/store/user'
import { downloadBlob, fetchBlobUrl } from '@/utils/download'
import AiLessonDialog from './AiLessonDialog.vue'

const { can } = useUserStore()
const meId = (window.localStorage.getItem('user') &&
  JSON.parse(window.localStorage.getItem('user')) || {}).id

const list = ref([])
const total = ref(0)
const loading = ref(false)
const onlyMine = ref(false)
const subjects = ref([])
const grades = ref([])
const formKnowledge = ref([])

const query = reactive({ page: 1, page_size: 20, subject_id: null,
  grade_id: null, keyword: '' })

async function load() {
  loading.value = true
  try {
    const params = Object.fromEntries(
      Object.entries({ ...query, only_mine: onlyMine.value })
        .filter(([, v]) => v !== null && v !== ''))
    const res = await lessonApi.list(params)
    list.value = res.data?.items || []
    total.value = res.data?.total || 0
  } finally { loading.value = false }
}

function reset() {
  Object.assign(query, { page: 1, subject_id: null, grade_id: null, keyword: '' })
  load()
}

const dialogVisible = ref(false)
const saving = ref(false)
const formRef = ref()
const form = reactive({
  id: null, title: '', topic: '', subject_id: null, grade_id: null,
  knowledge_point_id: null, duration_minutes: 45, period: '',
  objectives: '', key_points: '', difficulties: '',
  teaching_preparation: '', class_exercise: '',
  board_design: '', homework: '', reflection: '',
  is_shared: false, stages: []
})

const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  topic: [{ required: true, message: '请输入课题', trigger: 'blur' }],
  subject_id: [{ required: true, message: '请选择学科', trigger: 'change' }],
  grade_id: [{ required: true, message: '请选择年级', trigger: 'change' }]
}

function addStage() {
  form.stages.push({
    name: '', duration_minutes: 5, content: '',
    teacher_activity: '', student_activity: ''
  })
}

async function openDialog(row) {
  form.id = row?.id ?? null
  if (form.id) {
    const r = await lessonApi.detail(form.id)
    const d = r.data || {}
    Object.assign(form, {
      title: d.title, topic: d.topic,
      subject_id: d.subject_id, grade_id: d.grade_id,
      knowledge_point_id: d.knowledge_point_id,
      duration_minutes: d.duration_minutes || 45,
      period: d.period || '',
      objectives: d.objectives || '',
      key_points: d.key_points || '',
      difficulties: d.difficulties || '',
      teaching_preparation: d.teaching_preparation || '',
      class_exercise: d.class_exercise || '',
      board_design: d.board_design || '',
      homework: d.homework || '',
      reflection: d.reflection || '',
      is_shared: !!d.is_shared,
      stages: (d.stages || []).map(s => ({
        ...s,
        teacher_activity: s.teacher_activity || '',
        student_activity: s.student_activity || ''
      }))
    })
    if (form.subject_id && form.grade_id) {
      await loadFormKnowledge(form.grade_id, form.subject_id)
    }
    await loadAttachments()
  } else {
    Object.assign(form, {
      id: null, title: '', topic: '', subject_id: query.subject_id,
      grade_id: query.grade_id, knowledge_point_id: null,
      duration_minutes: 45, period: '',
      objectives: '', key_points: '', difficulties: '',
      teaching_preparation: '', class_exercise: '',
      board_design: '', homework: '', reflection: '',
      is_shared: false, stages: []
    })
    attachments.value = []
    form.stages.push({ name: '导入', duration_minutes: 3, content: '', teacher_activity: '', student_activity: '' })
    form.stages.push({ name: '新课讲授', duration_minutes: 25, content: '', teacher_activity: '', student_activity: '' })
    form.stages.push({ name: '课堂练习', duration_minutes: 10, content: '', teacher_activity: '', student_activity: '' })
    form.stages.push({ name: '课堂小结', duration_minutes: 5, content: '', teacher_activity: '', student_activity: '' })
    form.stages.push({ name: '布置作业', duration_minutes: 2, content: '', teacher_activity: '', student_activity: '' })
  }
  dialogVisible.value = true
}

async function onFormSubjectChange() {
  form.knowledge_point_id = null
  if (form.subject_id && form.grade_id) await loadFormKnowledge(form.grade_id, form.subject_id)
}
async function onFormGradeChange() {
  form.knowledge_point_id = null
  if (form.subject_id && form.grade_id) await loadFormKnowledge(form.grade_id, form.subject_id)
}
async function loadFormKnowledge(gid, sid) {
  if (!gid || !sid) { formKnowledge.value = []; return }
  const r = await eduApi.knowledgeList({ grade_id: gid, subject_id: sid, params_limit: 200 })
  formKnowledge.value = r.data || []
}

async function save() {
  await formRef.value.validate()
  saving.value = true
  try {
    const payload = {
      ...form,
      is_shared: form.is_shared ? 1 : 0,
      stages: form.stages
        .filter(s => s.name)
        .map((s, i) => ({ ...s, sort_order: i }))
    }
    if (form.id) {
      await lessonApi.update(form.id, payload)
      ElMessage.success('保存成功')
      dialogVisible.value = false
    } else {
      // 新建成功：回写 id 并保持弹窗打开，用户可继续上传课件附件
      const r = await lessonApi.create(payload)
      form.id = (r.data || {}).id
      ElMessage.success('教案已创建，可继续上传教学附件')
      await loadAttachments()
    }
    load()
  } finally { saving.value = false }
}

async function copyPlan(row) {
  const res = await lessonApi.copy(row.id, {})
  ElMessage.success(`已复制：${(res.data || {}).title || '教案'}`)
  load()
}

// ---------------- 附件（图片 / PPT / 文档） ----------------
const attachments = ref([])

async function loadAttachments() {
  if (!form.id) { attachments.value = []; return }
  const r = await lessonApi.attachments(form.id)
  attachments.value = r.data || []
}

// el-upload 自定义上传：直接带教案 id 走教案专用端点（含归属校验）
async function doUploadAttachment({ file }) {
  if (!form.id) return
  const fd = new FormData()
  fd.append('file', file)
  try {
    await lessonApi.uploadAttachment(form.id, fd)
    ElMessage.success(`${file.name} 上传成功`)
    loadAttachments()
  } catch (e) {
    ElMessage.error(`${file.name} 上传失败：${e?.response?.data?.message || e?.message || e}`)
  }
}

// 附件预览/下载：a.preview_url / a.download_url 是后端返回的裸 URL，
// window.open 不带 Authorization（后端只认 Bearer），必 401。
// 改为鉴权 blob 请求 + 本地 objectURL。
const previewUrls = []
async function previewAtt(a) {
  // await 之后再 window.open 会被浏览器弹窗拦截，先同步开一个空白页占位
  const win = window.open('', '_blank')
  try {
    const url = await fetchBlobUrl(attachmentApi.preview(a.id))
    previewUrls.push(url)
    if (win) win.location.href = url
    else window.open(url, '_blank')
  } catch {
    if (win) win.close()
  }
}
async function downloadAtt(a) {
  await downloadBlob(attachmentApi.download(a.id), a.filename || '教案附件')
}
async function removeAtt(a) {
  await ElMessageBox.confirm(`确定删除附件「${a.filename}」吗？`, '提示', { type: 'warning' })
  await lessonApi.removeAttachment(form.id, a.id)
  ElMessage.success('附件已删除')
  loadAttachments()
}

async function toggleShare(row) {
  const next = !row.is_shared
  await lessonApi.share(row.id, { is_shared: next })
  ElMessage.success(next ? '已共享给同科教师' : '已取消共享')
  load()
}

async function remove(row) {
  await ElMessageBox.confirm(`确定删除教案「${row.title}」吗？此操作不可恢复。`,
    '提示', { type: 'warning' })
  await lessonApi.remove(row.id)
  ElMessage.success('已删除')
  load()
}

// ---------------- AI 生成教案 ----------------
const aiVisible = ref(false)
const aiResumeJobId = ref(null)
const historyVisible = ref(false)
const historyLoading = ref(false)
const history = ref([])

function onAiSaved() {
  aiResumeJobId.value = null
  load()
  if (historyVisible.value) openHistory()
}

async function openHistory() {
  historyVisible.value = true
  historyLoading.value = true
  try {
    const r = await lessonAiApi.jobs(30)
    history.value = r.data?.items || []
  } finally {
    historyLoading.value = false
  }
}

function showJobError(row) {
  ElMessageBox.alert(row.error || '生成失败', `任务 #${row.job_id} 失败原因`,
    { type: 'error' })
}

// 从历史记录恢复一次生成结果：交给弹窗按 jobId 拉完整正文并直接进预览
function viewHistoryJob(row) {
  historyVisible.value = false
  aiResumeJobId.value = row.job_id
  aiVisible.value = true
}

// objectURL 给新标签页使用时不能提前释放，页面卸载时统一回收
onBeforeUnmount(() => previewUrls.forEach(u => URL.revokeObjectURL(u)))

onMounted(async () => {
  const [g, s] = await Promise.all([
    eduApi.grades(),
    eduApi.subjects({ distinct: true })
  ])
  grades.value = g.data || []
  subjects.value = s.data || []
  load()
})
</script>

<style scoped>
.filter-card { margin-bottom: 12px; }
.stage-block {
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 4px; padding: 10px; margin-bottom: 10px;
}
.stage-head { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.stage-unit { font-size: 13px; color: var(--el-text-color-secondary); }
.stage-spacer { flex: 1; }
.mt4 { margin-top: 4px; }
.mt8 { margin-top: 8px; }
.mt12 { margin-top: 12px; }
.mt16 { margin-top: 16px; }
.mr4 { margin-right: 4px; }
.w-full { width: 100%; }
.att-block { width: 100%; }
.att-list { display: flex; flex-direction: column; gap: 6px; }
.att-item { display: flex; align-items: center; gap: 4px; font-size: 13px; }
.att-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>