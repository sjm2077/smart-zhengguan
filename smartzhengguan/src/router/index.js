import { createRouter, createWebHashHistory } from 'vue-router'
import Home from '../views/Home.vue'
import AcademicStatus from '../views/AcademicStatus.vue'
import Training from '../views/Training.vue'
import Degree from '../views/Degree.vue'
import Scholarship from '../views/Scholarship.vue'
import Admission from '../views/Admission.vue'
import Employment from '../views/Employment.vue'
import QueryResults from '../views/QueryResults.vue'
import AcademicChange from '../views/AcademicChange.vue'
import TrainingCourse from '../views/TrainingCourse.vue'
import DegreeDefense from '../views/DegreeDefense.vue'
import IntelligentPrediction from '../views/IntelligentPrediction.vue'
import SystemSettings from '../views/SystemSettings.vue'
import PersonalCenter from '../views/PersonalCenter.vue'
import ChangePassword from '../views/ChangePassword.vue'
import Login from '../views/Login.vue'
import SearchResults from '../views/SearchResults.vue'
import DataManagement from '../views/DataManagement.vue'

const routes = [
  { path: '/', redirect: '/home' },
  { path: '/home', component: Home, meta: { requiresAuth: true } },
  { path: '/admission', component: Admission, meta: { requiresAuth: true } },
  { path: '/academic-status', component: AcademicStatus, meta: { requiresAuth: true } },
  { path: '/academic-change', component: AcademicChange, meta: { requiresAuth: true } },
  { path: '/training', component: Training, meta: { requiresAuth: true } },
  { path: '/training-course', component: TrainingCourse, meta: { requiresAuth: true } },
  { path: '/degree', component: Degree, meta: { requiresAuth: true } },
  { path: '/degree-defense', component: DegreeDefense, meta: { requiresAuth: true } },
  { path: '/intelligent-prediction', component: IntelligentPrediction, meta: { requiresAuth: true } },
  { path: '/scholarship', component: Scholarship, meta: { requiresAuth: true } },
  { path: '/employment', component: Employment, meta: { requiresAuth: true } },
  { path: '/query-results', component: QueryResults, meta: { requiresAuth: true } },
  { path: '/search', component: SearchResults, meta: { requiresAuth: true } },
  { path: '/data-management', component: DataManagement, meta: { requiresAuth: true } },
  { path: '/system', component: SystemSettings, meta: { requiresAuth: true } },
  { path: '/personal', component: PersonalCenter, meta: { requiresAuth: true } },
  { path: '/change-pwd', component: ChangePassword, meta: { requiresAuth: true } },
  { path: '/login', component: Login, meta: { public: true, hideLayout: true } },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to) => {
  const token = localStorage.getItem('token')

  if (to.path === '/login' && token) {
    return '/home'
  }

  if (to.meta?.requiresAuth && !token) {
    return {
      path: '/login',
      query: { redirect: to.fullPath },
    }
  }

  return true
})

export default router
