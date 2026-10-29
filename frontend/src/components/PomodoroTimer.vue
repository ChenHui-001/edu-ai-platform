<template>
  <div class="pomodoro-widget" :class="{ expanded: !minimized }">
    <div class="pomodoro-header" @click="minimized = !minimized">
      <el-icon><Timer /></el-icon>
      <span v-if="!minimized" class="pomodoro-title">专注番茄钟</span>
      <span class="pomodoro-time" :class="{ working: mode === 'work', resting: mode === 'rest' }">
        {{ displayTime }}
      </span>
      <el-icon v-if="minimized" class="expand-icon"><ArrowUp /></el-icon>
      <el-icon v-else class="expand-icon"><ArrowDown /></el-icon>
    </div>

    <transition name="slide">
      <div v-show="!minimized" class="pomodoro-body">
        <div class="pomodoro-ring" :class="mode">
          <svg viewBox="0 0 120 120" class="ring-svg">
            <circle cx="60" cy="60" r="52" fill="none" stroke="#e4e7ed" stroke-width="6" />
            <circle cx="60" cy="60" r="52" fill="none"
                    :stroke="mode === 'work' ? '#f56c6c' : '#67c23a'"
                    stroke-width="6" stroke-linecap="round"
                    :stroke-dasharray="326.7"
                    :stroke-dashoffset="ringOffset"
                    transform="rotate(-90 60 60)"
                    style="transition: stroke-dashoffset 1s linear" />
          </svg>
          <div class="ring-center">
            <div class="ring-time">{{ displayTime }}</div>
            <div class="ring-label">{{ modeText }}</div>
          </div>
        </div>

        <div class="pomodoro-stats">
          <div class="stat">
            <div class="stat-val">{{ completedPomodoros }}</div>
            <div class="stat-label">完成番茄</div>
          </div>
          <div class="stat">
            <div class="stat-val">{{ totalFocusMinutes }}</div>
            <div class="stat-label">专注分钟</div>
          </div>
        </div>

        <div class="pomodoro-controls">
          <el-button v-if="!running" type="primary" size="small" :icon="VideoPlay"
                     @click="start">开始专注</el-button>
          <el-button v-else type="warning" size="small" :icon="VideoPause"
                     @click="pause">暂停</el-button>
          <el-button size="small" :icon="RefreshRight" @click="reset">重置</el-button>
        </div>

        <div class="pomodoro-settings">
          <span>专注时长</span>
          <el-input-number v-model="workMinutes" :min="10" :max="50" :step="5" size="small"
                           :disabled="running" style="width: 80px" /> 分
          <span class="ml8">休息</span>
          <el-input-number v-model="restMinutes" :min="3" :max="15" :step="1" size="small"
                           :disabled="running" style="width: 70px" /> 分
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import { Timer, ArrowUp, ArrowDown, VideoPlay, VideoPause, RefreshRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const emit = defineEmits(['focus-complete'])

const minimized = ref(false)
const running = ref(false)
const mode = ref('work') // work | rest
const workMinutes = ref(25)
const restMinutes = ref(5)
const remaining = ref(25 * 60)
const completedPomodoros = ref(0)
const totalFocusSeconds = ref(0)
let timerId = null

const CIRCUMFERENCE = 2 * Math.PI * 52 // ~326.7

const totalSeconds = computed(() => mode.value === 'work' ? workMinutes.value * 60 : restMinutes.value * 60)

const ringOffset = computed(() => {
  const progress = (totalSeconds.value - remaining.value) / totalSeconds.value
  return CIRCUMFERENCE * (1 - progress)
})

const displayTime = computed(() => {
  const m = Math.floor(remaining.value / 60)
  const s = remaining.value % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
})

const modeText = computed(() => mode.value === 'work' ? '专注中' : '休息中')

const totalFocusMinutes = computed(() => Math.floor(totalFocusSeconds.value / 60))

function start() {
  if (running.value) return
  running.value = true
  timerId = setInterval(tick, 1000)
}

function pause() {
  running.value = false
  if (timerId) clearInterval(timerId)
}

function reset() {
  pause()
  mode.value = 'work'
  remaining.value = workMinutes.value * 60
}

function tick() {
  if (remaining.value > 0) {
    remaining.value--
    if (mode.value === 'work') {
      totalFocusSeconds.value++
    }
  } else {
    // 一轮结束
    if (mode.value === 'work') {
      completedPomodoros.value++
      emit('focus-complete', { pomodoros: completedPomodoros.value, minutes: workMinutes.value })
      ElMessage.success(`专注完成！休息 ${restMinutes.value} 分钟`)
      mode.value = 'rest'
      remaining.value = restMinutes.value * 60
    } else {
      ElMessage.info('休息结束，继续专注吧！')
      mode.value = 'work'
      remaining.value = workMinutes.value * 60
    }
  }
}

watch([workMinutes, restMinutes], () => {
  if (!running.value) {
    remaining.value = mode.value === 'work' ? workMinutes.value * 60 : restMinutes.value * 60
  }
})

onUnmounted(() => {
  if (timerId) clearInterval(timerId)
})
</script>

<style scoped>
.pomodoro-widget {
  position: fixed;
  right: 20px;
  bottom: 20px;
  z-index: 999;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.12);
  border: 1px solid #e4e7ed;
  overflow: hidden;
  transition: all 0.3s;
}

.pomodoro-widget.expanded {
  width: 240px;
}

.pomodoro-widget:not(.expanded) {
  width: 160px;
}

.pomodoro-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  cursor: pointer;
  background: linear-gradient(135deg, #f56c6c 0%, #e6a23c 100%);
  color: #fff;
  font-size: 13px;
  font-weight: 500;
}

.pomodoro-title { flex: 1; }

.pomodoro-time {
  font-family: 'Courier New', monospace;
  font-weight: 700;
  font-size: 14px;
}

.pomodoro-time.working { color: #fff; }
.pomodoro-time.resting { color: #f0f9eb; }

.expand-icon { margin-left: auto; }

.pomodoro-body {
  padding: 16px;
  text-align: center;
}

.pomodoro-ring {
  position: relative;
  width: 120px;
  height: 120px;
  margin: 0 auto 12px;
}

.ring-svg { width: 120px; height: 120px; }

.ring-center {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.ring-time {
  font-size: 22px;
  font-weight: 700;
  font-family: 'Courier New', monospace;
  color: #303133;
}

.pomodoro-ring.working .ring-time { color: #f56c6c; }
.pomodoro-ring.resting .ring-time { color: #67c23a; }

.ring-label {
  font-size: 11px;
  color: #909399;
  margin-top: 2px;
}

.pomodoro-stats {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-bottom: 12px;
}

.stat-val {
  font-size: 18px;
  font-weight: 700;
  color: #409eff;
}

.stat-label {
  font-size: 11px;
  color: #909399;
}

.pomodoro-controls {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-bottom: 12px;
}

.pomodoro-settings {
  font-size: 12px;
  color: #606266;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.slide-enter-active, .slide-leave-active { transition: all 0.3s; }
.slide-enter-from, .slide-leave-to { opacity: 0; transform: translateY(-10px); }
</style>
