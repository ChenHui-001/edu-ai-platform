<template>
  <!-- 紧凑模式：页脚一行（点击/悬停看详情），窄屏自动省略构建号与更新时间 -->
  <el-tooltip v-if="compact" placement="top" effect="light" :show-after="120">
    <template #content>
      <div style="line-height: 1.9; font-size: 12px; min-width: 180px">
        <div>版本号：v{{ version }}</div>
        <div>构建号：{{ buildNumber || '—' }}</div>
        <div>构建时间：{{ builtAtText }}</div>
        <div>最后更新：{{ updatedAtText }}</div>
      </div>
    </template>
    <span class="ver-compact">
      <span>{{ info?.app_name || '版本' }} v{{ version }}</span>
      <span v-if="buildNumber" class="ver-extra"> · 构建 {{ buildNumber }}</span>
      <span v-if="info?.updated_at" class="ver-extra"> · 更新于 {{ updatedAtText }}</span>
    </span>
  </el-tooltip>

  <!-- 完整模式：卡片（系统配置页） -->
  <el-card v-else shadow="never" class="ver-card" v-loading="loading">
    <template #header>
      <div class="ver-head">
        <b>版本信息</b>
        <el-tag size="small" type="success" effect="plain">v{{ version }}</el-tag>
        <el-tag v-if="info?.prior_version" size="small" type="info" effect="plain">
          由 v{{ info.prior_version }} 升级
        </el-tag>
        <span class="ver-head-hint">版本更新时由系统自动记录更新时间</span>
      </div>
    </template>

    <div class="ver-grid">
      <div class="ver-cell">
        <div class="ver-label">当前版本号</div>
        <div class="ver-val">v{{ version }}</div>
      </div>
      <div class="ver-cell">
        <div class="ver-label">构建号</div>
        <div class="ver-val mono" :title="info?.commit || ''">{{ buildNumber || '—' }}</div>
      </div>
      <div class="ver-cell">
        <div class="ver-label">构建时间</div>
        <div class="ver-val">{{ builtAtText }}</div>
      </div>
      <div class="ver-cell">
        <div class="ver-label">最后更新时间</div>
        <div class="ver-val">
          {{ updatedAtText }}
          <span v-if="updatedAgo" class="ver-ago">（{{ updatedAgo }}）</span>
        </div>
      </div>
    </div>

    <div class="ver-foot">
      <el-icon><InfoFilled /></el-icon>
      <span>{{ sourceHint }}</span>
    </div>
  </el-card>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { InfoFilled } from '@element-plus/icons-vue'
import { systemApi } from '@/api'
import { parseServerDate } from '@/utils/date'

defineProps({
  // 页脚用紧凑模式；系统配置页用完整卡片
  compact: { type: Boolean, default: false }
})

const info = ref(null)
const loading = ref(false)

// 模块级缓存：同一页面里页脚与配置卡片可能同时存在，没必要请求两次。
// 版本信息一次部署内不会变，缓存到模块生命周期即可（不做 TTL）。
let cached = null
let inflight = null

async function fetchInfo(force = false) {
  if (cached && !force) {
    info.value = cached
    return cached
  }
  if (inflight) return inflight
  loading.value = true
  inflight = systemApi.versionInfo()
    .then((res) => {
      // 后端统一信封：{ code, message, data }
      cached = res?.data || null
      info.value = cached
      return cached
    })
    .catch(() => null)
    .finally(() => {
      loading.value = false
      inflight = null
    })
  return inflight
}

const version = computed(() => info.value?.version || '—')
const buildNumber = computed(() => info.value?.build_number || '')

// 后端返回的是服务端本地时间字符串（naive），统一走 parseServerDate，
// 不能用 new Date(str)（Safari 对 "YYYY-MM-DD HH:mm:ss" 解析为 Invalid Date）。
function fmtDateTime(value) {
  const d = parseServerDate(value)
  if (!d) return value ? String(value) : '—'
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

const builtAtText = computed(() => fmtDateTime(info.value?.built_at))
const updatedAtText = computed(() => fmtDateTime(info.value?.updated_at))

// 「3 天前」这类相对时间：绝对时间对「什么时候更新的」不直观，
// 相对时间能让用户一眼看出「这个部署是新的还是很久没动过」。
const updatedAgo = computed(() => {
  const d = parseServerDate(info.value?.updated_at)
  if (!d) return ''
  const diff = Date.now() - d.getTime()
  if (diff < 0) return ''
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return '刚刚'
  if (mins < 60) return `${mins} 分钟前`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours} 小时前`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days} 天前`
  const months = Math.floor(days / 30)
  return months < 12 ? `${months} 个月前` : `${Math.floor(months / 12)} 年前`
})

// 如实说明时间戳的来源，避免把「镜像构建时间」误读成「上线时间」
const sourceHint = computed(() => {
  switch (info.value?.updated_source) {
    case 'recorded':
      return '该时间由系统在版本号或构建号变化时自动记录，同版本重启不会刷新'
    case 'build':
      return '尚未记录版本更新时间，暂显示镜像构建时间（首次启动后自动补齐）'
    case 'startup':
      return '本地开发环境（无镜像构建信息），暂显示本次进程启动时间'
    default:
      return '版本信息加载中'
  }
})

onMounted(() => { fetchInfo() })

defineExpose({ refresh: () => fetchInfo(true) })
</script>

<style scoped>
/* ---------------- 紧凑模式（页脚） ---------------- */
.ver-compact {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  font-size: 12px;
  color: #909399;
  cursor: default;
  white-space: nowrap;
}

/* 窄屏只留版本号：构建号/更新时间在「系统配置 → 版本信息」里看 */
@media (max-width: 768px) {
  .ver-extra { display: none; }
}

/* ---------------- 完整模式（卡片） ---------------- */
/* 容器查询：列数按「卡片自身宽度」而不是视口宽度决定 —— 侧边栏 220px
   会吃掉一截，同一视口下卡片实际宽度可能差 150px，用 @media 判断会错档。
   下面 auto-fit 规则是不支持容器查询时的兜底。 */
.ver-card {
  container-type: inline-size;
}

.ver-head {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.ver-head-hint {
  margin-left: auto;
  font-size: 12px;
  font-weight: 400;
  color: #909399;
}

/* auto-fit + minmax 实现响应式：宽屏 4 列 → 中等 2 列 → 手机 1 列，
   不依赖 JS 监听 resize。240px 是「标签 + 一行日期」不换行的下限。 */
.ver-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
}

.ver-cell {
  padding: 12px 14px;
  border-radius: 8px;
  background: #f7f9fc;
  border: 1px solid #ebeef5;
}

.ver-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;
}

.ver-val {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  word-break: break-all;
}

.ver-val.mono {
  font-family: Consolas, Monaco, monospace;
  font-size: 14px;
  letter-spacing: 0.3px;
}

.ver-ago {
  font-size: 12px;
  font-weight: 400;
  color: #909399;
}

.ver-foot {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
  font-size: 12px;
  color: #909399;
}

@media (max-width: 768px) {
  .ver-head-hint { margin-left: 0; width: 100%; }
  .ver-grid { grid-template-columns: 1fr; gap: 10px; }
  .ver-val { font-size: 14px; }
}

/* 容器查询优先于上面的 auto-fit / 媒体查询：宽松屏 4 列、中等 2×2、
   窄屏 1 列。避免出现「3 列 + 孤零零 1 个」的不平衡排版。 */
@container (min-width: 1080px) {
  .ver-grid { grid-template-columns: repeat(4, 1fr); }
}

@container (min-width: 600px) and (max-width: 1079px) {
  .ver-grid { grid-template-columns: repeat(2, 1fr); }
}

@container (max-width: 599px) {
  .ver-grid { grid-template-columns: 1fr; gap: 10px; }
}
</style>
