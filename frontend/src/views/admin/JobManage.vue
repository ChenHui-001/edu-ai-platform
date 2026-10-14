<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">定时任务</h2>
      <div>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
        <el-button type="primary" :icon="Plus" @click="openDialog()">新增任务</el-button>
      </div>
    </div>

    <el-row :gutter="16" class="mb12">
      <el-col :span="8" v-for="s in statusCards" :key="s.label">
        <div class="stat-card">
          <div class="stat-value">{{ s.value }}</div>
          <div class="stat-label">{{ s.label }}</div>
        </div>
      </el-col>
    </el-row>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="list" border stripe>
        <el-table-column prop="name" label="任务名称" min-width="160" />
        <el-table-column prop="job_code" label="任务标识" width="160" />
        <el-table-column prop="cron_expression" label="Cron 表达式" width="160" />
        <el-table-column label="类型" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="row.is_builtin ? 'warning' : 'info'">
              {{ row.is_builtin ? '内置' : '自定义' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-switch :model-value="row.is_active" @change="toggle(row)" />
          </template>
        </el-table-column>
        <el-table-column prop="description" label="说明" min-width="200" show-overflow-tooltip />
        <el-table-column prop="last_run_at" label="上次执行" width="160" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openExecutions(row)">执行记录</el-button>
            <el-button link type="warning" @click="run(row)">立即执行</el-button>
            <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination class="mt16" background layout="total, prev, pager, next"
                     :total="total" v-model:current-page="query.page" @current-change="load" />
    </el-card>

    <el-dialog v-model="dlg" :title="form.id ? '编辑任务' : '新增任务'" width="560px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="任务名称">
          <el-input v-model="form.name" placeholder="如：错题提醒推送" />
        </el-form-item>
        <el-form-item label="任务标识">
          <el-input v-model="form.job_code" placeholder="英文标识，如 wrong_remind" />
        </el-form-item>
        <el-form-item label="Cron 表达式">
          <el-input v-model="form.cron_expression" placeholder="分 时 日 月 周，如 0 8 * * *" />
          <div class="tip">格式：秒 分 时 日 月 周（5 段：分 时 日 月 周）</div>
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.is_active" />
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

    <el-drawer v-model="execDrawer" title="任务执行记录" size="65%">
      <el-table v-loading="execLoading" :data="executions" border stripe>
        <el-table-column prop="started_at" label="开始时间" width="170" />
        <el-table-column prop="finished_at" label="结束时间" width="170" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
              {{ row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration_ms" label="耗时(ms)" width="100" />
        <el-table-column prop="result" label="执行结果" min-width="240" show-overflow-tooltip />
        <el-table-column prop="error_msg" label="错误信息" min-width="200" show-overflow-tooltip />
      </el-table>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { logApi } from '@/api'

const list = ref([])
const executions = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const dlg = ref(false)
const execDrawer = ref(false)
const execLoading = ref(false)
const scheduler = ref({})

const query = reactive({ page: 1, page_size: 20 })
const form = reactive({ id: null, name: '', job_code: '', cron_expression: '', is_active: true, description: '' })

const statusCards = computed(() => [
  { label: '调度器状态', value: scheduler.value.running ? '运行中' : '已停止' },
  { label: '任务总数', value: list.value.length },
  { label: '启用中', value: list.value.filter(j => j.is_active).length }
])

async function load() {
  loading.value = true
  try {
    const res = await logApi.jobs(query)
    const d = res.data.data || {}
    list.value = d.items || []
    total.value = d.total || 0
    const s = await logApi.schedulerStatus()
    scheduler.value = s.data.data || {}
  } finally {
    loading.value = false
  }
}

function openDialog(row) {
  Object.assign(form, row || { id: null, name: '', job_code: '', cron_expression: '', is_active: true, description: '' })
  dlg.value = true
}

async function save() {
  if (!form.name || !form.cron_expression) return ElMessage.warning('请填写任务名称与 Cron 表达式')
  saving.value = true
  try {
    if (form.id) await logApi.updateJob(form.id, form)
    else await logApi.createJob(form)
    ElMessage.success('保存成功')
    dlg.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function toggle(row) {
  await logApi.toggleJob(row.id)
  ElMessage.success(row.is_active ? '已停用' : '已启用')
  load()
}

async function run(row) {
  await ElMessageBox.confirm(`确认立即执行任务「${row.name}」？`, '提示', { type: 'info' })
  const res = await logApi.runJob(row.id)
  ElMessage.success(res.data.message || '执行完成')
  load()
}

async function remove(row) {
  await ElMessageBox.confirm(`确认删除任务「${row.name}」？`, '提示', { type: 'warning' })
  await logApi.removeJob(row.id)
  ElMessage.success('已删除')
  load()
}

async function openExecutions(row) {
  execDrawer.value = true
  execLoading.value = true
  try {
    const res = await logApi.jobExecutions(row.id, { page: 1, page_size: 100 })
    executions.value = res.data.data?.items || []
  } finally {
    execLoading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.mb12 { margin-bottom: 16px; }
.mt16 { margin-top: 16px; justify-content: flex-end; }
.tip { font-size: 12px; color: #909399; margin-top: 4px; }
</style>
