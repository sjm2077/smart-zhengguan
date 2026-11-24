export type UserRole = 'admin' | 'academic' | 'teacher' | 'student'

export interface StoredUser {
  id?: number
  username?: string
  name?: string
  role?: string
  avatar?: string | null
  [key: string]: unknown
}

const ROLE_ALIASES: Record<string, UserRole> = {
  admin: 'admin',
  administrator: 'admin',
  system_admin: 'admin',
  sysadmin: 'admin',
  管理员: 'admin',
  系统管理员: 'admin',
  academic: 'academic',
  academic_admin: 'academic',
  教务: 'academic',
  教务管理人员: 'academic',
  teacher: 'teacher',
  faculty: 'teacher',
  教师: 'teacher',
  student: 'student',
  学生: 'student',
}

export function normalizeRole(role: unknown): UserRole | null {
  const key = String(role ?? '').trim().toLowerCase()
  return ROLE_ALIASES[key] ?? null
}

export function getStoredUser(): StoredUser | null {
  try {
    const raw = localStorage.getItem('user_info')
    return raw ? (JSON.parse(raw) as StoredUser) : null
  } catch {
    return null
  }
}

export function getCurrentRole(): UserRole | null {
  return normalizeRole(getStoredUser()?.role)
}

export function getRoleHomePath(role: UserRole | null): string {
  if (role === 'teacher') return '/teacher-workbench'
  if (role === 'student') return '/student-home'
  if (role === 'admin' || role === 'academic') return '/'
  return '/login'
}

export function canAccessRole(allowedRoles: unknown, role: UserRole): boolean {
  return !Array.isArray(allowedRoles) || allowedRoles.length === 0 || allowedRoles.includes(role)
}