<template>
  <div class="page-container paper-wizard">
    <div class="page-header">
      <div>
        <h2 class="page-title">新建试卷</h2>
        <p class="page-sub">按湖北省学业水平考试标准组卷 · 支持自定义参数与 AI 智能一键出卷</p>
      </div>
      <div>
        <el-button :icon="Back" @click="goBack">返回试卷管理</el-button>
      </div>
    </div>

    <!-- 步骤条 -->
    <el-card shadow="never" class="step-card">
      <el-steps :active="step" align-center finish-status="success">
        <el-step title="选择模式" description="自定义 / AI 一键" />
        <el-step title="设定参数" description="年级学科·题型分值·难度" />
        <el-step title="预览调整" description="题目确认与编辑" />
        <el-step title="保存试卷" description="命名并入库" />
      </el-steps>
    </el-card>

    <!-- ============ Step 1：选择模式 ============ -->
    <el-card v-if="step === 0" shadow="never">
      <div class="mode-grid">
        <div class="mode-card" :class="{ active: form.mode === 'custom' }"
             @click="form.mode = 'custom'">
          <div class="mode-icon"><el-icon :size="34"><Tickets /></el-icon></div>
          <h3>自定义参数组卷</h3>
          <p>精确控制年级、学科、知识点范围、题型题量、分值分布与难度比例。适合常规命题与教研场景。</p>
          <ul>
            <li>按命题标准自动带出题型结构</li>
            <li>可选知识点范围，精准覆盖</li>
            <li>难度比例 7:2:1 可调</li>
          </ul>
        </div>
        <div class="mode-card" :class="{ active: form.mode === 'ai' }"
             @click="form.mode = 'ai'">
          <div class="mode-icon"><el-icon :size="34"><MagicStick /></el-icon></div>
          <h3>AI 智能一键组卷</h3>
          <p>用一句话描述需求，AI 自动匹配湖北统考题型结构与分值占比，一键生成完整试卷。</p>
          <ul>
            <li>自然语言描述即可出卷</li>
            <li>自动套用命题标准结构</li>
            <li>生成覆盖率/难度/题型三份报告</li>
          </ul>
        </div>
      </div>
      <div class="step-actions">
        <el-button type="primary" size="large" @click="step = 1">下一步</el-button>
      </div>
    </el-card>

    <!-- ============ Step 2：设定参数 ============ -->
    <el-card v-if="step === 1" shadow="never" v-loading="metaLoading">
      <!-- AI 模式：自然语言 -->
      <div v-if="form.mode === 'ai'" class="ai-input-block">
        <el-form-item label="组卷需求描述">
          <el-input v-model="form.request" ref="requestRef" type="textarea" :rows="4"
                    placeholder="例如：出一份七年级数学期末试卷，重点考有理数和整式，难度中等偏易，100分，90分钟" />
        </el-form-item>
        <div class="ai-hint">
          不写描述也可以：选好下面的<b>年级与学科</b>，直接按该学科命题标准生成题型结构与分值。
        </div>
      </div>

      <el-form :model="form" label-width="110px" class="param-form">
        <el-row :gutter="20">
          <el-col :span="8">
            <!-- AI 模式：年级可由大模型从描述中识别，不必强制手选 -->
            <el-form-item label="年级" :required="requiresGradeSubject(form.mode)">
              <el-select v-model="form.grade_id"
                         :placeholder="form.mode === 'ai' ? '可留空，由 AI 识别' : '请选择年级'"
                         style="width:100%" @change="onGradeChange">
                <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="学科" :required="requiresGradeSubject(form.mode)">
              <el-select v-model="form.subject_id"
                         :placeholder="form.mode === 'ai' ? '可留空，由 AI 识别'
                           : (form.grade_id ? '请选择学科' : '先选年级')"
                         style="width:100%"
                         :disabled="!form.grade_id"
                         @change="onSubjectChange">
                <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="命题标准">
              <el-select v-model="form.standard_id" placeholder="自动匹配" clearable
                         style="width:100%" @change="onStandardChange">
                <el-option v-for="s in matchedStandards" :key="s.id"
                           :label="`${s.name}（${s.item_count}题）`" :value="s.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 标准信息提示 -->
        <el-alert v-if="currentStandard" type="info" :closable="false" show-icon
                  class="std-tip">
          <template #title>
            {{ currentStandard.name }}
            <el-tag size="small" type="success" style="margin-left:8px">
              总分 {{ currentStandard.total_score }} · {{ currentStandard.duration }} 分钟 ·
              {{ currentStandard.item_count }} 题
            </el-tag>
          </template>
          <div class="std-sections">
            题型结构：
            <el-tag v-for="s in currentStandard.sections" :key="s.code" size="small"
                    style="margin-right:6px">
              {{ typeLabel[s.code] || s.code }} {{ s.count }}题×{{ s.score_per }}分
            </el-tag>
          </div>
        </el-alert>

        <!-- 该学科没有命题标准：不阻断组卷（会用通用结构），但必须说清楚，
             并给管理员一个就地补草案的入口 -->
        <el-alert v-if="standardMissing" type="warning" :closable="false" show-icon
                  class="std-tip">
          <template #title>
            「{{ currentSubjectName }}」暂无命题标准
          </template>
          <div class="std-sections">
            组卷会用<b>通用结构</b>（单选 10 / 填空 6 / 解答 4，分值按总分均摊），
            结构与分值不是教研口径。
            <el-button v-if="isAdmin" text type="primary" size="small"
                       :loading="genStdLoading" @click="generateStandards">
              一键生成标准草案
            </el-button>
            <span v-else class="muted">请联系管理员配置命题标准。</span>
          </div>
        </el-alert>
        <!-- 自定义模式：题型结构可编辑 -->
        <div v-if="form.mode === 'custom'" class="sections-editor">
          <div class="block-title">
            题型与分值
            <span class="block-sub">依据所选标准，可按需调整题量与单题分值</span>
            <el-button text type="primary" size="small" @click="resetSectionsToStandard">
              恢复标准结构
            </el-button>
          </div>
          <el-table :data="form.sections" size="small" border>
            <el-table-column label="大题名称" min-width="200">
              <template #default="{ row }">
                <el-input v-model="row.name" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="题型" width="130">
              <template #default="{ row }">
                <el-select v-model="row.code" size="small" style="width:100%">
                  <el-option v-for="(label, code) in typeLabel" :key="code"
                             :label="label" :value="code" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="题量" width="100">
              <template #default="{ row }">
                <el-input-number v-model="row.count" :min="0" :max="100" size="small"
                                 controls-position="right" style="width:100%" />
              </template>
            </el-table-column>
            <el-table-column label="单题分值" width="110">
              <template #default="{ row }">
                <el-input-number v-model="row.score_per" :min="0.5" :max="100" :step="0.5"
                                 :precision="1" size="small" controls-position="right"
                                 style="width:100%" />
              </template>
            </el-table-column>
            <el-table-column label="小计" width="90" align="center">
              <template #default="{ row }">
                {{ round2((row.count || 0) * (row.score_per || 0)) }}
              </template>
            </el-table-column>
            <el-table-column width="70" align="center">
              <template #default="{ $index }">
                <el-button text type="danger" :icon="Delete" size="small"
                           @click="form.sections.splice($index, 1)" />
              </template>
            </el-table-column>
          </el-table>
          <div class="sections-foot">
            <el-button text type="primary" :icon="Plus" size="small" @click="addSection">
              添加大题
            </el-button>
            <span class="total-line">
              卷面合计：<b :class="{ mismatch: scoreMismatch }">{{ sectionsTotal }}</b> 分
              <el-tag v-if="scoreMismatch" type="warning" size="small" style="margin-left:8px">
                与总分 {{ form.total_score }} 不一致
              </el-tag>
            </span>
          </div>
        </div>

        <el-row :gutter="20" style="margin-top:18px">
          <el-col :span="8">
            <el-form-item label="试卷总分">
              <el-input-number v-model="form.total_score" :min="10" :max="300" :step="10"
                               style="width:100%" controls-position="right" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="考试时长">
              <el-input-number v-model="form.duration" :min="10" :max="300" :step="10"
                               style="width:100%" controls-position="right" />
              <span class="unit-hint">分钟</span>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="出题来源">
              <el-select v-model="form.source" style="width:100%"
                         :disabled="form.mode === 'ai'">
                <el-option label="题库优先 + AI 补充（推荐）" value="bank_first" />
                <el-option label="仅使用题库" value="bank_only" />
                <el-option label="仅使用 AI 生成" value="ai_only" />
              </el-select>
              <span v-if="form.mode === 'ai'" class="unit-hint">
                AI 组卷固定「题库优先 + AI 补充」：模型只解析参数，抽题走题库；
                需要纯 AI 造题请切到「自定义参数组卷」
              </span>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 难度分布 -->
        <div class="block-title">难度分布</div>
        <div class="difficulty-row">
          <div class="diff-item">
            <span class="diff-label easy">简单</span>
            <el-slider v-model="form.difficulty_ratio.easy" :max="100" :step="5"
                       :disabled="form.mode === 'ai'" show-input />
          </div>
          <div class="diff-item">
            <span class="diff-label medium">中等</span>
            <el-slider v-model="form.difficulty_ratio.medium" :max="100" :step="5"
                       :disabled="form.mode === 'ai'" show-input />
          </div>
          <div class="diff-item">
            <span class="diff-label hard">困难</span>
            <el-slider v-model="form.difficulty_ratio.hard" :max="100" :step="5"
                       :disabled="form.mode === 'ai'" show-input />
          </div>
          <el-tag :type="difficultySum === 100 ? 'success' : 'warning'" size="small">
            合计 {{ difficultySum }}%{{ difficultySum === 100 ? '' : '（需为100）' }}
          </el-tag>
        </div>

        <!-- 知识点范围 -->
        <div class="block-title">
          知识点范围
          <span class="block-sub">不选则全范围抽题</span>
        </div>
        <div class="kp-tree-wrap">
          <el-tree ref="kpTreeRef" :data="kpTree" show-checkbox node-key="id"
                   :props="{ label: 'name', children: 'children' }"
                   :default-expanded-keys="[]" empty-text="该学科暂无知识点"
                   @check="onKpCheck" />
        </div>

        <!-- 高级选项 -->
        <el-collapse class="adv-collapse">
          <el-collapse-item title="高级选项" name="adv">
            <el-checkbox v-model="form.avoid_recent">不与近 3 次考试重复出题</el-checkbox>
            <el-checkbox v-model="form.avoid_duplicate_kp">避免同一知识点重复出题</el-checkbox>
          </el-collapse-item>
        </el-collapse>
      </el-form>

      <div class="step-actions">
        <el-button @click="step = 0">上一步</el-button>
        <!-- 自定义模式缺项时置灰并写明缺什么；AI 模式始终可点（点击后给提示） -->
        <span v-if="composeBlockReason && composeDisabled" class="block-reason">
          {{ composeBlockReason }}
        </span>
        <el-button type="primary" size="large" :loading="composing"
                   :disabled="composeDisabled" @click="doCompose">
          {{ form.mode === 'ai' ? 'AI 一键组卷' : '生成试卷预览' }}
        </el-button>
      </div>
    </el-card>

    <!-- ============ Step 3：预览调整 ============ -->
    <div v-if="step === 2">
      <!-- 缺口提示 -->
      <el-alert v-if="gaps.length" type="warning" :closable="false" show-icon class="gap-alert">
        <template #title>题库题目不足，以下大题存在缺口</template>
        <div v-for="g in gaps" :key="g.code">
          {{ g.name }}：需要 {{ g.need }} 题，题库仅有 {{ g.got }} 题
        </div>
        <div class="gap-hint">
          可切换到「题库优先 + AI 补充」由 AI 补题，或补充题库后重新生成。
        </div>
      </el-alert>
      <el-alert v-if="aiMessage" type="info" :closable="false" show-icon
                :title="aiMessage" class="gap-alert" />

      <!-- 报告卡片 -->
      <el-row :gutter="16" class="report-row">
        <el-col :span="8">
          <el-card shadow="never" class="report-card">
            <template #header><span>难度分布</span></template>
            <div class="report-line" v-for="d in ['easy','medium','hard']" :key="d">
              <span class="rl-label">{{ diffLabel[d] }}</span>
              <el-progress :percentage="reportPct(d)" :stroke-width="10"
                           :color="diffColor(d)" />
              <span class="rl-val">{{ reportPct(d) }}%</span>
            </div>
            <div class="report-foot">共 {{ previewItems.length }} 题 · 平均 {{ avgScore }} 分/题</div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="never" class="report-card">
            <template #header><span>题型结构</span></template>
            <div class="report-line" v-for="(cnt, code) in typeDist" :key="code">
              <span class="rl-label">{{ typeLabel[code] || code }}</span>
              <el-progress :percentage="pctOf(cnt)" :stroke-width="10" />
              <span class="rl-val">{{ cnt }} 题</span>
            </div>
            <div class="report-foot">卷面总分 {{ previewTotal }} 分</div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="never" class="report-card">
            <template #header><span>知识点覆盖</span></template>
            <div class="kp-cov-list">
              <el-tag v-for="kp in kpCoverage" :key="kp.name" size="small" class="kp-cov-tag">
                {{ kp.name }} ×{{ kp.count }}
              </el-tag>
              <span v-if="!kpCoverage.length" class="empty-hint">暂无数据</span>
            </div>
            <div class="report-foot">覆盖 {{ kpCoverage.length }} 个知识点</div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 题目列表 -->
      <el-card shadow="never" class="preview-card">
        <template #header>
          <div class="preview-head">
            <span>试卷预览（{{ previewItems.length }} 题 / {{ previewTotal }} 分）</span>
            <div>
              <el-button size="small" :icon="Refresh" @click="doCompose">重新生成</el-button>
              <el-button size="small" :icon="Sort" @click="restructureLocal">
                重构大题
              </el-button>
            </div>
          </div>
        </template>

        <div v-for="sec in previewSections" :key="sec.code" class="pv-section">
          <div class="pv-sec-title">
            <span>{{ sec.name }}</span>
            <span class="pv-sec-meta">
              {{ sec.items.length }} 题 · {{ sec.total }} 分
            </span>
          </div>
          <div v-for="(it, idx) in sec.items" :key="it.question_id" class="pv-item">
            <div class="pv-item-head">
              <span class="pv-no">{{ itemNo(sec.code, idx) }}.</span>
              <el-tag size="small" :type="diffTagType(it.difficulty)">
                {{ diffLabel[it.difficulty] || it.difficulty }}
              </el-tag>
              <span class="pv-score">{{ it.score }} 分</span>
              <span v-if="it.knowledge_point_name" class="pv-kp">
                {{ it.knowledge_point_name }}
              </span>
              <div class="pv-item-actions">
                <el-button text size="small" :icon="Edit" @click="editItem(sec.code, idx)">
                  编辑
                </el-button>
                <el-button text size="small" type="danger" :icon="Delete"
                           @click="removeLocalItem(sec.code, idx)">移除</el-button>
              </div>
            </div>
            <div class="pv-stem">{{ it.stem }}</div>
            <div v-if="it.options" class="pv-options">
              <span v-for="o in normalizeOptions(it.options)" :key="o.key" class="pv-opt">
                {{ o.key }}. {{ o.text }}
              </span>
            </div>
            <div v-if="it.answer" class="pv-answer">
              <b>答案：</b>{{ answerText(it.answer) }}
              <span v-if="it.analysis"> <b>解析：</b>{{ it.analysis }}</span>
            </div>
          </div>
        </div>
        <el-empty v-if="!previewItems.length" description="暂无题目" />
      </el-card>

      <div class="step-actions">
        <el-button @click="step = 1">上一步</el-button>
        <el-button type="primary" size="large" :disabled="!previewItems.length"
                   @click="step = 3">下一步：保存</el-button>
      </div>
    </div>

    <!-- ============ Step 4：保存 ============ -->
    <el-card v-if="step === 3" shadow="never">
      <el-form :model="saveForm" label-width="110px" style="max-width:620px">
        <el-form-item label="试卷名称" required>
          <el-input v-model="saveForm.name" maxlength="128" show-word-limit
                    placeholder="如：七年级数学期末学业水平考试" />
        </el-form-item>
        <el-form-item label="试卷说明">
          <el-input v-model="saveForm.description" type="textarea" :rows="3"
                    maxlength="2000" placeholder="命题思路、考查范围等（选填）" />
        </el-form-item>
        <el-form-item label="考试时长">
          <el-input-number v-model="saveForm.duration" :min="10" :max="300" :step="10"
                           controls-position="right" />
          <span class="unit-hint">分钟</span>
        </el-form-item>
        <el-form-item label="保存后">
          <el-radio-group v-model="saveForm.after">
            <el-radio value="edit">进入编辑（继续调整题目）</el-radio>
            <el-radio value="list">返回试卷列表</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <div class="save-summary">
        <div><span>题量</span><b>{{ previewItems.length }}</b></div>
        <div><span>总分</span><b>{{ previewTotal }}</b></div>
        <div><span>大题</span><b>{{ previewSections.length }}</b></div>
        <div><span>知识点</span><b>{{ kpCoverage.length }}</b></div>
      </div>
      <div class="step-actions">
        <el-button @click="step = 2">上一步</el-button>
        <el-button type="primary" size="large" :loading="saving" @click="doSave">
          保存试卷
        </el-button>
      </div>
    </el-card>

    <!-- 单题编辑抽屉 -->
    <el-drawer v-model="editDrawer" title="编辑题目" size="620px" destroy-on-close>
      <template v-if="editingItem">
        <el-form label-width="80px">
          <el-form-item label="题干">
            <el-input v-model="editingItem.stem" type="textarea" :rows="4" />
          </el-form-item>
          <el-form-item label="分值">
            <el-input-number v-model="editingItem.score" :min="0.5" :max="100" :step="0.5"
                             :precision="1" controls-position="right" />
          </el-form-item>
          <el-form-item label="难度">
            <el-select v-model="editingItem.difficulty">
              <el-option label="简单" value="easy" />
              <el-option label="中等" value="medium" />
              <el-option label="困难" value="hard" />
            </el-select>
          </el-form-item>
          <el-form-item label="答案">
            <el-input v-model="editingItem.answer" type="textarea" :rows="2" />
          </el-form-item>
          <el-form-item label="解析">
            <el-input v-model="editingItem.analysis" type="textarea" :rows="3" />
          </el-form-item>
        </el-form>
        <el-alert type="info" :closable="false" show-icon
                  title="此处修改仅作用于本次组卷预览，不修改题库原题。" />
      </template>
      <template #footer>
        <el-button @click="editDrawer = false">取消</el-button>
        <el-button type="primary" @click="editDrawer = false">确定</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Back, Delete, Edit, MagicStick, Plus, Refresh, Sort, Tickets
} from '@element-plus/icons-vue'
import { eduApi, knowledgeApi, questionApi } from '@/api'
import { useUserStore } from '@/store/user'
import {
  composeBlockReason as wizardComposeBlockReason,
  buildComposePayload as wizardBuildComposePayload,
  requiresGradeSubject,
  isComposeButtonDisabled,
  AI_MODE_SOURCE,
} from '@/utils/paperWizard'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const typeLabel = {
  single: '单选题', multiple: '多选题', judge: '判断题', blank: '填空题',
  short: '简答题', calc: '计算题', material: '材料分析题', composition: '作文题'
}
const diffLabel = { easy: '简单', medium: '中等', hard: '困难' }

const step = ref(0)
const metaLoading = ref(false)
const composing = ref(false)
const saving = ref(false)

const grades = ref([])
const allSubjects = ref([])
const standards = ref([])
const kpTree = ref([])
const kpTreeRef = ref(null)
const requestRef = ref(null)

const form = reactive({
  mode: 'custom',
  request: '',
  grade_id: null,
  subject_id: null,
  standard_id: null,
  sections: [],
  total_score: 100,
  duration: 90,
  source: 'bank_first',
  difficulty_ratio: { easy: 70, medium: 20, hard: 10 },
  avoid_recent: true,
  avoid_duplicate_kp: true
})

const saveForm = reactive({ name: '', description: '', duration: 90, after: 'edit' })

/**
 * 切到 AI 模式时把「出题来源」归位。
 *
 * 下拉在 AI 模式是禁用状态，但用户可能先在自定义模式选了 `ai_only` 再切过来：
 * 此时控件仍显示「仅使用 AI 生成」，而提交参数已被 `buildComposePayload`
 * 锁定为 `bank_first` —— 界面与实际行为不一致，用户会以为设置没生效。
 * 让值跟着模式走，UI 与 payload 始终一致。
 */
watch(() => form.mode, (mode) => {
  if (mode === 'ai') form.source = AI_MODE_SOURCE
})

const previewItems = ref([])
const gaps = ref([])
const aiMessage = ref('')
const reports = ref({})
const composedCtx = ref(null)

const editDrawer = ref(false)
const editingItem = ref(null)
let editTarget = null

// ---------------- 计算属性 ----------------
const subjects = computed(() =>
  allSubjects.value.filter(s => s.grade_id === form.grade_id))

const matchedStandards = computed(() =>
  standards.value.filter(s => {
    const sub = subjects.value.find(x => x.id === form.subject_id)
    return sub && s.subject_name === sub.name
  }))

const currentStandard = computed(() =>
  standards.value.find(s => s.id === form.standard_id) || null)

const difficultySum = computed(() =>
  (form.difficulty_ratio.easy || 0) + (form.difficulty_ratio.medium || 0) +
  (form.difficulty_ratio.hard || 0))

const sectionsTotal = computed(() =>
  round2(form.sections.reduce(
    (sum, s) => sum + (s.count || 0) * (s.score_per || 0), 0)))

const scoreMismatch = computed(() =>
  form.sections.length > 0 && Math.abs(sectionsTotal.value - form.total_score) > 0.01)

/**
 * 按钮禁用原因（空串 = 可提交）。判定实体在 `utils/paperWizard.js`，
 * 由 vitest 单测锁死 —— 这段逻辑一旦回归，表现就是「按钮恒灰」，
 * 只靠点页面很难在 CI 里发现。
 */
const composeBlockReason = computed(() => wizardComposeBlockReason({
  mode: form.mode,
  request: form.request,
  gradeId: form.grade_id,
  subjectId: form.subject_id,
  hasSections: form.sections.length > 0
}))

const isAdmin = computed(() => userStore.isAdmin)
const genStdLoading = ref(false)

/** 当前学科名（用于"暂无命题标准"提示） */
const currentSubjectName = computed(() =>
  (subjects.value.find(s => s.id === form.subject_id) || {}).name || '')

/**
 * 有学科但一条标准都没有 —— 组卷会落到通用结构兜底。
 * 让管理员能就地补草案，而不是让一线教师去别处找配置入口。
 */
const standardMissing = computed(() =>
  Boolean(form.grade_id && form.subject_id
    && !matchedStandards.value.length && !metaLoading.value))

async function generateStandards() {
  genStdLoading.value = true
  try {
    const res = await questionApi.generateMissingStandards()
    const n = res.data?.created_count ?? 0
    ElMessage.success(n ? `已生成 ${n} 条标准草案，可继续使用` : '已无缺失的标准')
    await loadStandards()
    // 生成后自动选中本学科的标准，省掉再点一次下拉
    if (matchedStandards.value.length === 1) {
      form.standard_id = matchedStandards.value[0].id
    }
  } catch (e) {
    ElMessage.error('生成标准草案失败：' + (e.message || '未知错误'))
  } finally {
    genStdLoading.value = false
  }
}

/** 是否置灰：AI 模式恒可点（缺描述时点击给提示），自定义模式才禁用 */
const composeDisabled = computed(() => isComposeButtonDisabled({
  mode: form.mode,
  reason: composeBlockReason.value
}))

const previewTotal = computed(() =>
  round2(previewItems.value.reduce((s, i) => s + (i.score || 0), 0)))

const avgScore = computed(() =>
  previewItems.value.length
    ? round2(previewTotal.value / previewItems.value.length) : 0)

const previewSections = computed(() => {
  const map = new Map()
  for (const it of previewItems.value) {
    const code = it.section_code || it.type
    if (!map.has(code)) {
      map.set(code, { code, name: it.section_name, items: [], total: 0 })
    }
    const sec = map.get(code)
    sec.items.push(it)
    sec.total = round2(sec.total + (it.score || 0))
  }
  return Array.from(map.values())
})

const typeDist = computed(() => {
  const m = {}
  for (const it of previewItems.value) {
    const k = it.type || 'single'
    m[k] = (m[k] || 0) + 1
  }
  return m
})

const kpCoverage = computed(() => {
  const m = {}
  for (const it of previewItems.value) {
    const k = it.knowledge_point_name || '综合'
    m[k] = (m[k] || 0) + 1
  }
  return Object.entries(m).map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
})

// ---------------- 工具函数 ----------------
function round2(n) { return Math.round((Number(n) || 0) * 100) / 100 }

function pctOf(cnt) {
  return previewItems.value.length
    ? Math.round((cnt / previewItems.value.length) * 100) : 0
}

function reportPct(diff) {
  const dist = reports.value?.difficulty_report?.distribution || {}
  const total = previewItems.value.length || 1
  return Math.round(((dist[diff] || 0) / total) * 100)
}

function diffColor(diff) {
  return { easy: '#67c23a', medium: '#e6a23c', hard: '#f56c6c' }[diff] || '#909399'
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

function itemNo(secCode, idx) {
  // 全局题号：累加前面大题的题量
  const secs = previewSections.value
  const pos = secs.findIndex(s => s.code === secCode)
  if (pos < 0) return idx + 1
  let base = 0
  for (let i = 0; i < pos; i++) base += secs[i].items.length
  return base + idx + 1
}

// ---------------- 数据加载 ----------------
/** 拉取命题标准选项（初始化与"一键生成草案"后都要用，抽出来避免两处口径漂移） */
async function loadStandards() {
  const std = await questionApi.standardOptions()
  const byStage = std.data?.by_stage || {}
  standards.value = Object.values(byStage).flat()
}

onMounted(async () => {
  // 从试卷管理点「AI 智能组卷」进来时直接预选 AI 模式并跳到参数步
  if (route.query.mode === 'ai') {
    form.mode = 'ai'
    step.value = 1
  }
  metaLoading.value = true
  try {
    const [g, s] = await Promise.all([
      eduApi.grades(), eduApi.subjects(), loadStandards()
    ])
    grades.value = g.data?.items || g.data || []
    allSubjects.value = s.data?.items || s.data || []
  } catch (e) {
    ElMessage.error('加载基础数据失败：' + (e.message || '未知错误'))
  } finally {
    metaLoading.value = false
  }
})

async function onGradeChange() {
  form.subject_id = null
  form.standard_id = null
  kpTree.value = []
  try {
    const res = await knowledgeApi.tree({ grade_id: form.grade_id })
    kpTree.value = res.data?.items || res.data || []
  } catch (e) {
    kpTree.value = []
  }
}

function onSubjectChange() {
  // 自动匹配默认标准
  const match = matchedStandards.value.find(s => s.is_default) || matchedStandards.value[0]
  form.standard_id = match?.id || null
  onStandardChange()
  loadKnowledgeTree()
}

async function loadKnowledgeTree() {
  if (!form.grade_id || !form.subject_id) return
  try {
    const res = await knowledgeApi.tree({
      grade_id: form.grade_id, subject_id: form.subject_id
    })
    kpTree.value = res.data?.items || res.data || []
  } catch (e) {
    kpTree.value = []
  }
}

function onStandardChange() {
  const std = currentStandard.value
  if (!std) return
  form.total_score = std.total_score
  form.duration = std.duration
  saveForm.duration = std.duration
  form.sections = std.sections.map(s => ({
    code: s.code, name: s.name, count: s.count, score_per: s.score_per
  }))
  if (std.difficulty_ratio) {
    form.difficulty_ratio = { ...std.difficulty_ratio }
  }
  if (!saveForm.name) {
    saveForm.name = buildDefaultName(std)
  }
}

function buildDefaultName(std) {
  const grade = grades.value.find(g => g.id === form.grade_id)
  const sub = subjects.value.find(s => s.id === form.subject_id)
  return `${grade?.name || ''}${sub?.name || ''}${std?.name?.includes('期末') ? '期末学业水平考试' : '学业水平考试'}`
}

function resetSectionsToStandard() {
  if (!currentStandard.value) return ElMessage.warning('请先选择命题标准')
  onStandardChange()
  ElMessage.success('已恢复为标准结构')
}

function addSection() {
  form.sections.push({
    code: 'single', name: '新增大题', count: 5, score_per: 2
  })
}

function onKpCheck() {
  // 占位：提交时通过 getCheckedKeys 读取
}

function checkedKpIds() {
  if (!kpTreeRef.value) return []
  return kpTreeRef.value.getCheckedKeys().filter(k => typeof k === 'number')
}

// ---------------- 组卷 ----------------
function buildPayload() {
  return wizardBuildComposePayload(form, {
    sections: form.sections,
    knowledgePointIds: checkedKpIds()
  })
}

async function doCompose() {
  // AI 模式按钮始终可点，缺描述时在这里给明确反馈（而不是让用户对着灰键猜）
  if (composeBlockReason.value) {
    ElMessage.warning(composeBlockReason.value)
    if (form.mode === 'ai') requestRef.value?.focus()
    return
  }
  if (form.mode === 'custom' && scoreMismatch.value) {
    return ElMessage.warning(
      `题型分值合计 ${sectionsTotal.value} 分，与总分 ${form.total_score} 不一致`)
  }
  if (difficultySum.value !== 100) {
    // AI 模式下难度滑块禁用且不参与提交，此时拦人只会让用户对着改不动的控件报错
    if (form.mode === 'custom') {
      return ElMessage.warning(`难度分布合计需为 100%，当前 ${difficultySum.value}%`)
    }
  }

  composing.value = true
  try {
    const payload = buildPayload()
    const res = form.mode === 'ai'
      ? await questionApi.composeAi({ ...payload, request: form.request })
      : await questionApi.composePreview(payload)

    const data = res.data || {}
    composedCtx.value = data
    previewItems.value = data.items || []
    gaps.value = data.gaps || []
    aiMessage.value = data.message || ''
    reports.value = {
      difficulty_report: data.difficulty_report,
      knowledge_report: data.knowledge_report,
      type_report: data.type_report
    }
    if (!saveForm.name && data.standard_name) {
      saveForm.name = `${data.grade_name}${data.subject_name}学业水平考试`
    }
    step.value = 2
    if (!previewItems.value.length) {
      ElMessage.warning('没有抽到题目，请检查题库或调整参数')
    }
  } catch (e) {
    ElMessage.error(e.message || '组卷失败')
  } finally {
    composing.value = false
  }
}

// ---------------- 预览编辑 ----------------
function editItem(secCode, idx) {
  const sec = previewSections.value.find(s => s.code === secCode)
  if (!sec) return
  editTarget = sec.items[idx]
  editingItem.value = { ...editTarget }
  editDrawer.value = true
}

function removeLocalItem(secCode, idx) {
  const sec = previewSections.value.find(s => s.code === secCode)
  if (!sec) return
  const target = sec.items[idx]
  previewItems.value = previewItems.value.filter(i => i !== target)
}

function restructureLocal() {
  // 本地按题型重排大题序号
  const cn = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
  const order = []
  const grouped = new Map()
  for (const it of previewItems.value) {
    const code = it.section_code || it.type
    if (!grouped.has(code)) {
      grouped.set(code, [])
      order.push(code)
    }
    grouped.get(code).push(it)
  }
  const reordered = []
  order.forEach((code, i) => {
    const items = grouped.get(code)
    const rawName = items[0].section_name || typeLabel[code] || code
    const bare = rawName.replace(/^[一二三四五六七八九十]+、/, '')
    const name = `${cn[i] || (i + 1)}、${bare}`
    for (const it of items) {
      it.section_name = name
      it.section_code = code
      it.section_sort = i + 1
      reordered.push(it)
    }
  })
  previewItems.value = reordered
  ElMessage.success('已重构大题结构')
}

// ---------------- 保存 ----------------
async function doSave() {
  if (!saveForm.name.trim()) return ElMessage.warning('请填写试卷名称')
  if (!previewItems.value.length) return ElMessage.warning('试卷没有题目')

  saving.value = true
  try {
    const payload = {
      ...buildPayload(),
      name: saveForm.name.trim(),
      description: saveForm.description,
      duration: saveForm.duration,
      mode: form.mode,
      items: previewItems.value.map(i => ({
        question_id: i.question_id,
        score: i.score,
        section_code: i.section_code || i.type,
        section_name: i.section_name,
        section_sort: i.section_sort || 0
      }))
    }
    const res = await questionApi.composeSave(payload)
    ElMessage.success('试卷已保存')
    const newId = res.data?.id
    if (saveForm.after === 'edit' && newId) {
      router.push(`/teacher/papers/${newId}/edit`)
    } else {
      router.push('/teacher/papers')
    }
  } catch (e) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

function goBack() { router.push('/teacher/papers') }
</script>

<style scoped>
.page-sub { margin: 4px 0 0; color: var(--el-text-color-secondary); font-size: 13px; }
.step-card { margin-bottom: 16px; }
.mode-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.mode-card {
  border: 2px solid var(--el-border-color); border-radius: 10px; padding: 22px;
  cursor: pointer; transition: all .2s;
}
.mode-card:hover { border-color: var(--el-color-primary-light-5); }
.mode-card.active {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}
.mode-icon { color: var(--el-color-primary); margin-bottom: 10px; }
.mode-card h3 { margin: 0 0 8px; font-size: 16px; }
.mode-card p { margin: 0 0 10px; color: var(--el-text-color-regular); font-size: 13px; line-height: 1.7; }
.mode-card ul { margin: 0; padding-left: 18px; color: var(--el-text-color-secondary); font-size: 12.5px; line-height: 1.9; }
.step-actions { margin-top: 22px; text-align: right; }
/* 灰键原因提示：贴在按钮左侧，弱化但可见，避免用户对着灰键猜 */
.block-reason {
  margin-right: 12px;
  font-size: 12.5px;
  color: var(--el-text-color-secondary);
}
.ai-input-block { margin-bottom: 8px; }
.ai-hint {
  margin: -4px 0 12px 110px;
  font-size: 12.5px;
  color: var(--el-text-color-secondary);
}
.std-tip { margin-bottom: 16px; }
.std-sections { margin-top: 8px; font-size: 12.5px; line-height: 2; }
.muted { color: var(--el-text-color-secondary); font-size: 12.5px; }
.block-title { font-size: 14px; font-weight: 600; margin: 20px 0 10px; }
.block-sub { font-weight: normal; font-size: 12px; color: var(--el-text-color-secondary); margin-left: 8px; }
.sections-foot { margin-top: 10px; display: flex; justify-content: space-between; align-items: center; }
.total-line { font-size: 13px; }
.total-line b { font-size: 15px; color: var(--el-color-primary); }
.total-line b.mismatch { color: var(--el-color-danger); }
.difficulty-row { display: flex; gap: 24px; align-items: center; flex-wrap: wrap; }
.diff-item { flex: 1; min-width: 220px; display: flex; align-items: center; gap: 10px; }
.diff-label { font-size: 13px; width: 36px; flex-shrink: 0; }
.diff-label.easy { color: #67c23a; }
.diff-label.medium { color: #e6a23c; }
.diff-label.hard { color: #f56c6c; }
.kp-tree-wrap { max-height: 240px; overflow: auto; border: 1px solid var(--el-border-color); border-radius: 6px; padding: 10px; }
.adv-collapse { margin-top: 16px; }
.unit-hint { margin-left: 8px; color: var(--el-text-color-secondary); font-size: 13px; }
.gap-alert { margin-bottom: 14px; }
.gap-hint { margin-top: 6px; font-size: 12.5px; color: var(--el-text-color-secondary); }
.report-row { margin-bottom: 14px; }
.report-card { height: 100%; }
.report-line { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.rl-label { width: 44px; font-size: 13px; flex-shrink: 0; }
.rl-val { width: 52px; text-align: right; font-size: 12.5px; color: var(--el-text-color-secondary); }
.report-foot { margin-top: 10px; font-size: 12.5px; color: var(--el-text-color-secondary); }
.kp-cov-list { max-height: 120px; overflow: auto; }
.kp-cov-tag { margin: 0 6px 6px 0; }
.empty-hint { color: var(--el-text-color-placeholder); font-size: 13px; }
.preview-head { display: flex; justify-content: space-between; align-items: center; }
.pv-section { margin-bottom: 20px; }
.pv-sec-title {
  font-size: 15px; font-weight: 600; padding-bottom: 6px; margin-bottom: 10px;
  border-bottom: 1px solid var(--el-border-color);
  display: flex; justify-content: space-between;
}
.pv-sec-meta { font-size: 12.5px; font-weight: normal; color: var(--el-text-color-secondary); }
.pv-item { padding: 12px 0; border-bottom: 1px dashed var(--el-border-color-lighter); }
.pv-item-head { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.pv-no { font-weight: 600; }
.pv-score { font-size: 12.5px; color: var(--el-text-color-secondary); }
.pv-kp { font-size: 12px; color: var(--el-color-primary); }
.pv-item-actions { margin-left: auto; }
.pv-stem { line-height: 1.8; font-size: 14px; }
.pv-options { margin-top: 8px; padding-left: 20px; display: flex; flex-wrap: wrap; gap: 8px 28px; }
.pv-opt { font-size: 13.5px; }
.pv-answer {
  margin-top: 8px; padding: 8px 12px; font-size: 12.5px; line-height: 1.7;
  background: var(--el-fill-color-light); border-left: 3px solid var(--el-color-primary);
  border-radius: 4px;
}
.save-summary {
  display: flex; gap: 40px; padding: 18px 20px; margin: 10px 0 0;
  background: var(--el-fill-color-light); border-radius: 8px;
}
.save-summary div { text-align: center; }
.save-summary span { display: block; font-size: 12.5px; color: var(--el-text-color-secondary); margin-bottom: 4px; }
.save-summary b { font-size: 20px; color: var(--el-color-primary); }
</style>
