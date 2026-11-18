import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import QuestionContent from '../QuestionContent.vue'

describe('QuestionContent', () => {
  it('shares formulas and analysis in one safe renderer', () => {
    const wrapper = mount(QuestionContent, { props: { question: { stem: '$x^2$' }, analysis: '$2x$' } })
    expect(wrapper.findAll('.katex').length).toBe(2)
  })
  it('renders the requested bounded fraction slices', () => {
    const wrapper = mount(QuestionContent, { props: { question: { visual: { kind: 'fraction', numerator: 2, denominator: 5 } } } })
    expect(wrapper.findAll('rect')).toHaveLength(5)
    expect(wrapper.findAll('rect').filter(part => part.attributes('fill') === '#409eff')).toHaveLength(2)
  })
  it('renders upstream geometry without executable attributes', () => {
    const wrapper = mount(QuestionContent, { props: { question: { figure: '<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0 L10 10" onmouseover="evil()" /></svg>' } } })
    expect(wrapper.find('path').exists()).toBe(true)
    expect(wrapper.html()).not.toContain('onmouseover')
  })
})
