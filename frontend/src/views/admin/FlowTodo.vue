<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">流程待办</h2>
      <div class="header-actions">
        <el-button type="warning" @click="openExamUrge">催交考试</el-button>
        <el-button @click="load">刷新</el-button>
      </div>
    </div>

    <el-card shadow="never">
      <el-tabs v-model="tab" @tab-change="onTabChange">
        <el-tab-pane name="todo">
          <template #label>
            待办
            <el-badge v-if="todoTotal" :value="todoTotal" class="tab-badge" />
          </template>
        </el-tab-pane>
        <el-tab-pane label="已办" name="done" />
        <el-tab-pane name="overdue">
          <template #label>
            逾期
            <el-badge v-if="overdueTotal" :value="overdueTotal" class="tab-badge" />
          </template>
        </el-tab-pane>
        <el-tab-pane label="我发起的" name="mine" />
      </el-tabs>

      <!-- 待办 / 已办 / 逾期：任务列表 -->
      <template v-if="tab !== 'mine'">
        <el-alert v-if="tab === 'overdue'" type="warning" :closable="false" show-icon
                  class="mb12"
                  title="逾期待办不会自动关闭"
                  description="流程卡在谁手上由人决定：可以催办、转办，或直接处理。系统不替人把事情结掉。" />
        <el-table v-loading="loading" :data="taskRows" border stripe>
          <template #empty>
            <TableEmpty :text="emptyText" />
          </template>
          <el-table-column prop="activity_name" label="待办事项" min-width="170" show-overflow-tooltip />
          <el-table-column prop="role_code" label="角色" width="120">
            <template #default="{ row }">
              <el-tag size="small" effect="plain">{{ roleLabel(row.role_code) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="assignee_name" label="处理人" width="110">
            <template #default="{ row }">
              {{ row.assignee_name || '未认领' }}
            </template>
          </el-table-column>
          <el-table-column label="截止时间" width="180">
            <template #default="{ row }">
              <div>{{ row.deadline || '无' }}</div>
              <div class="sub-text" :class="{ danger: row.is_overdue }">
                {{ remainingText(row.deadline, row.is_overdue) }}
              </div>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="taskStatusType(row.status)" size="small">
                {{ taskStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="逾期" width="90">
            <template #default="{ row }">
              <el-tag :type="overdueType(row.is_overdue)" size="small">
                {{ overdueText(row.is_overdue) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="催办/转办" width="100">
            <template #default="{ row }">
              <span class="count-text">催 {{ countText(row.urge_count) }}</span>
              <span class="count-text">转 {{ countText(row.transfer_count) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="产生时间" width="165" />
          <el-table-column prop="comment" label="处理意见" min-width="130" show-overflow-tooltip>
            <template #default="{ row }">{{ row.comment || '-' }}</template>
          </el-table-column>
          <el-table-column label="操作" width="340" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openDetail(row.instance_id)">详情</el-button>
              <template v-if="tab !== 'done'">
                <el-button v-if="row.status === 'TODO'" link type="warning"
                           @click="claim(row)">认领</el-button>
                <el-button link type="success" @click="openAction(row, 'approve')">通过</el-button>
                <el-button link type="danger" @click="openAction(row, 'reject')">驳回</el-button>
                <el-button link type="info" @click="openAction(row, 'return')">退回</el-button>
                <el-button link type="warning" @click="openTransfer(row)">转办</el-button>
                <el-button link type="danger" :disabled="urgeWait(row) > 0"
                           @click="openUrge(row)">催办</el-button>
              </template>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination class="mt16" background layout="total, prev, pager, next"
                       :total="total" v-model:current-page="page" @current-change="load" />
      </template>

      <!-- 我发起的：流程实例列表 -->
      <template v-else>
        <el-table v-loading="loading" :data="instanceRows" border stripe>
          <template #empty><TableEmpty text="暂无发起的流程" /></template>
          <el-table-column prop="flow_name" label="流程" min-width="180">
            <template #default="{ row }">
              {{ row.flow_name || row.flow_code || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="biz_label" label="业务对象" width="140">
            <template #default="{ row }">
              {{ row.biz_label || row.biz_type }}
              <span v-if="row.biz_key" class="sub-key">{{ row.biz_key }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="110">
            <template #default="{ row }">
              <el-tag :type="instanceStatusType(row.status)" size="small">
                {{ instanceStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="started_at" label="发起时间" width="170" />
          <el-table-column prop="ended_at" label="结束时间" width="170">
            <template #default="{ row }">{{ row.ended_at || '-' }}</template>
          </el-table-column>
          <el-table-column label="操作" width="90" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openDetail(row.id)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination class="mt16" background layout="total, prev, pager, next"
                       :total="total" v-model:current-page="page" @current-change="load" />
      </template>
    </el-card>

    <!-- 审批 / 驳回 / 退回 对话框 -->
    <el-dialog v-model="actionVisible" :title="actionTitle" width="520px">
      <el-form label-width="80px">
        <el-form-item v-if="action === 'return'" label="退回节点">
          <el-select v-model="returnTarget" placeholder="选择退回到的活动" style="width:100%">
            <el-option v-for="a in returnTargetOptions" :key="a.activity_id"
                       :label="a.activity_name || a.activity_id" :value="a.activity_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="意见">
          <el-input v-model="comment" type="textarea" :rows="3" maxlength="1000"
                    show-word-limit :placeholder="commentPlaceholder" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="actionVisible = false">取消</el-button>
        <el-button :type="action === 'reject' ? 'danger' : 'primary'" :loading="submitting"
                   @click="submitAction">确定</el-button>
      </template>
    </el-dialog>

    <!-- 转办 -->
    <el-dialog v-model="transferVisible" title="转办待办" width="520px">
      <el-form label-width="80px">
        <el-form-item label="待办事项">
          <span>{{ currentTask?.activity_name || '-' }}</span>
        </el-form-item>
        <el-form-item label="转办给">
          <el-select v-model="transferTarget" placeholder="选择接手人" style="width:100%"
                     filterable :loading="candidateLoading">
            <el-option v-for="c in candidates" :key="c.id"
                       :label="`${c.real_name || c.username}（${c.username}）`" :value="c.id" />
          </el-select>
          <div class="field-tip">
            仅列出持有「{{ roleLabel(currentTask?.role_code) }}」角色的其他用户。
          </div>
        </el-form-item>
        <el-form-item label="转办理由">
          <el-input v-model="transferReason" type="textarea" :rows="3" maxlength="500"
                    show-word-limit placeholder="选填，便于后续追溯" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="transferVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitTransfer">确定转办</el-button>
      </template>
    </el-dialog>

    <!-- 催办 -->
    <el-dialog v-model="urgeVisible" title="催办" width="520px">
      <el-form label-width="80px">
        <el-form-item label="待办事项">
          <span>{{ currentTask?.activity_name || '-' }}</span>
        </el-form-item>
        <el-form-item label="催办对象">
          <span>{{ currentTask?.assignee_name || '未认领（无法催办）' }}</span>
        </el-form-item>
        <el-form-item label="催办留言">
          <el-input v-model="urgeComment" type="textarea" :rows="3" maxlength="500"
                    show-word-limit placeholder="选填，会附在通知里" />
        </el-form-item>
        <el-alert type="info" :closable="false" show-icon
                  title="同一待办 30 分钟内只能催办一次，避免刷屏。" />
      </el-form>
      <template #footer>
        <el-button @click="urgeVisible = false">取消</el-button>
        <el-button type="danger" :loading="submitting" @click="submitUrge">确定催办</el-button>
      </template>
    </el-dialog>

    <!-- 选考试（催交入口） -->
    <el-dialog v-model="examPickerVisible" title="选择要催交的考试 / 作业" width="620px">
      <div v-loading="examLoading">
        <el-empty v-if="!examLoading && !examTasks.length"
                  description="没有可催交的任务（需任务创建者或管理员身份）" :image-size="70" />
        <el-table v-else :data="examTasks" border size="small" max-height="360">
          <el-table-column prop="title" label="任务标题" min-width="180" show-overflow-tooltip />
          <el-table-column prop="type" label="类型" width="80">
            <template #default="{ row }">
              <el-tag size="small" :type="row.type === 'exam' ? 'danger' : 'primary'">
                {{ row.type === 'exam' ? '考试' : '作业' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="进度" width="140">
            <template #default="{ row }">
              {{ row.submission_count || 0 }}/{{ row.assigned_count || 0 }} 人已交
            </template>
          </el-table-column>
          <el-table-column prop="end_at" label="截止时间" width="160" />
          <el-table-column label="操作" width="80" fixed="right">
            <template #default="{ row }">
              <el-button link type="warning" @click="pickExam(row)">催交</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="examPickerVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 催交考试 / 作业 -->
    <ExamUrgeDialog v-model="examUrgeVisible" :task="urgeTargetTask" />

    <!-- 实例详情 -->
    <el-dialog v-model="detailVisible" title="流程详情" width="760px">
      <template v-if="detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="流程">{{ detail.flow_name || detail.flow_code }}</el-descriptions-item>
          <el-descriptions-item label="业务对象">
            {{ detail.biz_label || detail.biz_type }} {{ detail.biz_key || '' }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="instanceStatusType(detail.status)" size="small">
              {{ instanceStatusText(detail.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="发起时间">{{ detail.started_at || '-' }}</el-descriptions-item>
        </el-descriptions>

        <h4 class="section-title">流转留痕</h4>
        <el-timeline v-if="(detail.history || []).length">
          <el-timeline-item
            v-for="h in detail.history" :key="h.id"
            :timestamp="h.created_at" placement="top"
            :type="historyType(h.action)">
            <div class="history-head">
              <strong>{{ h.activity_name || h.activity_id || '-' }}</strong>
              <el-tag size="small" effect="plain">{{ historyActionText(h.action) }}</el-tag>
              <span class="history-operator">{{ h.operator_name || '系统' }}</span>
            </div>
            <div v-if="h.comment" class="history-comment">{{ h.comment }}</div>
          </el-timeline-item>
        </el-timeline>
        <el-empty v-else description="暂无流转记录" :image-size="60" />
      </template>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { flowApi, taskApi } from '@/api'
import ExamUrgeDialog from '@/components/ExamUrgeDialog.vue'
import {
  countText,
  historyActionText,
  historyType,
  instanceStatusText,
  instanceStatusType,
  overdueText,
  overdueType,
  remainingText,
  roleLabel,
  returnTargets,
  taskStatusText,
  taskStatusType,
  urgeCooldownRemaining
} from '@/utils/flowTodo'

const tab = ref('todo')
const loading = ref(false)
const submitting = ref(false)
const page = ref(1)
const total = ref(0)
const taskRows = ref([])
const instanceRows = ref([])
const todoTotal = ref(0)
const overdueTotal = ref(0)

// ---- 动作对话框 ----
const actionVisible = ref(false)
const action = ref('approve')
const currentTask = ref(null)
const comment = ref('')
const returnTarget = ref('')
const detailVisible = ref(false)
const detail = ref(null)

// ---- 转办 ----
const transferVisible = ref(false)
const candidateLoading = ref(false)
const candidates = ref([])
const transferTarget = ref(null)
const transferReason = ref('')

// ---- 催办 ----
const urgeVisible = ref(false)
const urgeComment = ref('')

// ---- 催交考试 ----
const examPickerVisible = ref(false)
const examLoading = ref(false)
const examTasks = ref([])
const examUrgeVisible = ref(false)
const urgeTargetTask = ref(null)

const actionTitle = computed(() => ({
  approve: '审批通过', reject: '审批驳回', return: '退回重填'
}[action.value] || '处理'))

const commentPlaceholder = computed(() => {
  if (action.value === 'reject') return '驳回意见（部分流程规则要求必填）'
  if (action.value === 'return') return '退回原因'
  return '审批意见（选填）'
})

const returnTargetOptions = computed(() =>
  returnTargets(currentTask.value?.flow_code, detail.value?.history || []))

const emptyText = computed(() => ({
  todo: '暂无待办事项',
  done: '暂无已办记录',
  overdue: '没有逾期待办'
}[tab.value] || '暂无数据'))

function onTabChange() {
  page.value = 1
  load()
}

async function load() {
  loading.value = true
  try {
    if (tab.value === 'mine') {
      const res = await flowApi.instances({ page: page.value, page_size: 20 })
      instanceRows.value = res.data?.items || []
      total.value = res.data?.total || 0
      return
    }
    const api = tab.value === 'todo' ? flowApi.todo
      : tab.value === 'overdue' ? flowApi.overdue
        : flowApi.done
    const res = await api({ page: page.value, page_size: 20 })
    taskRows.value = res.data?.items || []
    total.value = res.data?.total || 0
    if (tab.value === 'todo') todoTotal.value = res.data?.total || 0
    if (tab.value === 'overdue') overdueTotal.value = res.data?.total || 0
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function claim(row) {
  try {
    await flowApi.claim(row.id)
    ElMessage.success('已认领')
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '认领失败')
  }
}

function openAction(row, kind) {
  currentTask.value = row
  action.value = kind
  comment.value = ''
  returnTarget.value = ''
  actionVisible.value = true
}

async function submitAction() {
  if (action.value === 'return' && !returnTarget.value) {
    ElMessage.warning('请选择退回节点')
    return
  }
  submitting.value = true
  try {
    const id = currentTask.value.id
    if (action.value === 'approve') {
      await flowApi.approve(id, { comment: comment.value })
    } else if (action.value === 'reject') {
      await flowApi.reject(id, { comment: comment.value })
    } else {
      await flowApi.returnTo(id, {
        target_activity_id: returnTarget.value,
        comment: comment.value
      })
    }
    ElMessage.success('已提交')
    actionVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

// ---- 转办 ----
async function openTransfer(row) {
  currentTask.value = row
  transferTarget.value = null
  transferReason.value = ''
  candidates.value = []
  transferVisible.value = true
  candidateLoading.value = true
  try {
    const res = await flowApi.transferCandidates(row.id)
    candidates.value = res.data || []
    if (!candidates.value.length) {
      ElMessage.warning('没有可转办的人：需持有该角色的其他用户')
    }
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '加载转办候选人失败')
    transferVisible.value = false
  } finally {
    candidateLoading.value = false
  }
}

async function submitTransfer() {
  if (!transferTarget.value) {
    ElMessage.warning('请选择转办对象')
    return
  }
  submitting.value = true
  try {
    await flowApi.transfer(currentTask.value.id, {
      to_user_id: transferTarget.value,
      reason: transferReason.value
    })
    ElMessage.success('已转办')
    transferVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '转办失败')
  } finally {
    submitting.value = false
  }
}

// ---- 催办 ----
function urgeWait(row) {
  return urgeCooldownRemaining(row)
}

function openUrge(row) {
  currentTask.value = row
  urgeComment.value = ''
  urgeVisible.value = true
}

async function submitUrge() {
  submitting.value = true
  try {
    await flowApi.urge(currentTask.value.id, { comment: urgeComment.value })
    ElMessage.success('已催办')
    urgeVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '催办失败')
  } finally {
    submitting.value = false
  }
}

// ---- 催交考试 ----
async function openExamUrge() {
  examPickerVisible.value = true
  examLoading.value = true
  examTasks.value = []
  try {
    const res = await taskApi.list({ page: 1, page_size: 100 })
    examTasks.value = res.data?.items || []
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '加载任务列表失败')
  } finally {
    examLoading.value = false
  }
}

function pickExam(row) {
  urgeTargetTask.value = row
  examPickerVisible.value = false
  examUrgeVisible.value = true
}

async function openDetail(instanceId) {
  try {
    const res = await flowApi.instance(instanceId)
    detail.value = res.data
    detailVisible.value = true
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '加载详情失败')
  }
}

onMounted(load)
</script>

<style scoped>
.tab-badge {
  margin-left: 6px;
  vertical-align: top;
}
.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}
/* 操作列按钮不折行：7 个 link 按钮换行后视觉上很乱，
   宁可表格横向滚动也不要按钮堆叠。 */
.el-table :deep(.el-button) {
  white-space: nowrap;
}
.mb12 {
  margin-bottom: 12px;
}
.section-title {
  margin: 20px 0 12px;
  font-size: 15px;
}
.history-head {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.history-operator {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}
.history-comment {
  margin-top: 4px;
  color: var(--el-text-color-regular);
  font-size: 13px;
  white-space: pre-wrap;
}
.sub-key {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  margin-left: 4px;
}
.sub-text {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  margin-top: 2px;
}
.sub-text.danger {
  color: var(--el-color-danger);
}
.count-text {
  display: inline-block;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-right: 6px;
}
.field-tip {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  line-height: 1.6;
  margin-top: 4px;
}
</style>
