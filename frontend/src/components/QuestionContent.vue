<template>
  <div class="question-content">
    <div class="question-text" v-html="renderMathContent(question.stem || question.prompt || '')" />
    <div v-if="figure" class="question-figure" v-html="figure" />
    <svg v-if="visual?.kind === 'number_line'" viewBox="0 0 400 95" role="img" aria-label="数轴">
      <line x1="20" y1="40" x2="385" y2="40" stroke="currentColor" />
      <path d="M378 35 L385 40 L378 45" fill="none" stroke="currentColor" />
      <g v-for="tick in ticks" :key="tick.value">
        <line :x1="tick.x" y1="34" :x2="tick.x" y2="46" stroke="currentColor" />
        <text :x="tick.x" y="65" text-anchor="middle">{{ tick.value }}</text>
      </g>
      <g v-for="point in visual.points || []" :key="point.label">
        <circle :cx="pointX(point.value)" cy="40" r="5" fill="#409eff" />
        <text :x="pointX(point.value)" y="20" text-anchor="middle">{{ point.label || point.value }}</text>
      </g>
    </svg>
    <svg v-else-if="visual?.kind === 'fraction'" viewBox="0 0 400 95" role="img" aria-label="分数示意图">
      <rect v-for="part in denominator" :key="part" :x="20 + (part - 1) * 360 / denominator"
            y="15" :width="360 / denominator" height="42" stroke="currentColor"
            :fill="part <= numerator ? '#409eff' : 'transparent'" />
      <text x="200" y="82" text-anchor="middle">{{ numerator }} / {{ denominator }}</text>
    </svg>
    <svg v-else-if="visual?.kind === 'polygon'" viewBox="0 0 400 240" role="img" aria-label="几何示意图">
      <polygon :points="polygonPoints" fill="#ecf5ff" stroke="#409eff" stroke-width="2" />
      <g v-for="(point, index) in visual.points || []" :key="index">
        <text :x="Number(point.x) + 5" :y="Number(point.y) - 5">{{ point.label }}</text>
      </g>
    </svg>
    <div v-if="analysis" class="question-analysis" v-html="renderMathContent(analysis)" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import 'katex/dist/katex.min.css'
import { numberTicks, parseVisual, renderMathContent, renderQuestionFigure } from '@/utils/mathContent'

const props = defineProps({
  question: { type: Object, required: true },
  analysis: { type: String, default: '' }
})
const visual = computed(() => parseVisual(props.question))
const figure = computed(() => renderQuestionFigure(props.question.figure))
const ticks = computed(() => numberTicks(visual.value))
const denominator = computed(() => Math.min(20, Math.max(1, Number(visual.value?.denominator) || 1)))
const numerator = computed(() => Math.min(denominator.value, Math.max(0, Number(visual.value?.numerator) || 0)))
const polygonPoints = computed(() => (visual.value?.points || []).slice(0, 20)
  .map(point => `${Number(point.x) || 0},${Number(point.y) || 0}`).join(' '))
function pointX(value) {
  return 30 + (Number(value) - Number(visual.value.min)) /
    (Number(visual.value.max) - Number(visual.value.min)) * 340
}
</script>

<style scoped>
.question-text { line-height: 1.8; overflow-wrap: anywhere; }
.question-text :deep(.katex-display) { overflow-x: auto; overflow-y: hidden; }
.question-figure :deep(svg) { width: 100%; max-width: 450px; max-height: 320px; }
svg { width: 100%; max-width: 450px; display: block; margin: 12px 0; }
text { fill: var(--el-text-color-primary); font-size: 14px; }
.question-analysis { margin-top: 12px; padding: 12px; background: var(--el-fill-color-light); }
</style>
