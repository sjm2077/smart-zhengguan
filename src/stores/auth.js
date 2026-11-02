import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// 演示账号：角色是学院真实存在的岗位，账号与密码是本平台演示用的，
// 不使用任何真实教师的账号信息；岗位职责展示见登录页“官网岗位对照”。
const MOCK_USERS = [
  {
    id: 1,
    username: 'dean',
    password: '123456',
    role: 'dean',
    roleName: '院长',
    avatar: '👔',
    name: '院长（演示）',
    college: '政治学与公共管理学院',
    email: 'dean@demo.local',
    office: '学院办公楼',
    joinDate: '2015-09-01',
    dutyKey: '院长'
  },
  {
    id: 2,
    username: 'admin',
    password: '123456',
    role: 'admin',
    roleName: '系统管理员',
    avatar: '👨‍💼',
    name: '系统管理员（演示）',
    college: '信息化中心',
    email: 'admin@demo.local',
    office: '信息中心',
    joinDate: '2018-03-15',
    dutyKey: ''
  },
  {
    id: 3,
    username: 'jw',
    password: '123456',
    role: 'jw',
    roleName: '教务教师',
    avatar: '👨‍🏫',
    name: '教务教师（演示）',
    college: '教务处',
    email: 'jw@demo.local',
    office: '教务处',
    joinDate: '2019-07-01',
    dutyKey: '分管本科教学'
  },
  {
    id: 4,
    username: 'ky',
    password: '123456',
    role: 'ky',
    roleName: '科研教师',
    avatar: '🔬',
    name: '科研教师（演示）',
    college: '科研管理办公室',
    email: 'ky@demo.local',
    office: '科研楼',
    joinDate: '2020-01-10',
    dutyKey: '分管科研'
  },
  {
    id: 5,
    username: 'rs',
    password: '123456',
    role: 'rs',
    roleName: '人事教师',
    avatar: '👩‍💼',
    name: '人事教师（演示）',
    college: '人事处',
    email: 'rs@demo.local',
    office: '人事处',
    joinDate: '2019-09-01',
    dutyKey: '分管人事'
  },
  {
    id: 6,
    username: 'yjs',
    password: '123456',
    role: 'yjs',
    roleName: '研究生教师',
    avatar: '🎓',
    name: '研究生教师（演示）',
    college: '研究生管理办公室',
    email: 'yjs@demo.local',
    office: '研究生院',
    joinDate: '2021-03-01',
    dutyKey: '分管研究生'
  },
  {
    id: 7,
    username: 'student',
    password: '123456',
    role: 'student',
    roleName: '学生',
    avatar: '🎒',
    name: '学生（演示）',
    college: '政治学与公共管理学院',
    email: 'student@demo.local',
    office: '学生公寓',
    joinDate: '2022-09-01',
    studentId: '2022010101',
    major: '行政管理',
    grade: '2022级',
    studentIdNote: '演示学号',
    enrollmentDate: '2022-09-01',
    gpa: '—',
    credits: '—',
    coursesCompleted: '—'
  }
]

const MENU_CONFIG = [
  { path: '/dashboard', title: '综合概览', icon: '🏠', roles: ['dean', 'admin', 'jw', 'ky', 'rs', 'yjs', 'student'] },
  { path: '/teaching', title: '教学管理', icon: '📚', roles: ['dean', 'admin', 'jw'] },
  { path: '/research', title: '科研管理', icon: '🔬', roles: ['dean', 'admin', 'ky'] },
  { path: '/hr', title: '人事系统', icon: '🏢', roles: ['dean', 'admin', 'rs'] },
  { path: '/graduate', title: '研究生管理', icon: '🎓', roles: ['dean', 'admin', 'yjs'] },
  { path: '/warning', title: '智能预警', icon: '⚠️', roles: ['dean', 'admin'] },
  { path: '/portrait', title: '师生画像', icon: '👤', roles: ['dean', 'admin', 'rs'] },
  { path: '/wordcloud', title: '词云分析', icon: '☁️', roles: ['dean', 'admin', 'ky'] },
  { path: '/treehole', title: '校园树洞', icon: '💭', roles: ['dean', 'admin', 'jw', 'ky', 'rs', 'yjs', 'student'] }
]

const KPI_PERMISSIONS = {
  students: { roles: ['dean', 'admin', 'jw', 'ky', 'rs', 'yjs', 'student'], level: 'full' },
  undergrad: { roles: ['dean', 'admin', 'jw', 'rs', 'yjs', 'student'], level: 'full', else: '--' },
  master: { roles: ['dean', 'admin', 'jw', 'rs', 'yjs', 'student'], level: 'full', else: '--' },
  doctor: { roles: ['dean', 'admin', 'jw', 'rs', 'yjs', 'student'], level: 'full', else: '--' },
  staff: { roles: ['dean', 'admin', 'jw', 'ky', 'rs', 'yjs', 'student'], level: 'full' },
  projects: { roles: ['dean', 'admin', 'ky'], level: 'full', else: '--' },
  funding: { roles: ['dean', 'admin', 'ky'], level: 'full', else: '--' },
  budget: { roles: ['dean', 'admin'], level: 'full', else: 'hidden' }
}

export const useAuthStore = defineStore('auth', () => {
  // 演示用登录态：本地 token + 12 小时有效期（与真实 SSO 的会话超时口径一致）
  const SESSION_HOURS = 12
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('userInfo') || 'null'))
  const expireAt = ref(Number(localStorage.getItem('tokenExpire') || 0))

  const isExpired = computed(() => !expireAt.value || Date.now() > expireAt.value)

  const isLoggedIn = computed(() => !!token.value && !!userInfo.value && !isExpired.value)

  const sessionRemain = computed(() => {
    if (!expireAt.value) return 0
    return Math.max(0, Math.round((expireAt.value - Date.now()) / 60000))
  })

  const currentRole = computed(() => userInfo.value?.role || '')

  const menuList = computed(() => {
    if (!userInfo.value) return []
    return MENU_CONFIG.filter(menu => menu.roles.includes(userInfo.value.role))
  })

  const hasPermission = (roles) => {
    if (!userInfo.value) return false
    if (typeof roles === 'string') roles = [roles]
    return roles.includes(userInfo.value.role)
  }

  const getKpiPermission = (key) => {
    const config = KPI_PERMISSIONS[key]
    if (!config) return 'hidden'
    if (config.roles.includes(currentRole.value)) return 'full'
    return config.else || 'hidden'
  }

  const login = async (credentials) => {
    const user = MOCK_USERS.find(
      u => u.username === credentials.username && u.password === credentials.password
    )

    if (!user) {
      throw new Error('用户名或密码错误')
    }

    const mockToken = `demo_token_${Date.now()}_${user.id}`
    const deadline = Date.now() + SESSION_HOURS * 3600 * 1000
    token.value = mockToken
    expireAt.value = deadline
    userInfo.value = {
      id: user.id,
      username: user.username,
      role: user.role,
      roleName: user.roleName,
      avatar: user.avatar,
      name: user.name,
      college: user.college,
      email: user.email,
      office: user.office,
      joinDate: user.joinDate,
      dutyKey: user.dutyKey,
      isDemoAccount: true,
      studentId: user.studentId,
      major: user.major,
      grade: user.grade,
      enrollmentDate: user.enrollmentDate,
      gpa: user.gpa,
      credits: user.credits,
      coursesCompleted: user.coursesCompleted
    }

    localStorage.setItem('token', mockToken)
    localStorage.setItem('tokenExpire', String(deadline))
    localStorage.setItem('userInfo', JSON.stringify(userInfo.value))

    return userInfo.value
  }

  const logout = () => {
    token.value = ''
    userInfo.value = null
    expireAt.value = 0
    localStorage.removeItem('token')
    localStorage.removeItem('tokenExpire')
    localStorage.removeItem('userInfo')
  }

  const checkAuth = () => {
    const savedToken = localStorage.getItem('token')
    const savedUserInfo = localStorage.getItem('userInfo')
    const savedExpire = Number(localStorage.getItem('tokenExpire') || 0)

    if (savedToken && savedUserInfo && savedExpire && Date.now() <= savedExpire) {
      token.value = savedToken
      userInfo.value = JSON.parse(savedUserInfo)
      expireAt.value = savedExpire
    } else if (savedToken || savedUserInfo) {
      // 过期或数据不完整：直接清掉，避免半登录态
      logout()
    }
  }

  const updateUserInfo = (updated) => {
    userInfo.value = updated
    localStorage.setItem('userInfo', JSON.stringify(updated))
  }

  return {
    token,
    userInfo,
    expireAt,
    isExpired,
    isLoggedIn,
    sessionRemain,
    currentRole,
    menuList,
    hasPermission,
    getKpiPermission,
    login,
    logout,
    checkAuth,
    updateUserInfo
  }
})
