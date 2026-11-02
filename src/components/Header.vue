<template>
  <header class="header">
    <div class="header-row">
      <div class="header-left">
        <h1 class="system-title">山东大学政治学与公共管理学院</h1>
      </div>

      <div class="header-middle">
        <SearchBar />
        <div class="datetime-weather">
          <div class="datetime">
            <span class="date">{{ currentDate }}</span>
            <span class="time">{{ currentTime }}</span>
          </div>
          <div class="weather">
            <span class="weather-icon">☀️</span>
            <span class="weather-text">晴 17°C</span>
          </div>
        </div>
      </div>

      <div class="header-right">
        <button class="icon-btn" @click="toggleFullscreen" title="全屏">
          <span>{{ isFullscreen ? '⊠' : '⛶' }}</span>
        </button>
        
        <button class="icon-btn" :class="{ spinning: isRefreshing }" @click="refreshData" title="刷新">
          <span>↻</span>
        </button>

        <div class="notification" @click="toggleNotifications">
          <button class="icon-btn">
            <span>🔔</span>
          </button>
          <span v-if="unreadCount > 0" class="badge">{{ unreadCount }}</span>
          
          <div v-if="showNotifications" class="notification-panel">
            <div class="panel-header">
              <span class="panel-title">通知中心</span>
              <button v-if="unreadCount > 0" class="mark-read-btn" @click.stop="markAllRead">全部已读</button>
            </div>
            <div class="notification-list">
              <div 
                v-for="item in notifications" 
                :key="item.id" 
                class="notification-item"
                :class="{ unread: !item.read }"
                @click="handleNotificationClick(item)"
              >
                <div class="item-icon">{{ item.icon }}</div>
                <div class="item-content">
                  <div class="item-title">{{ item.title }}</div>
                  <div class="item-desc">{{ item.description }}</div>
                  <div class="item-time">{{ item.time }}</div>
                </div>
                <div v-if="!item.read" class="unread-dot"></div>
              </div>
            </div>
          </div>
        </div>

        <div class="user-menu">
          <button class="user-btn" @click="toggleUserMenu">
            <span class="avatar">{{ userInfo?.avatar }}</span>
            <span class="username">{{ userInfo?.roleName }}</span>
            <span class="arrow">▼</span>
          </button>
          
          <div v-if="showUserMenu" class="dropdown-menu">
            <button class="menu-item" @click="goToProfile">
              <span>👤</span> 个人中心
            </button>
            <div class="menu-divider"></div>
            <button class="menu-item logout" @click="handleLogout">
              <span>🚪</span> 退出登录
            </button>
          </div>
        </div>
      </div>
    </div>
    
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import SearchBar from './SearchBar.vue'

const emit = defineEmits(['refresh'])

const router = useRouter()
const authStore = useAuthStore()

const isFullscreen = ref(false)
const isRefreshing = ref(false)
const showUserMenu = ref(false)
const showNotifications = ref(false)
const currentDate = ref('')
const currentTime = ref('')

const notifications = ref([
  {
    id: 1,
    icon: '📊',
    title: '数据更新提醒',
    description: '2026年春季学期学生数据已更新完成，共1320名在校生。',
    time: '5分钟前',
    read: false,
    type: 'data'
  },
  {
    id: 2,
    icon: '📅',
    title: '会议通知',
    description: '明日上午9:00学院会议室召开教学工作研讨会，请相关教师准时参加。',
    time: '30分钟前',
    read: false,
    type: 'meeting'
  },
  {
    id: 3,
    icon: '⚠️',
    title: '智能预警提示',
    description: '检测到3名学生的学习预警状态已更新，请及时关注。',
    time: '1小时前',
    read: false,
    type: 'warning'
  },
  {
    id: 4,
    icon: '🎓',
    title: '研究生答辩安排',
    description: '2026届研究生论文答辩工作将于下周开始，请导师做好准备工作。',
    time: '2小时前',
    read: true,
    type: 'academic'
  },
  {
    id: 5,
    icon: '📝',
    title: '系统公告',
    description: '智慧政管问答系统已完成升级，新增3项智能分析功能。',
    time: '昨天',
    read: true,
    type: 'system'
  }
])

const unreadCount = computed(() => notifications.value.filter(n => !n.read).length)

const userInfo = computed(() => authStore.userInfo)



const updateDateTime = () => {
  const now = new Date()
  const weekdays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
  
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  const weekday = weekdays[now.getDay()]
  
  currentDate.value = `${year}年${month}月${day}日 ${weekday}`
  
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  const seconds = String(now.getSeconds()).padStart(2, '0')
  
  currentTime.value = `${hours}:${minutes}:${seconds}`
}

const toggleFullscreen = async () => {
  try {
    if (!document.fullscreenElement) {
      await document.documentElement.requestFullscreen()
      isFullscreen.value = true
    } else {
      await document.exitFullscreen()
      isFullscreen.value = false
    }
  } catch (error) {
    console.error('全屏切换失败:', error)
  }
}

const refreshData = () => {
  isRefreshing.value = true
  emit('refresh')
  setTimeout(() => {
    isRefreshing.value = false
  }, 1000)
}

const toggleNotifications = () => {
  showNotifications.value = !showNotifications.value
  if (showNotifications.value) {
    showUserMenu.value = false
  }
}

const markAllRead = () => {
  notifications.value.forEach(item => {
    item.read = true
  })
}

const handleNotificationClick = (item) => {
  item.read = true
  showNotifications.value = false
  console.log('点击通知:', item.title)
  
  // 根据通知类型跳转到对应页面
  const routeMap = {
    'warning': '/warning',
    'data': '/dashboard',
    'meeting': '/dashboard',
    'academic': '/graduate',
    'system': '/dashboard'
  }
  const path = routeMap[item.type]
  if (path) {
    router.push(path)
  }
}

const toggleUserMenu = () => {
  showUserMenu.value = !showUserMenu.value
  if (showUserMenu.value) {
    showNotifications.value = false
  }
}

const goToProfile = () => {
  showUserMenu.value = false
  router.push('/profile')
}

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

let dateTimer = null

onMounted(() => {
  updateDateTime()
  dateTimer = setInterval(updateDateTime, 1000)
  
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.user-menu')) {
      showUserMenu.value = false
    }
    if (!e.target.closest('.notification')) {
      showNotifications.value = false
    }
  })
})

onUnmounted(() => {
  if (dateTimer) {
    clearInterval(dateTimer)
  }
})
</script>

<style scoped>
.header {
  min-height: 100px;
  background: linear-gradient(180deg, rgba(0, 20, 40, 0.98) 0%, rgba(10, 31, 68, 0.95) 100%);
  border-bottom: 1px solid rgba(0, 212, 255, 0.2);
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 12px 30px;
  position: relative;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}



.menu-btn {
  width: 40px;
  height: 40px;
  background: rgba(0, 212, 255, 0.1);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 8px;
  color: #00d4ff;
  font-size: 20px;
  cursor: pointer;
  transition: all 0.3s;
}

.menu-btn:hover {
  background: rgba(0, 212, 255, 0.2);
}

.system-title {
  font-size: 22px;
  font-weight: 600;
  color: #fff;
  letter-spacing: 2px;
  background: linear-gradient(135deg, #00d4ff, #7b2cbf);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.header-search {
  width: 100%;
  max-width: 550px;
}

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.header-middle {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  gap: 30px;
  padding: 0 20px;
}

.datetime-weather {
  display: flex;
  align-items: center;
  gap: 20px;
}

.datetime {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.date {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
}

.time {
  font-size: 24px;
  font-family: 'Orbitron', monospace;
  color: #00d4ff;
  font-weight: 500;
}

.weather {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(0, 212, 255, 0.1);
  border-radius: 20px;
}

.weather-icon {
  font-size: 20px;
}

.weather-text {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.icon-btn {
  width: 40px;
  height: 40px;
  background: rgba(0, 212, 255, 0.1);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 8px;
  color: #fff;
  font-size: 18px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-btn:hover {
  background: rgba(0, 212, 255, 0.2);
  border-color: rgba(0, 212, 255, 0.5);
}

.icon-btn.spinning span {
  display: inline-block;
  animation: rotate 1s linear infinite;
}

.notification {
  position: relative;
}

.badge {
  position: absolute;
  top: -5px;
  right: -5px;
  width: 18px;
  height: 18px;
  background: #ff4d4f;
  border-radius: 50%;
  font-size: 11px;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

.user-menu {
  position: relative;
}

.user-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  background: rgba(0, 212, 255, 0.1);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 8px;
  color: #fff;
  cursor: pointer;
  transition: all 0.3s;
}

.user-btn:hover {
  background: rgba(0, 212, 255, 0.2);
}

.avatar {
  font-size: 20px;
}

.username {
  font-size: 14px;
}

.arrow {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.6);
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  width: 200px;
  background: rgba(10, 31, 68, 0.98);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 12px;
  padding: 15px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
  z-index: 1000;
}

.menu-section {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.menu-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  padding: 5px 10px;
  margin-bottom: 5px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}

.menu-item:hover {
  background: rgba(0, 212, 255, 0.1);
}

.menu-item.active {
  background: rgba(0, 212, 255, 0.2);
  color: #00d4ff;
}

.menu-item.logout {
  color: #ff4d4f;
}

.menu-divider {
  height: 1px;
  background: rgba(0, 212, 255, 0.2);
  margin: 10px 0;
}

.notification-panel {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  width: 360px;
  max-height: 480px;
  background: rgba(10, 31, 68, 0.98);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
  z-index: 1000;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px 18px;
  border-bottom: 1px solid rgba(0, 212, 255, 0.15);
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
}

.mark-read-btn {
  padding: 4px 12px;
  background: rgba(0, 212, 255, 0.1);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 4px;
  color: #00d4ff;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.mark-read-btn:hover {
  background: rgba(0, 212, 255, 0.2);
}

.notification-list {
  max-height: 400px;
  overflow-y: auto;
}

.notification-list::-webkit-scrollbar {
  width: 6px;
}

.notification-list::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
}

.notification-list::-webkit-scrollbar-thumb {
  background: rgba(0, 212, 255, 0.3);
  border-radius: 3px;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 18px;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 1px solid rgba(0, 212, 255, 0.08);
  position: relative;
}

.notification-item:hover {
  background: rgba(0, 212, 255, 0.05);
}

.notification-item.unread {
  background: rgba(0, 212, 255, 0.03);
}

.notification-item:last-child {
  border-bottom: none;
}

.item-icon {
  width: 36px;
  height: 36px;
  background: rgba(0, 212, 255, 0.1);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.item-content {
  flex: 1;
  min-width: 0;
}

.item-title {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 4px;
}

.item-desc {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-time {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 6px;
}

.unread-dot {
  position: absolute;
  top: 18px;
  right: 18px;
  width: 8px;
  height: 8px;
  background: #ff4d4f;
  border-radius: 50%;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
