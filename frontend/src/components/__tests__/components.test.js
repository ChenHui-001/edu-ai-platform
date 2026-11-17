import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { h } from 'vue'

import ErrorState from '@/components/ErrorState.vue'
import AiFallbackNotice from '@/components/AiFallbackNotice.vue'
import ExportButton from '@/components/ExportButton.vue'
import TableCards from '@/components/TableCards.vue'

const responsiveState = vi.hoisted(() => ({ mobile: true }))

vi.mock('@/utils/responsive', async () => {
  const { computed } = await import('vue')
  return {
    useIsMobile: () => computed(() => responsiveState.mobile),
    formatCellValue: (row, col) => row?.[col.prop] ?? ''
  }
})

vi.mock('@/utils/notify', () => ({
  toastIfUnhandled: vi.fn()
}))

const buttonStub = {
  props: ['loading', 'disabled', 'type', 'size', 'icon'],
  emits: ['click'],
  template: '<button :disabled="disabled || loading" @click.stop="$emit(\'click\')"><slot /></button>'
}

const alertStub = {
  props: ['title', 'type', 'closable', 'showIcon'],
  template: '<div class="alert"><div class="alert-title">{{ title }}</div><slot /></div>'
}

function mountError(props = {}) {
  return mount(ErrorState, {
    props,
    global: { stubs: { 'el-icon': true, 'el-button': buttonStub } }
  })
}

describe('ErrorState', () => {
  it('渲染标题、原因与错误码', () => {
    const wrapper = mountError({ title: '报表加载失败', message: '网络连接失败', code: 500 })
    expect(wrapper.text()).toContain('报表加载失败')
    expect(wrapper.text()).toContain('网络连接失败')
    expect(wrapper.text()).toContain('错误码：500')
  })

  it('点击重试只发出一次 retry 事件', async () => {
    const wrapper = mountError()
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('retry')).toHaveLength(1)
  })

  it('loading 时按钮文案切换并禁用', () => {
    const wrapper = mountError({ loading: true })
    const button = wrapper.find('button')
    expect(button.text()).toContain('重试中')
    expect(button.attributes('disabled')).toBeDefined()
  })
})

describe('AiFallbackNotice', () => {
  it('show=false 时不渲染告警', () => {
    const wrapper = mount(AiFallbackNotice, {
      props: { show: false },
      global: { stubs: { 'el-alert': alertStub } }
    })
    expect(wrapper.find('.alert').exists()).toBe(false)
  })

  it('show=true 时使用统一标题与原因说明', () => {
    const wrapper = mount(AiFallbackNotice, {
      props: { show: true, reason: '已用题库同条件题目替换' },
      global: { stubs: { 'el-alert': alertStub } }
    })
    expect(wrapper.text()).toContain('规则引擎降级生成')
    expect(wrapper.text()).toContain('已用题库同条件题目替换')
    expect(wrapper.text()).toContain('配置大模型后重试')
  })
})

describe('ExportButton', () => {
  beforeEach(() => {
    responsiveState.mobile = true
  })

  it('未传 handler 时只转发 click', async () => {
    const wrapper = mount(ExportButton, {
      global: { stubs: { 'el-button': buttonStub } }
    })
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('click')).toHaveLength(1)
  })

  it('handler 模式连点只执行一次，结束后恢复可点', async () => {
    let resolveHandler
    const handler = vi.fn(() => new Promise((resolve) => { resolveHandler = resolve }))
    const wrapper = mount(ExportButton, {
      props: { handler },
      global: { stubs: { 'el-button': buttonStub } }
    })
    const button = wrapper.find('button')
    await button.trigger('click')
    await button.trigger('click')
    expect(handler).toHaveBeenCalledTimes(1)
    expect(button.attributes('disabled')).toBeDefined()
    resolveHandler()
    await Promise.resolve()
    await Promise.resolve()
    expect(wrapper.vm.busy).toBe(false)
  })
})

describe('TableCards', () => {
  const columns = [
    { prop: 'name', label: '姓名' },
    { prop: 'status', label: '状态' }
  ]

  beforeEach(() => {
    responsiveState.mobile = true
  })

  it('移动端按列渲染卡片并支持自定义单元格插槽', () => {
    const wrapper = mount(TableCards, {
      props: { rows: [{ id: 1, name: '张三', status: 'active' }], columns },
      slots: {
        'cell-status': ({ row }) => h('span', { class: 'custom-status' }, row.status)
      },
      global: {
        stubs: { 'el-empty': true },
        directives: { loading: {} }
      }
    })
    expect(wrapper.find('.table-card').exists()).toBe(true)
    expect(wrapper.text()).toContain('张三')
    expect(wrapper.find('.custom-status').text()).toBe('active')
  })

  it('移动端空数据渲染空态文案', () => {
    const wrapper = mount(TableCards, {
      props: { rows: [], columns, emptyText: '暂无成绩' },
      global: {
        stubs: { 'el-empty': { props: ['description'], template: '<div class="empty">{{ description }}</div>' } },
        directives: { loading: {} }
      }
    })
    expect(wrapper.text()).toContain('暂无成绩')
  })

  it('桌面端原样渲染默认插槽', () => {
    responsiveState.mobile = false
    const wrapper = mount(TableCards, {
      props: { rows: [{ id: 1, name: '张三' }], columns },
      slots: { default: '<table class="desktop-table"><tr><td>桌面表格</td></tr></table>' },
      global: { stubs: { 'el-empty': true }, directives: { loading: {} } }
    })
    expect(wrapper.find('.desktop-table').exists()).toBe(true)
  })
})
