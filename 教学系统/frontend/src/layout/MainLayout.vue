<template>
  <div class="main-layout">
    <!-- 深蓝色侧边栏 -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-brand">
        <div class="brand-logo">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 10v6M2 10l10-5 10 5-10 5z"/>
            <path d="M6 12v5c0 1.1 2.7 2 6 2s6-.9 6-2v-5"/>
          </svg>
        </div>
        <span class="brand-text" v-show="!sidebarCollapsed">智慧教学平台</span>
      </div>

      <nav class="sidebar-nav">
        <template v-for="item in visibleMenuItems" :key="item.path">
          <!-- 有子菜单的项 -->
          <div v-if="item.children" class="nav-group" :class="{ open: openMenus.has(item.path) }">
            <div
              class="nav-item nav-item--parent"
              :class="{ active: isGroupActive(item) }"
              @click="router.push(item.path)"
            >
              <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path :d="item.icon" />
              </svg>
              <span class="nav-label" v-show="!sidebarCollapsed">{{ item.label }}</span>
              <svg
                v-show="!sidebarCollapsed"
                class="nav-arrow"
                role="button"
                tabindex="0"
                :aria-expanded="openMenus.has(item.path)"
                @click.stop="toggleSubMenu(item.path)"
                @keydown.enter.stop.prevent="toggleSubMenu(item.path)"
                @keydown.space.stop.prevent="toggleSubMenu(item.path)"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </div>
            <div class="nav-sub-list" v-show="!sidebarCollapsed && openMenus.has(item.path)">
              <router-link
                v-for="child in item.children"
                :key="child.path"
                :to="child.path"
                class="nav-item nav-item--sub"
                :class="{ active: isActive(child.path) }"
              >
                <span class="nav-sub-dot"></span>
                <span class="nav-label">{{ child.label }}</span>
              </router-link>
            </div>
          </div>
          <!-- 无子菜单的普通项 -->
          <router-link
            v-else
            :to="item.path"
            class="nav-item"
            :class="{ active: isActive(item.path) }"
          >
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path :d="item.icon" />
            </svg>
            <span class="nav-label" v-show="!sidebarCollapsed">{{ item.label }}</span>
          </router-link>
        </template>
      </nav>

      <div class="sidebar-footer" v-show="!sidebarCollapsed">
        <div class="sidebar-collapse-btn" @click="toggleSidebar">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <line x1="3" y1="12" x2="21" y2="12"/>
            <polyline points="10 5 3 12 10 19"/>
          </svg>
          <span>收起菜单</span>
        </div>
      </div>
    </aside>

    <!-- 右侧主体区域 -->
    <div class="main-area" :class="{ expanded: sidebarCollapsed }">
      <!-- 顶部导航栏 — 高校智慧校园平台风格 -->
      <header class="topbar">
        <div class="topbar-left">
          <button class="topbar-toggle" @click="toggleSidebar">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <line x1="3" y1="12" x2="21" y2="12"/>
              <line x1="3" y1="6" x2="21" y2="6"/>
              <line x1="3" y1="18" x2="21" y2="18"/>
            </svg>
          </button>
          <div class="topbar-brand-text">
            <span class="brand-name-cn">山东大学政治学与公共管理学院</span>
            <span class="brand-name-en">School of Political Science and Public Administration, SDU</span>
          </div>
        </div>
        <div class="topbar-right">
          <div class="topbar-search">
            <svg
              class="search-icon search-icon--clickable"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
              @click="handleSearch"
            >
              <circle cx="11" cy="11" r="8"/>
              <line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            <input
              ref="searchInputRef"
              v-model="searchKeyword"
              type="text"
              placeholder="搜索课程、教师、学生…"
              class="search-input"
              @keyup.enter="handleSearch"
              @keydown="onSearchKeydown"
              @focus="searchKeyword.trim() && getSearchSuggestions(searchKeyword).length > 0 && (showSuggestions = true)"
            />
            <!-- 搜索建议下拉 -->
            <div v-if="showSuggestions && searchSuggestions.length > 0" class="search-suggestions">
              <div
                v-for="(item, index) in searchSuggestions"
                :key="item.moduleId || item.path + item.label"
                class="suggestion-item"
                :class="{ highlighted: index === selectedSuggestionIndex }"
                @mousedown.prevent="selectSuggestion(item)"
              >
                <svg class="suggestion-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="11" cy="11" r="8"/>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
                <div class="suggestion-text">
                  <span class="suggestion-label">{{ item.label }}</span>
                  <span class="suggestion-path">{{ item.moduleId ? '页面内模块' : '页面跳转' }} · {{ routeLabel(item.path) }}</span>
                </div>
              </div>
            </div>
          </div>
          <button class="topbar-icon-btn" title="消息通知">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
              <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
            </svg>
            <span class="notify-dot"></span>
          </button>
          <div class="topbar-user-container">
            <div
              class="topbar-user"
              role="button"
              tabindex="0"
              :aria-expanded="userMenuOpen"
              aria-haspopup="menu"
              @click.stop="toggleUserMenu"
              @keydown.enter.prevent="toggleUserMenu"
              @keydown.space.prevent="toggleUserMenu"
            >
              <div class="user-avatar">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
              </div>
              <div class="user-info">
                <span class="user-name">{{ displayUserName }}</span>
                <span class="user-role">{{ displayUserRole }}</span>
              </div>
            </div>

            <div
              v-if="userMenuOpen"
              class="user-dropdown"
              role="menu"
              @click.stop
            >
              <div class="user-dropdown-header">
                <span class="user-dropdown-name">{{ displayUserName }}</span>
                <span class="user-dropdown-username">
                  账号：{{ currentUser?.username || '当前账号' }}
                </span>
              </div>

              <button
                type="button"
                class="user-dropdown-action"
                role="menuitem"
                @click="handleLogout"
              >
                退出登录 / 切换账号
              </button>
            </div>
          </div>
        </div>
      </header>

      <!-- 页面内容区 -->
      <main class="page-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { clearTokens } from '@/api/index'
import { findSearchMatch, getSearchSuggestions, type SearchModuleEntry } from '@/config/searchConfig'

interface MenuItem {
  path: string
  label: string
  icon: string
  children?: { path: string; label: string }[]
}

const route = useRoute()
const router = useRouter()
const sidebarCollapsed = ref(false)
const openMenus = ref(new Set<string>(['/dashboard']))
const searchKeyword = ref('')
const searchSuggestions = ref<SearchModuleEntry[]>([])
const showSuggestions = ref(false)
const selectedSuggestionIndex = ref(-1)
const searchInputRef = ref<HTMLInputElement | null>(null)


interface StoredUser {
  username?: string
  name?: string
  first_name?: string
  role?: string
}

function readStoredUser(): StoredUser | null {
  const raw = localStorage.getItem('user_info')

  if (!raw) {
    return null
  }

  try {
    return JSON.parse(raw) as StoredUser
  } catch {
    return null
  }
}

const currentUser = ref<StoredUser | null>(readStoredUser())
const userMenuOpen = ref(false)

const displayUserName = computed(() => {
  const role = currentUser.value?.role?.toLowerCase()

  if (role === 'admin') {
    return '系统管理员'
  }

  return (
    currentUser.value?.name ||
    currentUser.value?.first_name ||
    currentUser.value?.username ||
    '当前用户'
  )
})

const displayUserRole = computed(() => {
  const role = currentUser.value?.role?.toLowerCase()

  if (role === 'admin') return '平台管理'
  if (role === 'academic') return '教务管理'
  if (role === 'teacher') return '任课教师'
  if (role === 'student') return '学生用户'
  if (role === 'viewer') return '只读用户'

  return '账号信息'
})

function toggleUserMenu() {
  // 每次打开菜单时重新读取当前登录账号信息
  currentUser.value = readStoredUser()
  userMenuOpen.value = !userMenuOpen.value
}

function handleLogout() {
  userMenuOpen.value = false

  // 清除当前登录令牌和账号信息，再返回登录页
  clearTokens()
  localStorage.removeItem('user_info')

  router.replace({ name: 'login' })
}

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

const toggleSubMenu = (path: string) => {
  if (openMenus.value.has(path)) {
    openMenus.value.delete(path)
  } else {
    openMenus.value.add(path)
  }
  // 触发响应式更新
  openMenus.value = new Set(openMenus.value)
}

const isActive = (path: string) => {
  if (path === '/dashboard') {
    return route.path === '/' || route.path === '/dashboard'
  }
  return route.path.startsWith(path)
}

const isGroupActive = (item: MenuItem) => {
  if (!item.children) return false

  if (item.path === '/dashboard') {
    return route.path === '/' || route.path === '/dashboard'
  }

  return route.path === item.path
}

// 监听输入更新搜索建议
watch(searchKeyword, (val) => {
  if (val.trim()) {
    searchSuggestions.value = getSearchSuggestions(val)
    showSuggestions.value = searchSuggestions.value.length > 0
    selectedSuggestionIndex.value = -1
  } else {
    searchSuggestions.value = []
    showSuggestions.value = false
    selectedSuggestionIndex.value = -1
  }
})

// 导航到目标模块并高亮滚动
function navigateToModule(match: SearchModuleEntry | null) {
  if (!match) return

  const currentPath = route.path === '/dashboard' || route.path === '/' ? '/' : route.path

  if (currentPath === match.path) {
    // 已在目标页面，直接滚动到模块
    scrollToModule(match.moduleId)
  } else {
    // 需要跳转路由，通过 sessionStorage 传递目标模块 ID
    if (match.moduleId) {
      sessionStorage.setItem('searchScrollTarget', match.moduleId)
    }
    router.push(match.path)
  }
}

// 滚动到目标模块
function scrollToModule(moduleId?: string) {
  if (!moduleId) return
  // 等待 DOM 渲染完成后滚动
  setTimeout(() => {
    const el = document.getElementById(moduleId)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' })
      // 高亮动画
      el.classList.add('search-highlight')
      setTimeout(() => {
        el.classList.remove('search-highlight')
      }, 2500)
    }
  }, 300)
}

// 路由路径 → 显示名称映射
function routeLabel(path: string): string {
  const item = menuItems.find(m => m.path === path)
  return item?.label || path
}

// 点击搜索建议项
function selectSuggestion(entry: SearchModuleEntry) {
  showSuggestions.value = false
  searchKeyword.value = entry.label
  navigateToModule(entry)
  searchKeyword.value = ''
}

// 键盘导航搜索建议
function onSearchKeydown(e: KeyboardEvent) {
  if (!showSuggestions.value) return
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    selectedSuggestionIndex.value = Math.min(
      selectedSuggestionIndex.value + 1,
      searchSuggestions.value.length - 1
    )
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    selectedSuggestionIndex.value = Math.max(selectedSuggestionIndex.value - 1, 0)
  }
}

const handleSearch = () => {
  const keyword = searchKeyword.value.trim()
  if (!keyword) return

  // 优先使用精确匹配
  const match = findSearchMatch(keyword)
  if (match) {
    navigateToModule(match)
    searchKeyword.value = ''
    showSuggestions.value = false
    return
  }

  // 否则尝试建议中的第一条
  if (searchSuggestions.value.length > 0) {
    const firstSuggestion = searchSuggestions.value[0]

    if (firstSuggestion) {
      selectSuggestion(firstSuggestion)
    }
    return
  }

  // 无匹配时给出提示
  alert('未找到匹配的内容，请尝试搜索：学生地区来源、骨干教师画像、GPA分布、考试日历、教学热点词云等')
}

// 点击外部关闭搜索建议
function onDocumentClick(e: MouseEvent) {
  const target = e.target as HTMLElement

  // 点击搜索区域以外时关闭搜索建议
  if (!target.closest('.topbar-search')) {
    showSuggestions.value = false
  }

  // 点击用户区域以外时关闭账号菜单
  if (!target.closest('.topbar-user-container')) {
    userMenuOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', onDocumentClick)
  // 如果从搜索跳转过来且携带了模块 ID，滚动到目标模块
  const scrollTarget = sessionStorage.getItem('searchScrollTarget')
  if (scrollTarget) {
    sessionStorage.removeItem('searchScrollTarget')
    scrollToModule(scrollTarget)
  }
})

onUnmounted(() => {
  document.removeEventListener('click', onDocumentClick)
})

const menuItems: MenuItem[] = [
  {
    path: '/dashboard',
    label: '数据总览',
    icon: 'M3 3h7v7H3V3z M14 3h7v7h-7V3z M3 14h7v7H3v-7z M14 14h7v7h-7v-7z',
    children: [
      { path: '/dashboard/warning', label: '教学预警' },
    ],
  },
  { path: '/course', label: '课程管理', icon: 'M4 19.5A2.5 2.5 0 0 1 6.5 17H20 M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z' },
  { path: '/teacher', label: '教师管理', icon: 'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2 M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M23 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75' },
  { path: '/student', label: '学生管理', icon: 'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2 M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M23 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75' },
  { path: '/exam', label: '考试管理', icon: 'M9 11l3 3L22 4 M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11' },
  { path: '/grade', label: '成绩管理', icon: 'M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2 M9 5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v0a2 2 0 0 1-2 2h-2a2 2 0 0 1-2-2z M9 12h6 M9 16h6' },
  { path: '/analysis', label: '教学分析', icon: 'M12 20v-6 M6 20V10 M18 20V4' },
  { path: '/ai-warning', label: '智能分析预警', icon: 'M12 3L2 20h20L12 3z M12 9v4 M12 17h.01' },
]

const visibleMenuItems = computed<MenuItem[]>(() => {
  const role = String(currentUser.value?.role ?? '').trim().toLowerCase()
  const findItem = (path: string, label: string): MenuItem => {
    const source = menuItems.find((item) => item.path === path)
    return source
      ? { ...source, path, label, children: undefined }
      : { path, label, icon: 'M4 4h16v16H4z' }
  }

  if (role === 'student') {
    return [
      findItem('/student-home', '个人学习中心'),
    ]
  }

  if (role === 'teacher') {
    // 教师端使用独立导航，不混入管理员/教务管理菜单。
    return [
      {
        path: '/teacher-workbench',
        label: '教师工作台',
        icon: 'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',
      },
      {
        path: '/teacher-courses',
        label: '我的课程',
        icon: 'M4 19.5A2.5 2.5 0 0 1 6.5 17H20 M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z',
      },
      {
        path: '/teacher-classes',
        label: '教学班级',
        icon: 'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2 M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M20 8v6 M23 11h-6',
      },
      {
        path: '/teacher-grades',
        label: '成绩管理',
        icon: 'M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2 M9 5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2 M9 12h6 M9 16h6',
      },
    ]
  }

  // 管理员与教务管理角色保留原有完整管理菜单。
  if (role === 'admin' || role === 'academic') {
    return menuItems
  }

  // 未识别角色不显示管理菜单；路由守卫也会阻止其进入管理页面。
  return []
})
</script>

<style scoped>
/* ============================================================
   主布局 — 深蓝色侧边栏 + 深蓝色顶栏
   高校信息化平台风格
   ============================================================ */

.main-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: var(--bg-page);
}

/* ----- 侧边栏 ----- */
.sidebar {
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
  background: var(--bg-sidebar);
  display: flex;
  flex-direction: column;
  transition: width 0.25s ease, min-width 0.25s ease;
  overflow: hidden;
  z-index: 100;
}
.sidebar.collapsed {
  width: 64px;
  min-width: 64px;
}

/* 侧边栏品牌区 */
.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 18px 20px;
  height: var(--topbar-height);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
}
.brand-logo {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  background: rgba(59, 130, 246, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.brand-logo svg {
  width: 18px;
  height: 18px;
  color: #60A5FA;
}
.brand-text {
  font-size: var(--font-size-base);
  font-weight: 700;
  color: #FFFFFF;
  white-space: nowrap;
  letter-spacing: 1px;
}

/* 导航 */
.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  padding: 12px 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 20px;
  color: #94A3B8;
  text-decoration: none;
  font-size: var(--font-size-md);
  font-weight: 500;
  transition: all 0.15s;
  position: relative;
  white-space: nowrap;
}
.nav-item:hover {
  color: #E2E8F0;
  background: rgba(255, 255, 255, 0.04);
}
.nav-item.active {
  color: #FFFFFF;
  background: rgba(30, 58, 138, 0.5);
}
.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: #60A5FA;
  border-radius: 0 3px 3px 0;
}
.nav-icon {
  width: 17px;
  height: 17px;
  flex-shrink: 0;
}
.nav-label {
  flex: 1;
}

/* 导航分组（可展开子菜单） */
.nav-group {
  display: flex;
  flex-direction: column;
}
.nav-item--parent {
  cursor: pointer;
  user-select: none;
}
.nav-arrow {
  cursor: pointer;
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  transition: transform 0.2s ease;
  color: #64748B;
}
.nav-group.open .nav-arrow {
  transform: rotate(180deg);
}
.nav-sub-list {
  overflow: hidden;
}
.nav-item--sub {
  padding-left: 52px !important;
  font-size: 13px;
}
.nav-sub-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #475569;
  flex-shrink: 0;
  transition: background 0.15s;
}
.nav-item--sub:hover .nav-sub-dot,
.nav-item--sub.active .nav-sub-dot {
  background: #60A5FA;
}

/* 侧边栏底部 */
.sidebar-footer {
  flex-shrink: 0;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  padding: 12px 20px;
}
.sidebar-collapse-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #64748B;
  font-size: var(--font-size-sm);
  cursor: pointer;
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  transition: all 0.15s;
  white-space: nowrap;
}
.sidebar-collapse-btn svg {
  width: 15px;
  height: 15px;
}
.sidebar-collapse-btn:hover {
  color: #94A3B8;
  background: rgba(255, 255, 255, 0.04);
}

/* ----- 右侧主体 ----- */
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

/* ----- 顶栏 — 高校智慧校园平台风格 ----- */
.topbar {
  height: var(--topbar-height);
  min-height: var(--topbar-height);
  background: #0b2a5b;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
  position: relative;
  z-index: 50;
}
/* 左侧区域 */
.topbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 0 0 auto;
}
.topbar-toggle {
  width: 34px;
  height: 34px;
  border: none;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}
.topbar-toggle svg {
  width: 16px;
  height: 16px;
}
.topbar-toggle:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #FFFFFF;
}
/* 品牌文字区域（左侧） */
.topbar-brand-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.brand-name-cn {
  font-size: 16px;
  font-weight: 700;
  color: #FFFFFF;
  letter-spacing: 2px;
  white-space: nowrap;
  line-height: 1.3;
}
.brand-name-en {
  font-size: 11px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.6);
  white-space: nowrap;
  letter-spacing: 0.5px;
  line-height: 1.3;
}
/* 右侧区域 */
.topbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 0 0 auto;
}
/* 搜索框 */
.topbar-search {
  position: relative;
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  padding: 0 16px;
  height: 36px;
  gap: 8px;
  transition: all 0.25s;
  border: 1px solid rgba(255, 255, 255, 0.06);
}
.topbar-search:focus-within {
  background: rgba(255, 255, 255, 0.14);
  border-color: rgba(255, 255, 255, 0.25);
  box-shadow: 0 0 0 3px rgba(22, 119, 255, 0.15);
}
.search-icon {
  width: 15px;
  height: 15px;
  color: rgba(255, 255, 255, 0.5);
  flex-shrink: 0;
}
.search-icon--clickable {
  cursor: pointer;
  transition: color 0.15s;
}
.search-icon--clickable:hover {
  color: rgba(255, 255, 255, 0.85);
}
.search-input {
  border: none;
  background: transparent;
  outline: none;
  color: #FFFFFF;
  font-size: 13px;
  width: 200px;
  line-height: 1;
}
.search-input::placeholder {
  color: rgba(255, 255, 255, 0.4);
}

/* 搜索建议下拉 */
.search-suggestions {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 8px;
  background: #FFFFFF;
  border-radius: 12px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15), 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  z-index: 200;
  max-height: 360px;
  overflow-y: auto;
}

.suggestion-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 16px;
  cursor: pointer;
  transition: background 0.12s;
  border-bottom: 1px solid #F1F5F9;
}

.suggestion-item:last-child {
  border-bottom: none;
}

.suggestion-item:hover,
.suggestion-item.highlighted {
  background: #EFF6FF;
}

.suggestion-icon {
  width: 15px;
  height: 15px;
  color: #94A3B8;
  flex-shrink: 0;
}

.suggestion-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.suggestion-label {
  font-size: 14px;
  color: #1E293B;
  font-weight: 500;
}

.suggestion-path {
  font-size: 11px;
  color: #94A3B8;
}

.help-text-small {
  font-size: 13px;
  color: #64748B;
  padding: 12px 16px;
  text-align: center;
  border-top: 1px solid #F1F5F9;
  background: #FAFBFC;
  line-height: 1.4;
}

/* 图标按钮 */
.topbar-icon-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}
.topbar-icon-btn svg {
  width: 17px;
  height: 17px;
}
.topbar-icon-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #FFFFFF;
}
.notify-dot {
  position: absolute;
  top: 6px;
  right: 8px;
  width: 7px;
  height: 7px;
  background: #EF4444;
  border-radius: 50%;
  border: 2px solid #0b2a5b;
}
/* 用户区域 */
.topbar-user {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: 4px;
  cursor: pointer;
  padding: 4px 12px 4px 4px;
  border-radius: 8px;
  transition: all 0.2s;
}
.topbar-user:hover {
  background: rgba(255, 255, 255, 0.06);
}
.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.user-avatar svg {
  width: 17px;
  height: 17px;
  color: rgba(255, 255, 255, 0.7);
}
.user-info {
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.user-name {
  color: #FFFFFF;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.3;
}
.user-role {
  color: rgba(255, 255, 255, 0.45);
  font-size: 11px;
  line-height: 1.3;
}

/* 用户区域与账号下拉菜单 */
.topbar-user-container {
  position: relative;
}

.topbar-user:focus-visible {
  outline: 2px solid #ffffff;
  outline-offset: 2px;
}

.user-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 220px;
  padding: 8px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.16);
  z-index: 300;
}

.user-dropdown-header {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px 12px;
  border-bottom: 1px solid #e2e8f0;
}

.user-dropdown-name {
  color: #1e293b;
  font-size: 14px;
  font-weight: 600;
}

.user-dropdown-username {
  color: #64748b;
  font-size: 12px;
  overflow-wrap: anywhere;
}

.user-dropdown-action {
  display: block;
  width: 100%;
  margin-top: 6px;
  padding: 10px 12px;
  border: none;
  border-radius: 6px;
  background: #ffffff;
  color: #334155;
  font-size: 13px;
  text-align: left;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}

.user-dropdown-action:hover {
  background: #eff6ff;
  color: #1d4ed8;
}

/* ----- 页面内容区 ----- */
.page-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-lg);
  background: var(--bg-page);
}
</style>
<!-- 引入科研系统统一视觉主题 -->
<style src="./teaching-research-theme.css"></style>