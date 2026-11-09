import { describe, expect, it, vi } from 'vitest'

// confirm.js 依赖 Element Plus 的消息框；这里把它换成可编程的假实现，
// 专门复现「取消时 reject 的是裸字符串」这一行为（Element Plus 的真实语义）。
const mockConfirm = vi.fn()
const mockPrompt = vi.fn()
const mockAlert = vi.fn()

vi.mock('element-plus', () => ({
  ElMessageBox: {
    confirm: (...args) => mockConfirm(...args),
    prompt: (...args) => mockPrompt(...args),
    alert: (...args) => mockAlert(...args)
  }
}))

const { alertAction, confirmAction, promptAction } = await import('../confirm')

describe('confirmAction', () => {
  it('确认时返回 true', async () => {
    mockConfirm.mockResolvedValueOnce('confirm')
    await expect(confirmAction('确认删除？')).resolves.toBe(true)
  })

  it('取消（reject 裸字符串）时返回 false，不抛异常', async () => {
    // 这是 P1-9 的根因：reject 的是 'cancel' 而不是 Error
    mockConfirm.mockRejectedValueOnce('cancel')
    await expect(confirmAction('确认删除？')).resolves.toBe(false)
  })

  it('点右上角关闭（close）同样返回 false', async () => {
    mockConfirm.mockRejectedValueOnce('close')
    await expect(confirmAction('确认删除？')).resolves.toBe(false)
  })

  it('消息框自身异常也只返回 false，不把 rejection 漏给全局兜底', async () => {
    mockConfirm.mockRejectedValueOnce(new Error('dialog crashed'))
    await expect(confirmAction('确认删除？')).resolves.toBe(false)
  })

  it('默认标题是「提示」，且总是带上 warning 图标语义', async () => {
    mockConfirm.mockResolvedValueOnce('confirm')
    await confirmAction('确认？')
    expect(mockConfirm).toHaveBeenCalledWith('确认？', '提示', { type: 'warning' })
  })

  it('显式标题 + 自定义按钮文案会透传，title 不会重复覆盖', async () => {
    mockConfirm.mockResolvedValueOnce('confirm')
    await confirmAction('确认？', '删除确认', { confirmButtonText: '确认删除' })
    expect(mockConfirm).toHaveBeenCalledWith('确认？', '删除确认',
      { type: 'warning', confirmButtonText: '确认删除' })
  })

  it('只传 options 形式（title 写在 options 里）也能取到标题', async () => {
    mockConfirm.mockResolvedValueOnce('confirm')
    await confirmAction('确认？', { title: '停用确认', type: 'info' })
    expect(mockConfirm).toHaveBeenCalledWith('确认？', '停用确认', { type: 'info' })
  })
})

describe('promptAction', () => {
  it('确认时返回输入的字符串', async () => {
    mockPrompt.mockResolvedValueOnce({ value: '新名字' })
    await expect(promptAction('请输入')).resolves.toBe('新名字')
  })

  it('取消时返回 null（调用方据此区分"取消"与"提交空值"）', async () => {
    mockPrompt.mockRejectedValueOnce('cancel')
    await expect(promptAction('请输入')).resolves.toBeNull()
  })

  it('value 为空串时返回空串而不是 null', async () => {
    mockPrompt.mockResolvedValueOnce({ value: '' })
    await expect(promptAction('请输入')).resolves.toBe('')
  })

  it('value 为 null/undefined 时归一成空串', async () => {
    mockPrompt.mockResolvedValueOnce({ value: null })
    await expect(promptAction('请输入')).resolves.toBe('')
  })
})

describe('alertAction', () => {
  it('关闭提示的 rejection 被内部吃掉，调用方无需 catch', async () => {
    mockAlert.mockRejectedValueOnce('close')
    await expect(alertAction('提示')).resolves.toBeUndefined()
  })

  it('正文与标题正确传递', async () => {
    mockAlert.mockResolvedValueOnce('confirm')
    await alertAction('发现 2 道疑似重复', '查重结果')
    expect(mockAlert).toHaveBeenCalledWith('发现 2 道疑似重复', '查重结果', {})
  })
})
