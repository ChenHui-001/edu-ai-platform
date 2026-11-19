import request from './request'

export const extensionApi = {
  plans: () => request.get('/learning/remediation'),
  createPlan: diagnosis_id => request.post('/learning/remediation', { diagnosis_id }),
  plan: id => request.get(`/learning/remediation/${id}`),
  quiz: (id, data) => request.post(`/learning/remediation/${id}/quizzes`, data),
  submitQuiz: (id, data) => request.post(`/learning/remediation/${id}/answers`, data),
  classGraph: params => request.get('/teaching/graph', { params }),
  assign: data => request.post('/teaching/graph/assign', data),
  quality: params => request.get('/question/quality', { params }),
  publish: ids => request.post('/question/quality/publish', { ids }),
  visual: (id, visual) => request.put(`/question/quality/${id}/visual`, { visual }),
  tutor: (question_id, stage) => request.post('/learning/tutor', { question_id, stage }),
  feedback: data => request.post('/learning/tutor/feedback', data),
  feedbackList: params => request.get('/learning/tutor/feedback', { params }),
  reviewFeedback: (id, correction, confirm_scope = false) =>
    request.put(`/learning/tutor/feedback/${id}`, { correction, confirm_scope }),
  syncHistory: () => request.get('/system/taxonomy-sync'),
  syncPreview: ref => request.post('/system/taxonomy-sync/preview', { ref }, { timeout: 120000 }),
  syncApply: preview_id => request.post('/system/taxonomy-sync/apply', { preview_id }, { timeout: 120000 }),
  syncRestore: id => request.post(`/system/taxonomy-sync/${id}/restore`, {}, { timeout: 120000 })
}
