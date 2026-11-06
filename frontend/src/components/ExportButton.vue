<template>
  <el-button :icon="Download" :loading="loading" :type="type" @click="$emit('click')">
    <slot>导出</slot>
  </el-button>
</template>

<script setup>
import { Download } from '@element-plus/icons-vue'

// 全站 38 处导出按钮此前各写一遍 icon / loading / 文案。
// 先抽出一个最小公共件并在错题本接入，后续页面可逐步替换。
defineProps({
  loading: { type: Boolean, default: false },
  type: { type: String, default: 'default' },
})
defineEmits(['click'])
</script>
