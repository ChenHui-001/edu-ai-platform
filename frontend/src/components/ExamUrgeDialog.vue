<template>
  <el-dialog v-model="visible" :title="dialogTitle" width="640px">
    <div v-loading="loading">
      <el-alert v-if="info" type="info" :closable="false" show-icon class="mb12">
        应交 {{ info.total_assigned }} 人 · 已交 {{ info.total_submitted }} 人 ·
        待交 <b>{{ info.total_pending }}</b> 人
      </el-alert>

      <el-empty v-if="!loading && !students.length" description="没有待交学生" :image-size="70" />

      <template v-else>
        <div class="toolbar">
          <el-button size="small" @click="selectAll">全选待交</el-button>
          <el-button size="small" @click="clearAll">清空</el-button>
          <span class="muted">已选 {{ selected.length }} 人</span>
        </div>
        <el-table :data="students" border size="small" max-height="320">
          <el-table-column type="selection" width="44" :selectable="() => true" />
          <el-table-column prop="name" label="学生" min-width="140">
            <template #default="{ row }">{{ row.name || '未命名' }}</template>
          </el-table-column>
        </el-table>

        <el-form label-width="90px" class="mt12">
          <el-form-item label="催交留言">
            <el-input v-model="comment" type="textarea" :rows="2" maxlength="500"
                      show-word-limit placeholder="选填，会附在通知里" />
          </el-form-item>
        </el-form>
      </template>
    </div>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="danger" :loading="submitting" :disabled="!students.length"
                 @click="submit">确定催交</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { taskApi } from '@/api'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  // 被催办的考试/作业；为空时组件不工作
  task: { type: Object, default: null }
})
const emit = defineEmits(['update:modelValue', 'done'])

const visible = ref(false)
const loading = ref(false)
const submitting = ref(false)
const students = ref([])
const selected = ref([])
const comment = ref('')
const info = ref(null)

const dialogTitle = computed(() =>
  props.task ? `催交：${props.task.title}` : '催交考试 / 作业')

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) load()
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

async function load() {
  if (!props.task?.id) return
  loading.value = true
  students.value = []
  selected.value = []
  info.value = null
  try {
    const res = await taskApi.pendingStudents(props.task.id)
    const data = res.data || {}
    students.value = data.students || []
    info.value = {
      total_assigned: data.total_assigned ?? 0,
      total_submitted: data.total_submitted ?? 0,
      total_pending: data.total_pending ?? 0
    }
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '加载待交名单失败')
  } finally {
    loading.value = false
  }
}

function selectAll() {
  selected.value = students.value.map(s => s.id)
}

function clearAll() {
  selected.value = []
}

async function submit() {
  if (!props.task?.id) return
  submitting.value = true
  try {
    const res = await taskApi.urge(props.task.id, {
      student_ids: selected.value,
      comment: comment.value
    })
    const d = res.data || {}
    const skipped = d.skipped || 0
    if (skipped > 0) {
      ElMessage.warning(`已催办 ${d.urged || 0} 人，跳过 ${skipped} 人（已交卷或超上限）`)
    } else {
      ElMessage.success(`已催办 ${d.urged || 0} 人`)
    }
    visible.value = false
    emit('done', d)
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '催交失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.mb12 {
  margin-bottom: 12px;
}
.mt12 {
  margin-top: 12px;
}
.toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.toolbar :deep(.el-button + .el-button) {
  margin-left: 0;
}
.muted {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}
</style>
