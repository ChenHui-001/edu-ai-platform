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
          <div class="stat-value">{{ stats.subjects }}</div><div class="stat-label">学科单元</div>
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
          <span class="filter-tip">跨年级任课的教师会出现在多个年级中；「暂无教师」为任课缺口，请及时安排。</span>
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
              {{ g.subjects.length }} 门学科 · {{ gradeTeacherCount(g) }} 名教师参与
            </span>
          </div>
        </template>

        <el-table :data="g.subjects" size="small" stripe>
          <el-table-column prop="name" label="学科" width="110" />
          <el-table-column prop="textbook_version" label="教材版本" width="120" />
          <el-table-column label="任教教师" min-width="170">
            <template #default="{ row }">
              <template v-if="row.teachers.length">
                <el-tag v-for="t in row.teachers" :key="t.teacher_id"
                        :type="hit(t) ? 'warning' : 'info'" effect="plain" class="t-tag">
                  {{ t.name }}
                </el-tag>
              </template>
              <el-tag v-else type="danger" effect="plain">暂无教师（缺口）</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="任教明细（教师 · 所带班级）" min-width="300">
            <template #default="{ row }">
              <span v-if="row.teachers.length" class="detail">
                {{ row.teachers.map(t => `${t.name}（${t.classes.join('、')}）`).join('；') }}
              </span>
              <span v-else class="muted">—</span>
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
const stats = ref({ grades: 0, subjects: 0, assignments: 0, teachers: 0 })
const query = ref({ grade_id: null })
const keyword = ref('')

const stageText = (s) => (s === 'primary' ? '小学' : s === 'junior' ? '初中' : (s || ''))

async function load() {
  loading.value = true
  try {
    const res = await eduApi.teachingMatrix(
      query.value.grade_id ? { grade_id: query.value.grade_id } : {})
    items.value = res.data?.items || []
    stats.value = res.data?.stats || { grades: 0, subjects: 0, assignments: 0, teachers: 0 }
  } finally {
    loading.value = false
  }
}

// 前端过滤：年级走后端参数（grade_admin 有年级硬约束），姓名/用户名走前端即时过滤
const filteredItems = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  return items.value
    .filter(g => !query.value.grade_id || g.grade_id === query.value.grade_id)
    .map(g => {
      if (!kw) return g
      const subjects = g.subjects.filter(s => s.teachers.some(t => hit(t)))
      return { ...g, subjects }
    })
    .filter(g => !kw || g.subjects.length > 0)
})

function hit(t) {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return false
  return (t.name || '').toLowerCase().includes(kw)
    || (t.username || '').toLowerCase().includes(kw)
}

function gradeTeacherCount(g) {
  const ids = new Set()
  for (const s of g.subjects) for (const t of s.teachers) ids.add(t.teacher_id)
  return ids.size
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
.t-tag { margin-right: 6px; }
.detail { font-size: 13px; color: #606266; }
.muted { color: #c0c4cc; }
</style>
