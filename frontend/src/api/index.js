import request from './request'

// ---------------- 认证 ----------------
export const authApi = {
  captcha: () => request.get('/auth/captcha'),
  login: (data) => request.post('/auth/login', data),
  register: (data) => request.post('/auth/register', data),
  profile: () => request.get('/auth/profile'),
  updateProfile: (data) => request.put('/auth/profile', data),
  changePassword: (data) => request.put('/auth/password', data),
  logout: () => request.post('/auth/logout'),
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
  knowledge: (params) => request.get('/edu/knowledge', { params }),
  knowledgeList: (params) => request.get('/edu/knowledge/list', { params }),
  createKnowledge: (data) => request.post('/edu/knowledge', data),
  updateKnowledge: (id, data) => request.put(`/edu/knowledge/${id}`, data),
  deleteKnowledge: (id) => request.delete(`/edu/knowledge/${id}`),
  reindex: () => request.post('/edu/knowledge/reindex'),
  classes: (params) => request.get('/edu/classes', { params }),
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

// ---------------- 题库与试卷 ----------------
export const questionApi = {
  list: (params) => request.get('/question/questions', { params }),
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
  papers: (params) => request.get('/question/papers', { params }),
  paperDetail: (id) => request.get(`/question/papers/${id}`),
  createPaper: (data) => request.post('/question/papers', data),
  updatePaper: (id, data) => request.put(`/question/papers/${id}`, data),
  removePaper: (id) => request.delete(`/question/papers/${id}`),
  copyPaper: (id, data) => request.post(`/question/papers/${id}/copy`, data),
  sharePaper: (id, data) => request.post(`/question/papers/${id}/share`, data),
  exportPaperUrl: (id) => `/api/v1/question/papers/${id}/export`
}

// ---------------- 作业与考试 ----------------
export const taskApi = {
  list: (params) => request.get('/task/tasks', { params }),
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
  detail: (id) => request.get(`/grading/submissions/${id}`),
  grade: (id, data) => request.post(`/grading/submissions/${id}/grade`, data),
  reject: (id, data) => request.post(`/grading/submissions/${id}/reject`, data),
  publish: (id) => request.post(`/grading/submissions/${id}/publish`),
  report: (taskId) => request.post(`/grading/tasks/${taskId}/report`),
  aiComment: (taskId) => request.post(`/grading/tasks/${taskId}/ai-comment`)
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
  logs: (params) => request.get('/agent/logs', { params })
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
  jobs: (params) => request.get('/jobs', { params }),
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
  batchUpload: (formData) => request.post('/attachments/batch', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  list: (params) => request.get('/attachments', { params }),
  previewUrl: (id) => `/api/v1/attachments/${id}/preview`,
  downloadUrl: (id) => `/api/v1/attachments/${id}/download`,
  bind: (id, data) => request.put(`/attachments/${id}/bind`, data),
  remove: (id) => request.delete(`/attachments/${id}`)
}
