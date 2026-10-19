<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">{{ typeName }}管理</h2>
      <div>
        <el-button :icon="Refresh" @click="loadAll">刷新</el-button>
        <el-button type="primary" :icon="Plus" @click="openDialog()">新增{{ typeName }}</el-button>
      </div>
    </div>

    <!-- 学科专用：视图模式切换（按年级 vs 平铺） -->
    <div v-if="isSubject" class="mode-bar mb12">
      <el-radio-group v-model="viewMode" size="default">
        <el-radio-button label="byGrade">
          <el-icon class="mr4"><Grid /></el-icon>按年级查看
        </el-radio-button>
        <el-radio-button label="flat">
          <el-icon class="mr4"><List /></el-icon>平铺列表
        </el-radio-button>
      </el-radio-group>
      <span class="tip ml12" v-if="viewMode === 'byGrade'">
        点击左侧年级查看该年级下的学科，跨年级同名学科不再混淆
      </span>
    </div>

    <!-- ====================== 学科 · 按年级视图 ====================== -->
    <template v-if="isSubject && viewMode === 'byGrade'">
      <el-row :gutter="12" class="by-grade">
        <el-col :span="6">
          <el-card shadow="never" class="grade-list">
            <template #header>
              <div class="flex-between">
                <b>年级</b>
                <el-tag size="small">{{ grades.length }} 个</el-tag>
              </div>
            </template>
            <el-input v-model="gradeKeyword" placeholder="搜索年级" clearable
                      :prefix-icon="Search" class="mb8" size="small" />
            <div class="grade-items" v-loading="loadingGrades">
              <div v-for="g in filteredGrades" :key="g.id"
                   class="grade-item"
                   :class="{ active: selectedGradeId === g.id }"
                   @click="selectGrade(g)">
                <span class="gname">{{ g.name }}</span>
                <el-badge :value="subjectByGrade(g.id).length" :max="99" type="primary" />
              </div>
              <el-empty v-if="!filteredGrades.length" description="无匹配年级" :image-size="50" />
            </div>
          </el-card>
        </el-col>
        <el-col :span="18">
          <el-card shadow="never">
            <template #header>
              <div class="flex-between">
                <b>
                  <template v-if="selectedGrade">
                    {{ selectedGrade.name }}的学科
                  </template>
                  <template v-else>请选择左侧年级</template>
                </b>
                <div v-if="selectedGrade">
                  <el-button size="small" :icon="RefreshLeft" @click="openCloneDialog()">
                    跨年级复制
                  </el-button>
                </div>
              </div>
            </template>
            <el-table v-if="selectedGrade" v-loading="loading" :data="currentGradeSubjects" border stripe>
              <el-table-column prop="sort_order" label="排序" width="70" align="center" />
              <el-table-column prop="name" label="学科名称" min-width="160" />
              <el-table-column prop="code" label="代码" width="140" show-overflow-tooltip />
              <el-table-column prop="textbook_version" label="教材版本" width="120" show-overflow-tooltip />
              <el-table-column label="状态" width="90">
                <template #default="{ row }">
                  <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
                    {{ row.is_active ? '启用' : '停用' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="240" fixed="right">
                <template #default="{ row }">
                  <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
                  <el-button link type="warning" @click="openCloneDialog(row)">复制到其他年级</el-button>
                  <el-button link type="danger" @click="remove(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-else description="请选择左侧年级" :image-size="80" />
            <div v-if="selectedGrade" class="tip mt12">
              该年级共 {{ currentGradeSubjects.length }} 个学科
            </div>
          </el-card>
        </el-col>
      </el-row>
    </template>

    <!-- ====================== 通用 · 列表视图（年级页 / 学科平铺页） ====================== -->
    <template v-else>
      <el-card shadow="never" class="filter-card">
        <el-form :inline="true" :model="query">
          <el-form-item label="关键词">
            <el-input v-model="query.keyword" placeholder="名称" clearable style="width:180px"
                      @keyup.enter="load" />
          </el-form-item>
          <el-form-item v-if="isSubject" label="所属年级">
            <el-select v-model="query.grade_id" placeholder="全部" clearable style="width:140px">
              <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :icon="Search" @click="load">查询</el-button>
            <el-button :icon="RefreshLeft" @click="reset">重置</el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <el-card shadow="never">
        <el-table v-loading="loading" :data="list" border stripe>
          <el-table-column prop="sort_order" label="排序" width="70" align="center" />
          <el-table-column prop="name" label="名称" min-width="160" />
          <el-table-column v-if="isSubject" prop="grade_name" label="所属年级" width="140" />
          <el-table-column prop="description" label="说明" min-width="200" show-overflow-tooltip />
          <el-table-column prop="created_at" label="创建时间" width="160" />
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
                {{ row.is_active ? '启用' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
              <el-button link type="danger" @click="remove(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination class="mt16" background layout="total, prev, pager, next"
                       :total="total" v-model:current-page="query.page"
                       @current-change="load" />
      </el-card>
    </template>

    <!-- 新增/编辑 弹窗 -->
    <el-dialog v-model="dlg" :title="`${form.id ? '编辑' : '新增'}${typeName}`" width="480px">
      <el-form :model="form" label-width="90px">
        <el-form-item v-if="isSubject" label="所属年级">
          <el-select v-model="form.grade_id" style="width:100%">
            <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item v-if="isSubject" label="代码">
          <el-input v-model="form.code" placeholder="可选" />
        </el-form-item>
        <el-form-item v-if="isSubject" label="教材版本">
          <el-input v-model="form.textbook_version" placeholder="可选" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" :max="999" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.active" active-text="启用" inactive-text="停用" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">确定</el-button>
      </template>
    </el-dialog>

    <!-- 跨年级复制 弹窗 -->
    <el-dialog v-model="cloneDlg" title="跨年级复制学科" width="480px">
      <el-alert :closable="false" type="info" class="mb12" v-if="cloneSource">
        将 <b>{{ cloneSource.name }}</b>（当前所在：{{ gradeNameOf(cloneSource.grade_id) }}）复制到：
      </el-alert>
      <el-form label-width="80px">
        <el-form-item label="目标年级">
          <el-checkbox-group v-model="cloneTargetIds">
            <el-checkbox v-for="g in grades.filter(x => x.id !== cloneSource?.grade_id)"
                         :key="g.id" :value="g.id">
              {{ g.name }}<span class="tip" v-if="subjectByGrade(g.id).find(x => x.name === cloneSource?.name)">
                （已有同名）
              </span>
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="cloneDlg = false">取消</el-button>
        <el-button type="primary" :loading="cloning" :disabled="!cloneTargetIds.length"
                   @click="doClone">复制到 {{ cloneTargetIds.length }} 个年级</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Search, Refresh, RefreshLeft, Grid, List,
} from '@element-plus/icons-vue'
import { eduApi } from '@/api'

const route = useRoute()
const isSubject = computed(() => route.name === 'SubjectManage')
const typeName = computed(() => (isSubject.value ? '学科' : '年级'))

// -------- 列表视图（年级页 / 学科平铺页）通用状态 --------
const list = ref([])
const grades = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const dlg = ref(false)
const query = reactive({ page: 1, page_size: 50, keyword: '', grade_id: null })
const form = reactive({
  id: null, name: '', grade_id: null, sort_order: 0, active: true,
  description: '', code: '', textbook_version: '',
})

// -------- 学科 · 按年级视图 状态 --------
const viewMode = ref('byGrade')          // 'byGrade' | 'flat'
const allSubjects = ref([])              // 全量学科（按年级视图用）
const selectedGradeId = ref(null)
const gradeKeyword = ref('')
const loadingGrades = ref(false)
const filteredGrades = computed(() => {
  const kw = gradeKeyword.value.trim()
  if (!kw) return grades.value
  return grades.value.filter(g => g.name.includes(kw))
})
const selectedGrade = computed(() => grades.value.find(g => g.id === selectedGradeId.value))
const currentGradeSubjects = computed(() => subjectByGrade(selectedGradeId.value))
function subjectByGrade(gid) {
  if (!gid) return []
  return allSubjects.value.filter(s => s.grade_id === gid)
}
function gradeNameOf(gid) {
  return grades.value.find(g => g.id === gid)?.name || `#${gid}`
}

// -------- 跨年级复制 弹窗 --------
const cloneDlg = ref(false)
const cloneSource = ref(null)
const cloneTargetIds = ref([])
const cloning = ref(false)
function openCloneDialog(row) {
  cloneSource.value = row || currentGradeSubjects.value[0]
  cloneTargetIds.value = []
  cloneDlg.value = true
}
async function doClone() {
  if (!cloneSource.value || !cloneTargetIds.value.length) return
  cloning.value = true
  try {
    const res = await eduApi.cloneSubject(cloneSource.value.id, {
      target_grade_ids: cloneTargetIds.value,
    })
    const d = res.data || {}
    ElMessage.success(
      `已创建 ${d.created?.length || 0} 条，跳过 ${d.skipped?.length || 0} 条`)
    cloneDlg.value = false
    loadAll()
  } finally {
    cloning.value = false
  }
}

// -------- 加载逻辑 --------
async function load() {
  loading.value = true
  try {
    const api = isSubject.value ? eduApi.subjects : eduApi.grades
    const res = await api(query)
    // /edu/grades 与 /edu/subjects 返回数组（非分页 items），两种结构都兼容
    const d = res.data
    list.value = Array.isArray(d) ? d : (d?.items || [])
    total.value = Array.isArray(d) ? d.length : (d?.total || 0)
  } finally { loading.value = false }
}

// 学科按年级视图：拉一次全量 + 全年级
async function loadAll() {
  loadingGrades.value = true
  loading.value = true
  try {
    const [gRes, sRes] = await Promise.all([eduApi.grades(), eduApi.subjects()])
    grades.value = Array.isArray(gRes.data) ? gRes.data : (gRes.data?.data || [])
    allSubjects.value = Array.isArray(sRes.data) ? sRes.data : (sRes.data?.data || [])
    // 首次进入自动选中第一个年级
    if (isSubject.value && !selectedGradeId.value && grades.value.length) {
      selectGrade(grades.value[0])
    }
  } finally {
    loadingGrades.value = false
    loading.value = false
  }
}

function selectGrade(g) {
  selectedGradeId.value = g.id
  query.grade_id = g.id  // 同步平铺视图的年级筛选
}

function reset() {
  Object.assign(query, { page: 1, keyword: '', grade_id: null })
  load()
}

// -------- 增改删 --------
function openDialog(row) {
  Object.assign(form, row
    ? { ...row, active: row.is_active ?? true,
        code: row.code || '', textbook_version: row.textbook_version || '',
        description: row.description || '' }
    : { id: null, name: '', grade_id: null,
        sort_order: 0, active: true, description: '',
        code: '', textbook_version: '' })
  dlg.value = true
}
async function save() {
  if (!form.name) return ElMessage.warning('请输入名称')
  if (isSubject.value && !form.grade_id) return ElMessage.warning('请选择所属年级')
  saving.value = true
  const payload = { ...form, is_active: form.active ? 1 : 0, status: undefined }
  delete payload.active
  try {
    if (isSubject.value) {
      if (form.id) await eduApi.updateSubject(form.id, payload)
      else await eduApi.createSubject(payload)
    } else {
      if (form.id) await eduApi.updateGrade(form.id, payload)
      else await eduApi.createGrade(payload)
    }
    ElMessage.success('保存成功')
    dlg.value = false
    if (viewMode.value === 'byGrade' && isSubject.value) loadAll()
    else load()
  } finally { saving.value = false }
}

async function remove(row) {
  await ElMessageBox.confirm(`确认删除「${row.name}」？`, '提示', { type: 'warning' })
  if (isSubject.value) await eduApi.deleteSubject(row.id)
  else await eduApi.deleteGrade(row.id)
  ElMessage.success('已删除')
  if (viewMode.value === 'byGrade' && isSubject.value) loadAll()
  else load()
}

watch(() => route.name, () => {
  selectedGradeId.value = null
  loadAll()
})

onMounted(() => {
  loadAll()
  // 平铺视图共用 list 字段：年级页 + 学科平铺页都用同一列表后端。
  // 首次进入若 viewMode='flat'，需加载 list。
  if (!isSubject.value || viewMode.value === 'flat') load()
})

// 切视图时按需懒加载：按年级 → 平铺 时 list 还没拉
watch(viewMode, (m) => {
  if (m === 'flat' && !list.value.length) load()
})
</script>

<style scoped>
.mb8 { margin-bottom: 8px; }
.mb12 { margin-bottom: 12px; }
.mt12 { margin-top: 12px; }
.mr4 { margin-right: 4px; }
.ml12 { margin-left: 12px; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
.tip { color: #909399; font-size: 12px; }

.mode-bar {
  display: flex; align-items: center;
  padding: 10px 14px;
  background: #f5f7fa;
  border-radius: 4px;
}

.grade-list .grade-items {
  max-height: 600px;
  overflow-y: auto;
}
.grade-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.15s;
}
.grade-item:hover { background: #eef3fb; }
.grade-item.active { background: #2f6fd0; color: #fff; }
.grade-item.active .gname { color: #fff; }
.grade-item .gname { flex: 1; }

.by-grade { align-items: stretch; }
</style>
