# -*- coding: utf-8 -*-
"""考试页导航同步：scroll 监听 -> IntersectionObserver（.el-main 内部滚动）。"""
import io

f = "frontend/src/views/student/ExamPaper.vue"
s = io.open(f, encoding="utf-8").read()

OLD_FN = '''/** 滚动时把当前可视题目同步到题号导航（此前无同步，用户不知道在答第几题） */
function onScroll() {
  if (state.value !== 'answering' || !itemRefs.value.length) return
  const mid = window.innerHeight * 0.32
  let idx = 0
  itemRefs.value.forEach((el, i) => {
    if (el && el.getBoundingClientRect().top <= mid) idx = i
  })
  activeIndex.value = idx
}'''

NEW_FN = '''/** 当前可视题目同步到题号导航。
 * 用 IntersectionObserver 而非 window scroll：内容区是 .el-main 内部滚动，
 * window scroll 事件不会触发（实测滚动后高亮卡在第 1 题）。 */
let navObserver = null
function setupNavObserver() {
  if (navObserver) navObserver.disconnect()
  navObserver = new IntersectionObserver((entries) => {
    if (state.value !== 'answering') return
    const visible = entries.filter(e => e.isIntersecting)
    if (!visible.length) return
    const tops = visible.map(e => ({
      i: itemRefs.value.indexOf(e.target),
      top: e.boundingClientRect.top,
    })).filter(x => x.i >= 0)
    if (!tops.length) return
    tops.sort((a, b) => a.top - b.top)
    activeIndex.value = tops[0].i
  }, { root: null, threshold: [0.2, 0.5] })
  itemRefs.value.forEach(el => el && navObserver.observe(el))
}'''

assert OLD_FN in s, "onScroll 未匹配"
s = s.replace(OLD_FN, NEW_FN)

OLD_MOUNT = "    window.addEventListener('scroll', onScroll, { passive: true })"
NEW_MOUNT = """    // 等下一帧，题卡渲染完成后再观察
    requestAnimationFrame(() => setupNavObserver())"""
assert OLD_MOUNT in s, "挂载未匹配"
s = s.replace(OLD_MOUNT, NEW_MOUNT)

OLD_UN = """  document.removeEventListener('visibilitychange', onVisibility)
  window.removeEventListener('scroll', onScroll)"""
NEW_UN = """  document.removeEventListener('visibilitychange', onVisibility)
  if (navObserver) navObserver.disconnect()"""
assert OLD_UN in s, "卸载未匹配"
s = s.replace(OLD_UN, NEW_UN)

io.open(f, "w", encoding="utf-8", newline="\n").write(s)
print("导航同步改 IntersectionObserver 完成")
