import { describe, expect, it } from 'vitest'

import { CANCEL_REASONS, describeError, isBusinessError } from '../errors'

/**
 * 这组用例守的是 reaudit3 P2-B：
 * 修 P1-9（点取消弹全屏红条）时，判据一度写成「一切非对象都是业务错误」，
 * 于是 `throw undefined` / `Promise.reject('boom')` 这类真故障被静默吞掉。
 * 现在只放行两个已知取消原因，其余一律算故障。
 */
describe('isBusinessError', () => {
  it('用户取消（cancel / close）不算故障', () => {
    expect(isBusinessError('cancel')).toBe(true)
    expect(isBusinessError('close')).toBe(true)
    expect(CANCEL_REASONS).toEqual(['cancel', 'close'])
  })

  it('其它裸字符串一律算真故障', () => {
    expect(isBusinessError('boom')).toBe(false)
    expect(isBusinessError('Error: x')).toBe(false)
    expect(isBusinessError('')).toBe(false)
  })

  it('undefined / null 是真故障，不能被当成"什么都没发生"', () => {
    expect(isBusinessError(undefined)).toBe(false)
    expect(isBusinessError(null)).toBe(false)
  })

  it('数字 / 布尔等非对象 rejection 也算故障', () => {
    expect(isBusinessError(0)).toBe(false)
    expect(isBusinessError(false)).toBe(false)
    expect(isBusinessError(42)).toBe(false)
  })

  it('拦截器已提示（__handled）的请求错误不重复上报', () => {
    const e = new Error('该题目已被 6 份试卷引用')
    e.__handled = true
    expect(isBusinessError(e)).toBe(true)
  })

  it('axios 错误与带 response 的错误视为已处理', () => {
    expect(isBusinessError({ isAxiosError: true })).toBe(true)
    expect(isBusinessError({ response: { status: 400 } })).toBe(true)
  })

  it('普通未标记的 Error 是真故障（要弹红条）', () => {
    expect(isBusinessError(new Error('Cannot read properties of undefined'))).toBe(false)
    expect(isBusinessError({ message: 'x' })).toBe(false)
  })
})

describe('describeError', () => {
  it('保留原始 message', () => {
    expect(describeError(new Error('保存失败'))).toBe('保存失败')
  })

  it('undefined / null 给出可读说明，不渲染成空话', () => {
    expect(describeError(undefined)).toContain('undefined')
    expect(describeError(null)).toContain('null')
  })

  it('字符串与对象都能落到一句话', () => {
    expect(describeError('boom')).toBe('boom')
    expect(describeError({ code: 500 })).toBe('[object Object]')
  })
})
