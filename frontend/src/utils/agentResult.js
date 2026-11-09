/**
 * AI 生成结果的「空产出」判定。
 *
 * 抽出来的原因和 errors.js 一样：这段逻辑一旦回退，症状是"后端返回 0 条、
 * 前端弹绿色生成完成"，只靠点页面很难稳定复现，必须用单测钉住。
 *
 * 三个能力的载荷键各不相同：
 *   补题 / 变式 → `items`
 *   AI 出题     → `questions`
 *   智能组卷    → `paper`（预览态只有 items，保存态才有 id）
 * 只认其中一个就会出现「0 条也算有产出」的假成功（reaudit P1-2）。
 *
 * @param {any} payload 接口返回的 data
 * @returns {boolean} true = 没有任何产出
 */
export function hasNoOutput(payload) {
  if (!payload || typeof payload !== 'object') return true
  // paper 先判：组卷载荷会额外展开 report（distribution/coverage 等），
  // 将来若 report 里出现同名字段，放前面才不会被误判
  if ('paper' in payload) {
    const paper = payload.paper
    if (!paper || typeof paper !== 'object') return true
    // 预览态没有 id，但有 items；保存态两者都有
    if (Array.isArray(paper.items)) return paper.items.length === 0
    return !paper.id
  }
  if (Array.isArray(payload.questions)) return payload.questions.length === 0
  if (Array.isArray(payload.items)) return payload.items.length === 0
  // 载荷键存在但不是数组（`items: null` / `questions: "oops"`）：结构残缺。
  // 按空产出处理 —— 宁可提示"没产出、请重试"，也不要把残缺数据渲染成成功页。
  const has = (k) => Object.prototype.hasOwnProperty.call(payload, k)
  if (has('questions') || has('items')) return true
  return Object.keys(payload).length === 0
}
