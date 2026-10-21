// 密码规则必须与后端一致：backend/app/core/security.py::validate_password_strength
// 后端要求「至少 8 位 + 同时包含字母和数字」，前端两处表单（注册、个人中心改密）
// 此前都写「至少 6 位」且不校验复杂度 —— 用户按提示填 6 位纯数字，
// 提交后才被后端 400 打回，属于纯无效引导。规则只在这里维护一份。
export const PASSWORD_MIN_LENGTH = 8

export function validatePassword(_rule, value, callback) {
  const pwd = value || ''
  if (!pwd) return callback(new Error('请输入密码'))
  if (pwd.length < PASSWORD_MIN_LENGTH) {
    return callback(new Error(`密码至少 ${PASSWORD_MIN_LENGTH} 位`))
  }
  if (pwd.length > 64) return callback(new Error('密码不能超过 64 位'))
  if (!(/[A-Za-z]/.test(pwd) && /\d/.test(pwd))) {
    return callback(new Error('密码需同时包含字母和数字'))
  }
  return callback()
}
