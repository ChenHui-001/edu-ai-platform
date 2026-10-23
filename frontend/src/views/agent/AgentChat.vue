<template>
  <div class="chat-page">
    <aside class="side">
      <div class="engine-status" :class="{ on: status.llm_enabled }">
        <div class="st-title">
          <el-icon><Cpu /></el-icon> AI 引擎状态
        </div>
        <div class="st-row"><span>提供商</span><b>{{ providerName }}</b></div>
        <div class="st-row"><span>模型</span><b>{{ modelName }}</b></div>
        <div class="st-row">
          <span>API Key</span>
          <b><el-tag size="small" :type="keyTagType" effect="plain">{{ keyLabel }}</el-tag></b>
        </div>
        <div class="st-row"><span>编排</span><b>{{ status.orchestrator_mode === 'langgraph' ? 'LangGraph' : '顺序编排' }}</b></div>
        <div class="st-row"><span>向量库</span><b>{{ status.vector_db || '-' }}</b></div>
        <div class="st-row"><span>Agent</span><b>{{ status.agents || 0 }} 个</b></div>
        <el-alert v-if="status.tip" type="warning" :closable="false" show-icon style="margin-top:8px">
          <template #title><span style="font-size:12px">{{ status.tip }}</span></template>
        </el-alert>
        <!-- 未启用 AI：给出配置入口（管理员可跳转，非管理员提示联系管理员） -->
        <el-alert v-if="showConfigHint" type="warning" :closable="false" show-icon style="margin-top:8px">
          <template #title>
            <span style="font-size:12px">
              AI 未启用，当前走规则引擎降级。
              <el-link v-if="isAdmin" type="primary" :underline="false" @click="goAiConfig">
                前往 AI 大模型配置
              </el-link>
              <template v-else>请联系管理员在「AI 大模型配置」中启用。</template>
            </span>
          </template>
        </el-alert>
      </div>

      <div class="side-block">
        <div class="sb-title">试试这样问</div>
        <div v-for="q in samples" :key="q" class="sample" @click="ask(q)">{{ q }}</div>
      </div>

      <el-button :icon="Delete" style="width:100%" @click="clear">新对话</el-button>
    </aside>

    <section class="main">
      <div ref="scrollBox" class="messages">
        <div v-if="messages.length === 0" class="welcome">
          <el-icon :size="54" color="#2f6fd0"><MagicStick /></el-icon>
          <h2>你好，{{ userStore.realName }}！我是你的 AI 教学助手</h2>
          <p>我可以帮你出题、组卷、批改、规划学习、解答疑惑、整理笔记</p>
        </div>

        <div v-for="(m, i) in messages" :key="i" class="msg" :class="m.role">
          <div class="bubble" v-if="m.role === 'user'">{{ m.content }}</div>
          <div class="bubble ai" v-else>
            <div v-if="m.thinking" class="typing">
              <span></span><span></span><span></span>
            </div>
            <template v-else>
              <div class="markdown-body" v-html="renderMd(m.content)"></div>

              <div v-if="m.data?.paper" class="result-block">
                <div class="rb-title">试卷预览（{{ m.data.paper.item_count }} 题 / {{ m.data.paper.total_score }} 分）</div>
                <div v-for="(it, n) in m.data.paper.items" :key="n" class="paper-item">
                  {{ n + 1 }}. {{ stripHtml(it.stem).slice(0, 60) }}
                  <el-tag size="small" style="margin-left:6px">{{ it.score }}分</el-tag>
                </div>
                <div v-if="m.data.knowledge_coverage" class="rb-note">
                  知识点覆盖 {{ m.data.knowledge_coverage.total_points }} 个 ·
                  {{ m.data.knowledge_coverage.balance }}
                </div>
              </div>

              <div v-if="m.data?.questions?.length" class="result-block">
                <div v-for="(q, n) in m.data.questions" :key="n" class="paper-item">
                  {{ n + 1 }}. {{ stripHtml(q.stem).slice(0, 70) }}
                </div>
              </div>

              <div v-if="m.data?.related_questions?.length" class="result-block">
                <div class="rb-title">同类练习</div>
                <div v-for="(q, n) in m.data.related_questions" :key="n" class="paper-item">
                  {{ n + 1 }}. {{ stripHtml(q.stem).slice(0, 60) }}
                  <el-button link type="primary" size="small" @click="toggleA(i, n)">
                    {{ expanded[`${i}-${n}`] ? '收起' : '看答案' }}
                  </el-button>
                  <div v-if="expanded[`${i}-${n}`]" class="answer-box">
                    <div><b>答案：</b>{{ q.answer }}</div>
                    <div v-if="q.analysis"><b>解析：</b>{{ q.analysis }}</div>
                  </div>
                </div>
              </div>

              <div v-if="m.data?.study_tips?.length" class="result-block">
                <div class="rb-title">学习建议</div>
                <ul style="margin:0;padding-left:18px">
                  <li v-for="(t, n) in m.data.study_tips" :key="n">{{ t }}</li>
                </ul>
              </div>

              <div v-if="m.data?.references?.length" class="result-block">
                <div class="rb-title">引用来源</div>
                <div v-for="(ref, n) in m.data.references" :key="`ref-${n}`" class="ref-item">
                  <el-tag size="small" effect="plain">{{ ref.type }}</el-tag>
                  <span class="ref-name">{{ ref.name }}</span>
                  <span v-if="ref.knowledge_point_name || ref.path" class="muted">
                    {{ ref.knowledge_point_name || '' }}<template v-if="ref.path"> · {{ ref.path }}</template>
                  </span>
                </div>
              </div>

              <div v-if="m.data?.weak_points?.length" class="result-block">
                <div class="rb-title">薄弱知识点</div>
                <el-tag v-for="w in m.data.weak_points" :key="w.name" size="small"
                        type="danger" style="margin:2px">{{ w.name }} {{ w.mastery }}%</el-tag>
              </div>

              <div v-if="m.data?.daily_plan?.length" class="result-block">
                <div class="rb-title">学习计划</div>
                <div v-for="d in m.data.daily_plan.slice(0, 5)" :key="d.date" class="plan-day">
                  <b>{{ d.date }}</b>（{{ d.duration }}分钟）
                  <ul style="margin:4px 0 0;padding-left:18px">
                    <li v-for="(t, n) in d.tasks" :key="n">{{ t.content }}</li>
                  </ul>
                </div>
              </div>

              <div class="msg-meta">
                <el-tag size="small" effect="plain">{{ agentLabel(m.agent) }}</el-tag>
                <span v-if="m.duration">{{ m.duration }}ms</span>
                <el-tag v-if="m.fallback" size="small" type="warning" effect="plain">规则引擎降级</el-tag>
                <el-tag v-if="m.stopped" size="small" type="info" effect="plain">已停止</el-tag>
                <span class="msg-actions">
                  <el-button v-if="!m.thinking && m.content" link type="primary" size="small"
                             @click="copyAnswer(m)">复制</el-button>
                  <el-button v-if="i === messages.length - 1 && !loading && lastUserIndex >= 0"
                             link type="primary" size="small" @click="regenerate">重新生成</el-button>
                </span>
              </div>
            </template>
          </div>
        </div>
      </div>

      <div class="input-bar">
        <div class="filters">
          <el-select v-model="ctx.grade_id" placeholder="年级（选填）" clearable size="small" style="width:140px">
            <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
          <el-select v-model="ctx.subject_id" placeholder="学科（选填）" clearable size="small" style="width:140px">
            <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
          <el-button v-if="!loading && lastUserText" size="small" :icon="RefreshRight"
                     @click="regenerate">重新生成</el-button>
        </div>
        <div class="input-row">
          <el-input ref="inputRef" v-model="input" type="textarea" :rows="2" resize="none" maxlength="500"
                    placeholder="描述你的需求，Enter 发送，Shift+Enter 换行"
                    @keydown.enter.exact.prevent="send" />
          <el-button v-if="loading" type="danger" plain :icon="VideoPause"
                     @click="stopGeneration">停止生成</el-button>
          <el-button v-else type="primary" :icon="Promotion" @click="send">发送</el-button>
        </div>
        <div class="tip">{{ input.length }}/500 · AI 生成内容仅供参考，请结合教材核实</div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import MarkdownIt from 'markdown-it'
import { sanitizeHtml } from '@/utils/sanitize'
import { Delete, Promotion, Cpu, MagicStick, RefreshRight, VideoPause } from '@element-plus/icons-vue'
import { agentApi, eduApi } from '@/api'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()
const router = useRouter()
const isAdmin = computed(() => userStore.isAdmin === true)
const md = new MarkdownIt()

const input = ref('')
const messages = ref([])
const loading = ref(false)
const status = ref({})
const grades = ref([])
const subjects = ref([])
const expanded = ref({})
const scrollBox = ref()
const ctx = ref({ grade_id: null, subject_id: null })
let abortController = null

// 对话持久化：localStorage 保留最近 50 条，刷新不丢
const STORAGE_KEY = 'edu_chat_v2'
const MAX_MESSAGES = 50

// 状态卡：兼容新旧字段名，key_configured 缺失时显示「未知」
const providerName = computed(() =>
  status.value?.provider || status.value?.llm_provider || '-')
const modelName = computed(() =>
  status.value?.model || status.value?.llm_model || '未配置')
const keyConfigured = computed(() => {
  const v = status.value?.key_configured
  return typeof v === 'boolean' ? v : null
})
const keyLabel = computed(() => {
  if (keyConfigured.value === true) return '已配置'
  if (keyConfigured.value === false) return '未配置'
  return '未知'
})
const keyTagType = computed(() => {
  if (keyConfigured.value === true) return 'success'
  if (keyConfigured.value === false) return 'danger'
  return 'info'
})
const showConfigHint = computed(() => status.value?.llm_enabled === false)

function goAiConfig() { router.push('/admin/ai-config') }

const lastUserIndex = computed(() => {
  for (let i = messages.value.length - 1; i >= 0; i--) {
    if (messages.value[i]?.role === 'user') return i
  }
  return -1
})
const lastUserText = computed(() => {
  const i = lastUserIndex.value
  return i >= 0 ? String(messages.value[i]?.content || '') : ''
})

const samples = [
  '帮我出一套七年级数学有理数单元测试卷',
  '什么是艾宾浩斯遗忘曲线',
  '帮我规划一周的复习计划',
  '这道题为什么错了：2x + 3 = 7'
]

const AGENT_LABEL = {
  question_generator: '题库生成', paper_composer: '智能组卷',
  grading_assistant: '智能批改', study_planner: '学习规划',
  tutor: '答疑助教', note_organizer: '笔记整理', router: '需求路由'
}

function agentLabel(n) { return AGENT_LABEL[n] || n || 'AI 助手' }
// markdown-it 默认 html:false（不解析裸标签），但 [x](javascript:...) 这类
// 链接语法仍会生成可点击的恶意 href；LLM 输出也可能夹带 <img onerror>。
// 统一再走一次白名单净化，杜绝 AI 回复成为 XSS 载体。
function renderMd(t) { return sanitizeHtml(md.render(t || '')) }
function stripHtml(s) { return String(s || '').replace(/<[^>]*>/g, '') }
function toggleA(i, n) { expanded.value[`${i}-${n}`] = !expanded.value[`${i}-${n}`] }

async function scrollBottom() {
  await nextTick()
  if (scrollBox.value) scrollBox.value.scrollTop = scrollBox.value.scrollHeight
}

/** 持久化最近 50 条消息（去掉 thinking/streaming 等瞬时字段）。 */
function persistMessages() {
  try {
    const payload = messages.value
      // 过滤「正在生成、尚无内容」的空 AI 气泡，避免刷新后出现空白回答
      .filter(m => !(m.role === 'ai' && !m.content && !m.data))
      .slice(-MAX_MESSAGES)
      .map(m => ({
        role: m.role,
        content: m.content,
        data: m.data,
        agent: m.agent,
        duration: m.duration,
        fallback: m.fallback,
        stopped: m.stopped
      }))
    localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
  } catch {
    // 存储满/隐私模式时忽略
  }
}

function loadStoredMessages() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return
    const arr = JSON.parse(raw)
    if (!Array.isArray(arr)) return
    messages.value = arr
      .filter(m => !(m.role === 'ai' && !m.content && !m.data))
      .slice(-MAX_MESSAGES)
      .map(m => ({
        ...m,
        thinking: false,
        streaming: false,
        content: m.thinking ? (m.content || '（上次生成已中断）') : m.content
      }))
  } catch {
    // 历史数据损坏时忽略
  }
}

/** 流式发送：fetch + ReadableStream 逐段渲染（SSE 协议手动解析）。
 *  优势：首字延迟 ~1s，用户不必盯着转圈 20-60 秒。
 *  兼容：若服务端未返回流（旧版本/网关缓冲），自动回退为普通请求。 */
async function send(explicitText) {
  const text = (typeof explicitText === 'string' ? explicitText : input.value).trim()
  if (!text || loading.value) return
  input.value = ''
  messages.value.push({ role: 'user', content: text })
  const idx = messages.value.length
  messages.value.push({ role: 'ai', thinking: true, content: '', streaming: true })
  loading.value = true
  persistMessages()
  scrollBottom()

  const controller = new AbortController()
  abortController = controller
  const signal = controller.signal
  const token = localStorage.getItem('access_token') || ''
  const base = import.meta.env.VITE_API_BASE || '/api/v1'
  let acc = ''
  let meta = {}
  let fallback = false
  try {
    const resp = await fetch(`${base}/agent/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({
        message: text, grade_id: ctx.value.grade_id, subject_id: ctx.value.subject_id
      }),
      signal
    })
    if (!resp.ok || !resp.body) throw new Error(`HTTP ${resp.status}`)
    const ctype = resp.headers.get('content-type') || ''
    if (!ctype.includes('event-stream')) throw new Error('服务端未启用流式')

    const reader = resp.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buf = ''
    let dataBlock = null

    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buf += decoder.decode(value, { stream: true })
      const parts = buf.split('\n\n')
      buf = parts.pop() || ''
      for (const part of parts) {
        const line = part.split('\n').find(l => l.startsWith('data:'))
        if (!line) continue
        let ev
        try { ev = JSON.parse(line.slice(5).trim()) } catch { continue }
        if (ev.type === 'meta') {
          meta = ev
          messages.value[idx].agent = ev.agent
        } else if (ev.type === 'delta') {
          acc += ev.text || ''
          messages.value[idx].content = acc
          messages.value[idx].thinking = false
          scrollBottom()
        } else if (ev.type === 'done') {
          dataBlock = ev.data || null
          fallback = !!ev.is_fallback
          messages.value[idx] = {
            ...messages.value[idx],
            content: acc || messages.value[idx].content || '（无内容返回）',
            data: dataBlock,
            agent: ev.agent || meta.agent,
            duration: ev.duration_ms,
            fallback,
            thinking: false,
            streaming: false
          }
        } else if (ev.type === 'error') {
          throw new Error(ev.message || '生成失败')
        }
      }
    }
    if (messages.value[idx]?.thinking) {
      messages.value[idx] = {
        ...messages.value[idx],
        content: acc || '（无内容返回）',
        thinking: false, streaming: false,
        agent: meta.agent, fallback
      }
    }
  } catch (e) {
    const current = messages.value[idx]
    if (e?.name === 'AbortError' || signal.aborted) {
      // 用户主动停止生成：保留已生成的部分内容
      if (current) {
        messages.value[idx] = {
          ...current,
          content: current.content || '已停止生成',
          thinking: false, streaming: false, stopped: true
        }
      }
    } else {
      // 流式不可用时回退到普通请求（用户已停止则不再回退）
      try {
        const res = await agentApi.chat({
          message: text, grade_id: ctx.value.grade_id, subject_id: ctx.value.subject_id
        })
        const d = res.data || {}
        messages.value[idx] = {
          role: 'ai',
          content: d.answer || '（无内容返回）',
          data: d.data,
          agent: d.agent,
          duration: d.duration_ms,
          fallback: d.is_fallback
        }
      } catch (e2) {
        messages.value[idx] = { role: 'ai', content: `请求失败：${e2.message || e.message}` }
      }
    }
  } finally {
    abortController = null
    loading.value = false
    persistMessages()
    scrollBottom()
  }
}

/** 停止流式生成（AbortController）。 */
function stopGeneration() {
  if (abortController) abortController.abort()
}

/** 复制 AI 回答（优先 clipboard，失败回退 textarea）。 */
async function copyAnswer(m) {
  const text = String(m?.content || '')
  if (!text) return
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text)
    } else {
      const ta = document.createElement('textarea')
      ta.value = text
      ta.style.position = 'fixed'
      ta.style.opacity = '0'
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
    }
    ElMessage.success('已复制回答')
  } catch {
    ElMessage.error('复制失败，请手动选择文本复制')
  }
}

/** 重新生成：删掉最后一次问答，用同样的提问重新发送。 */
function regenerate() {
  if (loading.value) return ElMessage.warning('正在生成中，请先停止或等待完成')
  const idx = lastUserIndex.value
  if (idx < 0) return ElMessage.warning('没有可重新生成的问题')
  const text = String(messages.value[idx]?.content || '')
  messages.value = messages.value.slice(0, idx)
  persistMessages()
  scrollBottom()
  send(text)
}

function ask(q) { send(q) }

function clear() {
  if (loading.value) stopGeneration()
  messages.value = []
  expanded.value = {}
  localStorage.removeItem(STORAGE_KEY)
  scrollBottom()
}

onMounted(async () => {
  loadStoredMessages()
  scrollBottom()
  const s = await agentApi.status()
  status.value = s.data || {}
  const g = await eduApi.grades()
  grades.value = g.data
  const sub = await eduApi.subjects({ distinct: true })
  subjects.value = sub.data
})
</script>

<style scoped>
.chat-page { display: flex; height: calc(100vh - 60px); background: var(--page-bg); }
.side {
  width: 250px; background: #fff; border-right: 1px solid #ebeef5;
  padding: 14px; display: flex; flex-direction: column; gap: 14px; overflow-y: auto;
}
.engine-status {
  padding: 12px; border-radius: 8px; background: #fdf6ec; border: 1px solid #f5dab1;
}
.engine-status.on { background: #f0f9eb; border-color: #e1f3d8; }
.st-title { display: flex; align-items: center; gap: 6px; font-weight: 600; margin-bottom: 8px; font-size: 13px; }
.st-row { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px; color: #606266; }
.st-row b { color: #303133; font-weight: 500; }
.side-block { flex: 1; }
.sb-title { font-size: 12px; color: #909399; margin-bottom: 8px; }
.sample {
  padding: 8px 10px; margin-bottom: 6px; border-radius: 6px; background: #f5f7fa;
  font-size: 12px; cursor: pointer; line-height: 1.5;
}
.sample:hover { background: #ecf5ff; color: #2f6fd0; }
.main { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.messages { flex: 1; overflow-y: auto; padding: 20px; }
.welcome { text-align: center; padding: 80px 20px; color: #909399; }
.welcome h2 { color: #303133; font-size: 20px; margin: 16px 0 8px; }
.msg { display: flex; margin-bottom: 18px; }
.msg.user { justify-content: flex-end; }
.bubble {
  max-width: 78%; padding: 12px 16px; border-radius: 10px; background: #2f6fd0;
  color: #fff; line-height: 1.7; white-space: pre-wrap;
}
.bubble.ai {
  background: #fff; color: #303133; max-width: 88%; width: 88%;
  box-shadow: 0 1px 4px rgba(0,0,0,.06); border: 1px solid #ebeef5;
}
.bubble.ai :deep(.markdown-body h1),
.bubble.ai :deep(.markdown-body h2),
.bubble.ai :deep(.markdown-body h3) { font-size: 15px; margin: 12px 0 6px; }
.typing { display: flex; gap: 5px; padding: 6px 0; }
.typing span {
  width: 7px; height: 7px; border-radius: 50%; background: #909399;
  animation: bounce 1.4s infinite ease-in-out;
}
.typing span:nth-child(2) { animation-delay: .2s; }
.typing span:nth-child(3) { animation-delay: .4s; }
@keyframes bounce { 0%,80%,100% { transform: scale(.6); opacity:.5 } 40% { transform: scale(1); opacity:1 } }
.result-block {
  margin-top: 12px; padding: 10px 12px; background: #f8fafc;
  border-radius: 6px; border-left: 3px solid #2f6fd0; font-size: 13px;
}
.rb-title { font-weight: 600; margin-bottom: 6px; color: #2f6fd0; }
.paper-item { margin-bottom: 5px; line-height: 1.6; }
.rb-note { margin-top: 6px; color: #909399; font-size: 12px; }
.answer-box { margin-top: 5px; padding: 8px; background: #fff; border-radius: 4px; font-size: 12px; }
.ref-item { display: flex; align-items: center; gap: 8px; padding: 4px 0; font-size: 13px; }
.ref-name { font-weight: 500; }
.plan-day { margin-bottom: 8px; font-size: 12px; }
.refs { margin-top: 10px; font-size: 12px; color: #909399; }
.msg-meta {
  display: flex; align-items: center; gap: 8px; margin-top: 10px;
  padding-top: 8px; border-top: 1px solid #f0f0f0; font-size: 11px; color: #c0c4cc;
}
.msg-actions { margin-left: auto; display: inline-flex; align-items: center; gap: 4px; }
.input-bar { padding: 12px 20px 14px; background: #fff; border-top: 1px solid #ebeef5; }
.filters { display: flex; gap: 8px; margin-bottom: 8px; }
.input-row { display: flex; gap: 10px; align-items: flex-end; }
.tip { font-size: 11px; color: #c0c4cc; margin-top: 6px; text-align: right; }
@media (max-width: 900px) { .side { display: none; } .bubble { max-width: 94%; } }
</style>
