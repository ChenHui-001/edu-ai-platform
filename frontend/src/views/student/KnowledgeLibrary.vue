<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">知识资料</h2>
      <el-button :icon="Refresh" @click="loadTree">刷新</el-button>
    </div>

    <el-card shadow="never">
      <el-row :gutter="18">
        <el-col :xs="24" :md="8" class="tree-col">
          <el-input v-model="keyword" clearable placeholder="搜索知识点"
                    :prefix-icon="Search" class="mb12" />
          <el-tree ref="treeRef" v-loading="treeLoading" :data="tree" node-key="id"
                   :props="{ label: 'name', children: 'children' }"
                   default-expand-all highlight-current :expand-on-click-node="false"
                   :filter-node-method="filterNode" @node-click="selectNode">
            <template #default="{ data }">
              <span class="node-label">
                <span>{{ data.name }}</span>
                <el-tag v-if="data.question_count" size="small" type="info" effect="plain">
                  {{ data.question_count }} 题
                </el-tag>
              </span>
            </template>
          </el-tree>
          <el-empty v-if="!treeLoading && !tree.length" description="本年级暂无已发布知识点"
                    :image-size="60" />
        </el-col>

        <el-col :xs="24" :md="16" class="detail-col">
          <template v-if="current">
            <div class="detail-title">
              <h3>{{ current.name }}</h3>
              <el-tag v-if="current.difficulty" size="small" effect="plain">
                {{ difficultyLabel(current.difficulty) }}
              </el-tag>
            </div>
            <div class="muted mb8">{{ current.path || '' }}</div>
            <p v-if="current.description" class="desc">{{ current.description }}</p>

            <el-divider content-position="left">资料附件（{{ attachments.length }}）</el-divider>
            <el-table v-loading="attLoading" :data="attachments" size="small" border
                      empty-text="该知识点暂无资料">
              <el-table-column prop="filename" label="文件名" min-width="220"
                               show-overflow-tooltip />
              <el-table-column label="大小" width="90" align="center">
                <template #default="{ row }">{{ formatFileSize(row.file_size) }}</template>
              </el-table-column>
              <el-table-column label="上传时间" width="150">
                <template #default="{ row }">{{ formatLocalDate(row.created_at) }}</template>
              </el-table-column>
              <el-table-column label="操作" width="140" align="center">
                <template #default="{ row }">
                  <el-button link type="primary" :disabled="!isPreviewable(row.ext)"
                             @click="previewAttachment(row)">预览</el-button>
                  <el-button link type="primary" @click="downloadAttachment(row)">下载</el-button>
                </template>
              </el-table-column>
            </el-table>
          </template>
          <el-empty v-else description="请在左侧选择知识点查看资料" :image-size="70" />
        </el-col>
      </el-row>
    </el-card>

    <el-dialog v-model="previewVisible" title="资料预览" width="72%" top="5vh"
               destroy-on-close @closed="clearPreview">
      <img v-if="previewIsImage && previewUrl" :src="previewUrl"
           style="max-width:100%;max-height:70vh;display:block;margin:0 auto" />
      <iframe v-else-if="previewUrl" :src="previewUrl"
              style="width:100%;height:70vh;border:0;border-radius:6px" />
      <el-empty v-else description="附件加载失败" :image-size="70" />
      <template #footer>
        <el-button @click="previewVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Search } from '@element-plus/icons-vue'
import { attachmentApi, knowledgeApi } from '@/api'
import { downloadBlob, fetchBlobUrl } from '@/utils/download'
import { formatLocalDate } from '@/utils/date'

const treeRef = ref(null)
const tree = ref([])
const treeLoading = ref(false)
const keyword = ref('')
const current = ref(null)
const attachments = ref([])
const attLoading = ref(false)
const previewVisible = ref(false)
const previewUrl = ref('')
const previewIsImage = ref(false)
let previewObjectUrl = ''

watch(keyword, (v) => treeRef.value?.filter(v))

function filterNode(value, data) {
  const kw = String(value || '').trim().toLowerCase()
  if (!kw) return true
  return String(data.name || '').toLowerCase().includes(kw)
    || String(data.keywords || '').toLowerCase().includes(kw)
}

function difficultyLabel(v) {
  return ({ easy: '简单', medium: '中等', hard: '困难' })[v] || v || '-'
}

function isPreviewable(ext) {
  return ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.webp'].includes(String(ext || '').toLowerCase())
}

function formatFileSize(size) {
  const n = Number(size || 0)
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / 1024 / 1024).toFixed(1)} MB`
}

async function loadTree() {
  treeLoading.value = true
  try {
    const res = await knowledgeApi.tree({ status: 'published' })
    tree.value = res.data?.items || []
    if (current.value) {
      const hit = findNode(tree.value, current.value.id)
      if (hit) selectNode(hit)
      else { current.value = null; attachments.value = [] }
    }
  } finally {
    treeLoading.value = false
  }
}

function findNode(nodes, id) {
  for (const n of nodes || []) {
    if (n.id === id) return n
    const hit = findNode(n.children || [], id)
    if (hit) return hit
  }
  return null
}

async function selectNode(data) {
  current.value = data
  attLoading.value = true
  try {
    const res = await knowledgeApi.attachments(data.id)
    attachments.value = Array.isArray(res.data) ? res.data : (res.data?.items || [])
  } catch {
    attachments.value = []
  } finally {
    attLoading.value = false
  }
}

async function previewAttachment(row) {
  if (!isPreviewable(row.ext)) return ElMessage.warning('该文件类型请下载后查看')
  clearPreview()
  try {
    const url = await fetchBlobUrl(attachmentApi.preview(row.id))
    previewObjectUrl = url
    previewUrl.value = url
    previewIsImage.value = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
      .includes(String(row.ext || '').toLowerCase())
    previewVisible.value = true
  } catch {
    ElMessage.error('附件预览失败')
  }
}

function clearPreview() {
  if (previewObjectUrl) {
    URL.revokeObjectURL(previewObjectUrl)
    previewObjectUrl = ''
  }
  previewUrl.value = ''
  previewIsImage.value = false
}

async function downloadAttachment(row) {
  try {
    await downloadBlob(attachmentApi.download(row.id), row.filename || '资料附件')
  } catch {
    ElMessage.error('附件下载失败')
  }
}

onMounted(loadTree)
onBeforeUnmount(clearPreview)
</script>

<style scoped>
.tree-col { border-right: 1px solid var(--el-border-color-lighter); min-height: 520px; }
.detail-col { min-height: 520px; }
.node-label { display: flex; align-items: center; gap: 8px; }
.detail-title { display: flex; align-items: center; gap: 10px; }
.desc { color: var(--el-text-color-regular); line-height: 1.7; }
@media (max-width: 992px) {
  .tree-col { border-right: 0; border-bottom: 1px solid var(--el-border-color-lighter); margin-bottom: 16px; }
}
</style>
