<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">学习笔记</h2>
      <div>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
        <el-button type="primary" :icon="Plus" @click="openDialog()">新建笔记</el-button>
      </div>
    </div>

    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="query">
        <el-form-item label="学科">
          <el-select v-model="query.subject_id" placeholder="全部" clearable style="width:130px">
            <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="query.keyword" placeholder="标题 / 内容" clearable style="width:180px"
                    @keyup.enter="load" />
        </el-form-item>
        <el-form-item label="收藏">
          <el-select v-model="query.is_favorite" placeholder="全部" clearable style="width:110px">
            <el-option label="已收藏" :value="true" />
            <el-option label="未收藏" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="load">查询</el-button>
          <el-button :icon="Refresh" @click="reset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-empty v-if="!loading && !list.length" description="还没有笔记，记录下你的学习心得吧" />

    <el-row :gutter="16">
      <el-col :span="8" v-for="n in list" :key="n.id">
        <el-card shadow="hover" class="note-card">
          <div class="note-head" @click="view(n)">
            <h3 class="note-title">
              <el-icon v-if="n.is_favorite" color="#f7ba2a"><StarFilled /></el-icon>
              {{ n.title }}
            </h3>
            <div class="note-meta">
              <el-tag v-if="n.subject_name" size="small" type="info" effect="plain">{{ n.subject_name }}</el-tag>
              <span class="tip">{{ n.updated_at }}</span>
            </div>
          </div>
          <p class="note-preview" @click="view(n)">{{ n.content_preview }}</p>
          <div v-if="n.tags?.length" class="note-tags">
            <el-tag v-for="t in n.tags" :key="t" size="small" effect="plain" class="mr4">#{{ t }}</el-tag>
          </div>
          <div class="note-actions">
            <el-button link type="primary" size="small" @click="organize(n)">
              <el-icon><MagicStick /></el-icon> AI 整理
            </el-button>
            <el-button link type="primary" size="small" @click="openDialog(n)">编辑</el-button>
            <el-button link :type="n.is_favorite ? 'warning' : 'info'" size="small" @click="fav(n)">
              {{ n.is_favorite ? '取消收藏' : '收藏' }}
            </el-button>
            <el-button link type="danger" size="small" @click="remove(n)">删除</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-pagination v-if="total > query.page_size" class="mt16" background
                   layout="total, prev, pager, next" :total="total"
                   v-model:current-page="query.page" @current-change="load" />

    <!-- 笔记详情 -->
    <el-drawer v-model="viewDrawer" :title="current?.title" size="60%">
      <div v-loading="viewLoading">
        <div class="detail-meta" v-if="current">
          <el-tag v-if="current.subject_name" size="small" type="info">{{ current.subject_name }}</el-tag>
          <span class="tip">创建：{{ current.created_at }}</span>
          <span class="tip">更新：{{ current.updated_at }}</span>
          <span class="tip">浏览：{{ current.view_count }} 次</span>
        </div>

        <div v-if="current?.ai_summary" class="ai-box">
          <b><el-icon><MagicStick /></el-icon> AI 摘要</b>
          <p>{{ current.ai_summary }}</p>
        </div>

        <div v-if="current?.ai_outline?.length" class="ai-box">
          <b>AI 大纲</b>
          <ul>
            <li v-for="(o, i) in current.ai_outline" :key="i">{{ o }}</li>
          </ul>
        </div>

        <div v-if="current?.ai_mindmap" class="ai-box">
          <b>思维导图</b>
          <pre class="mindmap">{{ current.ai_mindmap }}</pre>
        </div>

        <el-divider content-position="left">笔记正文</el-divider>
        <div class="note-content" v-html="current?.content"></div>
      </div>
      <template #footer>
        <el-button :icon="MagicStick" @click="organize(current)">AI 整理</el-button>
        <el-button type="primary" @click="openDialog(current)">编辑</el-button>
      </template>
    </el-drawer>

    <!-- 编辑 -->
    <el-dialog v-model="dlg" :title="form.id ? '编辑笔记' : '新建笔记'" width="720px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="form.title" placeholder="如：一元一次方程的解法总结" />
        </el-form-item>
        <el-form-item label="学科">
          <el-select v-model="form.subject_id" clearable style="width:100%">
            <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="标签">
          <el-select v-model="tagList" multiple filterable allow-create default-first-option
                     placeholder="输入后回车创建" style="width:100%">
            <el-option v-for="t in tagList" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="正文">
          <el-input v-model="form.content" type="textarea" :rows="12" placeholder="支持 HTML 标签" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, MagicStick, StarFilled } from '@element-plus/icons-vue'
import { learningApi, eduApi } from '@/api'

const list = ref([])
const subjects = ref([])
const current = ref(null)
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const dlg = ref(false)
const viewDrawer = ref(false)
const viewLoading = ref(false)
const tagList = ref([])

const query = reactive({ page: 1, page_size: 20, subject_id: null, keyword: '', is_favorite: null })
const form = reactive({ id: null, title: '', subject_id: null, content: '', tags: '' })

async function load() {
  loading.value = true
  try {
    const res = await learningApi.notes(query)
    const d = res.data || {}
    list.value = d.items || []
    total.value = d.total || 0
  } finally {
    loading.value = false
  }
}

function reset() {
  Object.assign(query, { page: 1, subject_id: null, keyword: '', is_favorite: null })
  load()
}

async function view(n) {
  viewDrawer.value = true
  viewLoading.value = true
  try {
    const res = await learningApi.note(n.id)
    current.value = res.data
  } finally {
    viewLoading.value = false
  }
}

function openDialog(n) {
  Object.assign(form, n
    ? { id: n.id, title: n.title, subject_id: n.subject_id, content: n.content || '', tags: '' }
    : { id: null, title: '', subject_id: query.subject_id, content: '', tags: '' })
  tagList.value = n?.tags ? [...n.tags] : []
  dlg.value = true
}

async function save() {
  if (!form.title) return ElMessage.warning('请输入笔记标题')
  saving.value = true
  try {
    form.tags = tagList.value.join(',')
    if (form.id) await learningApi.updateNote(form.id, form)
    else await learningApi.createNote(form)
    ElMessage.success('保存成功')
    dlg.value = false
    load()
  } finally {
    saving.value = false
  }
}

const organizing = ref(false)
async function organize(n) {
  if (organizing.value) return
  if (!n?.id) { organizing.value = false; return }
  try {
    const res = await learningApi.organizeNote(n.id)
    ElMessage.success(res.data.message || 'AI 整理完成')
    if (current.value?.id === n.id) await view(n)
    load()
  } finally {
    organizing.value = false
  }
}

async function fav(n) {
  await learningApi.updateNote(n.id, { is_favorite: !n.is_favorite })
  ElMessage.success(n.is_favorite ? '已取消收藏' : '已收藏')
  load()
}

async function remove(n) {
  await ElMessageBox.confirm(`确认删除笔记「${n.title}」？`, '提示', { type: 'warning' })
  await learningApi.removeNote(n.id)
  ElMessage.success('已删除')
  load()
}

onMounted(async () => {
  await load()
  const s = await eduApi.subjects()
  subjects.value = s.data.data || []
})
</script>

<style scoped>
.mt16 { margin-top: 16px; justify-content: flex-end; }
.mr4 { margin-right: 4px; }
.tip { font-size: 12px; color: #909399; }
.note-card { margin-bottom: 16px; min-height: 210px; }
.note-head { cursor: pointer; }
.note-title {
  margin: 0 0 6px; font-size: 15px; display: flex; align-items: center; gap: 4px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.note-meta { display: flex; align-items: center; gap: 8px; }
.note-preview {
  color: #606266; font-size: 13px; line-height: 1.7; margin: 10px 0; cursor: pointer;
  display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
}
.note-actions {
  display: flex; gap: 4px; border-top: 1px solid #f0f2f5; padding-top: 10px; margin-top: 10px;
}
.detail-meta { display: flex; gap: 14px; align-items: center; margin-bottom: 14px; flex-wrap: wrap; }
.ai-box {
  background: #f0f6ff; border-left: 3px solid var(--el-color-primary);
  padding: 10px 14px; border-radius: 6px; margin-bottom: 12px;
}
.ai-box b { display: flex; align-items: center; gap: 4px; font-size: 13px; margin-bottom: 6px; }
.ai-box p, .ai-box ul { margin: 4px 0; font-size: 13px; line-height: 1.8; }
.mindmap { white-space: pre-wrap; font-family: inherit; font-size: 12px; margin: 4px 0; line-height: 1.7; }
.note-content { line-height: 2; font-size: 14px; }
.filter-card :deep(.el-form-item) { margin-bottom: 12px; }
</style>
