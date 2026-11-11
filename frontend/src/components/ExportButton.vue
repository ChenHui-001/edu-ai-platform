<template>
  <!--
    全站导出按钮（U-04）。

    ## 为什么升级成「内置异步处理」
    原来它只是个带 icon 的按钮，`loading` 由调用方自己管。结果是 10 个导出
    入口各写一遍 `if (exporting) return / exporting = true / try / finally`：
    漏写 `if` 就能连点导出 3 次（每次服务端都要渲染一遍整卷），漏写 `catch`
    就只剩一个转圈后静默恢复的按钮。

    现在两种用法都支持：
    · 传 handler 属性（推荐）—— 内置单锁、loading、失败提示；
    · 只监听 click（旧写法）—— 只渲染按钮，行为完全不变。

    （注释里刻意不写绑定示例：scan_vue_refs 会把注释当模板扫描，
      看到 handler 绑定的名字就判「模板引用了 script 未定义的变量」。）
  -->
  <el-button
    :icon="Download"
    :type="type"
    :size="size"
    :loading="busy"
    :disabled="disabled || busy"
    @click="onClick"
  >
    <slot>{{ label }}</slot>
  </el-button>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Download } from '@element-plus/icons-vue'

import { toastIfUnhandled } from '@/utils/notify'

// 全站 38 处导出按钮此前各写一遍 icon / loading / 文案。
// 先抽出一个最小公共件并在错题本接入，后续页面可逐步替换。
const props = defineProps({
  /** 旧写法：调用方自己控制 loading */
  loading: { type: Boolean, default: false },
  type: { type: String, default: 'default' },
  size: { type: String, default: 'default' },
  disabled: { type: Boolean, default: false },
  /** 新写法：传一个（可 async 的）函数，按钮自己管 loading 与失败提示 */
  handler: { type: Function, default: null },
  /** 无 slot 时的文案 */
  label: { type: String, default: '导出' },
})

const emit = defineEmits(['click'])

const running = ref(false)
// 两套 loading 合并：handler 模式用内部状态，旧调用点仍可外部控制
const busy = computed(() => running.value || props.loading)

async function onClick() {
  if (!props.handler) {
    emit('click')
    return
  }
  // 单锁：连点不重复导出。导出一次要服务端渲染整卷，重复的代价是秒级 CPU
  if (running.value) return
  running.value = true
  try {
    await props.handler()
  } catch (e) {
    toastIfUnhandled(e, '导出失败')
  } finally {
    running.value = false
  }
}
</script>
