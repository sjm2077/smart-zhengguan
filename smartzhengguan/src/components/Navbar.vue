<template>
  <div class="navbar">
    <div class="nav-left">
      <div class="logo-badge">
        <img
          class="logo-image"
          src="/branding/college-logo.png"
          alt="山东大学政治学与公共管理学院"
        />
      </div>
    </div>

    <div class="nav-right">
      <div ref="searchShell" class="search-shell" @click.stop>
        <div class="search-box" @click="focusSearch">
          <svg class="search-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            ref="searchInput"
            v-model.trim="searchKeyword"
            placeholder="搜索学生 / 学号 / 模块 / 通知 / 待办"
            @focus="openSearchPanel"
            @input="openSearchPanel"
            @keydown.enter.prevent="submitSearch"
            @keydown.esc="closeSearchPanel"
          />
        </div>

        <div v-if="searchPanelVisible" class="search-panel">
          <template v-if="searchKeyword">
            <div class="search-panel-header">
              <span>找到 {{ searchResultCount }} 条相关结果</span>
              <el-button link type="primary" @click="submitSearch">查看全部</el-button>
            </div>

            <div v-if="searchQuickResults.length" class="search-panel-list">
              <button
                v-for="item in searchQuickResults"
                :key="`${item.kind}-${item.title}-${item.meta}`"
                type="button"
                class="search-result-item"
                @mousedown.prevent="openSearchResult(item)"
              >
                <div class="search-result-top">
                  <span class="search-result-title">{{ item.title }}</span>
                  <span class="search-result-kind">{{ item.kindLabel }}</span>
                </div>
                <div class="search-result-summary">{{ item.summary }}</div>
                <div class="search-result-meta">
                  <span>{{ item.moduleName }}</span>
                  <span>{{ item.actionLabel }}</span>
                </div>
              </button>
            </div>

            <div v-else class="search-panel-empty">
              未找到直接结果，按回车进入全局搜索页查看更多结果。
            </div>
          </template>

          <template v-else>
            <div class="search-panel-header">
              <span>支持搜索学生、学号、模块、通知和待办</span>
              <el-button v-if="searchHistory.length" link type="primary" @click="clearStoredSearchHistory">
                清空历史
              </el-button>
            </div>

            <div v-if="searchHistory.length" class="search-panel-section">
              <div class="search-panel-title">最近搜索</div>
              <div class="search-keyword-list">
                <button
                  v-for="item in searchHistory"
                  :key="`history-${item}`"
                  type="button"
                  class="search-keyword-chip"
                  @mousedown.prevent="applyKeyword(item)"
                >
                  {{ item }}
                </button>
              </div>
            </div>

            <div class="search-panel-section">
              <div class="search-panel-title">推荐搜索</div>
              <div class="search-keyword-list">
                <button
                  v-for="item in recommendedKeywords"
                  :key="`recommend-${item}`"
                  type="button"
                  class="search-keyword-chip"
                  @mousedown.prevent="applyKeyword(item)"
                >
                  {{ item }}
                </button>
              </div>
            </div>
          </template>
        </div>
      </div>

      <el-popover
        placement="bottom"
        :width="340"
        trigger="click"
        :visible="msgVisible"
        @show="msgVisible = true"
        @hide="msgVisible = false"
      >
        <template #reference>
          <div class="notify-bell" @click="msgVisible = !msgVisible">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="bell-icon">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
            <span v-if="unreadCount > 0" class="badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
          </div>
        </template>
        <div class="msg-popover">
          <div class="msg-header">
            <span>消息提醒</span>
            <el-button link type="primary" size="small" @click="markAllRead">全部已读</el-button>
          </div>
          <div class="msg-list">
            <div
              v-for="msg in messages"
              :key="msg.id"
              class="msg-item"
              :class="{ unread: !msg.read }"
              @click="openMessage(msg)"
            >
              <span v-if="!msg.read" class="msg-dot"></span>
              <div class="msg-content">
                <div class="msg-title">{{ msg.title }}</div>
                <div class="msg-time">{{ msg.time }}</div>
              </div>
            </div>
          </div>
        </div>
      </el-popover>

      <el-popover
        placement="bottom"
        :width="160"
        trigger="click"
        :visible="userVisible"
        @show="userVisible = true"
        @hide="userVisible = false"
      >
        <template #reference>
          <div class="user-area" @click="userVisible = !userVisible">
            <el-avatar :size="32" class="user-avatar" :src="user.avatar">
              <svg
                v-if="!user.avatar"
                class="user-avatar-pattern"
                viewBox="0 0 24 24"
                fill="none"
                aria-hidden="true"
              >
                <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.6" opacity="0.24" />
                <circle cx="12" cy="9" r="2.7" fill="currentColor" />
                <path
                  d="M7.2 17.4c0-2.85 2.15-4.9 4.8-4.9s4.8 2.05 4.8 4.9"
                  stroke="currentColor"
                  stroke-width="2.2"
                  stroke-linecap="round"
                />
              </svg>
            </el-avatar>
            <span class="user-name">{{ user.name }} {{ user.role }}</span>
            <svg class="arrow-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </div>
        </template>
        <div class="user-menu">
          <div class="user-menu-item" @click="goUserMenu('/system')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="um-icon">
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.2a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.2a1.7 1.7 0 0 0 1.5-1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3h.1a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.2a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8v.1a1.7 1.7 0 0 0 1.5 1.1H21a2 2 0 1 1 0 4h-.2a1.7 1.7 0 0 0-1.4.9Z" />
            </svg>
            <span>系统设置</span>
          </div>
          <div class="user-menu-item" @click="goUserMenu('/personal')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="um-icon">
              <circle cx="12" cy="8" r="4" />
              <path d="M4 20c0-4 4-7 8-7s8 3 8 7" />
            </svg>
            <span>个人中心</span>
          </div>
          <div class="user-menu-item" @click="goUserMenu('/change-pwd')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="um-icon">
              <rect x="3" y="11" width="18" height="11" rx="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
            <span>修改密码</span>
          </div>
          <div class="user-menu-divider"></div>
          <div class="user-menu-item logout" @click="handleLogout">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="um-icon">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
            <span>退出登录</span>
          </div>
        </div>
      </el-popover>
    </div>

    <el-dialog v-model="messageDialogVisible" title="消息详情" width="420px">
      <div v-if="activeMessage" class="message-detail">
        <div class="message-detail-title">{{ activeMessage.title }}</div>
        <div class="message-detail-time">{{ activeMessage.time }}</div>
        <div class="message-detail-body">{{ activeMessage.content || activeMessage.title }}</div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import {
  DEFAULT_SEARCH_KEYWORDS,
  clearSearchHistory,
  getSearchHistory,
  saveSearchHistory,
} from '../utils/searchEngine'
import { getGlobalSearchResults } from '../services/mockDataService'

const MESSAGE_STORAGE_KEY = 'mock-navbar-messages'

const DEFAULT_MESSAGES = [
  {
    id: 1,
    title: '2024年研究生学籍信息核对通知',
    time: '2024-05-18 09:30',
    read: false,
    content: '请于本周内完成研究生学籍信息核对，并核验异常记录。',
  },
  {
    id: 2,
    title: '学位申请阶段工作安排提醒',
    time: '2024-05-15 14:20',
    read: false,
    content: '学位申请进入材料复核阶段，请尽快确认论文和答辩安排。',
  },
  {
    id: 3,
    title: '研究生学术论坛报名通知',
    time: '2024-05-10 10:00',
    read: true,
    content: '本学期研究生学术论坛报名通道已开放，请通知相关学生按时参加。',
  },
  {
    id: 4,
    title: '毕业答辩材料提交截止提醒',
    time: '2024-05-08 16:00',
    read: true,
    content: '本周毕业答辩材料提交截止，请督促学生按要求完成上传。',
  },
]

export default {
  data() {
    return {
      msgVisible: false,
      userVisible: false,
      messageDialogVisible: false,
      searchPanelVisible: false,
      searchKeyword: '',
      searchPreview: null,
      searchPreviewTimer: null,
      searchHistory: [],
      user: { name: '张老师', role: '教务秘书', avatar: '' },
      messages: [],
      activeMessage: null,
    }
  },
  computed: {
    unreadCount() {
      return this.messages.filter((message) => !message.read).length
    },
    searchQuickResults() {
      return this.searchPreview?.flatResults.slice(0, 8) || []
    },
    searchResultCount() {
      return this.searchPreview?.total || 0
    },
    recommendedKeywords() {
      return DEFAULT_SEARCH_KEYWORDS.filter((item) => !this.searchHistory.includes(item))
    },
  },
  watch: {
    '$route.query.q': {
      immediate: true,
      handler(value) {
        if (this.$route.path === '/search') {
          this.searchKeyword = String(value || '')
        }
      },
    },
    searchKeyword() {
      this.scheduleSearchPreview()
    },
  },
  mounted() {
    this.loadUser()
    this.loadMessages()
    this.refreshSearchHistory()
    window.addEventListener('mock-user-updated', this.loadUser)
    document.addEventListener('click', this.handleDocumentClick)
  },
  beforeUnmount() {
    window.removeEventListener('mock-user-updated', this.loadUser)
    document.removeEventListener('click', this.handleDocumentClick)
    if (this.searchPreviewTimer) {
      clearTimeout(this.searchPreviewTimer)
      this.searchPreviewTimer = null
    }
  },
  methods: {
    scheduleSearchPreview() {
      if (this.searchPreviewTimer) {
        clearTimeout(this.searchPreviewTimer)
        this.searchPreviewTimer = null
      }

      const keyword = String(this.searchKeyword || '').trim()
      if (!keyword) {
        this.searchPreview = null
        return
      }

      this.searchPreviewTimer = setTimeout(() => {
        this.fetchSearchPreview()
      }, 220)
    },
    async fetchSearchPreview() {
      const keyword = String(this.searchKeyword || '').trim()
      if (!keyword) {
        this.searchPreview = null
        return
      }

      const result = await getGlobalSearchResults(keyword)
      if (keyword !== String(this.searchKeyword || '').trim()) return
      this.searchPreview = result
    },
    focusSearch() {
      this.openSearchPanel()
      this.$refs.searchInput?.focus()
    },
    openSearchPanel() {
      this.searchPanelVisible = true
      this.refreshSearchHistory()
    },
    closeSearchPanel() {
      this.searchPanelVisible = false
    },
    handleDocumentClick(event) {
      if (!this.$refs.searchShell?.contains(event.target)) {
        this.closeSearchPanel()
      }
    },
    refreshSearchHistory() {
      this.searchHistory = getSearchHistory()
    },
    applyKeyword(keyword) {
      this.searchKeyword = keyword
      this.openSearchPanel()
      this.$nextTick(() => {
        this.$refs.searchInput?.focus()
      })
    },
    submitSearch() {
      const keyword = String(this.searchKeyword || '').trim()

      if (!keyword) {
        this.$message?.warning('请输入搜索关键词')
        return
      }

      saveSearchHistory(keyword)
      this.refreshSearchHistory()
      this.closeSearchPanel()
      this.$router.push({
        path: '/search',
        query: { q: keyword },
      })
    },
    openSearchResult(item) {
      const keyword = String(this.searchKeyword || item.title || '').trim()
      if (keyword) {
        saveSearchHistory(keyword)
        this.refreshSearchHistory()
      }

      this.closeSearchPanel()
      this.$router.push({
        path: item.route,
        query: item.routeQuery || {},
      })
    },
    clearStoredSearchHistory() {
      clearSearchHistory()
      this.refreshSearchHistory()
    },
    loadUser() {
      const storedUser = localStorage.getItem('mock-user')
      if (!storedUser) return
      try {
        this.user = {
          ...this.user,
          ...JSON.parse(storedUser),
        }
      } catch (error) {
        console.warn('用户信息读取失败', error)
      }
    },
    loadMessages() {
      const stored = localStorage.getItem(MESSAGE_STORAGE_KEY)
      if (!stored) {
        this.messages = DEFAULT_MESSAGES
        this.persistMessages()
        return
      }

      try {
        this.messages = JSON.parse(stored)
      } catch (error) {
        console.warn('消息读取失败', error)
        this.messages = DEFAULT_MESSAGES
        this.persistMessages()
      }
    },
    persistMessages() {
      localStorage.setItem(MESSAGE_STORAGE_KEY, JSON.stringify(this.messages))
    },
    openMessage(message) {
      message.read = true
      this.persistMessages()
      this.activeMessage = message
      this.messageDialogVisible = true
    },
    markAllRead() {
      this.messages = this.messages.map((message) => ({
        ...message,
        read: true,
      }))
      this.persistMessages()
    },
    goUserMenu(path) {
      this.userVisible = false
      this.$router.push(path)
    },
    handleLogout() {
      this.userVisible = false
      localStorage.removeItem('token')
      this.$router.push('/login')
    },
  },
}
</script>

<style scoped>
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #0A2463;
  color: #fff;
  height: 68px;
  padding: 0 20px;
  flex-shrink: 0;
  gap: 12px;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.logo-badge {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.logo-image {
  width: min(26vw, 360px);
  min-width: 220px;
  height: auto;
  display: block;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 18px;
  min-width: 0;
  flex-shrink: 0;
}

.search-shell {
  position: relative;
}

.search-box {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.12);
  border-radius: 18px;
  padding: 5px 14px;
  gap: 6px;
  min-width: 360px;
  cursor: text;
}

.search-box input {
  background: transparent;
  border: none;
  outline: none;
  color: #fff;
  width: 100%;
  font-size: 13px;
  font-weight: 400;
}

.search-box input::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.search-svg {
  width: 15px;
  height: 15px;
  opacity: 0.6;
  flex-shrink: 0;
}

.search-panel {
  position: absolute;
  top: calc(100% + 10px);
  left: 0;
  width: 420px;
  max-width: min(76vw, 420px);
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 16px 40px rgba(10, 36, 99, 0.2);
  color: #1d2939;
  padding: 14px;
  z-index: 30;
}

.search-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  color: #667085;
  margin-bottom: 12px;
}

.search-panel-section + .search-panel-section {
  margin-top: 14px;
}

.search-panel-title {
  font-size: 12px;
  color: #98a2b3;
  margin-bottom: 10px;
}

.search-panel-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.search-result-item {
  width: 100%;
  border: 1px solid #e4e7ec;
  background: #fff;
  border-radius: 12px;
  padding: 12px;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s;
}

.search-result-item:hover {
  border-color: #b2ccff;
  box-shadow: 0 8px 24px rgba(22, 93, 255, 0.12);
  transform: translateY(-1px);
}

.search-result-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.search-result-title {
  font-size: 14px;
  font-weight: 600;
  color: #101828;
}

.search-result-kind {
  flex-shrink: 0;
  font-size: 11px;
  color: #165dff;
  background: #eef4ff;
  border-radius: 999px;
  padding: 3px 8px;
}

.search-result-summary {
  margin-top: 6px;
  font-size: 12px;
  color: #475467;
  line-height: 1.5;
}

.search-result-meta {
  margin-top: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: #98a2b3;
}

.search-panel-empty {
  padding: 18px 10px 6px;
  font-size: 13px;
  color: #667085;
}

.search-keyword-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.search-keyword-chip {
  border: 1px solid #d0d5dd;
  background: #f8fafc;
  color: #344054;
  border-radius: 999px;
  padding: 6px 12px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.search-keyword-chip:hover {
  border-color: #bfd4ff;
  background: #eef4ff;
  color: #165dff;
}

.notify-bell {
  position: relative;
  cursor: pointer;
  padding: 4px;
}

.bell-icon {
  width: 20px;
  height: 20px;
  color: rgba(255, 255, 255, 0.85);
}

.notify-bell:hover .bell-icon {
  color: #fff;
}

.badge {
  position: absolute;
  top: 0;
  right: -2px;
  background: #ff4d4f;
  color: #fff;
  font-size: 10px;
  font-weight: 600;
  min-width: 16px;
  height: 16px;
  line-height: 16px;
  text-align: center;
  border-radius: 8px;
  padding: 0 4px;
  border: 1px solid #0A2463;
}

.user-area {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 4px;
}

.user-area:hover {
  background: rgba(255, 255, 255, 0.1);
}

.user-avatar {
  background: #409eff !important;
  font-size: 14px;
  flex-shrink: 0;
}

.user-avatar-pattern {
  width: 20px;
  height: 20px;
  color: #ffffff;
  display: block;
}

.user-name {
  font-size: 14px;
  font-weight: 400;
  white-space: nowrap;
}

.arrow-icon {
  width: 14px;
  height: 14px;
  opacity: 0.6;
}

.msg-popover {
  margin: -12px;
}

.msg-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
  font-weight: 600;
  font-size: 15px;
}

.msg-list {
  max-height: 260px;
  overflow-y: auto;
}

.msg-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 16px;
  border-bottom: 1px solid #f5f5f5;
  cursor: pointer;
  transition: background 0.15s;
}

.msg-item:hover {
  background: #f5f7fa;
}

.msg-item.unread {
  background: #f0f7ff;
}

.msg-dot {
  width: 8px;
  height: 8px;
  background: #409eff;
  border-radius: 50%;
  margin-top: 5px;
  flex-shrink: 0;
}

.msg-content {
  flex: 1;
}

.msg-title {
  font-size: 14px;
  color: #333;
  font-weight: 400;
  line-height: 1.4;
}

.msg-time {
  font-size: 12px;
  color: #999;
  margin-top: 3px;
}

.user-menu {
  margin: -12px;
}

.user-menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 16px;
  font-size: 14px;
  color: #333;
  cursor: pointer;
  transition: background 0.15s;
}

.user-menu-item:hover {
  background: #f5f7fa;
}

.user-menu-item.logout {
  color: #ff4d4f;
}

.user-menu-divider {
  height: 1px;
  background: #eee;
  margin: 4px 0;
}

.um-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.message-detail-title {
  font-size: 16px;
  font-weight: 600;
  color: #1d2939;
}

.message-detail-time {
  margin-top: 6px;
  font-size: 12px;
  color: #98a2b3;
}

.message-detail-body {
  margin-top: 14px;
  font-size: 14px;
  line-height: 1.7;
  color: #344054;
}

@media (max-width: 1400px) {
  .logo-image {
    width: min(24vw, 320px);
    min-width: 200px;
  }

  .search-box {
    min-width: 300px;
  }

  .search-panel {
    width: 380px;
  }
}

@media (max-width: 1200px) {
  .navbar {
    padding: 0 14px;
    height: 62px;
  }

  .logo-image {
    width: min(22vw, 270px);
    min-width: 170px;
  }

  .nav-right {
    gap: 12px;
  }

  .search-box {
    min-width: 260px;
  }
}

@media (max-width: 900px) {
  .navbar {
    height: 56px;
  }

  .search-shell {
    display: none;
  }

  .logo-image {
    width: min(46vw, 220px);
    min-width: 140px;
  }

  .user-name {
    display: none;
  }
}
</style>
