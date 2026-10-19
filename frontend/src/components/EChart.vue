<template>
  <div ref="el" class="echart-box" :style="{ height, width: '100%' }" />
</template>

<script setup>
/** ECharts 的 Vue3 包装组件。
 *
 * 此前项目误用 echarts-for-react（React 组件库），在 Vue3 下渲染时抛
 * 「Cannot set properties of undefined (setting 'props')」，全站图表
 * 无法显示。本组件用原生 echarts 封装，接口与原用法对齐：
 *   <EChart :option="opt" style="height: 300px" />
 * 支持 option 深度 watch 更新、容器 resize 自适应、卸载时 dispose。
 */
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  option: { type: Object, required: true },
  height: { type: String, default: '300px' },
})

const el = ref(null)
let chart = null
let ro = null

onMounted(() => {
  chart = echarts.init(el.value)
  if (props.option) chart.setOption(props.option)
  // 容器尺寸变化（侧栏折叠/窗口缩放）时自适应
  ro = new ResizeObserver(() => chart && chart.resize())
  ro.observe(el.value)
})

watch(
  () => props.option,
  (opt) => {
    if (chart && opt) chart.setOption(opt, { notMerge: true })
  },
  { deep: true }
)

onBeforeUnmount(() => {
  if (ro) ro.disconnect()
  if (chart) {
    chart.dispose()
    chart = null
  }
})
</script>

<style scoped>
.echart-box { min-height: 120px; }
</style>
