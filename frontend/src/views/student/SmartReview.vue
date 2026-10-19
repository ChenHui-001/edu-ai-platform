<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">智能复习</h2>
      <div>
        <el-button :icon="MagicStick" :loading="generating" @click="openGenDialog">AI 生成复习计划</el-button>
        <el-button :icon="Refresh" @click="loadAll">刷新</el-button>
      </div>
    </div>

    <el-row :gutter="16" class="mb16">
      <el-col :span="8">
        <div class="stat-card">
          <div class="stat-value" style="color:#f56c6c">{{ planData.today_count ?? 0 }}</div>
          <div class="stat-label">今日待复习</div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-card">
          <div class="stat-value">{{ planData.pending_count ?? 0 }}</div>
          <div class="stat-label">全部待完成</div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-card">
          <div class="stat-value" style="color:#67c23a">{{ mastery.avg_mastery ?? 0 }}%</div>
          <div class="stat-label">平均掌握度</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :span="14">
        <el-card shadow="never">
          <template #header>
            <div class="flex-between">
              <b>艾宾浩斯复习计划</b>
              <el-date-picker v-model="filterDate" type="date" value-format="YYYY-MM-DD"
                              placeholder="按日期筛选" clearable style="width:150px" @change="loadPlans" />
            </div>
          </template>
          <el-tabs v-model="tab" @tab-change="onTabChange">
            <el-tab-pane :label="`今日 (${planData.today_count || 0})`" name="today" />
            <el-tab-pane :label="`待完成 (${planData.pending_count || 0})`" name="pending" />
          </el-tabs>

          <el-list v-loading="loading" class="plan-list">
            <el-list-item v-for="p in plans" :key="p.id" class="plan-item"
                          :class="{ done: p.is_completed, today: p.scheduled_date === planData.today }">
              <div class="row-between">
                <div>
                  <b>{{ p.knowledge_point_name || '综合复习' }}</b>
                  <el-tag size="small" class="ml8" :type="stageTag(p.stage)">第 {{ p.stage }} 阶段</el-tag>
                  <span class="tip ml8">{{ p.scheduled_date }}</span>
                </div>
                <el-button v-if="!p.is_completed" size="small" type="primary"
                           @click="complete(p)">完成复习</el-button>
                <el-tag v-else type="success" size="small">已完成</el-tag>
              </div>
              <p v-if="p.stem" class="stem">{{ strip(p.stem) }}</p>
            </el-list-item>
            <el-empty v-if="!loading && !plans.length" description="暂无复习计划" :image-size="70" />
          </el-list>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card shadow="never">
          <template #header>
            <div class="flex-between">
              <b>知识点掌握地图</b>
              <el-select v-model="subjectId" placeholder="全部学科" clearable size="small"
                         style="width:130px" @change="loadMastery">
                <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
              </el-select>
            </div>
          </template>

          <template v-if="mastery.items?.length">
            <EChart v-if="mastery.items.length >= 3" :option="radarOption" style="height: 280px" />
            <el-divider content-position="left">
              薄弱知识点（{{ mastery.weak_points?.length || 0 }}）
            </el-divider>
            <div v-for="w in mastery.weak_points" :key="w.knowledge_point_id" class="weak-item">
              <div class="row-between">
                <span>{{ w.name }}</span>
                <span class="tip">{{ w.wrong_count }} 错 / {{ w.total_count }} 题</span>
              </div>
              <el-progress :percentage="Math.min(w.mastery, 100)" :stroke-width="8"
                           :color="w.mastery >= 60 ? '#67c23a' : '#f56c6c'" />
            </div>
            <el-empty v-if="!(mastery.weak_points || []).length" description="暂无薄弱点，很棒！" :image-size="60" />
          </template>
          <el-empty v-else description="暂无掌握度数据，先做几道题吧" :image-size="70" />
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="genDlg" title="AI 生成复习计划" width="520px">
      <el-alert type="info" :closable="false" class="mb12"
                title="系统会分析你的错题与掌握度，自动生成艾宾浩斯间隔复习节点（1/2/4/7/15/30 天）" />
      <el-form label-width="100px">
        <el-form-item label="规划天数">
          <el-input-number v-model="genForm.days" :min="3" :max="30" style="width:100%" />
        </el-form-item>
        <el-form-item label="每日学习时长">
          <el-input-number v-model="genForm.daily_minutes" :min="15" :max="300" :step="15" style="width:100%" />
          <span class="tip ml8">分钟</span>
        </el-form-item>
      </el-form>
      <div v-if="plan" class="plan-result">
        <el-divider content-position="left">
          <b>生成结果</b>
          <el-tag v-if="plan.is_fallback" type="warning" size="small" class="ml4">规则引擎</el-tag>
        </el-divider>
        <p><b>总体评估：</b>{{ plan.summary || plan.analysis || '-' }}</p>
        <div v-if="plan.weak_points?.length">
          <b>薄弱点：</b>
          <el-tag v-for="w in plan.weak_points" :key="w" size="small" type="danger" effect="plain" class="mr4">
            {{ w }}
          </el-tag>
        </div>
        <div v-if="plan.daily_plan?.length" class="mt8">
          <b>每日计划：</b>
          <div v-for="(d, i) in plan.daily_plan" :key="i" class="day-item">
            <b>{{ d.day ? `第 ${d.day} 天` : `Day ${i + 1}` }}</b>
            <span class="tip">{{ d.focus || d.topic || '' }}</span>
            <ul>
              <li v-for="(t, j) in (d.tasks || d.items || [])" :key="j">{{ t }}</li>
            </ul>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="genDlg = false">关闭</el-button>
        <el-button type="primary" :loading="generating" @click="genPlan">生成计划</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import EChart from '@/components/EChart.vue'
import { Refresh, MagicStick } from '@element-plus/icons-vue'
import { learningApi, eduApi } from '@/api'

const plans = ref([])
const planData = ref({})
const mastery = ref({})
const subjects = ref([])
const plan = ref(null)
const loading = ref(false)
const generating = ref(false)
const genDlg = ref(false)
const tab = ref('today')
const filterDate = ref('')
const subjectId = ref(null)

const genForm = reactive({ days: 7, daily_minutes: 90 })

const radarOption = computed(() => {
  const items = (mastery.value.items || []).slice(0, 8)
  return {
    tooltip: {},
    radar: { indicator: items.map(i => ({ name: i.name.slice(0, 7), max: 100 })), radius: '62%' },
    series: [{
      type: 'radar',
      data: [{ value: items.map(i => i.mastery), name: '掌握度' }],
      areaStyle: { opacity: 0.25, color: '#2f6fd0' }
    }]
  }
})

function strip(s) { return String(s || '').replace(/<[^>]+>/g, '') }
function stageTag(stage) {
  return ['success', 'warning', 'danger', 'primary', 'info'][Math.min((stage || 1) - 1, 4)]
}

async function loadPlans() {
  loading.value = true
  try {
    const params = {}
    if (filterDate.value) params.scheduled_date = filterDate.value
    if (tab.value === 'pending') params.is_completed = false
    const res = await learningApi.reviewPlans(params)
    planData.value = res.data || {}
    plans.value = planData.value.items || []
  } finally {
    loading.value = false
  }
}

async function loadMastery() {
  const res = await learningApi.masteryMap(subjectId.value ? { subject_id: subjectId.value } : {})
  mastery.value = res.data || {}
}

function onTabChange() { loadPlans() }

function loadAll() { loadPlans(); loadMastery() }

const completing = ref(false)
async function complete(p) {
  if (completing.value) return
  completing.value = true
  try {
    await learningApi.completeReview(p.id, { quality: 'good' })
    ElMessage.success('复习完成，下次复习时间已顺延')
    loadPlans()
  } finally {
    completing.value = false
  }
}

function openGenDialog() { plan.value = null; genDlg.value = true }

async function genPlan() {
  generating.value = true
  try {
    const res = await learningApi.generatePlan(genForm)
    plan.value = res.data || {}
    ElMessage.success(res.data.message || '计划生成成功')
    loadAll()
  } finally {
    generating.value = false
  }
}

onMounted(async () => {
  loadAll()
  const s = await eduApi.subjects()
  subjects.value = s.data.data || []
})
</script>

<style scoped>
.flex-between, .row-between { display: flex; align-items: center; justify-content: space-between; }
.mb12 { margin-bottom: 12px; }
.mt8 { margin-top: 8px; }
.mr4 { margin-right: 4px; }
.ml4 { margin-left: 4px; }
.ml8 { margin-left: 8px; }
.mb16 { margin-bottom: 16px; }
.tip { font-size: 12px; color: #909399; }
.plan-list { max-height: 560px; overflow-y: auto; }
.plan-item {
  border: 1px solid #ebeef5; border-radius: 8px; margin-bottom: 8px; padding: 10px;
}
.plan-item.today { border-color: #f7ba2a; background: #fdf6ec; }
.plan-item.done { opacity: 0.6; }
.stem { margin: 6px 0 0; color: #606266; font-size: 13px; }
.weak-item { margin-bottom: 12px; }
.weak-item .row-between { margin-bottom: 4px; font-size: 13px; }
.plan-result { background: #f7f9fc; padding: 12px; border-radius: 8px; max-height: 380px; overflow: auto; }
.day-item { margin-top: 8px; font-size: 13px; }
.day-item ul { margin: 4px 0 0; padding-left: 20px; line-height: 1.8; }
</style>
