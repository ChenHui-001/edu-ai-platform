import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store/user'

const routes = [
  { path: '/', redirect: '/dashboard' },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/Login.vue'),
    meta: { public: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/login/Register.vue'),
    meta: { public: true }
  },
  {
    path: '/',
    component: () => import('@/layout/MainLayout.vue'),
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('@/views/Dashboard.vue'),
        meta: { title: '工作台', icon: 'HomeFilled' } },

      // 管理员
      { path: 'admin/users', name: 'UserManage', component: () => import('@/views/admin/UserManage.vue'),
        meta: { title: '用户管理', icon: 'User', roles: ['sys_admin', 'grade_admin'] } },
      { path: 'admin/roles', name: 'RoleManage', component: () => import('@/views/admin/RoleManage.vue'),
        meta: { title: '角色权限', icon: 'Avatar', roles: ['sys_admin'] } },
      { path: 'admin/registrations', name: 'RegistrationAudit', component: () => import('@/views/admin/RegistrationAudit.vue'),
        meta: { title: '注册审批', icon: 'Stamp', roles: ['sys_admin'] } },
      { path: 'admin/grades', name: 'GradeManage', component: () => import('@/views/admin/ResourceManage.vue'),
        meta: { title: '年级管理', icon: 'School', perm: 'resource:grade:list' } },
      { path: 'admin/subjects', name: 'SubjectManage', component: () => import('@/views/admin/ResourceManage.vue'),
        meta: { title: '学科管理', icon: 'Collection', perm: 'resource:subject:list' } },
      { path: 'admin/knowledge', name: 'KnowledgeManage', component: () => import('@/views/admin/KnowledgeManage.vue'),
        meta: { title: '知识点管理', icon: 'Share', perm: 'resource:knowledge:list' } },
      { path: 'admin/classes', name: 'ClassManage', component: () => import('@/views/admin/ClassManage.vue'),
        meta: { title: '班级管理', icon: 'OfficeBuilding', perm: 'resource:class:list' } },
      { path: 'admin/logs', name: 'LogManage', component: () => import('@/views/admin/LogManage.vue'),
        meta: { title: '日志审计', icon: 'Document', roles: ['sys_admin', 'grade_admin'] } },
      { path: 'admin/jobs', name: 'JobManage', component: () => import('@/views/admin/JobManage.vue'),
        meta: { title: '定时任务', icon: 'Clock', roles: ['sys_admin'] } },
      { path: 'admin/attachments', name: 'AttachmentManage', component: () => import('@/views/admin/AttachmentManage.vue'),
        meta: { title: '附件管理', icon: 'Paperclip', roles: ['sys_admin', 'grade_admin'] } },
      { path: 'admin/reports', name: 'AdminReport', component: () => import('@/views/admin/AdminReport.vue'),
        meta: { title: '系统报表', icon: 'DataAnalysis', roles: ['sys_admin', 'grade_admin'] } },
      { path: 'admin/settings', name: 'SystemSetting', component: () => import('@/views/admin/SystemSetting.vue'),
        meta: { title: '系统配置', icon: 'Setting', roles: ['sys_admin'] } },
      { path: 'admin/ai-config', name: 'AiConfig', component: () => import('@/views/admin/AiConfig.vue'),
        meta: { title: 'AI 大模型配置', icon: 'Cpu', roles: ['sys_admin'] } },
      { path: 'admin/agent-logs', name: 'AgentLogs', component: () => import('@/views/admin/AgentLogs.vue'),
        meta: { title: 'AI 调用日志', icon: 'Cpu', roles: ['sys_admin', 'grade_admin'] } },

      // 教师
      { path: 'teacher/questions', name: 'QuestionBank', component: () => import('@/views/teacher/QuestionBank.vue'),
        meta: { title: '题库管理', icon: 'Notebook', perm: 'question:bank:list' } },
      { path: 'teacher/papers', name: 'PaperManage', component: () => import('@/views/teacher/PaperManage.vue'),
        meta: { title: '试卷管理', icon: 'Tickets', perm: 'paper:list' } },
      { path: 'teacher/tasks', name: 'TaskManage', component: () => import('@/views/teacher/TaskManage.vue'),
        meta: { title: '作业考试', icon: 'List', perm: 'task:list' } },
      { path: 'teacher/grading', name: 'GradingCenter', component: () => import('@/views/teacher/GradingCenter.vue'),
        meta: { title: '批改中心', icon: 'EditPen', perm: 'grading:list' } },
      { path: 'teacher/lessons', name: 'LessonPlanManage', component: () => import('@/views/teacher/LessonPlanManage.vue'),
        meta: { title: '教案管理', icon: 'Document', perm: 'lesson:plan:list' } },
      { path: 'teacher/analysis', name: 'ClassAnalysis', component: () => import('@/views/teacher/ClassAnalysis.vue'),
        meta: { title: '班级学情', icon: 'TrendCharts', perm: 'analysis:class' } },
      { path: 'teacher/students', name: 'StudentAnalysis', component: () => import('@/views/teacher/StudentAnalysis.vue'),
        meta: { title: '学生分析', icon: 'UserFilled', perm: 'analysis:student' } },
      { path: 'teacher/reports', name: 'TeacherReport', component: () => import('@/views/teacher/TeacherReport.vue'),
        meta: { title: '教学报表', icon: 'PieChart', perm: 'report:teacher' } },

      // 学生
      { path: 'student/practice', name: 'Practice', component: () => import('@/views/student/Practice.vue'),
        meta: { title: '随机练习', icon: 'Edit', perm: 'student:practice' } },
      { path: 'student/exams', name: 'MyExams', component: () => import('@/views/student/MyExams.vue'),
        meta: { title: '模拟考试', icon: 'Timer', perm: 'student:exam' } },
      { path: 'student/exam/:taskId', name: 'ExamPaper', component: () => import('@/views/student/ExamPaper.vue'),
        meta: { title: '答题', hidden: true, perm: 'student:exam' } },
      { path: 'student/wrong', name: 'WrongBook', component: () => import('@/views/student/WrongBook.vue'),
        meta: { title: '错题本', icon: 'Warning', perm: 'student:wrong' } },
      { path: 'student/notes', name: 'MyNotes', component: () => import('@/views/student/MyNotes.vue'),
        meta: { title: '学习笔记', icon: 'Notebook', perm: 'student:note' } },
      { path: 'student/review', name: 'SmartReview', component: () => import('@/views/student/SmartReview.vue'),
        meta: { title: '智能复习', icon: 'Refresh', perm: 'student:review' } },
      { path: 'student/report', name: 'MyReport', component: () => import('@/views/student/MyReport.vue'),
        meta: { title: '学习报表', icon: 'DataLine', perm: 'student:report' } },
      { path: 'student/scores', name: 'ScoreCenter', component: () => import('@/views/student/ScoreCenter.vue'),
        meta: { title: '成绩中心', icon: 'Medal', perm: 'student:score' } },
      { path: 'student/favorites', name: 'MyFavorites', component: () => import('@/views/student/MyFavorites.vue'),
        meta: { title: '题目收藏', icon: 'Star', perm: 'student:favorites' } },
      { path: 'student/mastery', name: 'MasteryMap', component: () => import('@/views/student/MasteryMap.vue'),
        meta: { title: '掌握图谱', icon: 'Histogram', perm: 'student:mastery' } },
      { path: 'student/custom', name: 'CustomPaper', component: () => import('@/views/student/CustomPaper.vue'),
        meta: { title: '自主组卷', icon: 'Tickets', perm: 'student:custom' } },
      { path: 'student/goals', name: 'StudyGoals', component: () => import('@/views/student/StudyGoals.vue'),
        meta: { title: '学习打卡', icon: 'Calendar', perm: 'student:goals' } },
      { path: 'student/path', name: 'LearningPath', component: () => import('@/views/student/LearningPath.vue'),
        meta: { title: '学习路径', icon: 'Guide', perm: 'student:path' } },
      { path: 'student/flashcard', name: 'Flashcards', component: () => import('@/views/student/Flashcards.vue'),
        meta: { title: '闪卡速记', icon: 'Box', perm: 'student:flashcard' } },
      { path: 'student/knowledge', name: 'KnowledgeLibrary', component: () => import('@/views/student/KnowledgeLibrary.vue'),
        meta: { title: '知识资料', icon: 'Reading', perm: 'student:knowledge' } },

      // AI
      { path: 'agent/chat', name: 'AgentChat', component: () => import('@/views/agent/AgentChat.vue'),
        meta: { title: 'AI 智能助手', icon: 'MagicStick', perm: 'agent:chat' } },
      { path: 'agent/generate', name: 'AgentGenerate', component: () => import('@/views/agent/AgentGenerate.vue'),
        meta: { title: 'AI 出题组卷', icon: 'Cpu', roles: ['sys_admin', 'grade_admin', 'teacher'] } },

      { path: 'profile', name: 'Profile', component: () => import('@/views/Profile.vue'),
        meta: { title: '个人中心', hidden: true } }
    ]
  },
  // 未知路径不再静默回首页：此前任何拼错的地址都表现为「点击后一闪，
  // 又回到 dashboard」，用户与排查者都无法判断是权限问题还是地址写错。
  { path: '/403', name: 'Forbidden',
    component: () => import('@/views/ErrorPage.vue'), meta: { title: '无权访问', public: true } },
  { path: '/:pathMatch(.*)*', name: 'NotFound',
    component: () => import('@/views/ErrorPage.vue'), meta: { title: '页面不存在', public: true } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')

  if (to.meta.public) {
    // 仅登录页在已登录时强制回首页；
    // 注册页必须始终可访问 —— 否则已登录用户点「注册账号」会被弹回
    // dashboard，表现为「点击无反应/无法跳转」（issue #3）。
    if (token && to.path === '/login') {
      return next('/dashboard')
    }
    return next()
  }

  if (!token) {
    return next({ path: '/login', query: { redirect: to.fullPath } })
  }

  // 权限校验：优先读 Pinia 内存态（启动 fetchProfile / 刷新令牌都会同步最新权限），
  // localStorage 仅作兜底 —— 刷新页面瞬间 Pinia 可能还没完成初始化，
  // 此时直接读空内存态会让已登录用户误跳 403。
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  let storePerms = null
  try {
    // pinia 在 main.js 里先于 router 安装，守卫内可安全取 store
    storePerms = useUserStore().permissions
  } catch { /* pinia 未就绪（极早期导航/单测）时走 localStorage 兜底 */ }
  const roles = (storePerms?.roles?.length ? storePerms.roles : user.permissions?.roles) || []
  const perms = (storePerms?.permissions?.length
    ? storePerms.permissions
    : user.permissions?.permissions) || []

  if (to.meta.roles && !to.meta.roles.some((r) => roles.includes(r))) {
    return next('/403')
  }
  if (to.meta.perm) {
    if (!perms.includes('*') && !perms.includes(to.meta.perm)) {
      return next('/403')
    }
  }
  next()
})

export default router
