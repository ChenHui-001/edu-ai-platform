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
                <p class="stem" v-html="safeStem(it.stem)"></p>
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
              <el-select v-model="form.grade_id" clearable style="width:100%"
                         @change="onFormGradeChange">
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

        <el-form-item label="筛选题目">
          <el-row :gutter="8" style="width:100%">
            <el-col :span="7">
              <el-select v-model="qFilter.qtype" clearable placeholder="题型" style="width:100%" @change="loadQuestions">
                <el-option v-for="(label, key) in TYPE_LABEL" :key="key" :label="label" :value="key" />
              </el-select>
            </el-col>
            <el-col :span="6">
              <el-select v-model="qFilter.difficulty" clearable placeholder="难度" style="width:100%" @change="loadQuestions">
                <el-option label="简单" value="easy" />
                <el-option label="中等" value="medium" />
                <el-option label="较难" value="hard" />
              </el-select>
            </el-col>
            <el-col :span="11">
              <el-input v-model="qFilter.keyword" placeholder="题干关键字，回车搜索" clearable @keyup.enter="loadQuestions" @clear="loadQuestions" />
            </el-col>
          </el-row>
        </el-form-item>
        <el-form-item label="题库勾选">
          <div style="width:100%">
            <el-table ref="qTableRef" :data="questions" size="small" max-height="260"
                      v-loading="qLoading" border @selection-change="onPickChange">
              <el-table-column type="selection" width="40" />
              <el-table-column label="题型" width="76">
                <template #default="{ row }">{{ TYPE_LABEL[row.type] || row.type }}</template>
              </el-table-column>
              <el-table-column label="难度" width="58">
                <template #default="{ row }">
                  <el-tag :type="diffTag(row.difficulty)" size="small">{{ row.difficulty }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="score" label="分值" width="52" />
              <el-table-column label="题干" min-width="260">
                <template #default="{ row }">{{ stripHtml(row.stem).slice(0, 60) }}</template>
              </el-table-column>
            </el-table>
            <div class="mt8">
              <el-button size="small" type="primary" :disabled="!picked.length" @click="addPicked">
                加入所选（{{ picked.length }}）
              </el-button>
              <el-button size="small" :icon="Refresh" @click="loadQuestions">刷新题库</el-button>
              <span class="tip ml8">已选 {{ selected.length }} 题，总分 {{ totalSelectedScore }} 分</span>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="已选题目" v-if="selected.length">
          <div style="width:100%">
            <el-tag v-for="id in selected" :key="id" closable size="small"
                    class="mr4" style="margin-bottom:4px" @close="removePicked(id)">
              {{ qLabel(id) }}
            </el-tag>
          </div>
        </el-form-item>
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
      <el-form :model="aiForm" label-width="90px">
        <el-row :gutter="10">
          <el-col :span="12">
            <el-form-item label="学科" required>
              <el-select v-model="aiForm.subject_id" style="width:100%"
                         @change="onAiSubjectChange">
                <el-option v-for="s in subjects" :key="s.id"
                           :label="s.name" :value="s.id">
                  <span>{{ s.name }}</span>
                  <span v-if="s.grade_count > 1"
                        style="float:right;color:var(--el-text-color-secondary);font-size:12px">
                    {{ s.grade_count }} 个年级
                  </span>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="年级">
              <el-select v-model="aiForm.grade_id" clearable style="width:100%"
                         @change="onAiGradeChange">
                <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
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
          <el-tag size="small" class="ml4" :type="aiResult.paper?.id ? 'success' : 'warning'">
            {{ aiResult.paper?.id ? '已入库' : '仅预览（未入库）' }}
          </el-tag>
        </el-divider>
        <p><b>试卷名称：</b>{{ aiResult.paper?.name }}</p>
        <p><b>题目数量：</b>{{ aiResult.paper?.item_count ?? '-' }}</p>
        <p><b>总分：</b>{{ aiResult.paper?.total_score ?? '-' }}</p>
        <p v-if="aiResult.difficulty_report || aiResult.analysis"><b>难度分析：</b>{{ aiResult.analysis || aiResult.difficulty_report }}</p>
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
          <p class="stem" v-html="safeStem(it.stem)"></p>
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
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, DocumentCopy, MagicStick } from '@element-plus/icons-vue'
import { questionApi, eduApi, agentApi } from '@/api'
import TYPE_LABEL from '@/constants/question'
import { sanitizeHtml } from '@/utils/sanitize'

// 题干由教师/AI 录入，后端不做净化就落库，直接 v-html 会执行其中的脚本。
// 统一走白名单净化后再渲染（同 MyNotes 的正文处理）。
function safeStem(s) { return sanitizeHtml(s) }


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
// AI 组卷必须显式带学科+年级：subjects 来自 /edu/subjects?distinct=true（同名前缀去重），
// 实际入库的 subject_id 是某具体年级的；selected_subject_id 记下选中的精确 id。
const aiForm = reactive({ subject_id: null, grade_id: null })
const shareTargets = ref([])
const shareRemark = ref('')
const selected = ref([])
const picked = ref([])
const qTableRef = ref(null)
const qFilter = reactive({ qtype: '', difficulty: '', keyword: '' })

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
    const d = res.data || {}
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
      qtype: qFilter.qtype || undefined,
      difficulty: qFilter.difficulty || undefined,
      keyword: qFilter.keyword || undefined,
      status: 'published', page_size: 200
    })
    questions.value = res.data?.items || []
    // 筛选/刷新后恢复已选题目的勾选状态
    await nextTick()
    questions.value.forEach(q => {
      if (selected.value.includes(q.id)) qTableRef.value?.toggleRowSelection(q, true)
    })
  } finally {
    qLoading.value = false
  }
}

function onPickChange(rows) { picked.value = rows }

function addPicked() {
  const fresh = picked.value.map(r => r.id).filter(id => !selected.value.includes(id))
  if (!fresh.length) return ElMessage.info('所选题目均已加入')
  selected.value = [...selected.value, ...fresh]
  ElMessage.success(`已加入 ${fresh.length} 题`)
}

function removePicked(id) {
  selected.value = selected.value.filter(x => x !== id)
}

function qLabel(id) {
  const q = questions.value.find(x => x.id === id)
  return q ? `[${TYPE_LABEL[q.type] || q.type}] ${stripHtml(q.stem).slice(0, 20)}` : `题目 #${id}`
}

function openDialog() {
  Object.assign(form, { id: null, name: '', grade_id: null, subject_id: null,
    total_score: 100, duration: 60, description: '' })
  selected.value = []
  Object.assign(qFilter, { qtype: '', difficulty: '', keyword: '' })
  dlg.value = true
}

async function save() {
  if (!form.name) return ElMessage.warning('请输入试卷名称')
  if (!form.subject_id) return ElMessage.warning('请选择学科')
  if (!selected.value.length) return ElMessage.warning('请至少选择一道题目')
  saving.value = true
  try {
    // 后端契约是 items:[{question_id, score}]（score 缺省用题目自身分值）。
    // 此前发 question_ids+item_scores，后端 items 为空 → 空卷 + 假总分。
    const qmap = Object.fromEntries(questions.value.map(q => [q.id, q]))
    await questionApi.createPaper({
      name: form.name, grade_id: form.grade_id, subject_id: form.subject_id,
      duration: form.duration, description: form.description,
      items: selected.value.map(id => ({
        question_id: id, score: qmap[id]?.score ?? null
      })),
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
  // 打开弹窗时把当前列表筛选的学科/年级带过来，subject_id 走 distinct
  // 模式代表记录 → 切换年级时再按 same_name_grade_ids 换成精确 id
  aiForm.subject_id = form.subject_id || query.subject_id || null
  aiForm.grade_id = form.grade_id || query.grade_id || null
  syncAiSubjectByGrade()
  aiDlg.value = true
}

// subjects 是 distinct 后的去重列表（同一条目带 same_name_grade_ids），
// 而后端入库要的是某具体年级的 subject_id。切换年级时必须同步换。
//
// 手动组卷与 AI 组卷共用同一套映射：此前手动组卷没做同步，
// 选「数学」拿到的是 sort 最小那条（一年级数学），题库按该 subject_id
// 过滤必为空 —— 表现为「题库勾选」区域永远「暂无数据」，且无任何提示。
function syncFormSubjectByGrade() {
  if (!form.subject_id) return
  const s = subjects.value.find((x) =>
    x.id === form.subject_id ||
    (x.same_name_ids || []).includes(form.subject_id))
  if (!s) return
  if (!form.grade_id) { form.subject_id = s.id; return }
  const idx = (s.same_name_grade_ids || []).indexOf(form.grade_id)
  if (idx >= 0) form.subject_id = s.same_name_ids[idx]
}

function onFormGradeChange() {
  syncFormSubjectByGrade()
  loadQuestions()
}

function syncAiSubjectByGrade() {
  if (!aiForm.subject_id) return
  const s = subjects.value.find((x) =>
    x.id === aiForm.subject_id ||
    (x.same_name_ids || []).includes(aiForm.subject_id))
  if (!s) return
  if (!aiForm.grade_id) { aiForm.subject_id = s.id; return }
  const idx = (s.same_name_grade_ids || []).indexOf(aiForm.grade_id)
  if (idx >= 0) aiForm.subject_id = s.same_name_ids[idx]
}

function onAiGradeChange() { syncAiSubjectByGrade() }
function onAiSubjectChange() { /* 学科变了不动年级 */ }

async function runAI() {
  if (!aiReq.value) return ElMessage.warning('请输入组卷需求')
  if (!aiForm.subject_id) return ElMessage.warning('请选择学科')
  // 提交前再对一次年级：subject_id 精确到年级
  syncAiSubjectByGrade()
  aiLoading.value = true
  try {
    // 后端 paper_composer 读 data["request"]、save 默认 False 不传则只预览
    const res = await agentApi.paperComposer({
      request: aiReq.value, save: true,
      subject_id: aiForm.subject_id, grade_id: aiForm.grade_id,
    })
    // res 是 axios 响应：{ data: {code, message, success, data? } }
    // envelope data 缺失（Agent 失败/降级）时不能裸取 res.data，会 NPE
    const envelope = res?.data || {}
    const payload = envelope.data || {}
    if (!envelope.success) {
      // 后端明确报失败：401/422/500 等
      ElMessage.error(envelope.message || '组卷请求失败')
    } else if (!payload.paper?.id) {
      // success=true 但无 paper —— 多半是题库空或 Agent 内部异常
      ElMessage.warning(payload.tip || envelope.message
                         || '未生成试卷：题库可用题目不足，请先补充题目')
    } else {
      ElMessage.success(payload.tip || envelope.message || '组卷完成')
    }
    aiResult.value = payload
    load()
  } catch (e) {
    // 兜底：网络/解析异常
    ElMessage.error('组卷请求异常：' + (e?.message || e))
  } finally {
    aiLoading.value = false
  }
}

function useResult() {
  aiDlg.value = false
  const p = aiResult.value?.paper || {}
  ElMessage.success(
    p.id
      ? `已创建试卷「${p.name}」（${p.item_count} 题 / ${p.total_score} 分），可在列表查看`
      : '本次仅生成预览，题库可用题目不足，未创建试卷'
  )
}

async function viewDetail(row) {
  viewDlg.value = true
  detailLoading.value = true
  try {
    const res = await questionApi.paperDetail(row.id)
    detailItems.value = res.data?.items || []
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

async function exportPaper(row) {
  // window.open 不带 Authorization（后端 get_current_teacher 必 401）
  const res = await questionApi.exportPaper(row.id)
  const url = URL.createObjectURL(res.data)
  const a = document.createElement('a')
  a.href = url; a.download = `试卷-${row.name}.xlsx`; a.click()
  URL.revokeObjectURL(url)
}

async function remove(row) {
  await ElMessageBox.confirm(`确认删除试卷「${row.name}」？`, '提示', { type: 'warning' })
  await questionApi.removePaper(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(async () => {
  await load()
  const [s, g] = await Promise.all([eduApi.subjects({ distinct: true }), eduApi.grades()])
  subjects.value = s.data || []
  grades.value = g.data || []
  // 出题人下拉：用人员简表（/system/users 为 admin 专属，教师必 403）
  const t = await eduApi.peopleBrief({ identity: 'teacher' })
  teachers.value = t.data?.items || []
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
