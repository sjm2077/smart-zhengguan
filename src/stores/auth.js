import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const MOCK_USERS = [
  { 
    id: 1, 
    username: 'dean', 
    password: '123456', 
    role: 'dean', 
    roleName: '院长', 
    avatar: '👔',
    name: '张明辉',
    college: '政治学与公共管理学院',
    email: 'dean@sdu.edu.cn',
    phone: '13800138001',
    office: '学院办公楼301室',
    joinDate: '2015-09-01'
  },
  { 
    id: 2, 
    username: 'admin', 
    password: '123456', 
    role: 'admin', 
    roleName: '系统管理员', 
    avatar: '👨‍💼',
    name: '李管理员',
    college: '信息化中心',
    email: 'admin@sdu.edu.cn',
    phone: '13800138002',
    office: '信息中心201室',
    joinDate: '2018-03-15'
  },
  { 
    id: 3, 
    username: 'jw', 
    password: '123456', 
    role: 'jw', 
    roleName: '教务教师', 
    avatar: '👨‍🏫',
    name: '王教务',
    college: '教务处',
    email: 'jw@sdu.edu.cn',
    phone: '13800138003',
    office: '教务处102室',
    joinDate: '2019-07-01'
  },
  { 
    id: 4, 
    username: 'ky', 
    password: '123456', 
    role: 'ky', 
    roleName: '科研教师', 
    avatar: '🔬',
    name: '陈科研',
    college: '科研管理办公室',
    email: 'ky@sdu.edu.cn',
    phone: '13800138004',
    office: '科研楼203室',
    joinDate: '2020-01-10'
  },
  { 
    id: 5, 
    username: 'rs', 
    password: '123456', 
    role: 'rs', 
    roleName: '人事教师', 
    avatar: '👩‍💼',
    name: '赵人事',
    college: '人事处',
    email: 'rs@sdu.edu.cn',
    phone: '13800138005',
    office: '人事处301室',
    joinDate: '2019-09-01'
  },
  { 
    id: 6, 
    username: 'yjs', 
    password: '123456', 
    role: 'yjs', 
    roleName: '研究生教师', 
    avatar: '🎓',
    name: '刘研究生',
    college: '研究生管理办公室',
    email: 'yjs@sdu.edu.cn',
    phone: '13800138006',
    office: '研究生院105室',
    joinDate: '2021-03-01'
  },
  { 
    id: 7, 
    username: 'student', 
    password: '123456', 
    role: 'student', 
    roleName: '学生', 
    avatar: '🎒',
    name: '孙同学',
    college: '政治学与公共管理学院',
    email: 'student@sdu.edu.cn',
    phone: '13800138007',
    studentId: '2022010101',
    major: '行政管理',
    grade: '2022级',
    advisor: '张明辉教授',
    dormitory: '学生公寓A栋302',
    enrollmentDate: '2022-09-01',
    gpa: '3.85',
    credits: '68',
    coursesCompleted: '24门'
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
  staff: { roles: ['dean', 'admin', 'jw', 'ky', 'rs', 'yjs', 'student'], level: 'full' },
  projects: { roles: ['dean', 'admin', 'ky'], level: 'full', else: '--' },
  funding: { roles: ['dean', 'admin', 'ky'], level: 'full', else: '--' },
  budget: { roles: ['dean', 'admin'], level: 'full', else: 'hidden' }
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('userInfo') || 'null'))

  const isLoggedIn = computed(() => !!token.value && !!userInfo.value)

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

    const mockToken = `mock_token_${Date.now()}_${user.id}`
    token.value = mockToken
    userInfo.value = {
      id: user.id,
      username: user.username,
      role: user.role,
      roleName: user.roleName,
      avatar: user.avatar,
      name: user.name,
      college: user.college,
      email: user.email,
      phone: user.phone,
      office: user.office,
      joinDate: user.joinDate,
      studentId: user.studentId,
      major: user.major,
      grade: user.grade,
      advisor: user.advisor,
      dormitory: user.dormitory,
      enrollmentDate: user.enrollmentDate,
      gpa: user.gpa,
      credits: user.credits,
      coursesCompleted: user.coursesCompleted
    }

    localStorage.setItem('token', mockToken)
    localStorage.setItem('userInfo', JSON.stringify(userInfo.value))

    return userInfo.value
  }

  const logout = () => {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
  }

  const checkAuth = () => {
    const savedToken = localStorage.getItem('token')
    const savedUserInfo = localStorage.getItem('userInfo')
    
    if (savedToken && savedUserInfo) {
      token.value = savedToken
      userInfo.value = JSON.parse(savedUserInfo)
    }
  }

  const updateUserInfo = (updated) => {
    userInfo.value = updated
    localStorage.setItem('userInfo', JSON.stringify(updated))
  }

  return {
    token,
    userInfo,
    isLoggedIn,
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
