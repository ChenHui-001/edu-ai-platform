/**
 * AI Agent 结果的统一信封解析。
 *
 * request.js 的响应拦截器 `return res` 交回来的是**信封本身**
 * `{code, message, success, data}`，业务载荷在 res.data。
 * PaperManage / AgentGenerate 两个千行级视图各写了一遍解包，其中一处多解
 * 一层导致「试卷已落库却恒弹失败」（P0-2）。把口径收敛到一处，
 * 也是把逻辑从巨型视图里往外抽的第一步。
 */
export function parseAgentEnvelope(res) {
  const envelope = res || {}
  return {
    ok: envelope.code === 200 && envelope.success !== false,
    message: envelope.message || '',
    data: envelope.data || {},
  }
}
