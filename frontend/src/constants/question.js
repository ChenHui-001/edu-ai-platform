/**
 * 题型常量 —— 与后端 QuestionType 枚举保持唯一对应
 * （backend/app/models/question.py: single/multiple/judge/blank/short/calc/material/composition）
 *
 * 此前 4 个页面各自维护一份且互不一致：
 *   - MyFavorites 写的是 short_answer（后端不存在，简答题显示成英文原文）
 *   - Practice/WrongBook 用 fill/calculate/proof，后端实际是 blank/calc
 * 统一从这里 import，禁止在页面内再定义本地映射。
 * ALIAS 仅做历史数据/旧客户端的显示兜底，新代码不应产生别名值。
 */
export const QUESTION_TYPE_LABELS = {
  single: '单选题',
  multiple: '多选题',
  judge: '判断题',
  blank: '填空题',
  short: '简答题',
  calc: '计算题',
  material: '材料分析题',
  composition: '作文题',
}

/** 历史别名 → 后端枚举值 */
export const QUESTION_TYPE_ALIAS = {
  fill: 'blank',
  calculate: 'calc',
  proof: 'calc',
  essay: 'composition',
  subjective: 'short',
  short_answer: 'short',
}

/** 合并别名后的映射：页面内 TYPES[type] 直接可用 */
const TYPES = { ...QUESTION_TYPE_LABELS }
for (const [alias, canonical] of Object.entries(QUESTION_TYPE_ALIAS)) {
  if (QUESTION_TYPE_LABELS[canonical]) TYPES[alias] = QUESTION_TYPE_LABELS[canonical]
}

/** 取题型显示名，未知值原样返回（加标记便于排查），空值返回 '-' */
export function questionTypeLabel(t) {
  if (!t) return '-'
  return TYPES[String(t).toLowerCase()] || String(t)
}

/** 归一化为后端合法枚举值，非法值回落 single */
export function normalizeQuestionType(t) {
  const v = QUESTION_TYPE_ALIAS[String(t || '').toLowerCase()] || String(t || '').toLowerCase()
  return QUESTION_TYPE_LABELS[v] ? v : 'single'
}

export default TYPES
