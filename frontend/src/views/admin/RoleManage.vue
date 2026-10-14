<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">角色与权限</h2>
      <div>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
        <el-button type="primary" :icon="Plus" @click="openDialog()">新增角色</el-button>
      </div>
    </div>

    <el-row :gutter="16">
      <!-- 角色列表 -->
      <el-col :span="9">
        <el-card shadow="never" v-loading="loading">
          <template #header><b>角色列表（{{ roles.length }}）</b></template>
          <el-table :data="roles" border stripe highlight-current-row @current-change="selectRole">
            <el-table-column prop="name" label="角色名称" />
            <el-table-column prop="code" label="角色标识" width="140" />
            <el-table-column label="用户数" width="80" align="center">
              <template #default="{ row }">{{ row.user_count ?? 0 }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 权限配置 -->
      <el-col :span="15">
        <el-card shadow="never">
          <template #header>
            <div class="flex-between">
              <b>{{ current ? `${current.name} - 权限配置` : '权限配置' }}</b>
              <div v-if="current && !current.builtin">
                <el-button size="small" :icon="DocumentCopy" @click="copyRole">复制角色</el-button>
                <el-button size="small" type="primary" :icon="Edit" @click="openDialog(current)">编辑</el-button>
                <el-button size="small" type="danger" :icon="Delete" @click="remove">删除</el-button>
              </div>
              <el-tag v-else-if="current" type="info">内置角色不可修改</el-tag>
            </div>
          </template>

          <el-alert v-if="!current" type="info" :closable="false" title="请先在左侧选择一个角色" />

          <el-tree v-else ref="treeRef" :data="permTree" show-checkbox node-key="key"
                   :props="{ label: 'label', children: 'children' }"
                   :default-checked-keys="checkedKeys" check-strictly
                   :default-expanded-keys="expandedKeys" class="perm-tree">
            <template #default="{ data }">
              <span>
                {{ data.label }}
                <el-tag v-if="data.type !== 'menu'" size="small" type="info" effect="plain" class="ml8">
                  {{ data.code }}
                </el-tag>
              </span>
            </template>
          </el-tree>

          <div class="mt16" v-if="current && !current.builtin">
            <el-button @click="treeRef?.setCheckedKeys([])">清空</el-button>
            <el-button @click="toggleExpandAll(true)">展开全部</el-button>
            <el-button @click="toggleExpandAll(false)">折叠全部</el-button>
            <el-button type="primary" :icon="Check" :loading="saving" @click="savePerm">保存权限</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="dlg" :title="form.id ? '编辑角色' : '新增角色'" width="480px">
      <el-form :model="form" :rules="rules" label-width="90px">
        <el-form-item label="角色名称" prop="name">
          <el-input v-model="form.name" placeholder="如：备课组长" />
        </el-form-item>
        <el-form-item label="角色标识" prop="code">
          <el-input v-model="form.code" placeholder="如：lesson_leader" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
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
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Edit, Delete, Check, DocumentCopy } from '@element-plus/icons-vue'
import { systemApi } from '@/api'

const roles = ref([])
const permTree = ref([])
const current = ref(null)
const checkedKeys = ref([])
const expandedKeys = ref([])
const loading = ref(false)
const saving = ref(false)
const dlg = ref(false)
const treeRef = ref(null)

const form = reactive({ id: null, name: '', code: '', remark: '' })
const rules = {
  name: [{ required: true, message: '请输入角色名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入角色标识', trigger: 'blur' }]
}

function selectRole(row) {
  if (!row) return
  current.value = row
  if (row.permissions) {
    checkedKeys.value = row.permissions.map(p => p.code || p)
  } else {
    loadRolePerm(row.id)
  }
}

async function loadRolePerm(roleId) {
  const res = await systemApi.permissions({ role_id: roleId })
  const items = res.data.data?.items || []
  checkedKeys.value = items.map(p => p.code)
}

async function load() {
  loading.value = true
  try {
    const res = await systemApi.roles()
    roles.value = res.data.data || []
    await loadPermTree()
  } finally {
    loading.value = false
  }
}

async function loadPermTree() {
  const res = await systemApi.permissions({ tree: true })
  permTree.value = res.data.data || []
  // 默认展开前两层
  expandedKeys.value = []
  const walk = (nodes, depth) => {
    nodes.forEach(n => {
      if (depth <= 1 && n.children) expandedKeys.value.push(n.key)
      if (n.children) walk(n.children, depth + 1)
    })
  }
  walk(permTree.value, 0)
}

function toggleExpandAll(open) {
  const ids = []
  const walk = nodes => nodes.forEach(n => {
    ids.push(n.key)
    if (n.children) walk(n.children)
  })
  walk(permTree.value)
  treeRef.value?.setExpandedNodes(open ? ids : [])
}

async function savePerm() {
  saving.value = true
  try {
    const checked = treeRef.value.getCheckedKeys()
    const half = treeRef.value.getHalfCheckedKeys()
    const codes = [...checked, ...half].filter(k => !k.includes(':group:'))
    await systemApi.updateRole(current.value.id, { ...current.value, permission_codes: codes })
    ElMessage.success('权限已保存')
    await load()
  } finally {
    saving.value = false
  }
}

function openDialog(row) {
  Object.assign(form, row || { id: null, name: '', code: '', remark: '' })
  dlg.value = true
}

async function save() {
  saving.value = true
  try {
    if (form.id) await systemApi.updateRole(form.id, form)
    else await systemApi.createRole(form)
    ElMessage.success('保存成功')
    dlg.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function copyRole() {
  const { name } = await ElMessageBox.prompt('请输入新角色名称', '复制角色', {
    inputValue: `${current.value.name} - 副本`
  })
  await systemApi.copyRole(current.value.id, { name })
  ElMessage.success('复制成功')
  load()
}

async function remove() {
  await ElMessageBox.confirm(`确认删除角色「${current.value.name}」？`, '提示', { type: 'warning' })
  await systemApi.deleteRole(current.value.id)
  ElMessage.success('已删除')
  current.value = null
  load()
}

onMounted(load)
</script>

<style scoped>
.flex-between { display: flex; align-items: center; justify-content: space-between; }
.perm-tree { max-height: 560px; overflow: auto; }
.ml8 { margin-left: 8px; }
.mt16 { margin-top: 16px; display: flex; gap: 8px; }
</style>
