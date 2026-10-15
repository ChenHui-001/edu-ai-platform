<template>
  <el-container class="layout">
    <el-aside :width="collapsed ? '64px' : '220px'" class="aside">
      <div class="logo">
        <el-icon><School /></el-icon>
        <span v-show="!collapsed">九年义务教育学习管理</span>
      </div>
      <el-scrollbar class="menu-scroll">
        <el-menu
          :default-active="activeMenu"
          :collapse="collapsed"
          :collapse-transition="false"
          router
          background-color="#1f2d3d"
          text-color="#bfcbd9"
          active-text-color="#409eff"
        >
          <el-menu-item index="/dashboard">
            <el-icon><HomeFilled /></el-icon>
            <template #title>工作台</template>
          </el-menu-item>

          <el-sub-menu v-for="group in menuGroups" :key="group.title" :index="group.title">
            <template #title>
              <el-icon><component :is="group.icon" /></el-icon>
              <span>{{ group.title }}</span>
            </template>
            <el-menu-item
              v-for="item in group.items"
              :key="item.path"
              :index="item.path"
            >
              <el-icon><component :is="item.icon" /></el-icon>
              <template #title>{{ item.title }}</template>
            </el-menu-item>
          </el-sub-menu>
        </el-menu>
      </el-scrollbar>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="collapsed = !collapsed">
            <Fold v-if="!collapsed" /><Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item>{{ route.meta.title || '首页' }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <div class="header-right">
          <el-tooltip content="AI 引擎状态" placement="bottom">
            <el-tag :type="aiStatus.llm_enabled ? 'success' : 'warning'" size="small"
                    effect="dark" round style="margin-right: 12px">
              <el-icon style="vertical-align: -2px"><Cpu /></el-icon>
              AI {{ aiStatus.llm_enabled ? '已启用' : '降级模式' }}
            </el-tag>
          </el-tooltip>

          <el-popover placement="bottom-end" :width="340" trigger="click">
            <template #reference>
              <el-badge :value="unread" :hidden="unread === 0" style="margin-right: 16px">
                <el-icon size="18" class="header-icon"><Bell /></el-icon>
              </el-badge>
            </template>
            <div class="notif-header">
              <span>通知</span>
              <el-link type="primary" :underline="false" @click="readAll">全部已读</el-link>
            </div>
            <el-scrollbar max-height="320px">
              <el-empty v-if="notifications.length === 0" description="暂无通知" :image-size="60" />
              <div
                v-for="n in notifications" :key="n.id"
                class="notif-item" :class="{ unread: !n.is_read }"
                @click="markRead(n)"
              >
                <div class="notif-title">{{ n.title }}</div>
                <div class="notif-content">{{ n.content }}</div>
                <div class="notif-time">{{ formatTime(n.created_at) }}</div>
              </div>
            </el-scrollbar>
          </el-popover>

          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-avatar :size="30" style="background:#409eff">
                {{ userStore.realName.charAt(0) }}
              </el-avatar>
              <span class="user-name">{{ userStore.realName }}</span>
              <el-tag size="small" type="info">{{ userStore.roleLabel }}</el-tag>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon> 个人中心
                </el-dropdown-item>
                <el-dropdown-item command="logout" divided>
                  <el-icon><SwitchButton /></el-icon> 退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/store/user'
import { agentApi, systemApi } from '@/api'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const collapsed = ref(false)
const notifications = ref([])
const unread = ref(0)
const aiStatus = ref({ llm_enabled: false })

const activeMenu = computed(() => route.path)

// 菜单分组（按角色/权限点过滤）
// allRoutes 是 router.getRoutes().filter() 返回的普通数组，不是 ref，
// 渲染时直接用 allRoutes，不能用 allRoutes.value（会得到 undefined）。
const allRoutes = router.getRoutes().filter(r => r.meta?.title && !r.meta.hidden && r.path.startsWith('/'))

const menuGroups = computed(() => {
  const roles = userStore.permissions.roles || []
  const perms = userStore.permissions.permissions || []
  const allowed = allRoutes.filter(r => {
    if (r.meta.roles && !r.meta.roles.some(x => roles.includes(x))) return false
    if (r.meta.perm && !perms.includes('*') && !perms.includes(r.meta.perm)) return false
    return true
  }).filter(r => r.path !== '/dashboard' && r.path !== '/')

  const groups = [
    { title: '教学资源', icon: 'Collection', match: ['/admin/grades', '/admin/subjects', '/admin/knowledge', '/admin/classes'] },
    { title: '题库试卷', icon: 'Notebook', match: ['/teacher/questions', '/teacher/papers'] },
    { title: '教学管理', icon: 'EditPen', match: ['/teacher/tasks', '/teacher/grading'] },
    { title: '学情分析', icon: 'TrendCharts', match: ['/teacher/analysis', '/teacher/students', '/teacher/reports'] },
    { title: '学习中心', icon: 'Reading', match: ['/student/practice', '/student/exams', '/student/wrong', '/student/notes', '/student/review', '/student/report', '/student/scores'] },
    { title: 'AI 智能', icon: 'MagicStick', match: ['/agent/chat', '/agent/generate', '/admin/agent-logs'] },
    { title: '系统管理', icon: 'Setting', match: ['/admin/users', '/admin/roles', '/admin/registrations', '/admin/logs', '/admin/jobs', '/admin/attachments', '/admin/reports', '/admin/settings'] }
  ]

  return groups.map(g => ({
    title: g.title,
    icon: g.icon,
    items: allowed.filter(r => g.match.includes(r.path)).map(r => ({
      path: r.path, title: r.meta.title, icon: r.meta.icon || 'Document'
    }))
  })).filter(g => g.items.length > 0)
})

function formatTime(t) {
  return t ? String(t).slice(5, 16) : ''
}

async function loadNotifications() {
  try {
    const res = await systemApi.notifications({ page: 1, page_size: 10 })
    notifications.value = res.data.items
    unread.value = res.data.unread
  } catch (e) { /* 忽略 */ }
}

async function markRead(n) {
  if (!n.is_read) {
    await systemApi.readNotification(n.id)
    n.is_read = true
    unread.value = Math.max(0, unread.value - 1)
  }
}

async function readAll() {
  await systemApi.readAllNotifications()
  notifications.value.forEach(n => (n.is_read = true))
  unread.value = 0
}

async function handleCommand(cmd) {
  if (cmd === 'profile') {
    router.push('/profile')
  } else if (cmd === 'logout') {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', { type: 'warning' })
    userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  }
}

onMounted(async () => {
  loadNotifications()
  try {
    const res = await agentApi.status()
    aiStatus.value = res.data
  } catch (e) { /* 忽略 */ }
})
</script>

<style scoped>
.layout { height: 100vh; }

.aside {
  background: #1f2d3d;
  transition: width 0.28s;
  overflow: hidden;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 18px;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  background: #1a2532;
  white-space: nowrap;
}

.menu-scroll { height: calc(100vh - 60px); }
.aside :deep(.el-menu) { border-right: none; }

.header {
  height: 60px;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.header-left, .header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.collapse-btn {
  font-size: 20px;
  cursor: pointer;
  color: #5a5e66;
}

.header-icon { cursor: pointer; color: #5a5e66; }

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  outline: none;
}

.user-name { font-size: 14px; color: #303133; }

.notif-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid #ebeef5;
  font-weight: 600;
}

.notif-item {
  padding: 10px 12px;
  border-bottom: 1px solid #f5f7fa;
  cursor: pointer;
}

.notif-item:hover { background: #f5f7fa; }
.notif-item.unread { background: #ecf5ff; }
.notif-title { font-size: 14px; font-weight: 500; margin-bottom: 4px; }
.notif-content { font-size: 12px; color: #909399; line-height: 1.5; }
.notif-time { font-size: 11px; color: #c0c4cc; margin-top: 4px; }

.main {
  padding: 0;
  background: var(--page-bg);
  overflow-y: auto;
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.18s; }
.fade-enter-from, .fade-to { opacity: 0; }
</style>
