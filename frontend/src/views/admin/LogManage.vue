<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">日志审计</h2>
      <div>
        <el-button :icon="Download" @click="exportExcel">导出 Excel</el-button>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
      </div>
    </div>

    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="query">
        <el-form-item label="日期范围">
          <el-date-picker v-model="dateRange" type="daterange" value-format="YYYY-MM-DD"
                          start-placeholder="开始" end-placeholder="结束" style="width:240px" />
        </el-form-item>
        <template v-if="tab === 'operation'">
          <el-form-item label="模块">
            <el-select v-model="query.module" placeholder="全部" clearable style="width:120px">
              <el-option label="认证" value="auth" />
              <el-option label="系统" value="system" />
              <el-option label="教学" value="edu" />
              <el-option label="题库" value="question" />
              <el-option label="任务" value="task" />
              <el-option label="批改" value="grading" />
              <el-option label="报表" value="report" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="query.status" placeholder="全部" clearable style="width:110px">
              <el-option label="成功" value="success" />
              <el-option label="失败" value="fail" />
            </el-select>
          </el-form-item>
        </template>
        <el-form-item v-if="tab === 'login'" label="结果">
          <el-select v-model="query.status" placeholder="全部" clearable style="width:110px">
            <el-option label="成功" value="success" />
            <el-option label="失败" value="fail" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="tab === 'error'" label="级别">
          <el-select v-model="query.level" placeholder="全部" clearable style="width:110px">
            <el-option label="错误" value="ERROR" />
            <el-option label="警告" value="WARNING" />
            <el-option label="严重" value="CRITICAL" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="tab !== 'error'" label="用户名">
          <el-input v-model="query.username" placeholder="关键词" clearable style="width:130px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="load">查询</el-button>
          <el-button :icon="Refresh" @click="reset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-tabs v-model="tab" @tab-change="onTabChange">
        <el-tab-pane label="登录日志" name="login" />
        <el-tab-pane label="操作日志" name="operation" />
        <el-tab-pane label="错误日志" name="error" />
      </el-tabs>

      <el-table v-loading="loading" :data="list" border stripe>
        <template v-if="tab === 'login'">
          <el-table-column prop="username" label="用户" width="120" />
          <el-table-column prop="ip_address" label="IP 地址" width="150" />
          <el-table-column prop="location" label="归属地" width="150" />
          <el-table-column prop="login_type" label="方式" width="100" />
          <el-table-column prop="user_agent" label="客户端" min-width="220" show-overflow-tooltip />
          <el-table-column label="结果" width="90">
            <template #default="{ row }">
              <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
                {{ row.status === 'success' ? '成功' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="message" label="说明" min-width="140" show-overflow-tooltip />
          <el-table-column prop="login_at" label="时间" width="170" />
        </template>

        <template v-else-if="tab === 'operation'">
          <el-table-column prop="username" label="用户" width="110" />
          <el-table-column prop="module" label="模块" width="100" />
          <el-table-column prop="action" label="操作" width="100" />
          <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
          <el-table-column prop="method" label="方法" width="90" />
          <el-table-column prop="path" label="路径" min-width="200" show-overflow-tooltip />
          <el-table-column prop="ip_address" label="IP" width="140" />
          <el-table-column prop="duration_ms" label="耗时(ms)" width="100" />
          <el-table-column label="结果" width="80">
            <template #default="{ row }">
              <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
                {{ row.status === 'success' ? '成功' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="时间" width="170" />
        </template>

        <template v-else>
          <el-table-column prop="level" label="级别" width="100">
            <template #default="{ row }">
              <el-tag :type="{ ERROR: 'danger', CRITICAL: 'danger', WARNING: 'warning' }[row.level] || 'info'"
                      size="small">{{ row.level }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="module" label="模块" width="110" />
          <el-table-column prop="message" label="错误信息" min-width="280" show-overflow-tooltip />
          <el-table-column prop="path" label="路径" min-width="180" show-overflow-tooltip />
          <el-table-column prop="traceback" label="堆栈" min-width="240" show-overflow-tooltip />
          <el-table-column prop="created_at" label="时间" width="170" />
        </template>
      </el-table>

      <el-pagination class="mt16" background layout="total, sizes, prev, pager, next"
                     :total="total" v-model:current-page="query.page"
                     v-model:page-size="query.page_size"
                     :page-sizes="[20, 50, 100, 200]"
                     @current-change="load" @size-change="load" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Search, Refresh, Download } from '@element-plus/icons-vue'
import { logApi } from '@/api'
import { downloadBlob } from '@/utils/download'

const tab = ref('login')
const list = ref([])
const total = ref(0)
const loading = ref(false)
const dateRange = ref([])
const query = reactive({ page: 1, page_size: 20, status: '', module: '', username: '', level: '' })

const API_MAP = { login: logApi.login, operation: logApi.operation, error: logApi.error }

async function load() {
  loading.value = true
  try {
    const params = { ...query }
    if (dateRange.value?.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    const res = await API_MAP[tab.value](params)
    const d = res.data || {}
    list.value = d.items || []
    total.value = d.total || 0
  } finally {
    loading.value = false
  }
}

function onTabChange() {
  Object.assign(query, { page: 1, status: '', module: '', username: '', level: '' })
  dateRange.value = []
  load()
}

function reset() {
  Object.assign(query, { page: 1, status: '', module: '', username: '', level: '' })
  dateRange.value = []
  load()
}

async function exportExcel() {
  // 裸 URL 下载不带 Authorization（必 401）；统一走 blob + 本地 objectURL
  const label = { login: '登录日志', operation: '操作日志', error: '错误日志' }[tab.value] || '日志'
  await downloadBlob(logApi.exportExcel(tab.value), `${label}.xlsx`)
}

onMounted(load)
</script>

<style scoped>
.mt16 { margin-top: 16px; justify-content: flex-end; }
.filter-card :deep(.el-form-item) { margin-bottom: 12px; }
</style>
