<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">{{ typeName }}管理</h2>
      <div>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
        <el-button type="primary" :icon="Plus" @click="openDialog()">新增{{ typeName }}</el-button>
      </div>
    </div>

    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="query">
        <el-form-item label="关键词">
          <el-input v-model="query.keyword" placeholder="名称" clearable style="width:180px"
                    @keyup.enter="load" />
        </el-form-item>
        <el-form-item v-if="isSubject" label="所属年级">
          <el-select v-model="query.grade_id" placeholder="全部" clearable style="width:140px">
            <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="load">查询</el-button>
          <el-button :icon="Refresh" @click="reset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="list" border stripe>
        <el-table-column prop="sort_order" label="排序" width="70" align="center" />
        <el-table-column prop="name" label="名称" min-width="160" />
        <el-table-column v-if="isSubject" prop="grade_name" label="所属年级" width="140" />
        <el-table-column prop="description" label="说明" min-width="200" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="160" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
              {{ row.status === 'active' ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination class="mt16" background layout="total, prev, pager, next"
                     :total="total" v-model:current-page="query.page"
                     @current-change="load" />
    </el-card>

    <el-dialog v-model="dlg" :title="`${form.id ? '编辑' : '新增'}${typeName}`" width="480px">
      <el-form :model="form" label-width="90px">
        <el-form-item v-if="isSubject" label="所属年级">
          <el-select v-model="form.grade_id" style="width:100%">
            <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" :max="999" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.active" active-text="启用" inactive-text="停用" />
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
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import { eduApi } from '@/api'

const route = useRoute()
const isSubject = computed(() => route.name === 'SubjectManage')
const typeName = computed(() => (isSubject.value ? '学科' : '年级'))

const list = ref([])
const grades = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const dlg = ref(false)
const query = reactive({ page: 1, page_size: 50, keyword: '', grade_id: null })
const form = reactive({ id: null, name: '', grade_id: null, sort_order: 0, active: true, description: '' })

async function load() {
  loading.value = true
  try {
    const api = isSubject.value ? eduApi.subjects : eduApi.grades
    const res = await api(query)
    const d = res.data.data || {}
    list.value = d.items || []
    total.value = d.total || 0
  } finally {
    loading.value = false
  }
}

function reset() {
  Object.assign(query, { page: 1, keyword: '', grade_id: null })
  load()
}

function openDialog(row) {
  Object.assign(form, row
    ? { ...row, active: row.status === 'active' }
    : { id: null, name: '', grade_id: null, sort_order: 0, active: true, description: '' })
  dlg.value = true
}

async function save() {
  if (!form.name) return ElMessage.warning('请输入名称')
  saving.value = true
  const payload = { ...form, status: form.active ? 'active' : 'inactive' }
  delete payload.active
  try {
    const api = isSubject.value ? eduApi : eduApi
    if (form.id) await (isSubject.value ? eduApi.updateSubject(form.id, payload) : eduApi.updateGrade(form.id, payload))
    else await (isSubject.value ? eduApi.createSubject(payload) : eduApi.createGrade(payload))
    ElMessage.success('保存成功')
    dlg.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function remove(row) {
  await ElMessageBox.confirm(`确认删除「${row.name}」？`, '提示', { type: 'warning' })
  if (isSubject.value) await eduApi.deleteSubject(row.id)
  else await eduApi.deleteGrade(row.id)
  ElMessage.success('已删除')
  load()
}

watch(() => route.name, () => load())

onMounted(async () => {
  await load()
  if (isSubject.value) {
    const g = await eduApi.grades()
    grades.value = g.data.data || []
  }
})
</script>

<style scoped>
.mt16 { margin-top: 16px; justify-content: flex-end; }
</style>
