<template>
  <div class="prereq-block mt12">
    <div class="toolbar">
      <div class="title-wrap">
        <b class="title">先修关系</b>
        <el-tag size="small" type="info" effect="plain">
          {{ prereqList.length }} 先修 / {{ dependentList.length }} 后继
        </el-tag>
        <span class="muted hint">先修关系独立于教材层级，用于诊断时向下回溯基础</span>
      </div>
      <div class="actions">
        <el-button v-if="canWrite" type="primary" :icon="Plus" :disabled="!subjectName"
                   @click="openDialog">新增先修</el-button>
        <el-button :icon="Refresh" :loading="loading" @click="loadRelations">刷新</el-button>
      </div>
    </div>

    <el-row :gutter="16" v-loading="loading">
      <el-col :span="12">
        <div class="rel-title">先修（前置知识点）</div>
        <div v-if="prereqList.length" class="rel-list">
          <div v-for="p in prereqList" :key="p.id" class="rel-item">
            <el-tag size="small" :type="p.strength === 'hard' ? 'danger' : 'info'"
                    effect="plain">
              {{ p.strength === 'hard' ? '硬先修' : '软先修' }}
            </el-tag>
            <div class="rel-main">
              <span class="rel-name">{{ p.name }}</span>
              <span class="tip">L{{ p.grade_num ?? '-' }} · {{ p.reason || '无说明' }}</span>
            </div>
            <el-button v-if="canWrite" text type="danger" size="small"
                       @click="removeEdge(p)">删除</el-button>
          </div>
        </div>
        <el-empty v-else description="暂无先修知识点" :image-size="50" />
      </el-col>
      <el-col :span="12">
        <div class="rel-title">后继（依赖当前节点）</div>
        <div v-if="dependentList.length" class="rel-list">
          <div v-for="d in dependentList" :key="d.id" class="rel-item">
            <el-tag size="small" :type="d.strength === 'hard' ? 'danger' : 'info'"
                    effect="plain">
              {{ d.strength === 'hard' ? '硬依赖' : '软依赖' }}
            </el-tag>
            <div class="rel-main">
              <span class="rel-name">{{ d.name }}</span>
              <span class="tip">L{{ d.grade_num ?? '-' }} · {{ d.reason || '无说明' }}</span>
            </div>
          </div>
        </div>
        <el-empty v-else description="暂无后继知识点" :image-size="50" />
      </el-col>
    </el-row>

    <el-dialog v-model="dialogVisible" title="新增先修关系" width="560px" destroy-on-close>
      <el-form label-width="96px">
        <el-form-item label="当前知识点">
          <el-input :model-value="kpName" disabled />
        </el-form-item>
        <el-form-item label="先修知识点">
          <el-select v-model="form.prerequisite_id" filterable clearable
                     placeholder="搜索同科知识点" style="width:100%">
            <el-option v-for="c in candidates" :key="c.id" :value="c.id"
                       :label="`${c.name}（${c.grade_name || ('L' + c.grade_id)}）`" />
          </el-select>
        </el-form-item>
        <el-form-item label="强度">
          <el-radio-group v-model="form.strength">
            <el-radio value="hard">硬先修（诊断必须回溯）</el-radio>
            <el-radio value="soft">软先修（建议掌握）</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="原因">
          <el-input v-model="form.reason" type="textarea" :rows="2"
                    maxlength="2000" show-word-limit placeholder="可选，说明为什么需要先掌握" />
        </el-form-item>
        <el-alert v-if="crossGrade" type="warning" :closable="false" show-icon
                  title="所选先修点跨年级，保存时会要求二次确认" />
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" :disabled="!form.prerequisite_id"
                   @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { knowledgeApi } from '@/api'
import { confirmAction } from '@/utils/confirm'

const props = defineProps({
  kpId: { type: Number, required: true },
  kpName: { type: String, default: '' },
  subjectName: { type: String, default: '' },
  gradeId: { type: Number, default: null },
  canWrite: { type: Boolean, default: false }
})

const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const prereqList = ref([])
const dependentList = ref([])
const candidates = ref([])
const form = reactive({ prerequisite_id: null, strength: 'hard', reason: '' })

const crossGrade = computed(() => {
  const hit = candidates.value.find(c => c.id === form.prerequisite_id)
  return Boolean(hit && props.gradeId && hit.grade_id !== props.gradeId)
})

function normalize(data) {
  return Array.isArray(data) ? data : (data?.items || [])
}

async function loadRelations() {
  if (!props.kpId) return
  loading.value = true
  const kpId = props.kpId
  try {
    const [pre, dep] = await Promise.all([
      knowledgeApi.prerequisites(kpId),
      knowledgeApi.dependents(kpId)
    ])
    if (props.kpId !== kpId) return
    prereqList.value = pre.data?.items || []
    dependentList.value = dep.data?.items || []
  } catch {
    if (props.kpId === kpId) {
      prereqList.value = []
      dependentList.value = []
    }
  } finally {
    loading.value = false
  }
}

async function openDialog() {
  form.prerequisite_id = null
  form.strength = 'hard'
  form.reason = ''
  dialogVisible.value = true
  try {
    const res = await knowledgeApi.list({
      subject_name: props.subjectName,
      status: 'published'
    })
    const existing = new Set(prereqList.value.map(p => p.id))
    candidates.value = normalize(res.data)
      .filter(c => c.id !== props.kpId && !existing.has(c.id))
  } catch {
    candidates.value = []
    ElMessage.error('先修知识点列表加载失败')
  }
}

async function save() {
  if (!form.prerequisite_id) return
  if (crossGrade.value) {
    const okToContinue = await confirmAction(
      '所选先修知识点不在当前年级，确认建立跨年级先修关系？',
      '跨年级先修确认',
      { confirmButtonText: '确认建立' }
    )
    if (!okToContinue) return
  }
  saving.value = true
  try {
    await knowledgeApi.addPrerequisite(props.kpId, {
      prerequisite_id: form.prerequisite_id,
      strength: form.strength,
      reason: form.reason || undefined,
      allow_cross_grade: crossGrade.value
    })
    ElMessage.success('先修关系已新增')
    dialogVisible.value = false
    await loadRelations()
  } catch {
    // 统一错误拦截器已提示，保留弹窗便于修改
  } finally {
    saving.value = false
  }
}

async function removeEdge(row) {
  const okToRemove = await confirmAction(
    `确认删除「${row.name}」先修关系？`, '删除先修关系',
    { confirmButtonText: '删除', type: 'warning' }
  )
  if (!okToRemove) return
  try {
    await knowledgeApi.removePrerequisite(props.kpId, row.id)
    ElMessage.success('先修关系已删除')
    await loadRelations()
  } catch {
    // 统一错误拦截器已提示
  }
}

watch(() => props.kpId, () => {
  dialogVisible.value = false
  loadRelations()
}, { immediate: true })
</script>

<style scoped>
.mt12 { margin-top: 12px; }
.muted { color: var(--el-text-color-secondary); }
.tip { color: var(--el-text-color-secondary); font-size: 12px; }
.prereq-block {
  padding-top: 12px;
  border-top: 1px dashed var(--el-border-color-lighter);
}
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}
.title-wrap { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; min-width: 0; }
.title { font-size: 14px; color: var(--el-text-color-primary); }
.hint { line-height: 1.4; }
.actions { display: flex; align-items: center; gap: 8px; }
.actions :deep(.el-button + .el-button) { margin-left: 0; }
.rel-title {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--el-text-color-regular);
}
.rel-list { display: flex; flex-direction: column; gap: 6px; }
.rel-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
}
.rel-main { display: flex; flex-direction: column; gap: 2px; min-width: 0; flex: 1; }
.rel-name { font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>
