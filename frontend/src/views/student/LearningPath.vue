<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">学习路径</h2>
      <div>
        <el-select v-model="subjectFilter" placeholder="全部学科" clearable style="width:140px"
                   @change="load">
          <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
        </el-select>
        <el-button :icon="Refresh" @click="load" class="ml8">刷新</el-button>
      </div>
    </div>

    <el-row :gutter="16" class="mb16" v-loading="loading">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-value">{{ data.avg_mastery || 0 }}%</div>
          <div class="stat-label">平均掌握度</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-value" style="color:#f56c6c">{{ data.weak_count || 0 }}</div>
          <div class="stat-label">薄弱知识点</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-value" style="color:#67c23a">{{ data.mastered_count || 0 }}</div>
          <div class="stat-label">已精通知识点</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-value">{{ data.total_kps || 0 }}</div>
          <div class="stat-label">学习知识点总数</div>
        </div>
      </el-col>
    </el-row>

    <el-card shadow="never" class="mb16" v-if="data.ai_advice">
      <template #header>
        <div class="flex-between">
          <b>AI 学习建议</b>
          <el-tag type="success" size="small" effect="dark" round>智能推荐</el-tag>
        </div>
      </template>
      <div class="ai-advice">{{ data.ai_advice }}</div>
    </el-card>

    <el-empty v-if="!loading && !data.recommendations?.length"
              description="暂无学习数据，先去练习几道题吧" :image-size="80" />

    <div v-if="data.recommendations?.length" class="path-timeline">
      <div v-for="(rec, idx) in data.recommendations" :key="rec.knowledge_point_id"
           class="path-node" :class="rec.priority.toLowerCase()">
        <div class="path-connector" v-if="idx < data.recommendations.length - 1"></div>
        <div class="path-circle">{{ idx + 1 }}</div>
        <div class="path-content">
          <el-card shadow="never" class="path-card">
            <div class="path-head">
              <b class="path-name">{{ rec.name }}</b>
              <el-tag size="small" :type="priorityType(rec.priority)">{{ rec.priority }}优先</el-tag>
              <span class="mastery-badge" :style="{ background: masteryColor(rec.mastery) }">
                {{ rec.mastery }}%
              </span>
            </div>
            <p class="path-desc" v-if="rec.description">{{ rec.description }}</p>
            <div class="path-stats">
              <span>做题 {{ rec.total_count }} 道</span>
              <span>正确 {{ rec.correct_count }} 道</span>
              <span>错误 {{ rec.wrong_count }} 道</span>
            </div>
            <div class="path-action">
              <el-icon><Aim /></el-icon>
              <span>{{ rec.recommended_action }}</span>
            </div>
            <el-button type="primary" size="small" @click="practice(rec)">
              去练习（{{ rec.recommended_difficulty === 'easy' ? '基础' : rec.recommended_difficulty === 'medium' ? '中等' : '困难' }}）
            </el-button>
          </el-card>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Refresh, Aim } from '@element-plus/icons-vue'
import { learningApi } from '@/api'
import { fetchSubjects, currentGradeId, resolveSubjectId } from '@/utils/subject'

const router = useRouter()
const loading = ref(false)
const data = ref({})
const subjects = ref([])
const subjectFilter = ref(null)

function priorityType(p) {
  return { '高': 'danger', '中': 'warning', '低': 'success' }[p] || 'info'
}

function masteryColor(v) {
  if (v >= 80) return '#67c23a'
  if (v >= 60) return '#e6a23c'
  if (v >= 40) return '#f0a020'
  return '#f56c6c'
}

async function load() {
  loading.value = true
  try {
    // 去重代表 id 指向最低年级，直接查会得到空的学习路径
    const sid = resolveSubjectId(subjects.value, subjectFilter.value, currentGradeId())
    const res = await learningApi.learningPath(sid ? { subject_id: sid } : {})
    data.value = res.data
  } finally {
    loading.value = false
  }
}

async function loadSubjects() {
  subjects.value = await fetchSubjects({ gradeId: currentGradeId() })
}

function practice(rec) {
  router.push({ path: '/student/practice', query: { kp: rec.knowledge_point_id, subject: rec.subject_id } })
}

onMounted(async () => {
  await loadSubjects()
  await load()
})
</script>

<style scoped>
.mb16 { margin-bottom: 16px; }
.ml8 { margin-left: 8px; }
.stat-card { text-align: center; padding: 16px; background: #f5f7fa; border-radius: 8px; }
.stat-value { font-size: 28px; font-weight: 700; color: #409eff; }
.stat-label { font-size: 12px; color: #909399; margin-top: 4px; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
.ai-advice { font-size: 14px; line-height: 1.8; color: #303133; white-space: pre-wrap; }
.path-timeline { display: flex; flex-direction: column; gap: 0; }
.path-node { display: flex; gap: 16px; position: relative; padding-bottom: 24px; }
.path-connector { position: absolute; left: 16px; top: 32px; bottom: 0; width: 2px; background: #dcdfe6; }
.path-circle { width: 32px; height: 32px; border-radius: 50%; background: #409eff; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; flex-shrink: 0; z-index: 1; }
.path-node.高 .path-circle { background: #f56c6c; }
.path-node.中 .path-circle { background: #e6a23c; }
.path-node.低 .path-circle { background: #67c23a; }
.path-content { flex: 1; }
.path-card { width: 100%; }
.path-head { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.path-name { font-size: 15px; }
.mastery-badge { color: #fff; font-size: 11px; padding: 2px 8px; border-radius: 10px; margin-left: auto; }
.path-desc { font-size: 13px; color: #606266; margin: 8px 0; }
.path-stats { display: flex; gap: 16px; font-size: 12px; color: #909399; margin: 8px 0; }
.path-action { display: flex; align-items: center; gap: 6px; font-size: 14px; color: #409eff; margin: 8px 0 12px; }
</style>
