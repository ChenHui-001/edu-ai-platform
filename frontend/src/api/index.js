import request from './request'

// ---------------- 认证 ----------------
export const authApi = {
  captcha: () => request.get('/auth/captcha'),
  login: (data) => request.post('/auth/login', data),
  register: (data) => request.post('/auth/register', data),
  profile: () => request.get('/auth/profile'),
  updateProfile: (data) => request.put('/auth/profile', data),
  changePassword: (data) => request.put('/auth/password', data),
  logout: (data) => request.post('/auth/logout', data || {}),
  registrations: (params) => request.get('/auth/registrations', { params }),
  auditRegistration: (data) => request.post('/auth/registrations/audit', data)
}

// ---------------- 系统管理 ----------------
export const systemApi = {
  users: (params) => request.get('/system/users', { params }),
  createUser: (data) => request.post('/system/users', data),
  updateUser: (id, data) => request.put(`/system/users/${id}`, data),
  deleteUser: (id) => request.delete(`/system/users/${id}`),
  resetPassword: (data) => request.put('/system/password/reset', data),
  roles: () => request.get('/system/roles'),
  createRole: (data) => request.post('/system/roles', data),
  updateRole: (id, data) => request.put(`/system/roles/${id}`, data),
  copyRole: (id, data) => request.post(`/system/roles/${id}/copy`, data),
  deleteRole: (id) => request.delete(`/system/roles/${id}`),
  permissions: (params) => request.get('/system/permissions', { params }),
  notifications: (params) => request.get('/system/notifications', { params }),
  readNotification: (id) => request.put(`/system/notifications/${id}/read`),
  readAllNotifications: () => request.put('/system/notifications/read-all'),
  config: () => request.get('/system/config'),
  aiConfig: () => request.get('/system/ai-config'),
  saveAiConfig: (data) => request.put('/system/ai-config', data),
  testAiConfig: (data) => request.post('/system/ai-config/test', data)
}

// ---------------- 教学资源 ----------------
export const eduApi = {
  grades: (params) => request.get('/edu/grades', { params }),
  createGrade: (data) => request.post('/edu/grades', data),
  updateGrade: (id, data) => request.put(`/edu/grades/${id}`, data),
  deleteGrade: (id) => request.delete(`/edu/grades/${id}`),
  subjects: (params) => request.get('/edu/subjects', { params }),
  createSubject: (data) => request.post('/edu/subjects', data),
  updateSubject: (id, data) => request.put(`/edu/subjects/${id}`, data),
  deleteSubject: (id) => request.delete(`/edu/subjects/${id}`),
  cloneSubject: (id, data) => request.post(`/edu/subjects/${id}/clone`, data),
  knowledge: (params) => request.get('/edu/knowledge', { params }),
  knowledgeList: (params) => request.get('/edu/knowledge/list', { params }),
  createKnowledge: (data) => request.post('/edu/knowledge', data),
  updateKnowledge: (id, data) => request.put(`/edu/knowledge/${id}`, data),
  deleteKnowledge: (id) => request.delete(`/edu/knowledge/${id}`),
  reindex: () => request.post('/edu/knowledge/reindex'),
  classes: (params) => request.get('/edu/classes', { params }),
  classStats: (params) => request.get('/edu/classes/stats', { params }),
  classStudents: (id, params) => request.get(`/edu/classes/${id}/students`, { params }),
  exportClassStudents: (id) => request.get(`/edu/classes/${id}/students/export`,
    { responseType: 'blob' }),
  batchRemoveStudents: (id, data) => request.post(
    `/edu/classes/${id}/students/batch-remove`, data),
  batchClasses: (data) => request.post('/edu/classes/batch', data),
  // 注册页专用：匿名可读的班级简表（注册页不能调用需登录的 /edu/classes）
  classesPublic: () => request.get('/edu/classes/public'),
  // 人员简表（教师端下拉专用；/system/users 是 admin 专属，教师调用必 403）
  peopleBrief: (params) => request.get('/edu/people/brief', { params }),
  masteryOverview: (classId) => request.get('/edu/knowledge/mastery-overview',
    { params: { class_id: classId } }),
  // 教师建班申请（审核制）
  createClassRequest: (data) => request.post('/edu/class-requests', data),
  myClassRequests: () => request.get('/edu/class-requests/mine'),
  classRequests: (params) => request.get('/edu/class-requests', { params }),
  reviewClassRequest: (id, data) => request.post(`/edu/class-requests/${id}/review`, data),
  withdrawClassRequest: (id) => request.delete(`/edu/class-requests/${id}`),
  createClass: (data) => request.post('/edu/classes', data),
  updateClass: (id, data) => request.put(`/edu/classes/${id}`, data),
  deleteClass: (id) => request.delete(`/edu/classes/${id}`),
  importStudents: (id, students) => request.post(`/edu/classes/${id}/students`, students),
  removeStudent: (cid, sid) => request.delete(`/edu/classes/${cid}/students/${sid}`)
}

// ---------------- 知识点 V2（树 / 批量 / 导入导出） ----------------
// 契约见 docs/KNOWLEDGE_V2.md（阶段 1+2）。旧 eduApi.knowledge* 保留给其他页面兼容，
// 知识点管理页统一走这里，不出现裸 URL。
export const knowledgeApi = {
  // 读取
  tree: (params) => request.get('/edu/knowledge/tree', { params }),
  list: (params) => request.get('/edu/knowledge', { params }),
  get: (id) => request.get(`/edu/knowledge/${id}`),
  stats: (params) => request.get('/edu/knowledge/stats', { params }),
  // 写入
  create: (data) => request.post('/edu/knowledge', data),
  update: (id, data) => request.put(`/edu/knowledge/${id}`, data),
  remove: (id) => request.delete(`/edu/knowledge/${id}`),
  batch: (data) => request.post('/edu/knowledge/batch', data),
  // 导入导出（二进制走 blob，模板/导出均为 xlsx）
  import: (formData) => request.post('/edu/knowledge/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  template: () => request.get('/edu/knowledge/template', { responseType: 'blob' }),
  export: (params) => request.get('/edu/knowledge/export',
    { params, responseType: 'blob' }),
  reindex: () => request.post('/edu/knowledge/reindex'),
  // 知识点资料附件（1.3.0）
  attachments: (kpId) => request.get(`/edu/knowledge/${kpId}/attachments`),
  uploadAttachment: (kpId, formData) => request.post(
    `/edu/knowledge/${kpId}/attachments`, formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }),
  updateAttachment: (kpId, attId, data) => request.put(
    `/edu/knowledge/${kpId}/attachments/${attId}`, data),
  removeAttachment: (kpId, attId) => request.delete(
    `/edu/knowledge/${kpId}/attachments/${attId}`),
  // AI / RAG（1.2.0，契约 docs/KNOWLEDGE_V2_RAG_AI.md）
  search: (params) => request.get('/edu/knowledge/search', { params }),
  ragStatus: () => request.get('/edu/knowledge/rag-status'),
  aiGenerate: (data) => request.post('/edu/knowledge/ai/generate', data),
  aiEnrich: (ids) => request.post('/edu/knowledge/ai/enrich', { ids })
}

// ---------------- 题库与试卷 ----------------
export const questionApi = {
  list: (params) => request.get('/question/questions', { params }),
  // 题库 V2：统计 / 批量 / AI（契约 docs/QUESTION_BANK_V2.md）
  stats: (params) => request.get('/question/questions/stats', { params }),
  batch: (data) => request.post('/question/questions/batch', data),
  aiVariants: (data) => request.post('/question/questions/ai/variants', data),
  aiEnrich: (ids) => request.post('/question/questions/ai/enrich', { ids }),
  aiQuality: (ids) => request.post('/question/questions/ai/quality', { ids }),
  create: (data) => request.post('/question/questions', data),
  update: (id, data) => request.put(`/question/questions/${id}`, data),
  remove: (id) => request.delete(`/question/questions/${id}`),
  changeStatus: (id, data) => request.put(`/question/questions/${id}/status`, data),
  duplicates: (id) => request.get(`/question/questions/${id}/duplicates`),
  import: (formData) => request.post('/question/questions/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  templateUrl: () => '/api/v1/question/questions/template',
  exportUrl: (params) => `/api/v1/question/questions/export?${new URLSearchParams(params)}`,
  // blob 导出（window.open 无法携带 Authorization，get_current_teacher 必 401）
  exportExcel: (params) => request.get('/question/questions/export',
    { params, responseType: 'blob' }),
  downloadTemplate: () => request.get('/question/questions/template',
    { responseType: 'blob' }),
  exportPaper: (id, fmt = 'excel') => request.get(`/question/papers/${id}/export`,
    { params: { fmt }, responseType: 'blob' }),
  papers: (params) => request.get('/question/papers', { params }),
  // 试卷 V2：统计 / 批量 / AI（契约 docs/PAPER_V2.md）
  paperStats: (params) => request.get('/question/papers/stats', { params }),
  paperBatch: (data) => request.post('/question/papers/batch', data),
  paperAiAnalyze: (id) => request.post(`/question/papers/${id}/ai/analyze`),
  paperAiRecommend: (id) => request.post(`/question/papers/${id}/ai/recommend`),
  paperDetail: (id) => request.get(`/question/papers/${id}`),
  createPaper: (data) => request.post('/question/papers', data),
  updatePaper: (id, data) => request.put(`/question/papers/${id}`, data),
  removePaper: (id) => request.delete(`/question/papers/${id}`),
  copyPaper: (id, data) => request.post(`/question/papers/${id}/copy`, data),
  sharePaper: (id, data) => request.post(`/question/papers/${id}/share`, data),
  exportPaperUrl: (id) => `/api/v1/question/papers/${id}/export`,

  // ---- 标准组卷 V3（命题标准 / 双模式组卷 / 预览编辑 / 导出 / 共享审核）----
  standards: (params) => request.get('/question/standards', { params }),
  standardOptions: (params) => request.get('/question/standards/options', { params }),
  standardDetail: (id) => request.get(`/question/standards/${id}`),
  createStandard: (data) => request.post('/question/standards', data),
  updateStandard: (id, data) => request.put(`/question/standards/${id}`, data),
  removeStandard: (id) => request.delete(`/question/standards/${id}`),
  duplicateStandard: (id, data) => request.post(`/question/standards/${id}/duplicate`, data),
  resetStandard: (id) => request.post(`/question/standards/${id}/reset`),
  seedStandards: (force = false) => request.post('/question/standards/seed', null,
    { params: { force } }),

  composePreview: (data) => request.post('/question/papers/compose/preview', data),
  composeAi: (data) => request.post('/question/papers/compose/ai', data),
  composeSave: (data) => request.post('/question/papers/compose/save', data),

  paperPreview: (id, params) => request.get(`/question/papers/${id}/preview`, { params }),
  updatePaperItems: (id, data) => request.post(`/question/papers/${id}/items`, data),
  regenerateItem: (id, itemId, data) => request.post(
    `/question/papers/${id}/items/${itemId}/regenerate`, data || {}),
  removePaperItem: (id, itemId) => request.delete(`/question/papers/${id}/items/${itemId}`),
  renameSection: (id, data) => request.post(`/question/papers/${id}/sections/rename`, data),
  restructurePaper: (id, data) => request.post(`/question/papers/${id}/restructure`, data || {}),

  paperVersions: (id) => request.get(`/question/papers/${id}/versions`),
  paperVersionDetail: (id, v) => request.get(`/question/papers/${id}/versions/${v}`),
  restorePaperVersion: (id, v) => request.post(`/question/papers/${id}/versions/${v}/restore`),

  paperLibrary: (params) => request.get('/question/papers/library/list', { params }),
  toggleFavorite: (id, favorite) => request.post(`/question/papers/${id}/favorite`, { favorite }),
  reviewPaper: (id, data) => request.post(`/question/papers/${id}/review`, data),
  setShareScope: (id, scope) => request.post(`/question/papers/${id}/share-scope`, { scope }),
  shareInfo: (id) => request.get(`/question/papers/${id}/share-info`),

  exportDocxUrl: (id, params) => `/api/v1/question/papers/${id}/export/docx`,
  exportPdf: (id, params) => request.get(`/question/papers/${id}/export/pdf`,
    { params, responseType: 'blob' }),
  exportDocx: (id, params) => request.get(`/question/papers/${id}/export/docx`,
    { params, responseType: 'blob' }),
  // 答题卡是 PDF 流，同样必须走 blob 请求（window.open 不带 Authorization → 401）
  exportAnswerSheet: (id, params) => request.get(`/question/papers/${id}/export/answer-sheet`,
    { params, responseType: 'blob' }),
  exportAnswerSheetUrl: (id, params) => `/api/v1/question/papers/${id}/export/answer-sheet`,
  // 打印 HTML：取文本后在浏览器新窗口渲染（避免 window.open 直连 401）
  exportPrintHtml: (id, params) => request.get(`/question/papers/${id}/export/html`,
    { params, responseType: 'text' }),
  exportPrintHtmlUrl: (id, params) => `/api/v1/question/papers/${id}/export/html`
}

// ---------------- 作业与考试 ----------------
export const taskApi = {
  list: (params) => request.get('/task/tasks', { params }),
  // 教学管理 V2：统计 / 批量（契约 docs/TEACHING_V2.md）
  stats: (params) => request.get('/task/tasks/stats', { params }),
  batch: (data) => request.post('/task/tasks/batch', data),
  create: (data) => request.post('/task/tasks', data),
  update: (id, data) => request.put(`/task/tasks/${id}`, data),
  remove: (id) => request.delete(`/task/tasks/${id}`),
  submissions: (id, params) => request.get(`/task/tasks/${id}/submissions`, { params }),
  myTasks: (params) => request.get('/task/my/tasks', { params }),
  taskPaper: (id) => request.get(`/task/tasks/${id}/paper`),
  submit: (id, data) => request.post(`/task/tasks/${id}/submit`, data),
  heartbeat: (id, data) => request.post(`/task/tasks/${id}/heartbeat`, data),
  submissionDetail: (id) => request.get(`/task/submissions/${id}`),
  myScores: (params) => request.get('/task/my/scores', { params }),
  practice: (data) => request.post('/learning/practice', data),
  practicePaper: (id) => request.get(`/learning/practice/${id}`),
  practiceHistory: (params) => request.get('/learning/practice/history', { params })
}

// ---------------- 批改 ----------------
export const gradingApi = {
  pending: (params) => request.get('/grading/pending', { params }),
  // 教学管理 V2：批改统计
  stats: (params) => request.get('/grading/stats', { params }),
  detail: (id) => request.get(`/grading/submissions/${id}`),
  grade: (id, data) => request.post(`/grading/submissions/${id}/grade`, data),
  reject: (id, data) => request.post(`/grading/submissions/${id}/reject`, data),
  publish: (id) => request.post(`/grading/submissions/${id}/publish`),
  report: (taskId) => request.post(`/grading/tasks/${taskId}/report`),
  aiComment: (taskId) => request.post(`/grading/tasks/${taskId}/ai-comment`),
  batchGrade: (data) => request.post('/grading/batch/grade', data),
  batchPublish: (data) => request.post('/grading/batch/publish', data),
}

// ---------------- 学习中心 ----------------
export const learningApi = {
  notes: (params) => request.get('/learning/notes', { params }),
  note: (id) => request.get(`/learning/notes/${id}`),
  createNote: (data) => request.post('/learning/notes', data),
  updateNote: (id, data) => request.put(`/learning/notes/${id}`, data),
  removeNote: (id) => request.delete(`/learning/notes/${id}`),
  organizeNote: (id) => request.post(`/learning/notes/${id}/organize`),
  wrongQuestions: (params) => request.get('/learning/wrong-questions', { params }),
  updateWrong: (id, data) => request.put(`/learning/wrong-questions/${id}`, data),
  analyzeWrong: (id) => request.post(`/learning/wrong-questions/${id}/analyze`),
  redoWrong: (id) => request.post(`/learning/wrong-questions/${id}/redo`),
  reviewPlans: (params) => request.get('/learning/review/plans', { params }),
  completeReview: (id, data) => request.put(`/learning/review/plans/${id}/complete`, data),
  masteryMap: (params) => request.get('/learning/review/mastery', { params }),
  generatePlan: (data) => request.post('/learning/review/plan', data),
  // 题目收藏
  favorites: (params) => request.get('/learning/favorites', { params }),
  addFavorite: (data) => request.post('/learning/favorites', data),
  removeFavorite: (id) => request.delete(`/learning/favorites/${id}`),
  removeFavoriteByQid: (qid) => request.delete(`/learning/favorites/by-question/${qid}`),
  checkFavorite: (qid) => request.get(`/learning/favorites/check/${qid}`),
  // 批量检查（练习页整卷一次拉取，替代逐题串行 N+1）
  checkFavoritesBatch: (qids) => request.get('/learning/favorites/check-batch',
    { params: { question_ids: qids.join(',') } }),
  favoritesPractice: (data) => request.post('/learning/favorites/practice', data),
  // 错题变式练习
  wrongVariant: (wid) => request.post(`/learning/wrong-questions/${wid}/variant`),
  // 自主组卷
  customPaper: (data) => request.post('/learning/custom-paper', data),
  // 学习目标
  goals: () => request.get('/learning/goals'),
  createGoal: (data) => request.post('/learning/goals', data),
  updateGoal: (id, data) => request.put(`/learning/goals/${id}`, data),
  deleteGoal: (id) => request.delete(`/learning/goals/${id}`),
  checkin: (id, data) => request.post(`/learning/goals/${id}/checkin`, data),
  // 学习路径
  learningPath: (params) => request.get('/learning/path/recommend', { params }),
  // 闪卡
  flashcards: (params) => request.get('/learning/flashcards', { params })
}

// ---------------- AI Agent ----------------
export const agentApi = {
  list: () => request.get('/agent/list'),
  status: () => request.get('/agent/status'),
  chat: (data) => request.post('/agent/chat', data),
  questionGenerator: (data) => request.post('/agent/question-generator', data),
  paperComposer: (data) => request.post('/agent/paper-composer', data),
  grading: (data) => request.post('/agent/grading', data),
  studyPlanner: (data) => request.post('/agent/study-planner', data),
  tutor: (data) => request.post('/agent/tutor', data),
  noteOrganizer: (data) => request.post('/agent/note-organizer', data),
  logs: (params) => request.get('/agent/logs', { params }),
  // 长任务：提交后轮询（出题/组卷在 LLM 下降需 20-60s）
  createJob: (data) => request.post('/agent/jobs', data),
  job: (id) => request.get(`/agent/jobs/${id}`),
  jobs: (params) => request.get('/agent/jobs', { params }),
}

// ---------------- 报表 ----------------
export const reportApi = {
  studentOverview: () => request.get('/report/student/overview'),
  scoreTrend: (params) => request.get('/report/student/score-trend', { params }),
  knowledgeRadar: (params) => request.get('/report/student/knowledge-radar', { params }),
  wrongAnalysis: (params) => request.get('/report/student/wrong-analysis', { params }),
  learningSuggestion: () => request.get('/report/student/learning-suggestion'),
  classOverview: (params) => request.get('/report/teacher/class-overview', { params }),
  studentComparison: (params) => request.get('/report/teacher/student-comparison', { params }),
  studentDetail: (params) => request.get('/report/teacher/student-detail', { params }),
  knowledgeEffect: (params) => request.get('/report/teacher/knowledge-effect', { params }),
  adminOverview: () => request.get('/report/admin/overview'),
  gradeComparison: () => request.get('/report/admin/grade-comparison'),
  subjectComparison: () => request.get('/report/admin/subject-comparison'),
  systemRuntime: () => request.get('/report/admin/system-runtime'),
  exportUrl: (params) => `/api/v1/report/export/excel?${new URLSearchParams(params)}`,
  // blob 下载：带 token 的 axios 请求。window.open 无法携带 Authorization，
  // 学生端此前导出必 401；report_type 未传时后端 422（Query 必填）。
  exportExcel: (params) => request.get('/report/export/excel', { params, responseType: 'blob' }),
}

// ---------------- 日志与任务 ----------------
export const logApi = {
  login: (params) => request.get('/logs/login', { params }),
  operation: (params) => request.get('/logs/operation', { params }),
  error: (params) => request.get('/logs/error', { params }),
  exportUrl: (type) => `/api/v1/logs/export?log_type=${type}`,
  // blob 下载：window.open 无法携带 Authorization，导出会 401
  exportExcel: (logType) => request.get('/logs/export',
    { params: { log_type: logType }, responseType: 'blob' }),
  jobs: (params) => request.get('/jobs', { params }),
  // 可用的执行逻辑（func_path 白名单）：任务标识必须从这里选，
  // 自由文本填不进后端白名单。
  jobHandlers: () => request.get('/jobs/handlers'),
  createJob: (data) => request.post('/jobs', data),
  updateJob: (id, data) => request.put(`/jobs/${id}`, data),
  toggleJob: (id) => request.put(`/jobs/${id}/toggle`),
  runJob: (id) => request.post(`/jobs/${id}/run`),
  removeJob: (id) => request.delete(`/jobs/${id}`),
  schedulerStatus: () => request.get('/jobs/status'),
  jobExecutions: (id, params) => request.get(`/jobs/${id}/executions`, { params })
}

// ---------------- 附件 ----------------
export const attachmentApi = {
  upload: (formData) => request.post('/attachments/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  // 注册页专用：匿名上传证明材料（后端仅接受图片，5MB 内）
  publicUpload: (formData) => request.post('/attachments/public-upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  batchUpload: (formData) => request.post('/attachments/batch', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  list: (params) => request.get('/attachments', { params }),
  previewUrl: (id) => `/api/v1/attachments/${id}/preview`,
  downloadUrl: (id) => `/api/v1/attachments/${id}/download`,
  // 鉴权预览 / 下载：裸 URL 放 iframe、window.open 都不带 Authorization，必然 401
  preview: (id) => request.get(`/attachments/${id}/preview`, { responseType: 'blob' }),
  download: (id) => request.get(`/attachments/${id}/download`, { responseType: 'blob' }),
  bind: (id, data) => request.put(`/attachments/${id}/bind`, data),
  remove: (id) => request.delete(`/attachments/${id}`)
}

// ---------------- 教案 ----------------
export const lessonApi = {
  list: (params) => request.get('/lesson/plans', { params }),
  // 教学管理 V2：统计 / 批量（契约 docs/TEACHING_V2.md）
  stats: (params) => request.get('/lesson/plans/stats', { params }),
  batch: (data) => request.post('/lesson/plans/batch', data),
  detail: (id) => request.get(`/lesson/plans/${id}`),
  create: (data) => request.post('/lesson/plans', data),
  update: (id, data) => request.put(`/lesson/plans/${id}`, data),
  remove: (id) => request.delete(`/lesson/plans/${id}`),
  copy: (id, data) => request.post(`/lesson/plans/${id}/copy`, data || {}),
  share: (id, data) => request.post(`/lesson/plans/${id}/share`, data),
  // 附件（图片 / PPT / 文档）：走教案专用端点（含归属校验）
  uploadAttachment: (planId, formData) => request.post(
    `/lesson/plans/${planId}/attachments`, formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }),
  attachments: (planId) => request.get(`/lesson/plans/${planId}/attachments`),
  removeAttachment: (planId, attId) => request.delete(
    `/lesson/plans/${planId}/attachments/${attId}`)
}

// ---------------- AI 教案（异步任务 + 轮询） ----------------
// 生成走异步任务：真实 LLM 下 20~60s，同步 HTTP 会被网关截断成 502/超时。
export const lessonAiApi = {
  // 表单候选（学科按年级过滤 —— 不传 grade_id 会返回 60+ 同名学科）
  options: (gradeId) => request.get('/lesson/ai/options',
    { params: gradeId ? { grade_id: gradeId } : {} }),
  generate: (data) => request.post('/lesson/ai/generate', data),
  job: (id) => request.get(`/lesson/ai/jobs/${id}`),
  jobs: (limit) => request.get('/lesson/ai/jobs', { params: { limit: limit || 20 } }),
  save: (id, data) => request.post(`/lesson/ai/jobs/${id}/save`, data || {}),
  // 导出是二进制下载，不走统一的 JSON 拦截器，直接用 blob
  exportUrl: (id) => `/api/v1/lesson/ai/jobs/${id}/export`,
  // 带 token 的 blob 导出（裸 URL 打开 / 前端 fetch 手拼 token 都不可靠）
  exportBlob: (id) => request.get(`/lesson/ai/jobs/${id}/export`,
    { responseType: 'blob' })
}
