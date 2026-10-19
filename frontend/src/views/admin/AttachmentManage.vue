<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">附件管理</h2>
      <div>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
        <el-button type="primary" :icon="Upload" @click="uploadDlg = true">上传附件</el-button>
      </div>
    </div>

    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="query">
        <el-form-item label="文件名">
          <el-input v-model="query.keyword" placeholder="关键词" clearable style="width:180px"
                    @keyup.enter="load" />
        </el-form-item>
        <el-form-item label="业务类型">
          <el-select v-model="query.biz_type" placeholder="全部" clearable style="width:140px">
            <el-option label="注册申请" value="registration" />
            <el-option label="作业提交" value="submission" />
            <el-option label="试卷" value="paper" />
            <el-option label="笔记" value="note" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.is_temp" placeholder="全部" clearable style="width:120px">
            <el-option label="临时" :value="true" />
            <el-option label="正式" :value="false" />
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
        <el-table-column prop="filename" label="文件名" min-width="240" show-overflow-tooltip />
        <el-table-column prop="ext" label="类型" width="90">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ (row.ext || '').replace('.', '').toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="大小" width="110">
          <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
        </el-table-column>
        <el-table-column prop="uploader_name" label="上传者" width="110" />
        <el-table-column label="业务" width="140">
          <template #default="{ row }">
            <span v-if="row.biz_type">{{ row.biz_type }} #{{ row.biz_id }}</span>
            <el-tag v-else type="warning" size="small">临时</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="170" />
        <el-table-column label="操作" width="190" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="preview(row)">预览</el-button>
            <el-button link type="primary" @click="download(row)">下载</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination class="mt16" background layout="total, sizes, prev, pager, next"
                     :total="total" v-model:current-page="query.page"
                     v-model:page-size="query.page_size"
                     @current-change="load" @size-change="load" />
    </el-card>

    <el-dialog v-model="uploadDlg" title="上传附件" width="560px">
      <el-upload drag :auto-upload="false" :limit="10" ref="uploadRef"
                 :on-change="onFileChange" :on-remove="onFileRemove">
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">将文件拖到此处，或 <em>点击选择</em></div>
        <template #tip>
          <div class="tip">支持图片、文档、音频等，单个文件不超过 50MB</div>
        </template>
      </el-upload>
      <template #footer>
        <el-button @click="uploadDlg = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="doUpload">上传</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="previewDlg" title="附件预览" width="70%" top="5vh">
      <iframe v-if="previewUrl" :src="previewUrl" style="width:100%;height:70vh;border:0;border-radius:6px" />
      <el-empty v-else description="该文件类型不支持在线预览，请下载后查看" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, UploadFilled, Search, Refresh } from '@element-plus/icons-vue'
import { attachmentApi } from '@/api'

const list = ref([])
const total = ref(0)
const loading = ref(false)
const uploading = ref(false)
const uploadDlg = ref(false)
const previewDlg = ref(false)
const previewUrl = ref('')
const uploadRef = ref(null)
const files = ref([])

const query = reactive({ page: 1, page_size: 20, keyword: '', biz_type: '', is_temp: null })

function formatSize(bytes) {
  if (!bytes) return '-'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let n = bytes
  while (n >= 1024 && i < units.length - 1) { n /= 1024; i++ }
  return `${n.toFixed(1)} ${units[i]}`
}

async function load() {
  loading.value = true
  try {
    const res = await attachmentApi.list(query)
    const d = res.data || {}
    list.value = d.items || []
    total.value = d.total || 0
  } finally {
    loading.value = false
  }
}

function reset() {
  Object.assign(query, { page: 1, keyword: '', biz_type: '', is_temp: null })
  load()
}

function onFileChange(file) { files.value.push(file.raw) }
function onFileRemove(file) { files.value = files.value.filter(f => f !== file.raw) }

async function doUpload() {
  if (!files.value.length) return ElMessage.warning('请先选择文件')
  uploading.value = true
  try {
    const fd = new FormData()
    files.value.forEach(f => fd.append('files', f))
    const res = await attachmentApi.batchUpload(fd)
    ElMessage.success(res.data.message || '上传成功')
    uploadDlg.value = false
    files.value = []
    uploadRef.value?.clearFiles()
    load()
  } finally {
    uploading.value = false
  }
}

function preview(row) {
  if (!row.previewable) return ElMessage.warning('该文件类型不支持在线预览')
  previewUrl.value = attachmentApi.previewUrl(row.id)
  previewDlg.value = true
}

function download(row) {
  window.open(attachmentApi.downloadUrl(row.id), '_blank')
}

async function remove(row) {
  await ElMessageBox.confirm(`确认删除附件「${row.filename}」？`, '提示', { type: 'warning' })
  await attachmentApi.remove(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>

<style scoped>
.mt16 { margin-top: 16px; justify-content: flex-end; }
.tip { font-size: 12px; color: #909399; margin-top: 8px; }
.filter-card :deep(.el-form-item) { margin-bottom: 12px; }
</style>
