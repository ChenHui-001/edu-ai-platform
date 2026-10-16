<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">知识点管理</h2>
      <div>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
        <el-button :icon="MagicStick" :loading="reindexing" @click="reindex">重建向量索引</el-button>
        <el-button v-if="can('resource:knowledge:write')" type="primary" :icon="Plus" @click="openDialog()">新增知识点</el-button>
      </div>
    </div>

    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="query">
        <el-form-item label="年级">
          <el-select v-model="query.grade_id" placeholder="全部" clearable style="width:130px"
                     @change="onGradeChange">
            <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="学科">
          <el-select v-model="query.subject_id" placeholder="全部" clearable style="width:130px">
            <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="query.keyword" placeholder="知识点名称" clearable style="width:160px"
                    @keyup.enter="load" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="load">查询</el-button>
          <el-button :icon="Refresh" @click="reset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="tree" row-key="id" border stripe
                :tree-props="{ children: 'children' }" default-expand-all>
        <el-table-column prop="name" label="知识点名称" min-width="260" />
        <el-table-column prop="code" label="编码" width="160" />
        <el-table-column label="层级" width="80" align="center">
          <template #default="{ row }">L{{ row.level }}</template>
        </el-table-column>
        <el-table-column prop="description" label="说明" min-width="200" show-overflow-tooltip />
        <el-table-column prop="sort_order" label="排序" width="70" align="center" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button v-if="can('resource:knowledge:write')" link type="primary" @click="openDialog(null, row)">添加子级</el-button>
            <el-button v-if="can('resource:knowledge:write')" link type="primary" @click="openDialog(row)">编辑</el-button>
            <el-button v-if="can('resource:knowledge:write')" link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dlg" :title="form.id ? '编辑知识点' : '新增知识点'" width="560px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="所属年级">
          <el-select v-model="form.grade_id" style="width:100%" @change="onFormGradeChange">
            <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属学科">
          <el-select v-model="form.subject_id" style="width:100%">
            <el-option v-for="s in formSubjects" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="上级知识点">
          <el-cascader v-model="cascader" :options="cascaderOptions" clearable
                       placeholder="不选则为顶级" style="width:100%" />
        </el-form-item>
        <el-form-item label="名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="编码">
          <el-input v-model="form.code" placeholder="如：MATH-FUNC-01" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" :max="999" />
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
const { can } = useUserStore()
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, MagicStick } from '@element-plus/icons-vue'
import { eduApi } from '@/api'
import { useUserStore } from '@/store/user'

const tree = ref([])
const grades = ref([])
const subjects = ref([])
const loading = ref(false)
const saving = ref(false)
const dlg = ref(false)
const reindexing = ref(false)
const cascader = ref([])

const query = reactive({ grade_id: null, subject_id: null, keyword: '' })
const form = reactive({ id: null, name: '', code: '', grade_id: null, subject_id: null,
  parent_id: null, sort_order: 0, description: '' })

const formSubjects = computed(() => {
  if (!form.grade_id) return subjects.value
  return subjects.value.filter(s => !s.grade_id || s.grade_id === form.grade_id)
})

const cascaderOptions = computed(() => buildOptions(tree.value))

function buildOptions(nodes, excludeId = null) {
  return nodes
    .filter(n => n.id !== excludeId)
    .map(n => ({ value: n.id, label: n.name, children: buildOptions(n.children || [], excludeId) }))
}

async function load() {
  loading.value = true
  try {
    const res = await eduApi.knowledge(query)
    tree.value = res.data.data || []
  } finally {
    loading.value = false
  }
}

function reset() {
  Object.assign(query, { grade_id: null, subject_id: null, keyword: '' })
  load()
}

function onGradeChange() { load() }
function onFormGradeChange() { form.subject_id = null }

function openDialog(row, parent) {
  cascader.value = []
  Object.assign(form, {
    id: row?.id || null,
    name: '', code: '',
    grade_id: row?.grade_id || query.grade_id || null,
    subject_id: row?.subject_id || query.subject_id || null,
    parent_id: parent?.id || null,
    sort_order: row?.sort_order ?? 0,
    description: row?.description || ''
  })
  if (parent) cascader.value = [parent.id]
  dlg.value = true
}

async function save() {
  if (!form.name) return ElMessage.warning('请输入知识点名称')
  saving.value = true
  try {
    const payload = { ...form, parent_id: cascader.value.length ? cascader.value[cascader.value.length - 1] : null }
    if (form.id) await eduApi.updateKnowledge(form.id, payload)
    else await eduApi.createKnowledge(payload)
    ElMessage.success('保存成功')
    dlg.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function remove(row) {
  await ElMessageBox.confirm(`确认删除知识点「${row.name}」及其所有子级？`, '提示', { type: 'warning' })
  await eduApi.deleteKnowledge(row.id)
  ElMessage.success('已删除')
  load()
}

async function reindex() {
  reindexing.value = true
  try {
    const res = await eduApi.reindex()
    ElMessage.success(res.data.message || '向量索引重建完成')
  } finally {
    reindexing.value = false
  }
}

onMounted(async () => {
  await load()
  const [g, s] = await Promise.all([eduApi.grades(), eduApi.subjects()])
  grades.value = g.data.data || []
  subjects.value = s.data.data || []
})
</script>

<style scoped>
.filter-card :deep(.el-form-item) { margin-bottom: 12px; }
</style>
