<template>
  <div class="page-container paper-edit" v-loading="loading">
    <div class="page-header">
      <div>
        <h2 class="page-title">{{ paper.name || '编辑试卷' }}</h2>
        <p class="page-sub">
          <span v-if="paper.grade_name">{{ paper.grade_name }}</span>
          <span v-if="paper.subject_name"> · {{ paper.subject_name }}</span>
          <span v-if="paper.exam_type"> · {{ examTypeLabel[paper.exam_type] || paper.exam_type }}</span>
          <span class="ver-tag">v{{ paper.current_version || 1 }}</span>
        </p>
      </div>
      <div class="head-actions">
        <el-dropdown trigger="click" @command="onExport">
          <el-button :icon="Download">导出<el-icon class="el-icon--right"><ArrowDown /></el-icon></el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="docx-teacher">Word 教师卷（含答案）</el-dropdown-item>
              <el-dropdown-item command="docx-student">Word 学生卷</el-dropdown-item>
              <el-dropdown-item command="pdf-teacher">PDF 教师卷</el-dropdown-item>
              <el-dropdown-item command="pdf-student">PDF 学生卷</el-dropdown-item>
              <el-dropdown-item command="answer-sheet" divided>答题卡</el-dropdown-item>
              <el-dropdown-item command="html">打印视图（A3 双栏）</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button :icon="Clock" @click="openVersions">版本记录</el-button>
        <el-button :icon="Star" @click="onFavorite">
          {{ paper.is_favorite ? '取消收藏' : '收藏' }}
        </el-button>
        <el-button :icon="Back" @click="goBack">返回列表</el-button>
      </div>
    </div>

    <!-- 试卷元信息 -->
    <el-card shadow="never" class="meta-card">
      <el-form :model="meta" label-width="96px" class="meta-form">
        <el-row :gutter="16">
          <el-col :span="10">
            <el-form-item label="试卷名称" required>
              <el-input v-model="meta.name" maxlength="128" show-word-limit />
            </el-form-item>
          </el-col>
          <el-col :span="7">
            <el-form-item label="考试时长">
              <el-input-number v-model="meta.duration" :min="10" :max="300" :step="10"
                               controls-position="right" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="7">
            <el-form-item label="卷面统计">
              <div class="stat-inline">
                <b>{{ items.length }}</b> 题 ·
                <b>{{ totalScore }}</b> 分 ·
                <b>{{ sections.length }}</b> 个大题
              </div>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="命题说明">
          <el-input v-model="meta.description" type="textarea" :rows="2" maxlength="2000"
                    placeholder="命题思路、考查范围等（选填）" />
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 缺口提示（来自生成时的报告） -->
    <el-alert v-if="gaps.length" type="warning" :closable="false" show-icon class="gap-alert">
      <template #title>该卷存在题目缺口（题库不足，已用现有题目凑齐）</template>
      <div v-for="g in gaps" :key="g.code">
        {{ g.name }}：需要 {{ g.need }} 题，实际 {{ g.got }} 题
      </div>
    </el-alert>

    <!-- 题项列表：按大题分组 -->
    <el-card shadow="never" class="items-card">
      <template #header>
        <div class="card-head">
          <span>题目编排（{{ items.length }} 题 / {{ totalScore }} 分）</span>
          <div>
            <el-button size="small" :icon="Sort" @click="doRestructure">重构大题</el-button>
            <el-button size="small" type="primary" :icon="Plus" @click="openAddDialog">
              从题库添加
            </el-button>
          </div>
        </div>
      </template>

      <div v-for="sec in sections" :key="sec.code" class="sec-block">
        <div class="sec-head">
          <div class="sec-title">
            <span class="sec-name">{{ sec.name }}</span>
            <el-button text size="small" :icon="Edit" @click="openRename(sec)">改大题名</el-button>
          </div>
          <span class="sec-meta">{{ sec.items.length }} 题 · {{ sec.total }} 分</span>
        </div>

        <div v-for="(it, idx) in sec.items" :key="it.item_id" class="item-row">
          <span class="item-no">{{ globalNo(sec.code, idx) }}.</span>
          <el-tag size="small" :type="diffTagType(it.difficulty)" class="item-tag">
            {{ diffLabel[it.difficulty] || it.difficulty }}
          </el-tag>
          <span class="item-stem" :title="it.stem">{{ truncate(it.stem, 90) }}</span>
          <span v-if="it.knowledge_point_name" class="item-kp">{{ it.knowledge_point_name }}</span>
          <div class="item-right">
            <el-input-number v-model="it.score" :min="0" :max="100" :step="0.5" size="small"
                             controls-position="right" class="score-input"
                             @change="onScoreChange(it)" />
            <el-button text size="small" :icon="View" @click="openItemDetail(it)">查看</el-button>
            <el-button text size="small" type="primary" :icon="RefreshRight"
                       :loading="regenerating === it.item_id"
                       @click="onRegenerate(it)">换一题</el-button>
            <el-button text size="small" type="danger" :icon="Delete"
                       @click="removeItem(it)">移除</el-button>
          </div>
        </div>
        <el-empty v-if="!sec.items.length" description="该大题暂无题目" :image-size="60" />
      </div>

      <el-empty v-if="!sections.length" description="该试卷暂无题目" />
    </el-card>

    <!-- 底部保存条 -->
    <div class="save-bar">
      <div class="save-hint">
        <span v-if="dirty" class="dirty-tag">有未保存的修改</span>
        <span v-else class="clean-tag">已同步</span>
        <span v-if="dropWarning" class="drop-warn">{{ dropWarning }}</span>
      </div>
      <div>
        <el-button @click="resetLocal">撤销本次修改</el-button>
        <el-button type="primary" size="large" :loading="saving" :disabled="!dirty"
                   @click="doSave">保存并重算成绩</el-button>
      </div>
    </div>

    <!-- 题目详情抽屉 -->
    <el-drawer v-model="detailDrawer" title="题目详情" size="640px" destroy-on-close>
      <template v-if="currentItem">
        <div class="detail-meta">
          <el-tag size="small">{{ typeLabel[currentItem.type] || currentItem.type }}</el-tag>
          <el-tag size="small" :type="diffTagType(currentItem.difficulty)">
            {{ diffLabel[currentItem.difficulty] || currentItem.difficulty }}
          </el-tag>
          <span class="detail-score">{{ currentItem.score }} 分</span>
          <span v-if="currentItem.knowledge_point_name" class="detail-kp">
            {{ currentItem.knowledge_point_name }}
          </span>
        </div>
        <div class="detail-stem">{{ currentItem.stem }}</div>
        <div v-if="currentItem.options" class="detail-options">
          <div v-for="o in normalizeOptions(currentItem.options)" :key="o.key" class="detail-opt">
            <b>{{ o.key }}.</b> {{ o.text }}
          </div>
        </div>
        <el-divider content-position="left">参考答案</el-divider>
        <div class="detail-answer">{{ answerText(currentItem.answer) || '（暂无）' }}</div>
        <template v-if="currentItem.analysis">
          <el-divider content-position="left">解析</el-divider>
          <div class="detail-analysis">{{ currentItem.analysis }}</div>
        </template>
      </template>
    </el-drawer>

    <!-- 改大题名 -->
    <el-dialog v-model="renameDialog" title="修改大题名称" width="420px">
      <el-input v-model="renameForm.name" maxlength="64" show-word-limit
                placeholder="例如：一、选择题（每题2分，共20分）" />
      <div class="rename-hint">
        仅改显示名称，题目分组与顺序不受影响（分组按题型 code 识别）。
      </div>
      <template #footer>
        <el-button @click="renameDialog = false">取消</el-button>
        <el-button type="primary" :loading="renaming" @click="doRename">确定</el-button>
      </template>
    </el-dialog>

    <!-- 从题库添加 -->
    <el-dialog v-model="addDialog" title="从题库添加题目" width="880px" top="6vh">
      <div class="add-filter">
        <el-select v-model="qFilter.qtype" placeholder="题型" clearable style="width:130px">
          <el-option v-for="(label, code) in typeLabel" :key="code" :label="label" :value="code" />
        </el-select>
        <el-select v-model="qFilter.difficulty" placeholder="难度" clearable style="width:110px">
          <el-option label="简单" value="easy" />
          <el-option label="中等" value="medium" />
          <el-option label="困难" value="hard" />
        </el-select>
        <el-input v-model="qFilter.keyword" placeholder="题干关键词" clearable style="width:220px"
                  @keyup.enter="loadCandidates" />
        <el-button type="primary" :icon="Search" @click="loadCandidates">搜索</el-button>
      </div>
      <el-table :data="candidates" height="420" size="small" @selection-change="onSelect">
        <el-table-column type="selection" width="44" />
        <el-table-column label="题干" min-width="360">
          <template #default="{ row }">
            <span class="cand-stem">{{ truncate(row.stem, 80) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="题型" width="90">
          <template #default="{ row }">{{ typeLabel[row.type] || row.type }}</template>
        </el-table-column>
        <el-table-column label="难度" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="diffTagType(row.difficulty)">
              {{ diffLabel[row.difficulty] || row.difficulty }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="score" label="分值" width="70" />
      </el-table>
      <template #footer>
        <span class="pick-hint">已选 {{ picked.length }} 题</span>
        <el-button @click="addDialog = false">取消</el-button>
        <el-button type="primary" :disabled="!picked.length" @click="doAddItems">添加</el-button>
      </template>
    </el-dialog>

    <!-- 版本记录 -->
    <el-drawer v-model="versionDrawer" title="版本记录" size="720px">
      <el-table :data="versions" size="small">
        <el-table-column prop="version" label="版本" width="70">
          <template #default="{ row }">v{{ row.version }}</template>
        </el-table-column>
        <el-table-column prop="change_note" label="变更说明" min-width="120" />
        <el-table-column prop="item_count" label="题量" width="70" />
        <el-table-column prop="total_score" label="总分" width="70" />
        <el-table-column prop="created_at" label="时间" width="150" />
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button text size="small" type="primary"
                       :disabled="row.version === paper.current_version"
                       @click="doRestore(row)">回溯</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!versions.length" description="暂无版本记录" />
      <div class="version-hint">
        回溯不会删除历史：每次改动都产生新版本，可随时再切回。
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowDown, Back, Clock, Delete, Download, Edit, Plus, Refresh, RefreshRight,
  Search, Sort, Star, View
} from '@element-plus/icons-vue'
import { knowledgeApi, questionApi } from '@/api'

const route = useRoute()
const router = useRouter()
const paperId = Number(route.params.id)

const typeLabel = {
  single: '单选题', multiple: '多选题', judge: '判断题', blank: '填空题',
  short: '简答题', calc: '计算题', material: '材料分析题', composition: '作文题'
}
const diffLabel = { easy: '简单', medium: '中等', hard: '困难' }
const examTypeLabel = {
  final: '期末', hsee: '中考模拟', unit: '单元测', monthly: '月考', custom: '自定义'
}

const loading = ref(false)
const saving = ref(false)
const renaming = ref(false)
const regenerating = ref(null)
const dirty = ref(false)
const dropWarning = ref('')

const paper = ref({})
const meta = reactive({ name: '', description: '', duration: 90 })
const sections = ref([])
const gaps = ref([])

const detailDrawer = ref(false)
const currentItem = ref(null)

const renameDialog = ref(false)
const renameForm = reactive({ code: '', name: '' })

const addDialog = ref(false)
const candidates = ref([])
const picked = ref([])
const qFilter = reactive({ qtype: '', difficulty: '', keyword: '' })

const versionDrawer = ref(false)
const versions = ref([])

// 扁平题项列表（保存时提交给后端）
const items = computed(() => sections.value.flatMap(s => s.items))
const totalScore = computed(() =>
  Math.round(items.value.reduce((a, b) => a + (Number(b.score) || 0), 0) * 100) / 100)

// ---------------- 工具 ----------------
function truncate(text, len) {
  const t = String(text || '').replace(/\s+/g, ' ').trim()
  return t.length > len ? t.slice(0, len) + '…' : t
}

function diffTagType(diff) {
  return { easy: 'success', medium: 'warning', hard: 'danger' }[diff] || 'info'
}

function normalizeOptions(options) {
  if (!options) return []
  if (Array.isArray(options)) {
    return options.map(o => typeof o === 'object'
      ? { key: o.key || '', text: o.text || o.content || '' }
      : { key: '', text: String(o) })
  }
  return []
}

function answerText(answer) {
  if (answer === null || answer === undefined) return ''
  if (Array.isArray(answer)) return answer.join('')
  if (typeof answer === 'object') return answer.value || answer.text || ''
  return String(answer).replace(/^"|"$/g, '')
}

function globalNo(secCode, idx) {
  const pos = sections.value.findIndex(s => s.code === secCode)
  if (pos < 0) return idx + 1
  let base = 0
  for (let i = 0; i < pos; i++) base += sections.value[i].items.length
  return base + idx + 1
}

/** 后端 preview 返回的大题分组 → 本地可编辑结构 */
function applyPreview(data) {
  const secs = (data.sections || []).map((s, si) => ({
    code: s.section_code,
    name: s.section_name,
    sort: s.section_sort || si + 1,
    items: (s.items || []).map(it => ({
      // 后端字段名是 paper_item_id，不是 item_id
      item_id: it.paper_item_id,
      question_id: it.question_id,
      type: it.type,
      difficulty: it.difficulty,
      stem: it.stem,
      options: it.options,
      answer: it.answer,
      analysis: it.analysis,
      knowledge_point_name: it.knowledge_point_name,
      section_code: s.section_code,
      section_name: s.section_name,
      section_sort: s.section_sort || si + 1,
      score: it.score
    }))
  }))
  secs.forEach(s => {
    s.total = Math.round(s.items.reduce((a, b) => a + (Number(b.score) || 0), 0) * 100) / 100
  })
  sections.value = secs
  // gap 报告存在 generation_params 里；后端 preview 顶层不直接给 gaps
  gaps.value = (data.generation_params && data.generation_params.gaps) || []
}

// ---------------- 加载 ----------------
async function loadPaper() {
  loading.value = true
  try {
    const res = await questionApi.paperPreview(paperId, { mode: 'teacher' })
    // 后端 _build_preview 把 paper 字段平铺在顶层（不是 { paper: {...} }）
    const data = res.data || {}
    paper.value = data
    meta.name = data.name || ''
    meta.description = data.description || ''
    meta.duration = data.duration || 90
    // 收藏态：preview 不返回，单独由试卷库接口补（失败不影响编辑）
    questionApi.paperLibrary({ scope: 'favorite', page: 1, size: 200 })
      .then(r => {
        const list = r.data?.items || r.data || []
        paper.value.is_favorite = list.some(x => Number(x.id) === paperId)
      })
      .catch(() => {})
    applyPreview(data)
    dirty.value = false
    dropWarning.value = ''
  } catch (e) {
    ElMessage.error('加载试卷失败：' + (e.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

onMounted(loadPaper)

// ---------------- 本地编辑 ----------------
function onScoreChange() {
  sections.value.forEach(s => {
    s.total = Math.round(s.items.reduce((a, b) => a + (Number(b.score) || 0), 0) * 100) / 100
  })
  dirty.value = true
}

function removeItem(it) {
  const sec = sections.value.find(s => s.code === it.section_code)
  if (!sec) return
  const pos = sec.items.findIndex(x => x.item_id === it.item_id)
  if (pos < 0) return
  sec.items.splice(pos, 1)
  onScoreChange()
  dropWarning.value = '移除题目后，该题的学生作答会随题项作废（保存时如实告知条数）'
}

function resetLocal() {
  ElMessageBox.confirm('撤销本次所有未保存的修改？', '提示', { type: 'warning' })
    .then(() => loadPaper())
    .catch(() => {})
}

async function doSave() {
  if (!meta.name.trim()) return ElMessage.warning('试卷名称不能为空')
  if (!items.value.length) return ElMessage.warning('请至少保留一道题目')

  saving.value = true
  try {
    const payload = {
      name: meta.name.trim(),
      description: meta.description || '',
      duration: meta.duration,
      items: items.value.map(it => ({
        question_id: it.question_id,
        score: Number(it.score) || 0,
        section_code: it.section_code,
        section_name: it.section_name,
        section_sort: it.section_sort,
        score_override: true
      }))
    }
    const res = await questionApi.updatePaperItems(paperId, payload)
    const d = res.data || {}
    dirty.value = false
    dropWarning.value = ''
    let msg = '已保存'
    if (d.affected_submissions) {
      msg += `，重算 ${d.affected_submissions} 份提交的成绩`
    }
    if (d.dropped_answers) {
      msg += `；${d.dropped_answers} 条作答因题目移除而作废`
    }
    ElMessage.success(msg)
    await loadPaper()
  } catch (e) {
    ElMessage.error('保存失败：' + (e.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

// ---------------- 换一题 ----------------
async function onRegenerate(it) {
  regenerating.value = it.item_id
  try {
    const res = await questionApi.regenerateItem(paperId, it.item_id, {
      section_code: it.section_code,
      difficulty: it.difficulty
    })
    const d = res.data || {}
    if (!d.question_id) {
      ElMessage.warning('未找到可替换的题目（同知识点同难度已用尽）')
      return
    }
    const sec = sections.value.find(s => s.code === it.section_code)
    const pos = sec ? sec.items.findIndex(x => x.item_id === it.item_id) : -1
    if (pos >= 0) {
      sec.items.splice(pos, 1, {
        ...it,
        // 新题尚未入卷：item_id 置空，保存时由后端重建题项
        item_id: null,
        question_id: d.question_id,
        type: d.type || it.type,
        difficulty: d.difficulty || it.difficulty,
        stem: d.stem || it.stem,
        options: d.options ?? it.options,
        answer: d.answer ?? it.answer,
        analysis: d.analysis ?? it.analysis,
        knowledge_point_name: d.knowledge_point_name || it.knowledge_point_name,
        score: d.score != null ? d.score : it.score
      })
    }
    dirty.value = true
    if (d.is_fallback) {
      ElMessage.warning('AI 不可用，已用题库同条件题目替换（记得保存生效）')
    } else {
      ElMessage.success('已换成 AI 新题（记得保存生效）')
    }
  } catch (e) {
    ElMessage.error('换题失败：' + (e.message || '未知错误'))
  } finally {
    regenerating.value = null
  }
}

// ---------------- 大题操作 ----------------
function openRename(sec) {
  renameForm.code = sec.code
  renameForm.name = sec.name
  renameDialog.value = true
}

async function doRename() {
  if (!renameForm.name.trim()) return ElMessage.warning('大题名称不能为空')
  renaming.value = true
  try {
    await questionApi.renameSection(paperId, {
      section_code: renameForm.code, section_name: renameForm.name.trim()
    })
    const sec = sections.value.find(s => s.code === renameForm.code)
    if (sec) {
      sec.name = renameForm.name.trim()
      sec.items.forEach(it => { it.section_name = sec.name })
    }
    renameDialog.value = false
    ElMessage.success('大题名称已更新')
  } catch (e) {
    ElMessage.error('改名失败：' + (e.message || '未知错误'))
  } finally {
    renaming.value = false
  }
}

async function doRestructure() {
  try {
    await ElMessageBox.confirm(
      '按题型重新归组并重排题号（题目本身不变）？', '重构大题', { type: 'info' })
  } catch { return }
  try {
    await questionApi.restructurePaper(paperId, {})
    ElMessage.success('已重构大题')
    await loadPaper()
  } catch (e) {
    ElMessage.error('重构失败：' + (e.message || '未知错误'))
  }
}

// ---------------- 详情抽屉 ----------------
function openItemDetail(it) {
  currentItem.value = it
  detailDrawer.value = true
}

// ---------------- 从题库添加 ----------------
function openAddDialog() {
  addDialog.value = true
  picked.value = []
  loadCandidates()
}

async function loadCandidates() {
  try {
    const res = await questionApi.list({
      grade_id: paper.value.grade_id,
      subject_id: paper.value.subject_id,
      // 题库筛选参数名是 qtype（不是 type），传错会被静默忽略
      qtype: qFilter.qtype || undefined,
      difficulty: qFilter.difficulty || undefined,
      keyword: qFilter.keyword || undefined,
      page: 1, size: 30
    })
    candidates.value = res.data?.items || []
  } catch (e) {
    candidates.value = []
    ElMessage.error('加载题库失败：' + (e.message || '未知错误'))
  }
}

function onSelect(rows) {
  picked.value = rows
}

function doAddItems() {
  if (!picked.value.length) return
  // 挂到与题型匹配的大题；没有则新建一个大题
  picked.value.forEach(q => {
    let sec = sections.value.find(s => s.code === q.type)
    if (!sec) {
      sec = {
        code: q.type, name: typeLabel[q.type] || '综合题',
        sort: sections.value.length + 1, items: [], total: 0
      }
      sections.value.push(sec)
    }
    sec.items.push({
      item_id: null,   // 新题尚无题项 id，保存时由后端创建
      question_id: q.id,
      type: q.type,
      difficulty: q.difficulty,
      stem: q.stem,
      options: q.options,
      answer: q.answer,
      analysis: q.analysis,
      knowledge_point_name: q.knowledge_point_name,
      section_code: sec.code,
      section_name: sec.name,
      section_sort: sec.sort,
      score: q.score || 5
    })
  })
  onScoreChange()
  addDialog.value = false
  ElMessage.success(`已添加 ${picked.value.length} 题（记得保存）`)
}

// ---------------- 导出 ----------------
async function onExport(cmd) {
  try {
    if (cmd === 'html') {
      // 走 axios 带 Token 取 HTML 文本，再写入新窗口；直接 window.open 会 401
      const res = await questionApi.exportPrintHtml(paperId, { mode: 'teacher' })
      const html = typeof res === 'string' ? res : (res.data ?? '')
      const w = window.open('', '_blank')
      if (!w) return ElMessage.warning('浏览器拦截了弹窗，请允许后重试')
      w.document.write(html)
      w.document.close()
      return
    }
    if (cmd === 'answer-sheet') {
      downloadBlob(await questionApi.exportAnswerSheet(paperId, {}),
        `${meta.name || '试卷'}_答题卡.pdf`, 'application/pdf')
      return
    }
    const [kind, mode] = cmd.split('-')
    const fn = kind === 'pdf' ? questionApi.exportPdf : questionApi.exportDocx
    const res = await fn(paperId, { mode })
    downloadBlob(res,
      `${meta.name || '试卷'}_${mode === 'teacher' ? '教师卷' : '学生卷'}.${kind}`,
      kind === 'pdf' ? 'application/pdf' : 'application/octet-stream')
  } catch (e) {
    ElMessage.error('导出失败：' + (e.message || '未知错误'))
  }
}

/** 拦截器对 blob 返回整个 response，这里统一兼容 response / Blob 两种形态 */
function downloadBlob(res, filename, mime) {
  const data = res?.data ?? res
  const blob = data instanceof Blob ? data : new Blob([data], { type: mime })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = filename
  a.click()
  URL.revokeObjectURL(a.href)
}

// ---------------- 收藏 / 版本 ----------------
async function onFavorite() {
  const next = !paper.value.is_favorite
  try {
    await questionApi.toggleFavorite(paperId, next)
    paper.value.is_favorite = next
    ElMessage.success(next ? '已收藏' : '已取消收藏')
  } catch (e) {
    ElMessage.error('操作失败：' + (e.message || '未知错误'))
  }
}

async function openVersions() {
  versionDrawer.value = true
  try {
    const res = await questionApi.paperVersions(paperId)
    versions.value = res.data?.items || res.data || []
  } catch (e) {
    versions.value = []
  }
}

async function doRestore(row) {
  try {
    await ElMessageBox.confirm(
      `回溯到 v${row.version}？当前内容会先存为一个新版本，不会丢失。`,
      '回溯版本', { type: 'warning' })
  } catch { return }
  try {
    await questionApi.restorePaperVersion(paperId, row.version)
    ElMessage.success(`已回溯到 v${row.version}`)
    versionDrawer.value = false
    await loadPaper()
  } catch (e) {
    ElMessage.error('回溯失败：' + (e.message || '未知错误'))
  }
}

function goBack() {
  router.push('/teacher/papers')
}
</script>

<style scoped>
.paper-edit { padding-bottom: 84px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }
.page-title { margin: 0 0 4px; font-size: 20px; }
.page-sub { margin: 0; color: var(--el-text-color-secondary); font-size: 13px; }
.ver-tag {
  margin-left: 8px; padding: 0 7px; border-radius: 8px;
  background: var(--el-color-primary-light-9); color: var(--el-color-primary);
  font-size: 12px;
}
.head-actions { display: flex; gap: 8px; }

.meta-card { margin-bottom: 14px; }
.meta-form :deep(.el-form-item) { margin-bottom: 12px; }
.stat-inline { color: var(--el-text-color-secondary); font-size: 13px; }
.stat-inline b { color: var(--el-color-primary); }

.gap-alert { margin-bottom: 14px; }
.items-card { margin-bottom: 16px; }
.card-head { display: flex; justify-content: space-between; align-items: center; }

.sec-block { margin-bottom: 22px; }
.sec-head {
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 12px; margin-bottom: 8px;
  background: var(--el-fill-color-light); border-left: 3px solid var(--el-color-primary);
  border-radius: 4px;
}
.sec-title { display: flex; align-items: center; gap: 6px; }
.sec-name { font-weight: 600; font-size: 14px; }
.sec-meta { font-size: 12px; color: var(--el-text-color-secondary); }

.item-row {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 10px; border-bottom: 1px dashed var(--el-border-color-lighter);
}
.item-row:hover { background: var(--el-fill-color-lighter); }
.item-no { width: 26px; text-align: right; color: var(--el-text-color-secondary); font-size: 13px; }
.item-tag { flex: 0 0 auto; }
.item-stem { flex: 1; font-size: 13px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.item-kp { font-size: 12px; color: var(--el-text-color-placeholder); flex: 0 0 auto; }
.item-right { display: flex; align-items: center; gap: 2px; flex: 0 0 auto; }
.score-input { width: 92px; }

.save-bar {
  position: fixed; left: 0; right: 0; bottom: 0; z-index: 10;
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 24px; background: var(--el-bg-color);
  border-top: 1px solid var(--el-border-color-light);
  box-shadow: 0 -2px 12px rgba(0, 0, 0, .06);
}
.save-hint { display: flex; align-items: center; gap: 12px; font-size: 13px; }
.dirty-tag { color: var(--el-color-warning); }
.clean-tag { color: var(--el-text-color-placeholder); }
.drop-warn { color: var(--el-color-danger); }

.detail-meta { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
.detail-score { color: var(--el-color-primary); font-weight: 600; }
.detail-kp { color: var(--el-text-color-secondary); font-size: 12px; }
.detail-stem { font-size: 14px; line-height: 1.9; white-space: pre-wrap; }
.detail-options { margin-top: 10px; }
.detail-opt { padding: 3px 0; font-size: 13px; }
.detail-answer { font-size: 13px; color: var(--el-color-success); white-space: pre-wrap; }
.detail-analysis { font-size: 13px; color: var(--el-text-color-regular); line-height: 1.8; }

.rename-hint { margin-top: 8px; font-size: 12px; color: var(--el-text-color-secondary); }
.add-filter { display: flex; gap: 8px; margin-bottom: 12px; }
.cand-stem { font-size: 12px; }
.pick-hint { float: left; line-height: 32px; color: var(--el-text-color-secondary); font-size: 13px; }
.version-hint { margin-top: 12px; font-size: 12px; color: var(--el-text-color-secondary); }
</style>
