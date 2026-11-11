<template>
  <!-- 桌面端：默认插槽原样透传（把既有 el-table 放进来），对现有页面零破坏 -->
  <div v-if="!isMobile">
    <slot />
  </div>
  <!-- 移动端：el-table 换成卡片列表，横向滚动表格在手机上会挤成竖排汉字 -->
  <div v-else class="table-cards" v-loading="loading">
    <el-empty v-if="!rows.length" :description="emptyText" :image-size="80" />
    <div v-for="(row, idx) in rows" :key="rowKey(row, idx)" class="table-card">
      <div v-for="col in columns" :key="col.prop" class="table-card__row">
        <span class="table-card__label">{{ col.label }}</span>
        <span class="table-card__value">
          <slot :name="`cell-${col.prop}`" :row="row">
            {{ formatCellValue(row, col) }}
          </slot>
        </span>
      </div>
      <div v-if="$slots.actions" class="table-card__actions">
        <slot name="actions" :row="row" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { useIsMobile, formatCellValue } from '@/utils/responsive'

// 用法：
//   <TableCards :rows="list" :columns="cols">
//     <el-table :data="list">...</el-table>   <!-- 桌面原样渲染 -->
//     <template #cell-status="{ row }">…</template>  <!-- 移动端某列自定义 -->
//     <template #actions="{ row }">…</template>      <!-- 移动端操作区 -->
//   </TableCards>
// columns 与桌面 el-table 的列保持同一份定义（prop/label），formatter 可选。
const props = defineProps({
  rows: { type: Array, default: () => [] },
  columns: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  emptyText: { type: String, default: '暂无数据' },
  rowKeyField: { type: String, default: 'id' },
})

const isMobile = useIsMobile()

function rowKey(row, idx) {
  const v = row ? row[props.rowKeyField] : undefined
  return v === undefined || v === null ? idx : v
}
</script>

<style scoped>
.table-card {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 10px;
}
.table-card__row {
  display: flex; justify-content: space-between; gap: 12px;
  padding: 4px 0; font-size: 14px; line-height: 1.5;
}
.table-card__label { color: var(--el-text-color-secondary); flex-shrink: 0; }
.table-card__value { text-align: right; word-break: break-word; }
.table-card__actions {
  display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end;
  border-top: 1px dashed var(--el-border-color-lighter);
  margin-top: 8px; padding-top: 8px;
}
</style>
