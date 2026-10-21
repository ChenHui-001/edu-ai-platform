/**
 * 学科下拉的统一取数逻辑。
 *
 * 背景：`Subject` 的唯一约束是 `(grade_id, name)`，种子数据给 1-9 年级各建了一遍，
 * 所以 `GET /edu/subjects` 不传参时会返回 57 条记录，其中「数学」出现 7 次。
 * 直接把这份数据喂给 el-select，用户看到的就是 7 个一模一样的「数学」选项。
 *
 * 更隐蔽的是「选错 id」：`distinct=true` 返回的代表记录取 sort 最小的那条
 * （也就是最低年级），如果一个高一学生选了「数学」，拿到的 subject_id 指向
 * 一年级数学，后续按该 id 查知识点/错题就会全部为空 —— 界面不报错，只是没数据。
 *
 * 因此这里统一做两件事：
 *   1. `fetchSubjects()`        —— 传 distinct，视觉上去重；
 *   2. `resolveSubjectId()`     —— 用名称回查同年级的那条精确 id。
 *
 * 需要「按年级精确取 subject_id」的场景（建题、组卷、知识点）必须走第 2 步，
 * 不能直接用 distinct 返回的代表 id。
 */
import { eduApi } from '@/api'

/** 当前登录用户的年级 id（非学生/未设置时返回 null）。 */
export function currentGradeId() {
  try {
    const raw = localStorage.getItem('user')
    if (!raw) return null
    const gid = JSON.parse(raw)?.grade_id
    return gid || null
  } catch {
    return null
  }
}

/**
 * 拉取去重后的学科列表。
 * @param {{ gradeId?: number|string|null, distinct?: boolean, ignoreGrade?: boolean }} [opts]
 *   - gradeId  按年级过滤（传 null 表示不过滤）
 *   - distinct 是否按名称去重，默认 true
 *   - ignoreGrade 忽略 gradeId，取全量去重（管理员配置页用）
 */
export async function fetchSubjects(opts = {}) {
  const { gradeId = null, distinct = true, ignoreGrade = false } = opts
  const params = {}
  if (distinct) params.distinct = true
  // 年级过滤 + 去重同时传是安全的：同一年级下学科名天然不重复，
  // 去重分支会把 grade_count 置为 1，不影响展示。
  if (!ignoreGrade && gradeId) params.grade_id = gradeId
  const res = await eduApi.subjects(params)
  const data = res?.data
  return Array.isArray(data) ? data : (data?.items || [])
}

/**
 * 把「去重列表里选中的代表 id」映射成「指定年级下的真实 subject_id」。
 *
 * distinct 返回的代表记录带 `same_name_ids` / `same_name_grade_ids`，
 * 二元一一对应，可直接定位到目标年级那条。
 *
 * @param {Array} subjects 去重后的学科列表
 * @param {number} subjectId 用户选中的 id（可能是代表 id）
 * @param {number|string|null} gradeId 目标年级
 * @returns {number|null} 该年级下的真实 subject_id；无 matching 记录时原样返回
 */
export function resolveSubjectId(subjects, subjectId, gradeId) {
  if (!subjectId) return null
  if (!gradeId) return subjectId
  const hit = (subjects || []).find(s => s.id === subjectId)
  if (!hit) return subjectId
  // 已经是目标年级那条，直接用
  if (hit.grade_id === gradeId) return hit.id
  const ids = hit.same_name_ids || []
  const gids = hit.same_name_grade_ids || []
  const idx = gids.findIndex(g => g === gradeId)
  if (idx >= 0 && ids[idx]) return ids[idx]
  return subjectId
}

/**
 * 便捷方法：拉某个年级的学科，并把代表 id 预解析成该年级的真实 id。
 * 用于「页面加载后直接按学科过滤列表」的场景（错题本、笔记、报表等）。
 */
export async function fetchSubjectsForGrade(gradeId) {
  const list = await fetchSubjects({ gradeId, distinct: true })
  return list
}
