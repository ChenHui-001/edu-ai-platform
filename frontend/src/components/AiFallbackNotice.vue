<template>
  <!--
    AI 降级提示条（U-03）。全站唯一口径：el-alert type=warning + show-icon。

    为什么必须统一：`is_fallback=true` 表示结果**不是模型产出的**，而是规则引擎
    按教材顺序挑的。同一个事实此前有 5 种表达（el-alert / el-tag / ElMessage.toast /
    tooltip / 什么都不显示），用户要么看不到、要么看到也不知道意味着什么。
    统一成一条可读的提示条，并在文案里说清「能不能用、为什么、怎么办」。
  -->
  <el-alert
    v-if="show"
    class="ai-fallback-notice"
    type="warning"
    :closable="false"
    show-icon
    :title="title"
  >
    <span class="ai-fallback-detail">{{ detail }}</span>
  </el-alert>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  /** 是否显示：一般直接绑后端返回的 `is_fallback` */
  show: { type: Boolean, default: false },
  /** 自定义标题；留空用统一文案 */
  title: { type: String, default: '' },
  /** 自定义说明；留空用统一说明 */
  detail: { type: String, default: '' },
  /** 传了就用它替换默认说明（例如「已用题库同条件题目替换」） */
  reason: { type: String, default: '' },
})

const title = computed(() =>
  props.title || '当前未接入可用的大模型，本次结果由规则引擎降级生成')

const detail = computed(() => {
  if (props.detail) return props.detail
  if (props.reason) return `${props.reason}；配置大模型后重试可获得更好的结果。`
  return '规则引擎按教材顺序与知识点匹配挑选，不会按难度梯度做智能调整；'
    + '到「系统设置 → AI 配置」配好模型后可重试获得更好的结果。'
})
</script>

<style scoped>
.ai-fallback-notice { margin-bottom: 12px; }
.ai-fallback-detail { font-size: 12px; line-height: 1.6; }
</style>
