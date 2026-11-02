import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../stores/auth';

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { public: true }
  },
  {
    path: '/',
    component: () => import('../components/Layout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '综合概览', icon: '🏠' }
      },
      {
        path: 'teaching',
        name: 'Teaching',
        component: () => import('../components/IframeView.vue'),
        props: { src: 'http://localhost:5174/', title: '教学管理' },
        meta: { title: '教学管理', icon: '📚', roles: ['dean', 'admin', 'jw'] }
      },
      {
        path: 'research',
        name: 'Research',
        component: () => import('../components/IframeView.vue'),
        props: { src: 'http://localhost:8888/', title: '科研管理' },
        meta: { title: '科研管理', icon: '🔬', roles: ['dean', 'admin', 'ky'] }
      },
      {
        path: 'hr',
        name: 'HR',
        component: () => import('../components/IframeView.vue'),
        props: { src: 'http://localhost:3002/', title: '人事系统' },
        meta: { title: '人事系统', icon: '🏢', roles: ['dean', 'admin', 'rs'] }
      },
      {
        path: 'graduate',
        name: 'Graduate',
        component: () => import('../components/IframeView.vue'),
        props: { src: 'http://localhost:3003/', title: '研究生管理' },
        meta: { title: '研究生管理', icon: '🎓', roles: ['dean', 'admin', 'yjs'] }
      },
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: () => import('../views/Knowledge.vue'),
        meta: { title: '知识库问答', icon: '🧠', roles: ['dean', 'admin', 'jw', 'ky', 'rs', 'yjs', 'student'] }
      },
      {
        path: 'warning',
        name: 'Warning',
        component: () => import('../views/Warning.vue'),
        meta: { title: '智能预警', icon: '⚠️', roles: ['dean', 'admin'] }
      },
      {
        path: 'portrait',
        name: 'Portrait',
        component: () => import('../views/Portrait.vue'),
        meta: { title: '师生画像', icon: '👤', roles: ['dean', 'admin', 'rs'] }
      },
      {
        path: 'wordcloud',
        name: 'WordCloud',
        component: () => import('../views/WordCloud.vue'),
        meta: { title: '词云分析', icon: '☁️', roles: ['dean', 'admin', 'ky'] }
      },
      {
        path: 'treehole',
        name: 'TreeHole',
        component: () => import('../views/TreeHole.vue'),
        meta: { title: '校园树洞', icon: '💭' }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('../views/ProfilePage.vue'),
        meta: { title: '个人中心', icon: '👤' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/NotFound.vue')
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();
  authStore.checkAuth();

  if (to.meta.public) {
    // 已登录再访问登录页：直接进大屏
    if (authStore.isLoggedIn) {
      next('/dashboard');
      return;
    }
    next();
    return;
  }

  if (!authStore.isLoggedIn) {
    next({ path: '/login', query: to.fullPath !== '/dashboard' ? { redirect: to.fullPath } : {} });
    return;
  }

  if (to.meta.roles) {
    if (!to.meta.roles.includes(authStore.currentRole)) {
      next('/dashboard');
      return;
    }
  }

  next();
});

export default router;
