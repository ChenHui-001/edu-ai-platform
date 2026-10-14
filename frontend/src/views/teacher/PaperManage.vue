<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">试卷管理</h2>
      <div>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
        <el-button :icon="DocumentCopy" @click="openAI">AI 智能组卷</el-button>
        <el-button type="primary" :icon="Plus" @click="openDialog()">手动组卷</el-button>
      </div>
    </div>

    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="query">
        <el-form-item label="关键词">
          <el-input v-model="query.keyword" placeholder="试卷名称" clearable style="width:170px"
                    @keyup.enter="load" />
        </el-form-item>
        <el-form-item label="学科">
          <el-select v-model="query.subject_id" placeholder="全部" clearable style="width:130px">
            <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源">
          <el-select v-model="query.source" placeholder="全部" clearable style="width:120px">
            <el-option label="AI 组卷" value="ai" />
            <el-option label="手动组卷" value="manual" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="load">查询</el-button>
          <el-button :icon="Refresh" @click="reset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="list" border stripe>
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="expand-box" v-loading="detailLoading">
              <div v-for="(it, idx) in detailItems" :key="idx" class="q-item">
                <p><b>{{ idx + 1 }}. [{{ it.type_label }}] {{ it.score }} 分</b>
                  <el-tag size="small" class="ml4" :type="diffTag(it.difficulty)">{{ DIFF[it.difficulty] }}</el-tag>
                  <el-tag v-if="it.knowledge_point_name" size="small" type="info" effect="plain" class="ml4">
                    {{ it.knowledge_point_name }}
                  </el-tag>
                </p>
                <p class="stem" v-html="it.stem"></p>
                <p v-if="it.options?.length" class="opts">
                  <span v-for="o in it.options" :key="o.key" class="opt">{{ o.key }}. {{ o.text }}</span>
                </p>
                <p class="answer">答案：{{ it.answer }}</p>
                <p v-if="it.analysis" class="analysis">解析：{{ it.analysis }}</p>
              </div>
              <el-empty v-if="!detailLoading && !detailItems.length" description="该试卷暂无题目" />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="试卷名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="subject_name" label="学科" width="100" />
        <el-table-column prop="grade_name" label="年级" width="110" />
        <el-table-column prop="item_count" label="题量" width="70" align="center" />
        <el-table-column prop="total_score" label="总分" width="80" align="center" />
        <el-table-column prop="duration" label="时长(分)" width="90" align="center" />
        <el-table-column label="来源" width="100">
          <template #default="{ row }">
            <el-tag :type="row.source === 'ai' ? 'success' : 'info'" size="small">
              {{ row.source === 'ai' ? 'AI 组卷' : '手动组卷' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="creator_name" label="创建者" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="160" />
        <el-table-column label="操作" width="230" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewDetail(row)">查看</el-button>
            <el-button link type="primary" @click="openShare(row)">共享</el-button>
            <el-button link type="primary" @click="copyPaper(row)">复制</el-button>
            <el-button link type="warning" @click="exportPaper(row)">导出</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination class="mt16" background layout="total, prev, pager, next"
                     :total="total" v-model:current-page="query.page" @current-change="load" />
    </el-card>

    <!-- 手动组卷 -->
    <el-dialog v-model="dlg" title="手动组卷" width="680px">
      <el-form :model="form" label-width="100px">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="试卷名称">
              <el-input v-model="form.name" placeholder="如：七年级数学期中卷" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="学科">
              <el-select v-model="form.subject_id" style="width:100%" @change="loadQuestions">
                <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="8">
            <el-form-item label="年级">
              <el-select v-model="form.grade_id" clearable style="width:100%">
                <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="总分">
              <el-input-number v-model="form.total_score" :min="10" :max="200" :step="10" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="时长(分)">
              <el-input-number v-model="form.duration" :min="5" :max="240" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>

        <el-form-item label="选题">
          <el-button :icon="Refresh" size="small" @click="loadQuestions">刷新题库</el-button>
          <span class="tip ml8">已选 {{ selected.length }} 题，总分 {{ totalSelectedScore }} 分</span>
        </el-form-item>
        <el-select v-model="selected" multiple filterable placeholder="从题库中选择题目"
                   style="width:100%" :loading="qLoading" class="q-select">
          <el-option v-for="q in questions" :key="q.id"
                     :label="`[${TYPE_LABEL[q.type] || q.type}] ${stripHtml(q.stem).slice(0, 40)}`"
                     :value="q.id" />
        </el-select>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">创建试卷</el-button>
      </template>
    </el-dialog>

    <!-- AI 组卷 -->
    <el-dialog v-model="aiDlg" title="AI 智能组卷" width="640px">
      <el-alert type="info" :closable="false" class="mb12"
                title="用自然语言描述需求，AI 自动解析并组卷。示例：生成七年级数学一元一次方程的试卷，10 题，难度中等偏难" />
      <el-form label-width="90px">
        <el-form-item label="需求描述">
          <el-input v-model="aiReq" type="textarea" :rows="3"
                    placeholder="如：生成八年级物理期中试卷，选择填空，20 题，60 分钟" />
        </el-form-item>
        <el-form-item label="快捷模板">
          <el-button v-for="t in templates" :key="t" size="small" class="mr4"
                     @click="aiReq = t">{{ t.slice(0, 12) }}…</el-button>
        </el-form-item>
      </el-form>

      <div v-if="aiResult" class="ai-result">
        <el-divider content-position="left">
          <b>组卷结果</b>
          <el-tag size="small" class="ml4" :type="aiResult.paper?.is_fallback ? 'warning' : 'success'">
            {{ aiResult.paper?.is_fallback ? '规则引擎（降级）' : '大模型组卷' }}
          </el-tag>
        </el-divider>
        <p><b>试卷名称：</b>{{ aiResult.paper?.name }}</p>
        <p><b>题目数量：</b>{{ aiResult.paper?.question_count ?? aiResult.paper?.total_score ?? '-' }}</p>
        <p v-if="aiResult.analysis"><b>难度分析：</b>{{ aiResult.analysis }}</p>
        <p v-if="aiResult.knowledge_coverage"><b>知识点覆盖：</b>{{ aiResult.knowledge_coverage }}</p>
        <p v-if="aiResult.paper?.id" class="mt8">
          <el-button type="success" size="small" @click="useResult">使用该试卷</el-button>
        </p>
      </div>

      <template #footer>
        <el-button @click="aiDlg = false">关闭</el-button>
        <el-button type="primary" :loading="aiLoading" :icon="MagicStick" @click="runAI">开始组卷</el-button>
      </template>
    </el-dialog>

    <!-- 共享 -->
    <el-dialog v-model="shareDlg" title="共享试卷给同科教师" width="480px">
      <el-form label-width="90px">
        <el-form-item label="选择教师">
          <el-select v-model="shareTargets" multiple filterable style="width:100%">
            <el-option v-for="t in teachers" :key="t.id" :label="`${t.real_name}（${t.username}）`" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="shareRemark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="shareDlg = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doShare">确认共享</el-button>
      </template>
    </el-dialog>

    <!-- 试卷预览 -->
    <el-dialog v-model="viewDlg" title="试卷详情" width="720px" top="5vh">
      <div v-loading="detailLoading">
        <h3 class="paper-title">{{ detail?.name }}</h3>
        <p class="paper-meta">
          {{ detail?.subject_name }} · {{ detail?.grade_name }} ·
          总分 {{ detail?.total_score }} · 时长 {{ detail?.duration }} 分钟 · 共 {{ detailItems.length }} 题
        </p>
        <div v-for="(it, idx) in detailItems" :key="idx" class="q-item">
          <p><b>{{ idx + 1 }}. [{{ it.type_label }}] {{ it.score }} 分</b></p>
          <p class="stem" v-html="it.stem"></p>
          <p v-if="it.options?.length" class="opts">
            <span v-for="o in it.options" :key="o.key" class="opt">{{ o.key }}. {{ o.text }}</span>
          </p>
          <p class="answer">答案：{{ it.answer }}</p>
          <p v-if="it.analysis" class="analysis">解析：{{ it.analysis }}</p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, DocumentCopy, MagicStick } from '@element-plus/icons-vue'
import { questionApi, eduApi, agentApi, systemApi } from '@/api'

const TYPE_LABEL = {
  single: '单选题', multiple: '多选题', judge: '判断题', fill: '填空题',
  short: '简答题', calculate: '计算题', proof: '证明题', essay: '论述题'
}
const DIFF = { easy: '简单', medium: '中等', hard: '困难' }

const list = ref([])
const subjects = ref([])
const grades = ref([])
const questions = ref([])
const teachers = ref([])
const detailItems = ref([])
const total = ref(0)
const loading = ref(false)
const detailLoading = ref(false)
const qLoading = ref(false)
const saving = ref(false)
const dlg = ref(false)
const aiDlg = ref(false)
const shareDlg = ref(false)
const viewDlg = ref(false)
const aiLoading = ref(false)
const aiResult = ref(null)
const aiReq = ref('')
const shareTargets = ref([])
const shareRemark = ref('')
const selected = ref([])

const query = reactive({ page: 1, page_size: 20, keyword: '', subject_id: null, source: '' })
const form = reactive({ id: null, name: '', grade_id: null, subject_id: null,
  total_score: 100, duration: 60, description: '' })

const templates = [
  '生成七年级数学一元一次方程专项练习卷，10 题，难度中等',
  '生成八年级物理期中试卷，包含选择填空，20 题，60 分钟',
  '生成九年级英语完形填空专项卷，15 题，难度偏难',
  '生成七年级生物细胞单元测试卷，20 题，基础难度'
]

const totalSelectedScore = computed(() => {
  const map = {}
  questions.value.forEach(q => { map[q.id] = q })
  return selected.value.reduce((s, id) => s + (map[id]?.score || 0), 0).toFixed(1)
})

function diffTag(d) { return { easy: 'success', medium: 'warning', hard: 'danger' }[d] || '' }
function stripHtml(s) { return String(s || '').replace(/<[^>]+>/g, '') }

async function load() {
  loading.value = true
  try {
    const res = await questionApi.papers(query)
    const d = res.data.data || {}
    list.value = d.items || []
    total.value = d.total || 0
  } finally {
    loading.value = false
  }
}

function reset() {
  Object.assign(query, { page: 1, keyword: '', subject_id: null, source: '' })
  load()
}

async function loadQuestions() {
  if (!form.subject_id) return
  qLoading.value = true
  try {
    const res = await questionApi.list({
      subject_id: form.subject_id, grade_id: form.grade_id,
      status: 'published', page_size: 200
    })
    questions.value = res.data.data?.items || []
  } finally {
    qLoading.value = false
  }
}

function openDialog() {
  Object.assign(form, { id: null, name: '', grade_id: null, subject_id: null,
    total_score: 100, duration: 60, description: '' })
  selected.value = []
  dlg.value = true
}

async function save() {
  if (!form.name) return ElMessage.warning('请输入试卷名称')
  if (!form.subject_id) return ElMessage.warning('请选择学科')
  if (!selected.value.length) return ElMessage.warning('请至少选择一道题目')
  saving.value = true
  try {
    await questionApi.createPaper({
      ...form, question_ids: selected.value, item_scores: selected.value.map(() => null)
    })
    ElMessage.success('试卷创建成功')
    dlg.value = false
    load()
  } finally {
    saving.value = false
  }
}

function openAI() {
  aiResult.value = null
  aiReq.value = templates[0]
  aiDlg.value = true
}

async function runAI() {
  if (!aiReq.value) return ElMessage.warning('请输入组卷需求')
  aiLoading.value = true
  try {
    const res = await agentApi.paperComposer({ requirement: aiReq.value })
    aiResult.value = res.data.data || {}
    ElMessage.success(res.data.message || '组卷完成')
    load()
  } finally {
    aiLoading.value = false
  }
}

function useResult() {
  aiDlg.value = false
  ElMessage.success(`已创建试卷「${aiResult.value.paper.name}」`)
}

async function viewDetail(row) {
  viewDlg.value = true
  detailLoading.value = true
  try {
    const res = await questionApi.paperDetail(row.id)
    detailItems.value = res.data.data?.items || []
  } finally {
    detailLoading.value = false
  }
}

async function onExpand(row) { await viewDetail(row) }

function openShare(row) {
  selectedPaper.value = row
  shareTargets.value = []
  shareRemark.value = ''
  shareDlg.value = true
}

const selectedPaper = ref(null)

async function doShare() {
  if (!shareTargets.value.length) return ElMessage.warning('请选择共享对象')
  saving.value = true
  try {
    await questionApi.sharePaper(selectedPaper.value.id,
      { user_ids: shareTargets.value, remark: shareRemark.value })
    ElMessage.success('共享成功')
    shareDlg.value = false
  } finally {
    saving.value = false
  }
}

async function copyPaper(row) {
  const { value } = await ElMessageBox.prompt('请输入新试卷名称', '复制试卷',
    { inputValue: `${row.name} - 副本` })
  await questionApi.copyPaper(row.id, { name: value })
  ElMessage.success('复制成功')
  load()
}

function exportPaper(row) { window.open(questionApi.exportPaperUrl(row.id), '_blank') }

async function remove(row) {
  await ElMessageBox.confirm(`确认删除试卷「${row.name}」？`, '提示', { type: 'warning' })
  await questionApi.removePaper(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(async () => {
  await load()
  const [s, g] = await Promise.all([eduApi.subjects(), eduApi.grades()])
  subjects.value = s.data.data || []
  grades.value = g.data.data || []
  const t = await systemApi.users({ identity: 'teacher', page_size: 200 })
  teachers.value = t.data.data?.items || []
})
</script>

<style scoped>
.mt16 { margin-top: 16px; justify-content: flex-end; }
.mb12 { margin-bottom: 12px; }
.mt8 { margin-top: 8px; }
.ml4 { margin-left: 4px; }
.ml8 { margin-left: 8px; }
.mr4 { margin-right: 4px; }
.tip { font-size: 12px; color: #909399; }
.q-select { margin-top: 6px; }
.filter-card :deep(.el-form-item) { margin-bottom: 12px; }
.expand-box { padding: 8px 16px; }
.q-item { padding: 10px 0; border-bottom: 1px dashed #ebeef5; }
.q-item:last-child { border-bottom: none; }
.stem { margin: 6px 0; line-height: 1.7; }
.opts { margin: 4px 0; }
.opt { display: inline-block; margin-right: 18px; }
.answer { margin: 4px 0; color: #67c23a; }
.analysis { margin: 4px 0; color: #909399; font-size: 13px; }
.paper-title { text-align: center; margin: 0 0 6px; }
.paper-meta { text-align: center; color: #909399; margin: 0 0 16px; font-size: 13px; }
.ai-result { background: #f7f9fc; padding: 12px; border-radius: 8px; }
.ai-result p { margin: 6px 0; }
</style>
