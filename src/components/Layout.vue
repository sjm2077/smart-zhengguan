<template>
  <div class="layout">
    <div class="main-container">
      <Header @refresh="handleRefresh" />
      <main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" :key="route.path" />
          </transition>
        </router-view>
      </main>
      <footer class="bottom-nav-container">
        <nav class="bottom-nav">
          <button 
            v-for="nav in navItems" 
            :key="nav.path"
            class="nav-item"
            :class="{ active: currentPath === nav.path, disabled: !nav.visible }"
            @click="nav.visible && navigateTo(nav.path)"
            :disabled="!nav.visible"
          >
            <span class="nav-icon">{{ nav.icon }}</span>
            <span class="nav-label">{{ nav.label }}</span>
          </button>
        </nav>
      </footer>
      <AIAssistant :real-data="aiData" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import Header from './Header.vue'
import AIAssistant from './AIAssistant.vue'
import { useAuthStore } from '../stores/auth'
import { useDashboardStore } from '../stores/dashboard'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const dashboardStore = useDashboardStore()

const aiData = computed(() => ({
  students: dashboardStore.students,
  staff: dashboardStore.staff,
  projects: dashboardStore.projects,
  funding: dashboardStore.funding,
  budget: dashboardStore.budget,
  maleRatio: dashboardStore.maleRatio,
  femaleRatio: dashboardStore.femaleRatio
}))

const currentPath = computed(() => route.path)

const allNavItems = [
  { path: '/dashboard', label: '综合概览', icon: '🏠', roles: ['dean', 'admin', 'jw', 'ky', 'rs', 'yjs', 'student'] },
  { path: '/teaching', label: '教学管理', icon: '📚', roles: ['dean', 'admin', 'jw'] },
  { path: '/research', label: '科研管理', icon: '🔬', roles: ['dean', 'admin', 'ky'] },
  { path: '/hr', label: '人事系统', icon: '🏢', roles: ['dean', 'admin', 'rs'] },
  { path: '/graduate', label: '研究生管理', icon: '🎓', roles: ['dean', 'admin', 'yjs'] },
  { path: '/warning', label: '智能预警', icon: '⚠️', roles: ['dean', 'admin'] },
  { path: '/portrait', label: '师生画像', icon: '👤', roles: ['dean', 'admin', 'rs'] },
  { path: '/wordcloud', label: '词云分析', icon: '☁️', roles: ['dean', 'admin', 'ky'] },
  { path: '/treehole', label: '校园树洞', icon: '💭', roles: ['dean', 'admin', 'jw', 'ky', 'rs', 'yjs', 'student'] }
]

const navItems = computed(() => {
  const role = authStore.currentRole
  return allNavItems.map(item => ({
    ...item,
    visible: item.roles.includes(role)
  }))
})

const navigateTo = (path) => {
  router.push(path)
}

const handleRefresh = () => {
  window.location.reload()
}
</script>

<style scoped>
.layout {
  width: 100vw;
  height: 100vh;
  display: flex;
  overflow: hidden;
  background: #0a1f44;
}

.main-container {
  width: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.main-content {
  flex: 1;
  overflow: auto;
  padding: 20px;
  background: linear-gradient(135deg, #0a1f44 0%, #0d2a4d 50%, #050d1f 100%);
}

.bottom-nav-container {
  flex-shrink: 0;
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 70px;
  background: linear-gradient(180deg, rgba(10, 31, 68, 0.98) 0%, rgba(0, 20, 40, 0.95) 100%);
  border-top: 1px solid rgba(0, 212, 255, 0.25);
  backdrop-filter: blur(15px);
  z-index: 100;
  display: flex;
  align-items: center;
}

.bottom-nav-container::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.5), transparent);
}

.bottom-nav {
  display: flex;
  justify-content: center;
  gap: 30px;
  padding: 0 20px;
  width: 100%;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  padding: 8px 22px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  color: rgba(255, 255, 255, 0.65);
  min-width: 90px;
  position: relative;
}

.nav-item::before {
  content: '';
  position: absolute;
  top: -1px;
  left: 20%;
  right: 20%;
  height: 2px;
  background: transparent;
  border-radius: 1px;
  transition: all 0.3s ease;
}

.nav-item:hover:not(.disabled) {
  background: rgba(0, 212, 255, 0.08);
  border-color: rgba(0, 212, 255, 0.25);
  color: rgba(255, 255, 255, 0.9);
}

.nav-item.active {
  background: rgba(0, 212, 255, 0.12);
  border-color: rgba(0, 212, 255, 0.4);
  color: #00d4ff;
  box-shadow: 0 0 25px rgba(0, 212, 255, 0.15);
}

.nav-item.active::before {
  background: linear-gradient(90deg, transparent, #00d4ff, transparent);
}

.nav-item.disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.nav-icon {
  font-size: 26px;
  transition: transform 0.3s ease;
}

.nav-item:hover:not(.disabled) .nav-icon {
  transform: scale(1.1);
}

.nav-item.active .nav-icon {
  transform: scale(1.15);
  filter: drop-shadow(0 0 8px rgba(0, 212, 255, 0.8));
}

.nav-label {
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.5px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 1024px) {
  .bottom-nav {
    gap: 20px;
  }
  
  .nav-item {
    padding: 8px 15px;
    min-width: 60px;
  }
  
  .nav-icon {
    font-size: 20px;
  }
  
  .nav-label {
    font-size: 11px;
  }
}
</style>
