<template>
  <div class="page-container" v-loading="loading">
    <div class="page-header"><h2>上游数学数据同步</h2><el-button @click="load">刷新历史</el-button></div>
    <el-alert type="info" :closable="false" title="数据来源 cn-math-taxonomy，许可 CC BY-NC 4.0。同步前预览，写入前备份，恢复仅作用于上游数学数据。" />
    <el-card shadow="never" class="mt12">
      <el-form :inline="true">
        <el-form-item label="分支、标签或提交"><el-input v-model="refName" placeholder="main 或提交 SHA" /></el-form-item>
        <el-button type="primary" :loading="loading" @click="preview">检查上游变更</el-button>
      </el-form>
      <template v-if="current">
        <p>固定版本：{{ current.source_commit }}</p>
        <p>知识点 {{ current.report.knowledge }} · 题目 {{ current.report.questions }} · 先修关系 {{ current.report.edges }}</p>
        <p>知识点：新增 {{ current.report.added_knowledge }} / 更新 {{ current.report.updated_knowledge }} / 归档 {{ current.report.archived_knowledge }}</p>
        <p>题目：新增 {{ current.report.added_questions }} / 更新 {{ current.report.updated_questions }} / 下架 {{ current.report.archived_questions }}</p>
        <p>先修关系：新增 {{ current.report.added_edges }} / 更新 {{ current.report.updated_edges }} / 删除 {{ current.report.removed_edges }}</p>
        <el-alert v-for="issue in current.report.errors" :key="issue" :title="issue" type="error" :closable="false" />
        <el-button type="primary" :disabled="current.report.errors.length > 0 || current.status !== 'preview'" @click="apply">备份并同步此版本</el-button>
      </template>
    </el-card>
    <ErrorState v-if="error" :message="error" @retry="load" />
    <el-table :data="history" class="mt12">
      <el-table-column prop="id" label="记录" width="75" />
      <el-table-column prop="source_commit" label="上游提交" min-width="180" show-overflow-tooltip />
      <el-table-column prop="status" label="状态" width="110" />
      <el-table-column prop="created_at" label="时间" min-width="170" />
      <el-table-column label="操作" width="150"><template #default="{ row }">
        <el-button v-if="row.status === 'preview'" size="small" @click="current = row">查看预览</el-button>
        <el-button v-if="row.status === 'applied'" size="small" type="warning" @click="restore(row)">恢复同步前</el-button>
      </template></el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { extensionApi } from '@/api/extensions'
import { confirmAction } from '@/utils/confirm'
import ErrorState from '@/components/ErrorState.vue'
const refName = ref('main')
const history = ref([])
const current = ref(null)
const loading = ref(false)
const error = ref('')
async function load() {
  loading.value = true; error.value = ''
  try { history.value = (await extensionApi.syncHistory()).data.items }
  catch { error.value = '同步记录读取失败，请重试' }
  finally { loading.value = false }
}
async function preview() {
  loading.value = true; error.value = ''
  try { current.value = (await extensionApi.syncPreview(refName.value)).data; await load() }
  catch { error.value = '上游检查失败，请确认版本名称和网络后重试' }
  finally { loading.value = false }
}
async function apply() {
  if (!await confirmAction('确认备份并同步预览中的固定版本？上游已删除的内容会归档。')) return
  loading.value = true
  try { current.value = (await extensionApi.syncApply(current.value.id)).data; ElMessage.success('同步完成'); await load() }
  finally { loading.value = false }
}
async function restore(row) {
  if (!await confirmAction('确认将上游数学数据恢复到此次同步前？其他业务数据不受影响。')) return
  loading.value = true
  try { await extensionApi.syncRestore(row.id); ElMessage.success('已恢复同步前的数据'); await load() }
  finally { loading.value = false }
}
onMounted(load)
</script>

<style scoped>
.mt12 { margin-top: 12px; }
</style>
