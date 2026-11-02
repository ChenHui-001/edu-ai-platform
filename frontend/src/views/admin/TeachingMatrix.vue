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

    <!-- 过滤 -->
    <el-card shadow="never" class="filter-card">
      <el-form :inline="true">
        <el-form-item label="年级">
          <el-select v-model="query.grade_id" placeholder="全部年级" clearable style="width: 140px">
            <el-option v-for="g in items" :key="g.grade_id"
                       :label="`${g.grade_name}（${stageText(g.stage)}）`" :value="g.grade_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="教师姓名">
          <el-input v-model="keyword" placeholder="输入教师姓名 / 用户名过滤" clearable
                    style="width: 220px" :prefix-icon="Search" />
        </el-form-item>
        <el-form-item>
          <span class="filter-tip">层级：年级 → 班级 → 科目 → 任教老师；跨年级任课的教师会出现在多个班级中，「暂无教师」为任课缺口。</span>
        </el-form-item>
      </el-form>
    </el-card>

    <div v-loading="loading">
      <el-card v-for="g in filteredItems" :key="g.grade_id" shadow="never" class="grade-card">
        <template #header>
          <div class="grade-head">
            <span class="grade-name">{{ g.grade_name }}</span>
            <el-tag :type="g.stage === 'primary' ? 'success' : 'primary'" size="small">
              {{ stageText(g.stage) }}
            </el-tag>
            <span class="grade-sub">
              {{ g.classes.length }} 个班级 · {{ g.teacher_count }} 名教师参与
            </span>
          </div>
        </template>

        <el-table :data="g.rows" size="small" :span-method="spanClass" :show-header="true">
          <el-table-column label="班级" width="220">
            <template #default="{ row }">
              <div class="cls-cell">
                <span class="cls-name">{{ row.class_name }}</span>
                <el-tag v-if="row.head_teacher" type="success" effect="plain" size="small">
                  班主任：{{ row.head_teacher }}
                </el-tag>
                <span v-else class="muted">暂无班主任</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="科目" width="120">
            <template #default="{ row }">{{ row.subject.name }}</template>
          </el-table-column>
          <el-table-column label="教材版本" width="120">
            <template #default="{ row }">{{ row.subject.textbook_version || '—' }}</template>
          </el-table-column>
          <el-table-column label="任教老师" min-width="220">
            <template #default="{ row }">
              <template v-if="row.subject.teacher">
                <el-tag :type="hit(row.subject.teacher) ? 'warning' : 'info'" effect="plain">
                  {{ row.subject.teacher.name }}
                </el-tag>
                <span class="muted">{{ row.subject.teacher.username }}</span>
              </template>
              <el-tag v-else type="danger" effect="plain">暂无教师（缺口）</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-empty v-if="!loading && !filteredItems.length" description="没有匹配的任课数据" />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Refresh, Search } from '@element-plus/icons-vue'
import { eduApi } from '@/api'

const loading = ref(false)
const items = ref([])
const stats = ref({ grades: 0, classes: 0, assignments: 0, teachers: 0 })
const query = ref({ grade_id: null })
const keyword = ref('')

const stageText = (s) => (s === 'primary' ? '小学' : s === 'junior' ? '初中' : (s || ''))

async function load() {
  loading.value = true
  try {
    const res = await eduApi.teachingMatrix(
      query.value.grade_id ? { grade_id: query.value.grade_id } : {})
    items.value = res.data?.items || []
    stats.value = res.data?.stats || { grades: 0, classes: 0, assignments: 0, teachers: 0 }
  } finally {
    loading.value = false
  }
}

// 把 年级→班级→科目 拍平成表格行；「班级」列用 rowspan 合并，
// 搜索时只保留命中教师的科目行（rowspan 随之重算，保证合并不错位）
const filteredItems = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  return items.value
    .filter(g => !query.value.grade_id || g.grade_id === query.value.grade_id)
    .map(g => {
      const rows = []
      const tids = new Set()
      for (const k of g.classes) {
        const kept = kw
          ? k.subjects.filter(s => s.teacher && hit(s.teacher))
          : k.subjects
        if (kw && !kept.length) continue
        kept.forEach((s, i) => {
          rows.push({
            class_name: k.class_name,
            head_teacher: k.head_teacher,
            rowspan: i === 0 ? kept.length : 0,
            subject: s,
          })
        })
        for (const s of kept) if (s.teacher) tids.add(s.teacher.teacher_id)
      }
      return {
        ...g,
        rows,
        teacher_count: tids.size,
      }
    })
    .filter(g => (kw ? g.rows.length > 0 : true))
})

function hit(t) {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return false
  return (t.name || '').toLowerCase().includes(kw)
    || (t.username || '').toLowerCase().includes(kw)
}

// 合并「班级」列：rowspan>0 的行占位，=0 的行被上方合并覆盖
function spanClass({ columnIndex, row }) {
  if (columnIndex === 0) {
    return { rowspan: row.rowspan, colspan: row.rowspan > 0 ? 1 : 0 }
  }
  return { rowspan: 1, colspan: 1 }
}

onMounted(load)
</script>

<style scoped>
.stats-row { margin-bottom: 14px; }
.stat-card { text-align: center; }
.stat-value { font-size: 26px; font-weight: 700; }
.stat-label { font-size: 13px; color: #909399; margin-top: 2px; }
.filter-card { margin-bottom: 14px; }
.filter-tip { font-size: 12px; color: #909399; }
.grade-card { margin-bottom: 14px; }
.grade-head { display: flex; align-items: center; gap: 8px; }
.grade-name { font-weight: 700; font-size: 15px; }
.grade-sub { font-size: 12px; color: #909399; }
.cls-cell { display: flex; flex-direction: column; gap: 4px; }
.cls-name { font-weight: 600; }
.muted { font-size: 12px; color: #909399; }
</style>
