<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">注册审批</h2>
      <el-radio-group v-model="query.status">
        <el-radio-button value="pending">待审批</el-radio-button>
        <el-radio-button value="approved">已通过</el-radio-button>
        <el-radio-button value="rejected">已拒绝</el-radio-button>
        <el-radio-button value="">全部</el-radio-button>
      </el-radio-group>
    </div>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="list" border stripe>
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="real_name" label="姓名" width="100" />
        <el-table-column label="申请身份" width="100">
          <template #default="{ row }">
            <el-tag :type="row.identity === 'teacher' ? 'success' : 'info'" size="small">
              {{ row.identity === 'teacher' ? '教师' : '学生' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="grade_name" label="年级" width="100" />
        <el-table-column prop="class_name" label="班级" width="120" />
        <el-table-column prop="phone" label="手机号" width="130" />
        <el-table-column prop="email" label="邮箱" min-width="180" show-overflow-tooltip />
        <el-table-column prop="reason" label="申请理由" min-width="160" show-overflow-tooltip />
        <el-table-column prop="created_at" label="申请时间" width="160" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="{ pending: 'warning', approved: 'success', rejected: 'danger' }[row.status]" size="small">
              {{ { pending: '待审批', approved: '已通过', rejected: '已拒绝' }[row.status] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'pending'">
              <el-button link type="success" @click="audit(row, 'approved')">通过</el-button>
              <el-button link type="danger" @click="audit(row, 'rejected')">拒绝</el-button>
            </template>
            <el-button v-else link type="primary" @click="detail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination class="mt16" background layout="total, prev, pager, next"
                     :total="total" v-model:current-page="query.page"
                     @current-change="load" />
    </el-card>

    <el-dialog v-model="dlg" title="注册申请详情" width="640px">
      <el-descriptions :column="2" border v-if="current">
        <el-descriptions-item label="用户名">{{ current.username }}</el-descriptions-item>
        <el-descriptions-item label="姓名">{{ current.real_name }}</el-descriptions-item>
        <el-descriptions-item label="身份">{{ current.identity === 'teacher' ? '教师' : '学生' }}</el-descriptions-item>
        <el-descriptions-item label="年级">{{ current.grade_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="班级">{{ current.class_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="手机号">{{ current.phone }}</el-descriptions-item>
        <el-descriptions-item label="邮箱" :span="2">{{ current.email }}</el-descriptions-item>
        <el-descriptions-item label="申请理由" :span="2">{{ current.reason || '-' }}</el-descriptions-item>
        <el-descriptions-item label="审核意见" :span="2">{{ current.audit_remark || '-' }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="dlg = false">关闭</el-button>
        <template v-if="current && current.status === 'pending'">
          <el-button type="danger" @click="audit(current, 'rejected')">拒绝</el-button>
          <el-button type="primary" @click="audit(current, 'approved')">通过并创建账号</el-button>
        </template>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api'

const list = ref([])
const total = ref(0)
const loading = ref(false)
const dlg = ref(false)
const current = ref(null)
const query = reactive({ page: 1, page_size: 20, status: 'pending' })

async function load() {
  loading.value = true
  try {
    const res = await authApi.registrations(query)
    const d = res.data || {}
    list.value = d.items || []
    total.value = d.total || 0
  } finally {
    loading.value = false
  }
}

function detail(row) {
  current.value = row
  dlg.value = true
}

async function audit(row, action) {
  const remark = await new Promise(resolve => {
    let v = ''
    // 简单提示：直接提交，可在详情里补录意见
    resolve(v)
  })
  await authApi.auditRegistration({ id: row.id, action, remark })
  ElMessage.success(action === 'approved' ? '已通过，账号已创建' : '已拒绝')
  dlg.value = false
  load()
}

onMounted(load)
</script>

<style scoped>
.mt16 { margin-top: 16px; justify-content: flex-end; }
</style>
