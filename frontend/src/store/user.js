import { defineStore } from 'pinia'
import { authApi } from '@/api'

export const useUserStore = defineStore('user', {
  state: () => ({
    userInfo: JSON.parse(localStorage.getItem('user') || '{}'),
    permissions: JSON.parse(localStorage.getItem('user') || '{}')?.permissions || {
      roles: [], permissions: [], menus: []
    }
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

    /**
     * 同步最新权限快照（令牌刷新、启动时 fetchProfile 共用）。
     * request.js 的刷新分支不能顶层 import 本 store（request ← api ← store 循环依赖），
     * 由它动态 import 后调用本 action，保证 Pinia 与 localStorage 不会各说各话。
     */
    applyPermission(permission, user) {
      if (user) this.userInfo = { ...this.userInfo, ...user }
      if (permission) this.permissions = permission
      localStorage.setItem('user', JSON.stringify({
        ...this.userInfo, permissions: this.permissions
      }))
    },

    async logout() {
      // 先通知后端注销：后端需 refresh_token 才能连带吊销刷新令牌，
      // 否则「退出登录」后旧令牌在过期前仍可继续调用接口。
      // 令牌可能已失效、网络也可能不可达，失败不阻断本地清理。
      const refreshToken = localStorage.getItem('refresh_token')
      await authApi.logout(refreshToken ? { refresh_token: refreshToken } : undefined)
        .catch(() => {})
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      this.userInfo = {}
      this.permissions = { roles: [], permissions: [], menus: [] }
    }
  }
})
