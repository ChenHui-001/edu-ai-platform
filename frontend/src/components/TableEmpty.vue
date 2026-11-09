<script setup>
/**
 * 表格空态。
 *
 * 为什么要有这个组件：Vue 里 `el-table` 的默认空态是 locale 里的「暂无数据」——
 * 一句话、没有图标、也不说明「为什么空」和「接下来能做什么」。全站 65 张表
 * 里此前有 62 张就停在这一句上（reaudit3 §3.5），同一个系统里有的表写
 * 「暂无待审批申请」、有的写「暂无任务」、有的什么都没写，读起来像不同的产品。
 *
 * 现在统一为：`<el-empty>` + 一句话。句式固定为「暂无{对象}」，需要引导时
 * 追加「，{动作}」；不写句号、不写感叹号。
 *
 * 全局注册在 main.js（而非逐文件 import）：它只是一个展示原子，被 29 个页面
 * 使用，逐页引入会把导入区撑长却没有任何收益。
 */
defineProps({
  /** 空态文案，统一句式「暂无{对象}」 */
  text: { type: String, default: '暂无数据' },
  /** 图片尺寸：表格内嵌留白有限，默认比 el-empty 的 100 小一档 */
  size: { type: Number, default: 64 }
})
</script>

<template>
  <el-empty :description="text" :image-size="size" class="table-empty" />
</template>

<style scoped>
.table-empty {
  padding: 4px 0;
}

/* el-empty 默认描述文字 14px/行高偏松，表格内需要更紧凑 */
.table-empty :deep(.el-empty__description) {
  margin-top: 4px;
}

.table-empty :deep(.el-empty__description p) {
  font-size: 13px;
  line-height: 1.5;
  color: var(--el-text-color-secondary);
  margin: 0;
}
</style>
