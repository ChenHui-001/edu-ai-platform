<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">题库管理</h2>
      <div>
        <el-button :icon="Download" @click="downloadTemplate">下载模板</el-button>
        <el-button :icon="Upload" @click="importVisible = true">批量导入</el-button>
        <el-button v-if="can('question:bank:export')" :icon="Download"
                   @click="exportExcel">导出</el-button>
        <el-button v-if="can('question:bank:write')" :icon="MagicStick" type="warning"
                   @click="openAiDlg">AI 智能出题</el-button>
        <el-button v-if="can('question:bank:write')" :icon="MagicStick" type="warning"
                   @click="openAiDlg">AI 智能出题</el-button>
        <el-button v-if="can('question:bank:write')" type="primary" :icon="Plus"
                   @click="openDialog()">新增题目</el-button>
      </div>
    </div>

    <!-- 筛选 -->
    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="query">
        <el-form-item label="年级">
          <el-select v-model="query.grade_id" placeholder="全部" clearable style="width:130px">
            <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="学科">
          <el-select v-model="query.subject_id" placeholder="全部" clearable style="width:130px"
                     @change="onSubjectChange">
            <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="知识点">
          <el-select v-model="query.knowledge_point_id" placeholder="全部" clearable filterable
                     style="width:180px">
            <el-option v-for="k in knowledgePoints" :key="k.id" :label="k.name" :value="k.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="题型">
          <el-select v-model="query.qtype" placeholder="全部" clearable style="width:130px">
            <el-option v-for="(label, val) in TYPE_LABEL" :key="val" :label="label" :value="val" />
          </el-select>
        </el-form-item>
        <el-form-item label="难度">
          <el-select v-model="query.difficulty" placeholder="全部" clearable style="width:110px">
            <el-option label="简单" value="easy" />
            <el-option label="中等" value="medium" />
            <el-option label="困难" value="hard" />
          </el-select>
        </el-form-item>
        <el-form-item label="题库">
          <el-select v-model="query.bank_type" placeholder="全部" clearable style="width:120px">
            <el-option label="我的题库" value="private" />
            <el-option label="公共题库" value="public" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" placeholder="全部" clearable style="width:120px">
            <el-option label="已上架" value="published" />
            <el-option label="待审核" value="draft" />
            <el-option label="已下架" value="offline" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="query.keyword" placeholder="题干/解析" clearable style="width:180px"
                    @keyup.enter="search" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="search">查询</el-button>
          <el-button :icon="Refresh" @click="reset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 列表 -->
    <el-card shadow="never">
      <el-table v-loading="loading" :data="list" border stripe>
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="expand-box">
              <p><b>题干：</b><span v-html="row.stem"></span></p>
              <p v-if="parseJson(row.options)?.length"><b>选项：</b>
                <span v-for="o in parseJson(row.options)" :key="o.key">{{ o.key }}. {{ o.text }}　</span>
              </p>
              <p><b>标准答案：</b>{{ parseJson(row.answer) }}</p>
              <p><b>解析：</b>{{ row.analysis || '暂无' }}</p>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="stem" label="题干" min-width="280" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-html="stripHtml(row.stem).slice(0, 60)"></span>
          </template>
        </el-table-column>
        <el-table-column label="题型" width="110">
          <template #default="{ row }">{{ typeLabel(row.type) }}</template>
        </el-table-column>
        <el-table-column label="难度" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="diffType(row.difficulty)" size="small">{{ row.difficulty_label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="score" label="分值" width="70" align="center" />
        <el-table-column prop="knowledge_point_name" label="知识点" width="130" show-overflow-tooltip>
          <template #default="{ row }">{{ row.knowledge_point_name || '未关联' }}</template>
        </el-table-column>
        <el-table-column label="题库" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.bank_type === 'public' ? 'warning' : 'info'" size="small">
              {{ row.bank_type === 'public' ? '公共' : '私有' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-switch :model-value="row.status === 'published'"
                       :disabled="!can('question:bank:write')"
                       @change="toggleStatus(row)" />
          </template>
        </el-table-column>
        <el-table-column prop="usage_count" label="使用" width="65" align="center" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button v-if="can('question:bank:write')" link type="primary" size="small"
                       @click="openDialog(row)">编辑</el-button>
            <el-button link type="primary" size="small" @click="checkDupe(row)">查重</el-button>
            <el-button v-if="can('question:bank:write')" link type="danger" size="small"
                       @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="query.page" v-model:page-size="query.page_size"
        :total="total" :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        style="margin-top:16px;justify-content:flex-end"
        @current-change="load" @size-change="search"
      />
    </el-card>

    <!-- 新增/编辑 -->
    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑题目' : '新增题目'" width="820px" top="5vh">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="年级" prop="grade_id">
              <el-select v-model="form.grade_id" style="width:100%" @change="onFormGradeChange">
                <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="学科" prop="subject_id">
              <el-select v-model="form.subject_id" style="width:100%" @change="onFormSubjectChange">
                <el-option v-for="s in formSubjects" :key="s.id" :label="s.name" :value="s.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="题型" prop="type">
              <el-select v-model="form.type" style="width:100%">
                <el-option v-for="(label, val) in TYPE_LABEL" :key="val" :label="label" :value="val" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="题干" prop="stem">
          <el-input v-model="form.stem" type="textarea" :rows="3"
                    placeholder="支持 HTML 富文本、公式（LaTeX）、图片" />
        </el-form-item>

        <!-- 选择题/判断题选项 -->
        <el-form-item v-if="showOptions" label="选项">
          <div class="options-editor">
            <div v-for="(opt, i) in optionList" :key="i" class="option-row">
              <el-radio v-if="form.type === 'single'" v-model="form.answer" :value="opt.key">正确</el-radio>
              <el-checkbox v-else-if="form.type === 'multiple'" v-model="multiAnswer" :label="opt.key" />
              <span class="opt-key">{{ opt.key }}</span>
              <el-input v-model="opt.text" placeholder="选项内容" />
              <el-button v-if="form.type !== 'judge'" link type="danger" :icon="Delete"
                         @click="optionList.splice(i, 1)" />
            </div>
            <el-button v-if="form.type !== 'judge'" size="small" :icon="Plus" @click="addOption">
              添加选项
            </el-button>
          </div>
        </el-form-item>

        <el-form-item v-if="form.type === 'multiple'" label="多选答案">
          <el-tag v-for="a in multiAnswer" :key="a" closable @close="multiAnswer.splice(multiAnswer.indexOf(a),1)">
            {{ a }}
          </el-tag>
          <span v-if="multiAnswer.length === 0" style="color:#f56c6c;font-size:12px">请勾选正确选项</span>
        </el-form-item>

        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="难度">
              <el-select v-model="form.difficulty" style="width:100%">
                <el-option label="简单" value="easy" />
                <el-option label="中等" value="medium" />
                <el-option label="困难" value="hard" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="分值">
              <el-input-number v-model="form.score" :min="1" :max="100" :precision="1" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="知识点">
              <el-select v-model="form.knowledge_point_id" filterable clearable style="width:100%">
                <el-option v-for="k in formKnowledge" :key="k.id" :label="k.name" :value="k.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="题库类型">
          <el-radio-group v-model="form.bank_type">
            <el-radio-button value="private">我的题库</el-radio-button>
            <el-radio-button value="public">公共题库</el-radio-button>
          </el-radio-group>
          <span v-if="form.bank_type === 'public'" style="margin-left:12px;color:#909399;font-size:12px">
            公共题库上架需管理员审核
          </span>
        </el-form-item>

        <el-form-item label="解析">
          <el-input v-model="form.analysis" type="textarea" :rows="3" placeholder="解题思路与易错点" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <!-- 批量导入 -->
    <el-dialog v-model="importVisible" title="批量导入题目" width="560px">
      <el-alert type="info" :closable="false" show-icon style="margin-bottom:14px">
        <template #title>请先下载模板，按模板格式填写后上传</template>
        <el-link type="primary" :underline="false" @click="downloadTemplate">下载 Excel 模板</el-link>
      </el-alert>
      <el-form label-width="90px">
        <el-form-item label="年级">
          <el-select v-model="importForm.grade_id" style="width:100%">
            <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="学科">
          <el-select v-model="importForm.subject_id" style="width:100%">
            <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <el-upload drag :auto-upload="false" :limit="1" accept=".xlsx,.xls"
                 :on-change="onFileChange" :file-list="fileList">
        <el-icon size="40" color="#909399"><UploadFilled /></el-icon>
        <div>将 Excel 拖到此处，或<em>点击选择文件</em></div>
      </el-upload>
      <div v-if="importResult" class="import-result">
        <el-alert :type="importResult.created ? 'success' : 'warning'" :closable="false" show-icon
                  :title="`成功导入 ${importResult.created} 道题目`"
                  :description="importResult.skipped_count ? `跳过 ${importResult.skipped_count} 道（重复或格式错误）` : ''" />
        <el-table v-if="importResult.skipped?.length" :data="importResult.skipped"
                  size="small" max-height="180" style="margin-top:10px">
          <el-table-column prop="line" label="行号" width="70" />
          <el-table-column prop="stem" label="题干" show-overflow-tooltip />
          <el-table-column prop="reason" label="原因" width="120" />
        </el-table>
      </div>
      <template #footer>
        <el-button @click="importVisible = false">关闭</el-button>
        <el-button type="primary" :loading="importing" :disabled="!file" @click="doImport">开始导入</el-button>
      </template>
    </el-dialog>
  </div>
  <!-- AI 智能出题：条件生成 → 直接入库（草稿态，审核后可用于组卷） -->
  <el-dialog v-model="aiDlg" title="AI 智能出题" width="640px" destroy-on-close>
    <el-form :model="aiForm" label-width="90px">
      <el-row :gutter="10">
        <el-col :span="12">
          <el-form-item label="学科" required>
            <el-select v-model="aiForm.subject_id" style="width:100%" @change="loadAiKps">
              <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="年级">
            <el-select v-model="aiForm.grade_id" clearable style="width:100%">
              <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="10">
        <el-col :span="8">
          <el-form-item label="题型">
            <el-select v-model="aiForm.type" style="width:100%">
              <el-option v-for="(label, key) in TYPE_LABEL" :key="key" :label="label" :value="key" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="难度">
            <el-select v-model="aiForm.difficulty" style="width:100%">
              <el-option label="简单" value="easy" />
              <el-option label="中等" value="medium" />
              <el-option label="较难" value="hard" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="数量">
            <el-input-number v-model="aiForm.count" :min="1" :max="20" style="width:100%" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-form-item label="知识点">
        <el-select v-model="aiForm.knowledge_point_id" clearable filterable
                   style="width:100%" placeholder="可选，AI 将紧扣该知识点出题">
          <el-option v-for="k in aiKps" :key="k.id" :label="k.name" :value="k.id" />
        </el-select>
      </el-form-item>
    </el-form>

    <div v-if="aiResult?.length" class="mb12">
      <el-alert type="success" :closable="false" show-icon
                :title="`已生成 ${aiResult.length} 题并保存至题库（草稿状态）`"
                description="草稿题审核通过后即可用于组卷；可在列表用「来源=AI」筛选查看" />
      <el-table :data="aiResult" size="small" border max-height="240" class="mt8">
        <el-table-column label="题型" width="76">
          <template #default="{ row }">{{ TYPE_LABEL[row.type] || row.type }}</template>
        </el-table-column>
        <el-table-column label="难度" width="58">
          <template #default="{ row }">{{ row.difficulty }}</template>
        </el-table-column>
        <el-table-column prop="score" label="分值" width="52" />
        <el-table-column label="题干" min-width="300">
          <template #default="{ row }">{{ stripStem(row.stem).slice(0, 70) }}</template>
        </el-table-column>
      </el-table>
    </div>

    <template #footer>
      <el-button @click="aiDlg = false">关闭</el-button>
      <el-button type="primary" :loading="aiLoading" :disabled="!aiForm.subject_id"
                 @click="generateAi">生成并入库</el-button>
    </template>
  </el-dialog>
  <!-- AI 智能出题：条件生成 → 直接入库（草稿态，审核后可用于组卷） -->
  <el-dialog v-model="aiDlg" title="AI 智能出题" width="640px" destroy-on-close>
    <el-form :model="aiForm" label-width="90px">
      <el-row :gutter="10">
        <el-col :span="12">
          <el-form-item label="学科" required>
            <el-select v-model="aiForm.subject_id" style="width:100%" @change="loadAiKps">
              <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="年级">
            <el-select v-model="aiForm.grade_id" clearable style="width:100%">
              <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="10">
        <el-col :span="8">
          <el-form-item label="题型">
            <el-select v-model="aiForm.type" style="width:100%">
              <el-option v-for="(label, key) in TYPE_LABEL" :key="key" :label="label" :value="key" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="难度">
            <el-select v-model="aiForm.difficulty" style="width:100%">
              <el-option label="简单" value="easy" />
              <el-option label="中等" value="medium" />
              <el-option label="较难" value="hard" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="数量">
            <el-input-number v-model="aiForm.count" :min="1" :max="20" style="width:100%" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-form-item label="知识点">
        <el-select v-model="aiForm.knowledge_point_id" clearable filterable
                   style="width:100%" placeholder="可选，AI 将紧扣该知识点出题">
          <el-option v-for="k in aiKps" :key="k.id" :label="k.name" :value="k.id" />
        </el-select>
      </el-form-item>
    </el-form>

    <div v-if="aiResult && aiResult.length" class="mb12">
      <el-alert type="success" :closable="false" show-icon
                :title="'已生成 ' + aiResult.length + ' 题并保存至题库（草稿状态）'"
                description="草稿题审核通过后即可用于组卷；可在列表用「来源=AI」筛选查看" />
      <el-table :data="aiResult" size="small" border max-height="240" class="mt8">
        <el-table-column label="题型" width="76">
          <template #default="{ row }">{{ TYPE_LABEL[row.type] || row.type }}</template>
        </el-table-column>
        <el-table-column label="难度" width="58">
          <template #default="{ row }">{{ row.difficulty }}</template>
        </el-table-column>
        <el-table-column prop="score" label="分值" width="52" />
        <el-table-column label="题干" min-width="300">
          <template #default="{ row }">{{ stripStem(row.stem).slice(0, 70) }}</template>
        </el-table-column>
      </el-table>
    </div>

    <template #footer>
      <el-button @click="aiDlg = false">关闭</el-button>
      <el-button type="primary" :loading="aiLoading" :disabled="!aiForm.subject_id"
                 @click="generateAi">生成并入库</el-button>
    </template>
  </el-dialog>
</template>

<script setup>

// ---------- AI 智能出题（复用题库生成 Agent；LLM 未配置时自动降级） ----------
const aiDlg = ref(false)
const aiLoading = ref(false)
const aiResult = ref(null)
const aiForm = reactive({ subject_id: null, grade_id: null, type: 'single',
  difficulty: 'medium', count: 5, knowledge_point_id: null })
const aiKps = ref([])

function stripStem(s) { return String(s || '').replace(/<[^>]+>/g, '') }

function openAiDlg() {
  Object.assign(aiForm, { subject_id: query.subject_id, grade_id: query.grade_id,
    type: 'single', difficulty: 'medium', count: 5, knowledge_point_id: null })
  aiResult.value = null
  aiDlg.value = true
  if (aiForm.subject_id) loadAiKps()
}

async function loadAiKps() {
  if (!aiForm.subject_id) { aiKps.value = []; return }
  try {
    const res = await eduApi.knowledge({ subject_id: aiForm.subject_id, params_limit: 200 })
    aiKps.value = res.data?.items || res.data || []
  } catch { aiKps.value = [] }
}

async function generateAi() {
  aiLoading.value = true
  try {
    const res = await agentApi.questionGenerator({ ...aiForm, save: true })
    const d = res.data || {}
    aiResult.value = d.questions || []
    if (aiResult.value.length) {
      ElMessage.success(`已生成 ${aiResult.value.length} 题并保存至题库（草稿）`)
      load()
    } else {
      ElMessage.warning(d.tip || '未能生成题目，请调整条件后重试')
    }
  } finally { aiLoading.value = false }
}


import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Plus, Refresh, Search, Upload, UploadFilled, Delete, MagicStick } from '@element-plus/icons-vue'
import { questionApi, eduApi, agentApi } from '@/api'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()
const can = (p) => userStore.hasPerm(p)

// 须与后端 QUESTION_TYPE_LABEL 保持一致（backend/app/api/v1/question.py）
const TYPE_LABEL = {
  single: '单选题', multiple: '多选题', judge: '判断题', blank: '填空题',
  short: '简答题', calc: '计算题', material: '材料分析题', composition: '作文题'
}

// 历史别名：早期后端未校验题型，库中可能存在 subjective 等非法值。
// 这里做一次归一化，避免下拉框匹配不到当前值而显示空白/原始英文。
const TYPE_ALIAS = { subjective: 'short', essay: 'composition' }

function normalizeType(t) {
  const v = String(t || 'single').toLowerCase()
  const fixed = TYPE_ALIAS[v] || v
  return TYPE_LABEL[fixed] ? fixed : 'single'
}

// 列表列渲染：未知值兜底显示「其他题型(x)」而不是裸英文
function typeLabel(t) {
  const v = String(t || '')
  if (TYPE_LABEL[v]) return TYPE_LABEL[v]
  if (TYPE_ALIAS[v]) return TYPE_LABEL[TYPE_ALIAS[v]]
  return v ? `其他题型(${v})` : '-'
}

const list = ref([])
const total = ref(0)
const loading = ref(false)
const grades = ref([])
const subjects = ref([])
const knowledgePoints = ref([])
const formSubjects = ref([])
const formKnowledge = ref([])

const query = reactive({ page: 1, page_size: 20, grade_id: null, subject_id: null,
  knowledge_point_id: null, qtype: null, difficulty: null, bank_type: null, status: null, keyword: '' })

const dialogVisible = ref(false)
const saving = ref(false)
const formRef = ref()
const form = reactive({ id: null, type: 'single', stem: '', options: [], answer: '',
  analysis: '', score: 5, difficulty: 'medium', grade_id: null, subject_id: null,
  knowledge_point_id: null, bank_type: 'private' })
const optionList = ref([])
const multiAnswer = ref([])

const importVisible = ref(false)
const importing = ref(false)
const file = ref(null)
const fileList = ref([])
const importResult = ref(null)
const importForm = reactive({ grade_id: null, subject_id: null })

const rules = {
  stem: [{ required: true, message: '请输入题干', trigger: 'blur' }],
  type: [{ required: true, message: '请选择题型', trigger: 'change' }],
  subject_id: [{ required: true, message: '请选择学科', trigger: 'change' }],
  grade_id: [{ required: true, message: '请选择年级', trigger: 'change' }]
}

const showOptions = computed(() => ['single', 'multiple', 'judge'].includes(form.type))

function parseJson(v) {
  if (!v) return null
  if (Array.isArray(v)) return v
  try { return JSON.parse(v) } catch { return null }
}
function stripHtml(s) { return String(s || '').replace(/<[^>]*>/g, '') }
function diffType(d) {
  return { easy: 'success', medium: 'warning', hard: 'danger' }[d] || 'info'
}

async function load() {
  loading.value = true
  try {
    const params = Object.fromEntries(Object.entries(query).filter(([, v]) => v !== null && v !== ''))
    const res = await questionApi.list(params)
    list.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function search() { query.page = 1; load() }
function reset() {
  Object.assign(query, { page: 1, page_size: query.page_size, grade_id: null, subject_id: null,
    knowledge_point_id: null, qtype: null, difficulty: null, bank_type: null, status: null, keyword: '' })
  load()
}

async function onSubjectChange() {
  query.knowledge_point_id = null
  await loadKnowledge(query.grade_id, query.subject_id)
}

async function loadKnowledge(gid, sid) {
  if (!gid || !sid) { knowledgePoints.value = []; return }
  const res = await eduApi.knowledgeList({ grade_id: gid, subject_id: sid, params_limit: 300 })
  knowledgePoints.value = res.data
}

function addOption() {
  const next = String.fromCharCode(65 + optionList.value.length)
  optionList.value.push({ key: next, text: '' })
}

function openDialog(row) {
  Object.assign(form, {
    // 归一化题型：库里可能存在历史非法值（如 subjective），
    // 直接赋给 el-select 会匹配不到选项，导致「题型显示空白」
    id: row?.id ?? null, type: normalizeType(row?.type),
    stem: row?.stem ?? '',
    analysis: row?.analysis ?? '', score: row?.score ?? 5,
    difficulty: row?.difficulty ?? 'medium', grade_id: row?.grade_id ?? query.grade_id,
    subject_id: row?.subject_id ?? query.subject_id,
    knowledge_point_id: row?.knowledge_point_id ?? null,
    bank_type: row?.bank_type ?? 'private', options: [], answer: ''
  })

  const opts = parseJson(row?.options) || []
  if (form.type === 'judge') {
    optionList.value = [{ key: 'A', text: '正确' }, { key: 'B', text: '错误' }]
    form.answer = typeof row?.answer === 'string' && /正确|true/i.test(row.answer) ? 'A' : ''
  } else {
    optionList.value = opts.length ? opts.map(o => ({ key: o.key, text: o.text })) : [
      { key: 'A', text: '' }, { key: 'B', text: '' }, { key: 'C', text: '' }, { key: 'D', text: '' }
    ]
    const ans = parseJson(row?.answer) ?? row?.answer ?? ''
    form.answer = Array.isArray(ans) ? '' : String(ans)
    multiAnswer.value = Array.isArray(ans) ? ans : (form.type === 'multiple' && String(ans) ? [String(ans)] : [])
  }

  if (form.grade_id) loadFormSubjects(form.grade_id)
  if (form.grade_id && form.subject_id) loadFormKnowledge(form.grade_id, form.subject_id)
  dialogVisible.value = true
}

async function loadFormSubjects(gid) {
  const res = await eduApi.subjects({ grade_id: gid })
  formSubjects.value = res.data
}
async function loadFormKnowledge(gid, sid) {
  const res = await eduApi.knowledgeList({ grade_id: gid, subject_id: sid, params_limit: 300 })
  formKnowledge.value = res.data
}
async function onFormGradeChange() {
  form.subject_id = null
  form.knowledge_point_id = null
  await loadFormSubjects(form.grade_id)
}
async function onFormSubjectChange() {
  form.knowledge_point_id = null
  await loadFormKnowledge(form.grade_id, form.subject_id)
}

async function save() {
  await formRef.value.validate()
  saving.value = true
  try {
    const payload = { ...form }
    if (showOptions.value) {
      payload.options = optionList.value.filter(o => o.text)
      payload.answer = form.type === 'multiple'
        ? multiAnswer.value
        : (form.type === 'judge' ? (form.answer === 'A' ? '正确' : '错误') : form.answer)
    }
    if (form.id) await questionApi.update(form.id, payload)
    else await questionApi.create(payload)
    ElMessage.success('保存成功')
    dialogVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function remove(row) {
  await ElMessageBox.confirm(`确定删除题目「${stripHtml(row.stem).slice(0, 20)}...」吗？`, '提示', { type: 'warning' })
  await questionApi.remove(row.id)
  ElMessage.success('已删除')
  load()
}

async function toggleStatus(row) {
  const next = row.status === 'published' ? 'offline' : 'published'
  await questionApi.changeStatus(row.id, { status: next })
  ElMessage.success(next === 'published' ? '已上架' : '已下架')
  load()
}

async function checkDupe(row) {
  const res = await questionApi.duplicates(row.id)
  const list2 = res.data
  if (!list2.length) return ElMessage.success('未发现重复题目')
  ElMessageBox.alert(
    list2.map(d => `ID ${d.id}：${d.stem}`).join('<br/>'),
    `发现 ${list2.length} 道疑似重复题目`, { dangerouslyUseHTMLString: true }
  )
}

async function downloadTemplate() {
  // window.open 不携带 Authorization，模板端点要求教师身份
  const res = await questionApi.downloadTemplate()
  const url = URL.createObjectURL(res.data)
  const a = document.createElement('a')
  a.href = url; a.download = '题目导入模板.xlsx'; a.click()
  URL.revokeObjectURL(url)
}

async function exportExcel() {
  const res = await questionApi.exportExcel({
    subject_id: query.subject_id || '', grade_id: query.grade_id || ''
  })
  const url = URL.createObjectURL(res.data)
  const a = document.createElement('a')
  a.href = url; a.download = '题库导出.xlsx'; a.click()
  URL.revokeObjectURL(url)
}

function onFileChange(f) { file.value = f.raw; fileList.value = [f]; importResult.value = null }

async function doImport() {
  if (!file.value) return ElMessage.warning('请选择文件')
  importing.value = true
  try {
    const fd = new FormData()
    fd.append('file', file.value)
    if (importForm.grade_id) fd.append('grade_id', importForm.grade_id)
    if (importForm.subject_id) fd.append('subject_id', importForm.subject_id)
    const res = await questionApi.import(fd)
    importResult.value = res.data
    ElMessage.success(res.message)
    load()
  } finally {
    importing.value = false
  }
}

onMounted(async () => {
  const g = await eduApi.grades()
  grades.value = g.data
  const s = await eduApi.subjects({})
  subjects.value = s.data
  load()
})
</script>

<style scoped>
.expand-box {
  padding: 8px 16px;
  line-height: 1.9;
  background: #fafafa;
}
.options-editor { width: 100%; }
.option-row {
  display: flex; align-items: center; gap: 10px; margin-bottom: 8px;
}
.opt-key {
  width: 24px; height: 24px; line-height: 24px; text-align: center;
  background: #f0f2f5; border-radius: 4px; font-size: 12px; flex-shrink: 0;
}
.import-result { margin-top: 14px; }
</style>
