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
          <span class="filter-tip">层级：年级 → 班级 → 科目 → 任教老师；跨年级任课的教师会出现在多个班级中。</span>
        </el-form-item>
      </el-form>
    </el-card>

    <div v-loading="loading">
      <el-card v-for="g in filteredItems" :key="g.grade_id" shadow="never" class="grade-card">
        <template #header>
          <div class="grade-head">
            <div class="grade-title">
              <span class="grade-bar"></span>
              <span>{{ g.grade_name }}</span>
              <el-tag :type="g.stage === 'primary' ? 'success' : 'primary'" size="small" effect="light">
                {{ stageText(g.stage) }}
              </el-tag>
            </div>
            <span class="grade-sub">{{ g.classes.length }} 个班级 · {{ g.teacher_count }} 名教师参与</span>
          </div>
        </template>

        <el-row :gutter="14">
          <el-col v-for="k in g.view_classes" :key="k.class_id" :xs="24" :sm="12" :md="8">
            <div class="class-card">
              <div class="class-head">
                <span class="class-name">{{ k.class_name }}</span>
                <span v-if="k.head_teacher" class="head-tag">班主任 · {{ k.head_teacher }}</span>
                <span v-else class="head-tag none">暂无班主任</span>
              </div>
              <div class="sub-list">
                <div v-for="s in k.subjects" :key="s.subject_id" class="sub-row">
                  <span class="sub-name">{{ s.name }}</span>
                  <span class="sub-line"></span>
                  <template v-if="s.teacher">
                    <el-tag size="small" effect="plain" :type="hit(s.teacher) ? 'warning' : 'info'"
                            :title="s.teacher.username">
                      {{ s.teacher.name }}
                    </el-tag>
                  </template>
                  <el-tag v-else size="small" type="danger" effect="plain">暂无教师</el-tag>
                </div>
              </div>
            </div>
          </el-col>
        </el-row>
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

function hit(t) {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return false
  return (t.name || '').toLowerCase().includes(kw)
    || (t.username || '').toLowerCase().includes(kw)
}

// 搜索时只保留命中教师的科目；班级/年级无命中则整块隐藏
const filteredItems = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  return items.value
    .filter(g => !query.value.grade_id || g.grade_id === query.value.grade_id)
    .map(g => {
      const tids = new Set()
      const view_classes = g.classes
        .map(k => {
          const subjects = kw
            ? k.subjects.filter(s => s.teacher && hit(s.teacher))
            : k.subjects
          for (const s of subjects) if (s.teacher) tids.add(s.teacher.teacher_id)
          return { ...k, subjects }
        })
        .filter(k => !kw || k.subjects.length > 0)
      return { ...g, view_classes, teacher_count: tids.size }
    })
    .filter(g => !kw || g.view_classes.length > 0)
})

onMounted(load)
</script>

<style scoped>
.grade-card { margin-bottom: 16px; border-radius: 10px; }
.grade-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.grade-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 700;
}
.grade-bar {
  width: 4px;
  height: 16px;
  border-radius: 2px;
  background: var(--el-color-primary);
  display: inline-block;
}
.grade-sub { font-size: 12px; color: #909399; }
.class-card {
  border: 1px solid #eceff4;
  border-radius: 10px;
  background: #fff;
  padding: 12px 14px;
  margin-bottom: 14px;
  box-shadow: 0 1px 4px rgba(31, 45, 61, 0.05);
  transition: box-shadow 0.2s, transform 0.2s;
}
.class-card:hover {
  box-shadow: 0 4px 14px rgba(31, 45, 61, 0.1);
  transform: translateY(-2px);
}
.class-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 8px;
  border-bottom: 1px dashed #ebeef5;
  margin-bottom: 6px;
  gap: 6px;
  flex-wrap: wrap;
}
.class-name { font-weight: 600; font-size: 14px; }
.head-tag {
  font-size: 12px;
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  border-radius: 10px;
  padding: 2px 8px;
  white-space: nowrap;
}
.head-tag.none { color: #c0c4cc; background: #f5f7fa; }
.sub-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  font-size: 13px;
}
.sub-name { color: #303133; min-width: 5.5em; }
.sub-line {
  flex: 1;
  border-bottom: 1px dotted #dcdfe6;
  height: 1px;
  margin: 0 2px;
  min-width: 8px;
}
.filter-tip { font-size: 12px; color: #909399; }
</style>
