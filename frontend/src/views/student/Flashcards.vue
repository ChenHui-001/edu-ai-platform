<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">闪卡速记</h2>
      <div>
        <el-select v-model="subjectFilter" placeholder="全部学科" clearable style="width:140px"
                   @change="load">
          <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
        </el-select>
        <el-button :icon="Refresh" @click="load" class="ml8">刷新</el-button>
      </div>
    </div>

    <el-row :gutter="16" class="mb16">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-value">{{ cards.length }}</div>
          <div class="stat-label">闪卡总数</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-value" style="color:#67c23a">{{ knownCount }}</div>
          <div class="stat-label">已认识</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-value" style="color:#f56c6c">{{ unknownCount }}</div>
          <div class="stat-label">待复习</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-value" style="color:#e6a23c">{{ weakCount }}</div>
          <div class="stat-label">薄弱知识点</div>
        </div>
      </el-col>
    </el-row>

    <el-empty v-if="!loading && !cards.length" description="暂无闪卡，请先选择学科" :image-size="80" />

    <div v-if="cards.length && currentIndex < cards.length" class="flashcard-area">
      <div class="progress-bar">
        <el-progress :percentage="Math.round((currentIndex / cards.length) * 100)" :stroke-width="4"
                     :format="() => `${currentIndex} / ${cards.length}`" />
      </div>

      <div class="card-counter">{{ currentIndex + 1 }} / {{ cards.length }}</div>

      <div class="flashcard" :class="{ flipped: isFlipped }" @click="isFlipped = !isFlipped">
        <div class="card-face card-front">
          <div class="card-label">知识点</div>
          <div class="card-content">{{ currentCard?.front }}</div>
          <div class="card-hint" v-if="currentCard?.is_weak">
            <el-tag type="danger" size="small">薄弱</el-tag>
          </div>
          <div class="card-tip">点击翻面查看详情</div>
        </div>
        <div class="card-face card-back">
          <div class="card-label">详情</div>
          <div class="card-content">{{ currentCard?.back }}</div>
          <div class="card-tip">点击翻回</div>
        </div>
      </div>

      <div class="card-actions">
        <el-button type="danger" size="large" :icon="Close" @click="markUnknown">
          不认识
        </el-button>
        <el-button type="success" size="large" :icon="Check" @click="markKnown">
          认识
        </el-button>
      </div>
    </div>

    <!-- 完成结果 -->
    <el-card v-if="cards.length && currentIndex >= cards.length" shadow="never" class="result-card">
      <el-result icon="success" title="本轮闪卡完成！"
                 :sub-title="`认识 ${knownCount} 张 · 不认识 ${unknownCount} 张 · 正确率 ${rate}%`">
        <template #extra>
          <el-button type="primary" @click="restart">再来一轮</el-button>
          <el-button v-if="unknownCount > 0" @click="restartUnknown">只练不认识的</el-button>
        </template>
      </el-result>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Refresh, Close, Check } from '@element-plus/icons-vue'
import { learningApi, eduApi } from '@/api'

const loading = ref(false)
const cards = ref([])
const subjects = ref([])
const subjectFilter = ref(null)
const currentIndex = ref(0)
const isFlipped = ref(false)
const knownIds = ref(new Set())
const unknownIds = ref(new Set())

const currentCard = computed(() => cards.value[currentIndex.value])
const knownCount = computed(() => knownIds.value.size)
const unknownCount = computed(() => unknownIds.value.size)
const weakCount = computed(() => cards.value.filter(c => c.is_weak).length)
const rate = computed(() => {
  const total = knownIds.value.size + unknownIds.value.size
  return total > 0 ? Math.round((knownIds.value.size / total) * 100) : 0
})

async function load() {
  loading.value = true
  try {
    const res = await learningApi.flashcards(subjectFilter.value ? { subject_id: subjectFilter.value } : {})
    cards.value = res.data?.items || []
    currentIndex.value = 0
    isFlipped.value = false
    knownIds.value = new Set()
    unknownIds.value = new Set()
  } finally {
    loading.value = false
  }
}

async function loadSubjects() {
  const res = await eduApi.subjects()
  subjects.value = res.data || []
}

function markKnown() {
  if (currentCard.value) {
    knownIds.value.add(currentCard.value.id)
    unknownIds.value.delete(currentCard.value.id)
  }
  nextCard()
}

function markUnknown() {
  if (currentCard.value) {
    unknownIds.value.add(currentCard.value.id)
    knownIds.value.delete(currentCard.value.id)
  }
  nextCard()
}

function nextCard() {
  isFlipped.value = false
  setTimeout(() => {
    currentIndex.value++
  }, 200)
}

function restart() {
  currentIndex.value = 0
  isFlipped.value = false
  knownIds.value = new Set()
  unknownIds.value = new Set()
}

function restartUnknown() {
  const unknownCards = cards.value.filter(c => unknownIds.value.has(c.id))
  cards.value = unknownCards
  restart()
}

onMounted(async () => {
  await loadSubjects()
  await load()
})
</script>

<style scoped>
.mb16 { margin-bottom: 16px; }
.ml8 { margin-left: 8px; }
.stat-card { text-align: center; padding: 16px; background: #f5f7fa; border-radius: 8px; }
.stat-value { font-size: 28px; font-weight: 700; color: #409eff; }
.stat-label { font-size: 12px; color: #909399; margin-top: 4px; }
.flashcard-area { display: flex; flex-direction: column; align-items: center; padding: 20px 0; }
.progress-bar { width: 100%; max-width: 500px; margin-bottom: 16px; }
.card-counter { font-size: 14px; color: #909399; margin-bottom: 16px; }
.flashcard {
  width: 420px; height: 280px; perspective: 1000px; cursor: pointer; position: relative;
}
.card-face {
  position: absolute; width: 100%; height: 100%; backface-visibility: hidden;
  border-radius: 16px; display: flex; flex-direction: column; align-items: center;
  justify-content: center; padding: 32px; transition: transform 0.5s;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08); border: 1px solid #e4e7ed;
}
.card-front { background: linear-gradient(135deg, #409eff 0%, #5b8def 100%); color: #fff; }
.card-back { background: #fff; transform: rotateY(180deg); }
.flashcard.flipped .card-front { transform: rotateY(180deg); }
.flashcard.flipped .card-back { transform: rotateY(0deg); }
.card-label { font-size: 12px; opacity: 0.7; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 2px; }
.card-content { font-size: 22px; font-weight: 600; text-align: center; line-height: 1.6; }
.card-hint { margin-top: 12px; }
.card-tip { position: absolute; bottom: 16px; font-size: 12px; opacity: 0.6; }
.card-actions { display: flex; gap: 24px; margin-top: 24px; }
.result-card { max-width: 500px; margin: 40px auto; }
</style>
