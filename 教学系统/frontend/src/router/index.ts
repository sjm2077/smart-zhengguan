import { createRouter, createWebHistory } from 'vue-router'
import { getAccessToken } from '@/api/index'
import {
  canAccessRole,
  getCurrentRole,
  getRoleHomePath,
  type UserRole,
} from '@/utils/roleAccess'

import MainLayout from '../layout/MainLayout.vue'
import Dashboard from '../views/dashboard/Dashboard.vue'
import Login from '../views/Login.vue'
import CourseManage from '../views/course/CourseManage.vue'
import GradeManage from '../views/grade/GradeManage.vue'
import TeacherManage from '../views/teacher/TeacherManage.vue'
import StudentManage from '../views/student/StudentManage.vue'
import ExamManage from '../views/exam/ExamManage.vue'
import TeachingAnalysis from '../views/analysis/TeachingAnalysis.vue'
import WarningCenter from '../views/dashboard/WarningCenter.vue'
import TeacherWorkbench from '../views/teacher/TeacherWorkbench.vue'
import TeacherCourses from '../views/teacher/TeacherCourses.vue'
import TeacherClasses from '../views/teacher/TeacherClasses.vue'
import TeacherGrades from '../views/teacher/TeacherGrades.vue'
import StudentHome from '../views/student/StudentHome.vue'

const MANAGEMENT_ROLES: UserRole[] = ['admin', 'academic']

import AIWarningCenter from '../views/ai/AIWarningCenter.vue'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: Login,
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'dashboard',
        component: Dashboard,
        meta: { roles: MANAGEMENT_ROLES },
      },
      {
        path: 'dashboard',
        redirect: '/',
      },
      {
        path: 'teacher-workbench',
        name: 'teacher-workbench',
        component: TeacherWorkbench,
        meta: { roles: ['teacher'] as UserRole[] },
      },
      {
        path: 'teacher-courses',
        name: 'teacher-courses',
        component: TeacherCourses,
        meta: { roles: ['teacher'] as UserRole[] },
      },
      {
        path: 'teacher-classes',
        name: 'teacher-classes',
        component: TeacherClasses,
        meta: { roles: ['teacher'] as UserRole[] },
      },
      {
        path: 'teacher-grades',
        name: 'teacher-grades',
        component: TeacherGrades,
        meta: { roles: ['teacher'] as UserRole[] },
      },
      {
        path: 'student-home',
        name: 'student-home',
        component: StudentHome,
        meta: { roles: ['student'] as UserRole[] },
      },
      {
        path: 'course',
        name: 'course',
        component: CourseManage,
        meta: { roles: MANAGEMENT_ROLES },
      },
      {
        path: 'grade',
        name: 'grade',
        component: GradeManage,
        meta: { roles: MANAGEMENT_ROLES },
      },
      {
        path: 'teacher',
        name: 'teacher',
        component: TeacherManage,
        meta: { roles: MANAGEMENT_ROLES },
      },
      {
        path: 'student',
        name: 'student',
        component: StudentManage,
        meta: { roles: MANAGEMENT_ROLES },
      },
      {
        path: 'exam',
        name: 'exam',
        component: ExamManage,
        meta: { roles: MANAGEMENT_ROLES },
      },
      {
        path: 'analysis',
        name: 'analysis',
        component: TeachingAnalysis,
        meta: { roles: MANAGEMENT_ROLES },
      },

      {
        path: 'ai-warning',
        name: 'ai-warning',
        component: AIWarningCenter,
        meta: { roles: MANAGEMENT_ROLES },
      },
      {
        path: 'dashboard/warning',
        name: 'warning',
        component: WarningCenter,
        meta: { roles: MANAGEMENT_ROLES },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const token = getAccessToken()
  const role = getCurrentRole()

  if (to.meta.requiresAuth !== false && !token) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.name === 'login' && token && role) {
    return getRoleHomePath(role)
  }

  if (!token) {
    return true
  }

  // A token without a recognized role must not gain access to role-specific pages.
  if (!role) {
    // 已在登录页时允许停留，避免未识别角色产生重定向循环。
    if (to.name === 'login') return true
    return { name: 'login' }
  }

  const roleRules = to.matched
    .map((record) => record.meta.roles as UserRole[] | undefined)
    .filter((roles): roles is UserRole[] => Array.isArray(roles))

  if (!roleRules.every((roles) => canAccessRole(roles, role))) {
    return getRoleHomePath(role)
  }

  return true
})

export default router