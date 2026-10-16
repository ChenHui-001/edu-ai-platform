import { defineStore } from 'pinia'
import { authApi } from '@/api'

export const useUserStore = defineStore('user', {
  state: () => ({
    userInfo: JSON.parse(localStorage.getItem('user') || '{}'),
    permissions: JSON.parse(localStorage.getItem('user') || '{}')?.permissions || {
      roles: [], permissions: [], menus: []
    },
    notificationCount: 0
  }),

  getters: {
    isAdmin: (state) => state.permissions.roles?.includes('sys_admin'),
    // 权限点判断（按钮级权限）。sys_admin 登录时后端返回 perms=['*'] 通配。
    can: (state) => (code) => {
      const perms = state.permissions.permissions || []
      return perms.includes('*') || perms.includes(code)
    },
    isTeacher: (state) => state.permissions.roles?.some(r => ['teacher', 'grade_admin', 'sys_admin'].includes(r)),
    isStudent: (state) => state.permissions.roles?.includes('student'),
    realName: (state) => state.userInfo.real_name || '用户',
    roleLabel: (state) => {
      const map = {
        sys_admin: '系统管理员', grade_admin: '年级管理员',
        teacher: '任课教师', student: '学生', guest: '访客'
      }
      const r = state.permissions.roles?.[0]
      return map[r] || '用户'
    }
  },

  actions: {
    async login(payload) {
      const res = await authApi.login(payload)
      const { access_token, refresh_token, user, permission } = res.data
      localStorage.setItem('access_token', access_token)
      localStorage.setItem('refresh_token', refresh_token)
      const merged = { ...user, permissions: permission }
      localStorage.setItem('user', JSON.stringify(merged))
      this.userInfo = merged
      this.permissions = permission
      return res
    },

    async fetchProfile() {
      const res = await authApi.profile()
      const merged = { ...res.data, permissions: res.data.permission }
      localStorage.setItem('user', JSON.stringify(merged))
      this.userInfo = merged
      this.permissions = res.data.permission
      return res.data
    },

    hasPerm(code) {
      const p = this.permissions.permissions || []
      return p.includes('*') || p.includes(code)
    },

    logout() {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      this.userInfo = {}
      this.permissions = { roles: [], permissions: [], menus: [] }
    }
  }
})
