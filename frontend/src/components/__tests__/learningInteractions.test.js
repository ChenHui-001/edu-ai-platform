import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount, shallowMount } from '@vue/test-utils'
import EChart from '../EChart.vue'
import KnowledgeGraph from '@/views/student/KnowledgeGraph.vue'
import KnowledgeDiagnosis from '@/views/student/KnowledgeDiagnosis.vue'
import Practice from '@/views/student/Practice.vue'
import ErrorState from '../ErrorState.vue'

const mocks = vi.hoisted(() => ({
  graph: vi.fn(), list: vi.fn(), get: vi.fn(), answerDiagnosis: vi.fn(),
  diagnosisTargets: vi.fn(), handlers: {}, dispose: vi.fn(), setOption: vi.fn(),
  push: vi.fn(), submit: vi.fn()
}))
vi.mock('@/utils/echarts', () => ({
  default: { init: () => ({
    on: (name, handler) => { mocks.handlers[name] = handler },
    setOption: mocks.setOption, dispose: mocks.dispose, resize: vi.fn()
  }) }
}))
vi.mock('@/api', () => ({
  eduApi: {
    grades: vi.fn().mockResolvedValue({ data: [{ id: 1, name: '一年级' }] }),
    subjects: vi.fn().mockResolvedValue({ data: [{ id: 1, name: '数学' }, { id: 2, name: '语文' }] })
  },
  knowledgeApi: {
    graph: mocks.graph, list: mocks.list, get: mocks.get,
    answerDiagnosis: mocks.answerDiagnosis, diagnosisTargets: mocks.diagnosisTargets
  },
  taskApi: { submit: mocks.submit },
  learningApi: {}
}))
vi.mock('@/store/user', () => ({ useUserStore: () => ({ isStudent: false, userInfo: { grade_id: 1 } }) }))
vi.mock('vue-router', () => ({ useRouter: () => ({ push: mocks.push }), useRoute: () => ({ query: {} }) }))
vi.mock('@/utils/subject', () => ({
  currentGradeId: () => 1, fetchSubjects: () => Promise.resolve([{ id: 1, name: '数学' }]),
  resolveSubjectId: () => 1
}))
vi.mock('element-plus', () => ({ ElMessage: { error: vi.fn(), warning: vi.fn(), success: vi.fn() } }))
vi.mock('@/utils/confirm', () => ({ confirmAction: vi.fn().mockResolvedValue(true) }))
vi.mock('@/api/extensions', () => ({ extensionApi: {} }))

const stubs = {
  'el-card': { template: '<section><slot name="header" /><slot /></section>' },
  'el-row': { template: '<div><slot /></div>' }, 'el-col': { template: '<div><slot /></div>' },
  'el-checkbox-group': { name: 'ElCheckboxGroup', props: ['modelValue'], template: '<div><slot /></div>' },
  'el-radio-group': { props: ['modelValue'], template: '<div><slot /></div>' },
  'el-select': true, 'el-option': true, 'el-button': true, 'el-alert': true,
  'el-input-number': true, 'el-checkbox': true, 'el-radio': true, 'el-empty': true,
  'el-tag': true, 'el-divider': true, 'el-icon': true, 'el-input': true,
  'el-progress': true, 'el-descriptions': true, 'el-descriptions-item': true,
  'el-tooltip': true, 'el-table': true, 'el-table-column': true
}
const wrappers = []
const sample = name => ({ data: { nodes: [{ id: 1, name, subject_id: 1, child_count: 0 }], edges: [] } })
function graphPage() {
  const wrapper = shallowMount(KnowledgeGraph, { global: { stubs } })
  wrappers.push(wrapper)
  return wrapper
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.graph.mockResolvedValue(sample('初始图谱'))
  mocks.list.mockResolvedValue({ data: [] })
  mocks.diagnosisTargets.mockResolvedValue({ data: { items: [] } })
})
afterEach(() => {
  wrappers.forEach(wrapper => wrapper.unmount())
  wrappers.length = 0
  vi.useRealTimers()
})

describe('learning interactions', () => {
  it('forwards chart double-click events and disposes its chart', () => {
    const wrapper = mount(EChart, { props: { option: {} } })
    const params = { dataType: 'node', data: { id: 1 } }
    mocks.handlers.dblclick(params)
    expect(wrapper.emitted('chart-dblclick')[0]).toEqual([params])
    wrapper.unmount()
    expect(mocks.dispose).toHaveBeenCalledOnce()
  })
  it('double-clicking a graph node requests centered expansion', async () => {
    const wrapper = graphPage()
    await flushPromises()
    wrapper.findComponent(EChart).vm.$emit('chart-dblclick', { dataType: 'node', data: { id: 1 } })
    await flushPromises()
    expect(mocks.graph).toHaveBeenLastCalledWith(expect.objectContaining({ root_id: 1, depth: 2, params_limit: 600 }))
  })
  it('debounces graph search and only requests the latest keyword', async () => {
    const wrapper = graphPage()
    await flushPromises()
    vi.useFakeTimers()
    wrapper.vm.searchNodes('旧搜索')
    wrapper.vm.searchNodes('新搜索')
    await vi.advanceTimersByTimeAsync(249)
    expect(mocks.list).not.toHaveBeenCalled()
    await vi.advanceTimersByTimeAsync(1)
    expect(mocks.list).toHaveBeenCalledOnce()
    expect(mocks.list).toHaveBeenCalledWith(expect.objectContaining({ keyword: '新搜索' }))
  })
  it('ignores stale graph responses after the subject changes', async () => {
    const wrapper = graphPage()
    await flushPromises()
    let resolveOld
    let resolveNew
    mocks.graph.mockImplementationOnce(() => new Promise(resolve => { resolveOld = resolve }))
      .mockImplementationOnce(() => new Promise(resolve => { resolveNew = resolve }))
    const oldRequest = wrapper.vm.loadGraph()
    wrapper.vm.form.subject_id = 2
    const newRequest = wrapper.vm.loadGraph()
    resolveNew(sample('新学科'))
    await newRequest
    resolveOld(sample('旧学科'))
    await oldRequest
    expect(wrapper.vm.graph.nodes[0].name).toBe('新学科')
  })
  it('shows an error state and clears it after retry succeeds', async () => {
    mocks.graph.mockRejectedValueOnce(new Error('offline'))
    const wrapper = graphPage()
    await flushPromises()
    expect(wrapper.findComponent(ErrorState).props('message')).toContain('加载失败')
    wrapper.findComponent(ErrorState).vm.$emit('retry')
    await flushPromises()
    expect(wrapper.vm.error).toBe('')
    expect(wrapper.vm.graph.nodes[0].name).toBe('初始图谱')
  })
  it('initializes multi-select as an array and submits both selections', async () => {
    const wrapper = shallowMount(KnowledgeDiagnosis, { global: { stubs } })
    wrappers.push(wrapper)
    await flushPromises()
    wrapper.vm.applySession({
      id: 8, summary: {}, next: { knowledge_point_id: 1, question: {
        id: '12', type: 'multiple', stem: '选择两项',
        options: [{ key: 'A', text: '甲' }, { key: 'C', text: '丙' }]
      } }
    })
    await flushPromises()
    expect(wrapper.vm.answer).toEqual([])
    const groups = wrapper.findAllComponents({ name: 'ElCheckboxGroup' })
    expect(groups.some(group => Array.isArray(group.props('modelValue')))).toBe(true)
    wrapper.vm.answer = ['A', 'C']
    mocks.answerDiagnosis.mockResolvedValue({ data: { asked: 1, summary: {}, next: null } })
    await wrapper.vm.submit()
    expect(mocks.answerDiagnosis).toHaveBeenCalledWith(8, expect.objectContaining({ answer: ['A', 'C'] }))
  })
  it('practice results map paper-item grades to questions and display answers after submission', async () => {
    const wrapper = shallowMount(Practice, { global: { stubs } })
    wrappers.push(wrapper)
    await flushPromises()
    wrapper.vm.paper = { task_id: 9, total_score: 5, items: [{ paper_item_id: 7, question_id: 12, type: 'single', stem: '1+1=?', score: 5 }] }
    wrapper.vm.answers = { 12: 'A' }
    mocks.submit.mockResolvedValue({ data: { score: 5, answers: [
      { paper_item_id: 7, score: 5, is_correct: true, answer: 'A', analysis: '$1+1=2$' }
    ] } })
    await wrapper.vm.submitPractice()
    expect(wrapper.vm.paper.items[0].answer).toBe('A')
    expect(wrapper.vm.paper.items[0].analysis).toBe('$1+1=2$')
    expect(wrapper.vm.isCorrect(wrapper.vm.paper.items[0])).toBe(true)
    expect(wrapper.vm.totalScore).toBe('5.0')
  })
})
