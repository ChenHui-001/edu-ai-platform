<template>
  <!--
    页面级错误态（U-05）。此前报表/图表请求失败时只有两条路：
    整页空白，或者一条 3 秒后消失的红色 toast —— 两者都只能靠刷新页面重来。

    与全局红条的分工：全局红条说明「刚才那个操作失败了」，本组件说明
    「这一块数据没加载出来，可以就地重试」，所以必须带重试按钮与错误码。
  -->
  <div class="error-state">
    <el-icon class="error-state-icon"><WarningFilled /></el-icon>
    <p class="error-state-title">{{ title }}</p>
    <p v-if="message" class="error-state-msg">{{ message }}</p>
    <p v-if="code" class="error-state-code">错误码：{{ code }}</p>
    <el-button :loading="loading" type="primary" plain @click="$emit('retry')">
      {{ loading ? '重试中…' : '重新加载' }}
    </el-button>
    <slot />
  </div>
</template>

<script setup>
import { WarningFilled } from '@element-plus/icons-vue'

defineProps({
  title: { type: String, default: '数据加载失败' },
  /** 已 humanize 过的中文原因（`humanizeError` 的输出），不要塞原始异常 */
  message: { type: String, default: '' },
  /** 便于用户报障时对上号：后端信封里的 code / HTTP 状态 */
  code: { type: [String, Number], default: '' },
  /** 重试请求进行中：按钮转圈并禁用，避免连点打爆接口 */
  loading: { type: Boolean, default: false },
})

defineEmits(['retry'])
</script>

<style scoped>
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 40px 16px;
  text-align: center;
}
.error-state-icon {
  font-size: 40px;
  color: var(--el-color-warning);
  margin-bottom: 4px;
}
.error-state-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}
.error-state-msg {
  margin: 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  max-width: 520px;
  line-height: 1.6;
}
.error-state-code {
  margin: 0;
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}
</style>
