<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">成绩中心</h2>
      <div>
        <el-button :icon="Download" @click="exportExcel">导出 Excel</el-button>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
      </div>
    </div>

    <el-row :gutter="16" class="mb16" v-if="summary">
      <el-col :span="5" v-for="c in cards" :key="c.label">
        <div class="stat-card">
          <div class="stat-value" :style="{ color: c.color }">{{ c.value }}</div>
          <div class="stat-label">{{ c.label }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :span="16">
        <el-card shadow="never">
          <template #header><b>成绩记录</b></template>
          <el-table v-loading="loading" :data="list" border stripe>
            <el-table-column prop="task_title" label="任务名称" min-width="200" show-overflow-tooltip />
            <el-table-column label="类型" width="90">
              <template #default="{ row }">
                <el-tag size="small" :type="row.type === 'exam' ? 'danger' : 'primary'">
                  {{ row.type_label }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="得分" width="120">
              <template #default="{ row }">
                <span class="score" :class="scoreClass(row)">{{ row.score ?? '-' }}</span>
                <span class="tip">/ {{ row.total_score }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="class_rank" label="班级排名" width="100" align="center">
              <template #default="{ row }">{{ row.class_rank ? `第 ${row.class_rank} 名` : '-' }}</template>
            </el-table-column>
            <el-table-column label="结果" width="90">
              <template #default="{ row }">
                <el-tag :type="row.is_passed ? 'success' : 'danger'" size="small">
                  {{ row.is_passed ? '及格' : '不及格' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="submit_time" label="提交时间" width="160" />
            <el-table-column label="操作" width="110">
              <template #default="{ row }">
                <el-button link type="primary" @click="viewDetail(row)">查看解析</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination class="mt16" background layout="total, prev, pager, next"
                         :total="total" v-model:current-page="query.page" @current-change="load" />
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card shadow="never">
          <template #header><b>成绩趋势</b></template>
          <ReactEcharts v-if="list.length" :option="trendOption" style="height: 300px" />
          <el-empty v-else description="暂无成绩" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="detailDlg" title="答题解析" width="720px" top="5vh">
      <div v-loading="detailLoading">
        <el-descriptions v-if="detail" :column="3" border class="mb12">
          <el-descriptions-item label="得分">{{ detail.score ?? '-' }}</el-descriptions-item>
          <el-descriptions-item label="满分">{{ detail.total_score }}</el-descriptions-item>
          <el-descriptions-item label="排名">{{ detail.class_rank ? `第 ${detail.class_rank} 名` : '-' }}</el-descriptions-item>
        </el-descriptions>

        <div v-for="(r, idx) in results" :key="idx" class="q-item">
          <p><b>第 {{ idx + 1 }} 题</b>
            <el-tag size="small" class="ml4" :type="r.is_correct ? 'success' : 'danger'">
              {{ r.is_correct ? '正确' : '错误' }}
            </el-tag>
          </p>
          <p class="stem">{{ r.stem || strip(r.question_stem) }}</p>
          <p class="mine">我的答案：{{ format(r.student_answer) }}</p>
          <p class="correct">正确答案：{{ format(r.correct_answer) }}</p>
          <p v-if="r.analysis" class="analysis">解析：{{ r.analysis }}</p>
          <p v-if="r.ai_comment" class="ai">AI 评语：{{ r.ai_comment }}</p>
        </div>
        <el-empty v-if="!detailLoading && !results.length" description="暂无答题明细" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import ReactEcharts from 'echarts-for-react'
import { Refresh, Download } from '@element-plus/icons-vue'
import { taskApi, reportApi } from '@/api'

const list = ref([])
const results = ref([])
const detail = ref(null)
const summary = ref(null)
const total = ref(0)
const loading = ref(false)
const detailLoading = ref(false)
const detailDlg = ref(false)
const query = reactive({ page: 1, page_size: 20 })

const cards = computed(() => summary.value ? [
  { label: '参考次数', value: summary.value.count, color: '#2f6fd0' },
  { label: '平均分', value: summary.value.avg_score, color: '#67c23a' },
  { label: '最高分', value: summary.value.max_score, color: '#67c23a' },
  { label: '最低分', value: summary.value.min_score, color: '#f56c6c' },
  { label: '及格率', value: `${summary.value.pass_rate}%`, color: '#e6a23c' }
] : [])

const trendOption = computed(() => {
  const data = [...list.value].reverse()
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 45, right: 20, top: 30, bottom: 50 },
    xAxis: { type: 'category', data: data.map(t => (t.task_title || '').slice(0, 8)),
             axisLabel: { rotate: 30, fontSize: 10 } },
    yAxis: { type: 'value', name: '分数' },
    series: [{
      type: 'line', smooth: true, data: data.map(t => t.score),
      itemStyle: { color: '#2f6fd0' }, areaStyle: { opacity: 0.12 }
    }]
  }
})

function scoreClass(row) {
  if (row.score === null || row.score === undefined) return ''
  const pct = row.score / (row.total_score || 100)
  return pct >= 0.6 ? 'text-success' : 'text-danger'
}
function strip(s) { return String(s || '').replace(/<[^>]+>/g, '') }
function format(v) {
  if (v === null || v === undefined || v === '') return '未作答'
  if (typeof v === 'object') return Array.isArray(v) ? v.join(',') : JSON.stringify(v)
  return String(v)
}

async function load() {
  loading.value = true
  try {
    const res = await taskApi.myScores(query)
    const d = res.data.data || {}
    list.value = d.items || []
    total.value = d.total || 0
    summary.value = d.summary
  } finally {
    loading.value = false
  }
}

async function viewDetail(row) {
  detailDlg.value = true
  detailLoading.value = true
  results.value = []
  try {
    const res = await taskApi.submissionDetail(row.id)
    detail.value = res.data.data
    results.value = detail.value?.results || []
  } finally {
    detailLoading.value = false
  }
}

function exportExcel() {
  window.open(reportApi.exportUrl({ scope: 'student' }), '_blank')
}

onMounted(load)
</script>

<style scoped>
.flex-between { display: flex; align-items: center; justify-content: space-between; }
.mb12 { margin-bottom: 12px; }
.mb16 { margin-bottom: 16px; }
.mt16 { margin-top: 16px; justify-content: flex-end; }
.ml4 { margin-left: 4px; }
.tip { font-size: 12px; color: #909399; }
.score { font-size: 16px; font-weight: 700; }
.text-success { color: #67c23a; }
.text-danger { color: #f56c6c; }
.q-item { padding: 12px 0; border-bottom: 1px dashed #ebeef5; }
.q-item:last-child { border-bottom: none; }
.stem { line-height: 1.7; margin: 6px 0; }
.mine { color: #f56c6c; margin: 4px 0; }
.correct { color: #67c23a; margin: 4px 0; }
.analysis { color: #606266; font-size: 13px; margin: 4px 0; }
.ai { color: #2f6fd0; background: #f0f6ff; padding: 4px 8px; border-radius: 4px; font-size: 13px; }
</style>
