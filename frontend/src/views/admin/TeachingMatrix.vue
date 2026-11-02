<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">任课总览</h2>
      <div class="header-actions">
        <el-button :icon="Refresh" @click="load">刷新</el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="14" class="stats-row">
      <el-col :xs="12" :md="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-value">{{ stats.grades }}</div><div class="stat-label">覆盖年级</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :md="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-value">{{ stats.classes }}</div><div class="stat-label">班级总数</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :md="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-value">{{ stats.assignments }}</div><div class="stat-label">授课关系</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :md="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-value">{{ stats.teachers }}</div><div class="stat-label">参与教师</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 搜索：年级 / 班级 / 科目 / 教师 -->
    <el-card shadow="never" class="filter-card">
      <el-form :inline="true">
        <el-form-item label="年级">
          <el-select v-model="filters.grade_id" placeholder="全部年级" clearable style="width: 150px">
            <el-option v-for="g in items" :key="g.grade_id"
                       :label="`${g.grade_name}（${stageText(g.stage)}）`" :value="g.grade_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="班级">
          <el-select v-model="filters.class_id" placeholder="全部班级" clearable filterable
                     style="width: 170px">
            <el-option-group v-for="grp in classGroups" :key="grp.grade_id" :label="grp.grade_name">
              <el-option v-for="c in grp.classes" :key="c.class_id"
                         :label="c.class_name" :value="c.class_id" />
            </el-option-group>
          </el-select>
        </el-form-item>
        <el-form-item label="科目">
          <el-select v-model="filters.subject" placeholder="全部科目" clearable style="width: 130px">
            <el-option v-for="s in subjectNames" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="教师">
          <el-input v-model="teacherKw" placeholder="姓名 / 用户名" clearable
                    style="width: 170px" :prefix-icon="Search" />
        </el-form-item>
        <el-form-item>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 宽表：年级 → 班级 → 科目 → 任教老师（年级/班级列纵向合并） -->
    <el-card shadow="never" class="table-card" v-loading="loading">
      <template #header>
        <div class="table-head">
          <span class="table-title">任课明细</span>
          <span class="table-sub">共 {{ filteredRows.length }} 条 · 同年级/同班级已合并显示</span>
        </div>
      </template>

      <el-table :data="filteredRows" border :span-method="spanMethod" class="matrix-table">
        <el-table-column label="年级" width="110" align="center">
          <template #default="{ row }">
            <div class="grade-cell">
              <div class="grade-name">{{ row.grade_name }}</div>
              <el-tag size="small" effect="light" :type="row.stage === 'primary' ? 'success' : 'primary'">
                {{ stageText(row.stage) }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="班级" width="210">
          <template #default="{ row }">
            <div class="class-cell">
              <div class="class-name">{{ row.class_name }}</div>
              <div v-if="row.head_teacher" class="head-sub">班主任：{{ row.head_teacher }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="科目" width="130">
          <template #default="{ row }">{{ row.subject.name }}</template>
        </el-table-column>
        <el-table-column label="任教老师" min-width="220">
          <template #default="{ row }">
            <template v-if="row.subject.teacher">
              <el-tag effect="plain" :type="isHit(row.subject.teacher) ? 'warning' : 'info'">
                {{ row.subject.teacher.name }}
              </el-tag>
              <span class="username">{{ row.subject.teacher.username }}</span>
            </template>
            <el-tag v-else type="danger" effect="plain">暂无教师</el-tag>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && !filteredRows.length" description="没有匹配的任课数据" />
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Refresh, Search } from '@element-plus/icons-vue'
import { eduApi } from '@/api'

const loading = ref(false)
const items = ref([])
const stats = ref({ grades: 0, classes: 0, assignments: 0, teachers: 0 })
const filters = ref({ grade_id: null, class_id: null, subject: null })
const teacherKw = ref('')

const stageText = (s) => (s === 'primary' ? '小学' : s === 'junior' ? '初中' : (s || ''))

async function load() {
  loading.value = true
  try {
    // 一次取全量（grade_admin 由后端强制本年级），四维过滤全部前端完成，
    // 合并单元格随过滤结果实时重算
    const res = await eduApi.teachingMatrix({})
    items.value = res.data?.items || []
    stats.value = res.data?.stats || { grades: 0, classes: 0, assignments: 0, teachers: 0 }
  } finally {
    loading.value = false
  }
}

// 拍平：年级 → 班级 → 科目（严格保持层级顺序，合并连续性由此保证）
const allRows = computed(() => {
  const rows = []
  for (const g of items.value) {
    for (const k of g.classes) {
      for (const s of k.subjects) {
        rows.push({
          grade_id: g.grade_id,
          grade_name: g.grade_name,
          stage: g.stage,
          class_id: k.class_id,
          class_name: k.class_name,
          head_teacher: k.head_teacher,
          subject: s,
        })
      }
    }
  }
  return rows
})

const classGroups = computed(() => {
  const groups = items.value.map(g => ({
    grade_id: g.grade_id,
    grade_name: g.grade_name,
    classes: g.classes.map(c => ({ class_id: c.class_id, class_name: c.class_name })),
  }))
  if (filters.value.grade_id) {
    return groups.filter(g => g.grade_id === filters.value.grade_id)
  }
  return groups
})

const subjectNames = computed(() => {
  const seen = new Set()
  for (const g of items.value) {
    for (const k of g.classes) {
      for (const s of k.subjects) seen.add(s.name)
    }
  }
  return [...seen]
})

function isHit(t) {
  const kw = teacherKw.value.trim().toLowerCase()
  if (!kw) return false
  return (t.name || '').toLowerCase().includes(kw)
    || (t.username || '').toLowerCase().includes(kw)
}

// 过滤 + 重算合并跨度：档内连续分组，保证 rowspan 不串档
const filteredRows = computed(() => {
  const kw = teacherKw.value.trim().toLowerCase()
  const rows = allRows.value.filter(r => {
    if (filters.value.grade_id && r.grade_id !== filters.value.grade_id) return false
    if (filters.value.class_id && r.class_id !== filters.value.class_id) return false
    if (filters.value.subject && r.subject.name !== filters.value.subject) return false
    if (kw) {
      const t = r.subject.teacher
      if (!t) return false
      if (!isHit(t)) return false
    }
    return true
  })

  let i = 0
  while (i < rows.length) {
    let j = i
    while (j < rows.length && rows[j].grade_id === rows[i].grade_id) j++
    rows[i].grade_span = j - i
    for (let k = i + 1; k < j; k++) rows[k].grade_span = 0

    let a = i
    while (a < j) {
      let b = a
      while (b < j && rows[b].class_id === rows[a].class_id) b++
      rows[a].class_span = b - a
      for (let k = a + 1; k < b; k++) rows[k].class_span = 0
      a = b
    }
    i = j
  }
  return rows
})

function spanMethod({ row, columnIndex }) {
  if (columnIndex === 0) {
    return { rowspan: row.grade_span, colspan: row.grade_span > 0 ? 1 : 0 }
  }
  if (columnIndex === 1) {
    return { rowspan: row.class_span, colspan: row.class_span > 0 ? 1 : 0 }
  }
  return { rowspan: 1, colspan: 1 }
}

function resetFilters() {
  filters.value = { grade_id: null, class_id: null, subject: null }
  teacherKw.value = ''
}

onMounted(load)
</script>

<style scoped>
.table-card { border-radius: 10px; }
.table-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}
.table-title { font-size: 15px; font-weight: 700; }
.table-sub { font-size: 12px; color: #909399; }
.matrix-table { font-size: 14px; }
.grade-cell { font-weight: 700; font-size: 15px; }
.class-cell { line-height: 1.5; }
.class-name { font-weight: 600; }
.head-sub { font-size: 12px; color: #909399; }
.username { margin-left: 8px; font-size: 12px; color: #909399; }
</style>
