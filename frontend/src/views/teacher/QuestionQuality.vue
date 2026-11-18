<template>
  <div class="page-container" v-loading="loading">
    <div class="page-header"><h2>题库质量工作台</h2><el-button @click="load">重新检查</el-button></div>
    <el-alert type="info" :closable="false" title="结构检查用于发现缺项和明确冲突；语义正确性仍需教师核对。AI 题发布前必须通过检查。" />
    <ErrorState v-if="error" :message="error" @retry="load" />
    <template v-else-if="report">
      <p>扫描 {{ report.total_scanned }} 道题 · {{ report.errors }} 道存在阻断问题</p>
      <el-alert v-if="report.truncated" type="warning" :closable="false" title="本次只检查前 5000 道题" />
      <div class="mt12">
        <el-input v-model="keyword" placeholder="题号或题干搜索" clearable style="width: 240px" />
        <el-checkbox v-model="onlyIssues" style="margin-left: 12px">仅显示待审或有问题的题目</el-checkbox>
      </div>
      <el-table :data="visibleItems" @selection-change="selection = $event.map(item => item.id)">
        <el-table-column type="selection" width="45" />
        <el-table-column prop="id" label="编号" width="75" />
        <el-table-column prop="stem" label="题干" min-width="200" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100" />
        <el-table-column label="检查结果" min-width="220">
          <template #default="{ row }">
            <div v-for="issue in row.errors" :key="issue" class="danger">{{ issue }}</div>
            <div v-for="issue in row.warnings" :key="issue">{{ issue }}</div>
          </template>
        </el-table-column>
        <el-table-column label="图形" width="100"><template #default="{ row }">
          <el-button size="small" :disabled="!row.can_edit" @click="openVisual(row)">编辑</el-button>
        </template></el-table-column>
      </el-table>
      <el-pagination v-model:current-page="page" :total="filteredItems.length" :page-size="50" layout="total, prev, pager, next" />
      <el-button class="mt12" type="primary" :disabled="!selection.length || !canAudit" @click="publish">核对后发布所选题目</el-button>
      <p v-if="!canAudit">当前账号没有公共题库审核权限，可先修正题目后提交管理员审核。</p>
      <el-collapse class="mt12"><el-collapse-item :title="`题量不足的知识点（${report.gaps.length}）`">
        <p v-for="item in report.gaps" :key="item.id">{{ item.name }} · {{ item.question_count }} 题</p>
      </el-collapse-item></el-collapse>
    </template>
    <el-dialog v-model="visualOpen" title="题目图形编辑" width="min(600px, 95vw)">
      <el-select v-model="kind" @change="resetVisual">
        <el-option label="数轴" value="number_line" /><el-option label="分数" value="fraction" /><el-option label="几何图" value="polygon" />
      </el-select>
      <template v-if="kind === 'fraction'">
        <p>分子 <el-input-number v-model="visual.numerator" :min="0" :max="visual.denominator" /></p>
        <p>分母 <el-input-number v-model="visual.denominator" :min="1" :max="20" /></p>
      </template>
      <template v-else-if="kind === 'number_line'">
        <p>起点 <el-input-number v-model="visual.min" :min="-1000" :max="999" /></p>
        <p>终点 <el-input-number v-model="visual.max" :min="visual.min + 1" :max="1000" /></p>
      </template>
      <el-input v-if="kind !== 'fraction'" v-model="pointsText" type="textarea" :rows="4" placeholder='数轴：[{"value":3,"label":"A"}]；几何：[{"x":40,"y":180,"label":"A"},...]' />
      <el-button class="mt12" @click="previewVisual">预览</el-button>
      <QuestionContent v-if="previewQuestion" :question="previewQuestion" />
      <template #footer><el-button @click="visualOpen = false">取消</el-button><el-button type="primary" :loading="saving" @click="saveVisual">保存图形</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { extensionApi } from '@/api/extensions'
import { useUserStore } from '@/store/user'
import { confirmAction } from '@/utils/confirm'
import QuestionContent from '@/components/QuestionContent.vue'
import ErrorState from '@/components/ErrorState.vue'

const store = useUserStore()
const canAudit = computed(() => store.can('question:bank:audit') || store.permissions.roles?.some(role => ['sys_admin', 'grade_admin'].includes(role)))
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const report = ref(null)
const selection = ref([])
const page = ref(1)
const keyword = ref('')
const onlyIssues = ref(true)
const filteredItems = computed(() => (report.value?.items || []).filter(item =>
  (!onlyIssues.value || item.status === 'draft' || item.errors.length || item.warnings.length) &&
  (!keyword.value || String(item.id).includes(keyword.value.trim()) || item.stem?.includes(keyword.value.trim()))))
const visibleItems = computed(() => filteredItems.value.slice((page.value - 1) * 50, page.value * 50))
watch([keyword, onlyIssues], () => { page.value = 1; selection.value = [] })
const visualOpen = ref(false)
const editing = ref(null)
const kind = ref('number_line')
const visual = reactive({ kind: 'number_line', min: 0, max: 10, numerator: 1, denominator: 4 })
const pointsText = ref('[]')
const previewQuestion = ref(null)
async function load() {
  loading.value = true; error.value = ''
  selection.value = []
  try { report.value = (await extensionApi.quality()).data }
  catch { error.value = '质检加载失败，请重试' }
  finally { loading.value = false }
}
async function publish() {
  if (!await confirmAction('已核对所选题目的答案与解析，确认发布？')) return
  loading.value = true
  try { await extensionApi.publish(selection.value); ElMessage.success('已发布'); await load() }
  finally { loading.value = false }
}
function resetVisual() {
  visual.kind = kind.value
  pointsText.value = kind.value === 'polygon' ? '[{"x":40,"y":180,"label":"A"},{"x":180,"y":30,"label":"B"},{"x":340,"y":180,"label":"C"}]' : '[]'
  previewQuestion.value = null
}
function openVisual(row) {
  editing.value = row; visualOpen.value = true; kind.value = row.visual?.kind || 'number_line'; resetVisual()
  if (row.visual) {
    Object.assign(visual, row.visual)
    pointsText.value = JSON.stringify(row.visual.points || [], null, 2)
  }
}
function makeVisual() {
  if (kind.value === 'fraction') return { kind: kind.value, numerator: visual.numerator, denominator: visual.denominator }
  if (kind.value === 'polygon') return { kind: kind.value, points: JSON.parse(pointsText.value) }
  return { kind: kind.value, min: visual.min, max: visual.max, points: JSON.parse(pointsText.value) }
}
function previewVisual() {
  try { previewQuestion.value = { stem: editing.value.stem, visual: makeVisual() } }
  catch { ElMessage.warning('点坐标格式不正确，请填写 JSON 数组') }
}
async function saveVisual() {
  let value
  try { value = makeVisual() } catch { ElMessage.warning('点坐标格式不正确'); return }
  saving.value = true
  try { await extensionApi.visual(editing.value.id, value); visualOpen.value = false; ElMessage.success('图形已保存'); await load() }
  finally { saving.value = false }
}
onMounted(load)
</script>

<style scoped>
.mt12 { margin-top: 12px; }
.danger { color: var(--el-color-danger); }
</style>
