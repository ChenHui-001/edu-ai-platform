/**
 * 全局错误分拣。
 *
 * 抽成独立模块的两个理由：
 *   1) 它是「哪些异常该弹红条、哪些只是用户点了取消」的唯一判据，值得被单测锁住；
 *   2) 原来写在 main.js 里，而 main.js 会 `import './styles/index.css'`、
 *      创建 app、挂 router —— 测试根本 import 不进来。
 *
 * 判据（reaudit3 P2-B 收紧过一次，别改回去）：
 *   - `'cancel'` / `'close'` —— Element Plus 消息框被取消时 reject 的字符串，
 *     是用户主动放弃操作，不是故障；
 *   - 带 `__handled` 的错误 —— 拦截器已经弹过中文提示，不要再弹第二次；
 *   - axios 错误 / 带 response 的错误 —— 请求失败，属于「已由拦截器处理」。
 *   - **其余一律算真故障**。上一版把"一切非对象"都当成取消，结果
 *     `throw undefined`、`Promise.reject('boom')` 既不提示也不挂红条，只在控制台
 *     留一行 warn —— 在装着学生数据的后台里，"什么都不知道"比"报个错"更难查。
 */

export const CANCEL_REASONS = ['cancel', 'close']

export function isBusinessError(err) {
  if (err === undefined || err === null) return false
  if (typeof err === 'string') return CANCEL_REASONS.includes(err)
  if (typeof err !== 'object') return false
  return err.__handled === true || err.isAxiosError === true || !!err.response
}

/** 把任意 rejection 值渲染成一句人能读的话（`undefined` 别变成空话） */
export function describeError(err) {
  if (err === undefined) return '未知错误（rejection 内容为 undefined）'
  if (err === null) return '未知错误（rejection 内容为 null）'
  return err?.message || String(err)
}
