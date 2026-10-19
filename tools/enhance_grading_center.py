# -*- coding: utf-8 -*-
"""批改中心增强：多选批量 / 分页加载 / 键盘快捷键。"""
import io

f = "frontend/src/views/teacher/GradingCenter.vue"
s = io.open(f, encoding="utf-8").read()

# 1) import
s = s.replace(
    "import { Search, Refresh } from '@element-plus/icons-vue'",
    "import { Search, Refresh, QuestionFilled } from '@element-plus/icons-vue'")
s = s.replace(
    "import { ref, reactive, computed, onMounted } from 'vue'",
    "import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'")

# 2) 状态
OLD_STATE = """const loading = ref(false)
const detailLoading = ref(false)
const saving = ref(false)"""
NEW_STATE = """const loading = ref(false)
const detailLoading = ref(false)
const saving = ref(false)
// 批量 / 分页 / 快捷键
const checkedIds = ref([])
const batching = ref(false)
const total = ref(0)
const PAGE_SIZE = 30
const page = ref(1)
const loadingMore = ref(false)
const focusedIdx = ref(0)   // Alt+F/Alt+Z 作用的题目索引"""
assert OLD_STATE in s, "state"
s = s.replace(OLD_STATE, NEW_STATE)

# 3) hasMore
s = s.replace(
    "const needManualCount = computed(() => list.value.filter(i => i.needs_manual).length)",
    "const needManualCount = computed(() => list.value.filter(i => i.needs_manual).length)\n"
    "const hasMore = computed(() => list.value.length < total.value)")

# 4) load 分页 + loadMore + 批量 + 快捷键
OLD_LOAD = """async function load() {
  loading.value = true
  try {
    const res = await gradingApi.pending({ page: 1, page_size: 100 })
    list.value = res.data?.items || []
  } finally {
    loading.value = false
  }
}"""
NEW_LOAD = """async function load() {
  loading.value = true
  page.value = 1
  try {
    const res = await gradingApi.pending({ page: 1, page_size: PAGE_SIZE })
    list.value = res.data?.items || []
    total.value = res.data?.total ?? list.value.length
    checkedIds.value = []
  } finally {
    loading.value = false
  }
}

/** 分页追加：待批量大时不必一次全拉（此前固定 100 条，超出看不到） */
async function loadMore() {
  loadingMore.value = true
  try {
    page.value += 1
    const res = await gradingApi.pending({ page: page.value, page_size: PAGE_SIZE })
    const more = res.data?.items || []
    const seen = new Set(list.value.map(x => x.submission_id))
    list.value = [...list.value, ...more.filter(x => !seen.has(x.submission_id))]
    total.value = res.data?.total ?? list.value.length
  } finally {
    loadingMore.value = false
  }
}

function toggleCheck(sid, v) {
  if (v) {
    if (!checkedIds.value.includes(sid)) checkedIds.value.push(sid)
  } else {
    checkedIds.value = checkedIds.value.filter(x => x !== sid)
  }
}

/** 批量采纳：把选中提交的当前分数直接落库（AI 已批的抽检确认场景） */
async function batchGrade() {
  batching.value = true
  try {
    const res = await gradingApi.batchGrade({ submission_ids: checkedIds.value })
    const d = res.data || {}
    ElMessage.success(
      '批量批改 ' + (d.graded?.length || 0) + ' 份' +
      (d.skipped?.length ? '，跳过 ' + d.skipped.length + ' 份' : ''))
    await load()
  } catch (e) {
    ElMessage.error('批量批改失败：' + (e?.message || e))
  } finally {
    batching.value = false
  }
}

/** 批量发布：仅对已批改且未发布的记录生效（未批改的自动跳过） */
async function batchPublish() {
  try {
    await ElMessageBox.confirm(
      '将发布 ' + checkedIds.value.length + ' 份成绩，学生立即可见。确认？',
      '批量发布', { type: 'warning' })
  } catch { return }
  batching.value = true
  try {
    const res = await gradingApi.batchPublish({ submission_ids: checkedIds.value })
    const d = res.data || {}
    ElMessage.success(
      '已发布 ' + (d.published?.length || 0) + ' 份' +
      (d.skipped?.length ? '，跳过 ' + d.skipped.length + ' 份（未批改/已发布）' : ''))
    await load()
  } catch (e) {
    ElMessage.error('批量发布失败：' + (e?.message || e))
  } finally {
    batching.value = false
  }
}

/** 快捷键：Ctrl+Enter 保存并下一份 / Ctrl+S 保存 / Alt+F 满分 / Alt+Z 零分 / 数字键跳题 */
function onKeydown(e) {
  if (!detail.value) return
  const tag = (e.target?.tagName || '').toLowerCase()
  const editing = tag === 'input' || tag === 'textarea'
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    e.preventDefault()
    saveAndNext()
  } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
    e.preventDefault()
    saveGrade()
  } else if (e.altKey && e.key.toLowerCase() === 'f') {
    e.preventDefault()
    const it = detail.value.items?.[focusedIdx.value]
    if (it) setScore(it, it.full_score)
  } else if (e.altKey && e.key.toLowerCase() === 'z') {
    e.preventDefault()
    const it = detail.value.items?.[focusedIdx.value]
    if (it) setScore(it, 0)
  } else if (!editing && /^[1-9]$/.test(e.key)) {
    const i = Number(e.key) - 1
    if (i < (detail.value.items?.length || 0)) {
      focusedIdx.value = i
      document.querySelectorAll('.q-item')[i]?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }
}"""
assert OLD_LOAD in s, "load"
s = s.replace(OLD_LOAD, NEW_LOAD)

# 5) mounted / unmounted
OLD_MOUNT = """onMounted(async () => {
  await load()
  await focusFromQuery()
})"""
NEW_MOUNT = """onMounted(async () => {
  await load()
  await focusFromQuery()
  window.addEventListener('keydown', onKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
})"""
assert OLD_MOUNT in s, "mount"
s = s.replace(OLD_MOUNT, NEW_MOUNT)

# 6) 样式
OLD_STYLE = ".name { font-weight: 600; font-size: 14px; }"
NEW_STYLE = """.name-line { display: flex; align-items: center; gap: 6px; min-width: 0; }
.name { font-weight: 600; font-size: 14px; }

.batch-bar {
  display: flex; align-items: center; justify-content: space-between; gap: 8px;
  background: #f0f6ff; border: 1px solid #d9e8ff; border-radius: 6px;
  padding: 6px 10px; margin-bottom: 10px;
}
.batch-actions { display: flex; gap: 6px; }
.load-more { text-align: center; padding: 8px 0; }
.kb-tip { line-height: 1.8; font-size: 12px; }"""
assert OLD_STYLE in s, "style"
s = s.replace(OLD_STYLE, NEW_STYLE)

io.open(f, "w", encoding="utf-8", newline="\n").write(s)
print("批改中心增强完成：多选/批量/分页/快捷键")
