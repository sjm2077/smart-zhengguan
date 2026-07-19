<template>
  <div class="search-bar" ref="searchBarRef">
    <div class="search-input-wrapper" :class="{ 'focused': isFocused }">
      <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"></circle>
        <path d="m21 21-4.35-4.35"></path>
      </svg>
      <input
        v-model="searchValue"
        type="text"
        :placeholder="placeholder"
        @focus="isFocused = true"
        @blur="handleBlur"
        @input="handleInput"
        @keydown="handleKeydown"
        ref="inputRef"
        class="search-input"
      />
      <div v-if="searchValue" class="clear-btn" @mousedown.stop.prevent @click="clearSearch">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="m18 6-12 12M6 6l12 12"></path>
        </svg>
      </div>
    </div>
    
    <transition name="fade">
      <div v-if="showDropdown && filteredRoutes.length > 0" class="search-dropdown">
        <div class="dropdown-list">
          <div
            v-for="(item, index) in filteredRoutes"
            :key="item.path"
            class="dropdown-item"
            :class="{ active: highlightedIndex === index }"
            @click="selectItem(item)"
            @mouseenter="highlightedIndex = index"
          >
            <span class="item-icon">{{ item.icon }}</span>
            <div class="item-content">
              <span class="item-name">{{ item.name }}</span>
              <span class="item-keywords">
                <span v-for="kw in item.keywords.slice(0, 3)" :key="kw" class="keyword-tag">
                  {{ kw }}
                </span>
              </span>
            </div>
            <span class="item-shortcut">Enter</span>
          </div>
        </div>
        <div class="dropdown-tip">
          <span>按 ⬆/⬇ 选择，Enter 跳转</span>
        </div>
      </div>
    </transition>
    
    <transition name="fade">
      <div v-if="showNoMatch" class="search-dropdown no-match">
        <div class="no-match-content">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <path d="m15 9-6 6M9 9l6 6"></path>
          </svg>
          <span>未找到对应功能页面</span>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  placeholder: {
    type: String,
    default: '搜索功能页面... (Ctrl+S)'
  }
})

const emit = defineEmits(['select'])

const router = useRouter()

const routeMap = [
  { path: '/dashboard', name: '综合概览', icon: '🏠', keywords: ['综合', '概览', '首页', '总览', '大盘', '整体数据', '智慧政管', '平台首页'] },
  { path: '/teaching', name: '教学管理', icon: '📚', keywords: ['教学', '生源', '专业人数', '男女比例', '招生', '课程', '培养方案', '教学计划'] },
  { path: '/research', name: '科研管理', icon: '🔬', keywords: ['科研', '项目', '经费', '科研产出', '在研', '研究', '论文', '课题'] },
  { path: '/portrait', name: '师生画像', icon: '👤', keywords: ['师生', '画像', '学生画像', '教工画像', '个人', '教师画像', '师资力量', '师资队伍', '教师', '教职工', '职称', '教授', '讲师', '副教授', '师资'] },
  { path: '/graduate', name: '研究生管理', icon: '🎓', keywords: ['研究生', '在校生', '就业率', '就业', '硕士', '博士', '招生简章', 'MPA', '公共管理硕士'] },
  { path: '/warning', name: '智能预警', icon: '⚠️', keywords: ['预警', '预算', '执行率', '风险', '警告', '监控', '异常'] },
  { path: '/wordcloud', name: '词云分析', icon: '☁️', keywords: ['词云', '文本', '舆情', '词分析', '关键词', '语义分析', '文本挖掘'] },
  { path: '/hr', name: '人事系统', icon: '🏢', keywords: ['人事', 'HR', '员工', '招聘', '考勤', '薪酬', '组织架构'] },
  { path: '/treehole', name: '校园树洞', icon: '💭', keywords: ['树洞', '匿名', '吐槽', '心情', '评价', '反馈', '互助', '小组', '组队'] },
  { path: '/profile', name: '个人中心', icon: '👤', keywords: ['个人中心', '个人信息', '修改密码', '编辑资料', '账户', '设置', '我的'] }
]

const searchValue = ref('')
const isFocused = ref(false)
const showDropdown = ref(false)
const showNoMatch = ref(false)
const highlightedIndex = ref(0)
const debounceTimer = ref(null)

const searchBarRef = ref(null)
const inputRef = ref(null)

const filteredRoutes = computed(() => {
  const kw = searchValue.value.trim().toLowerCase()
  if (!kw) return []
  
  return routeMap.filter(item => {
    const nameMatch = item.name.toLowerCase().includes(kw)
    const keywordMatch = item.keywords.some(k => k.toLowerCase().includes(kw))
    return nameMatch || keywordMatch
  }).sort((a, b) => {
    const aName = a.name.toLowerCase().includes(kw) ? 0 : 1
    const bName = b.name.toLowerCase().includes(kw) ? 0 : 1
    return aName - bName
  })
})

const handleInput = () => {
  if (debounceTimer.value) {
    clearTimeout(debounceTimer.value)
  }
  
  debounceTimer.value = setTimeout(() => {
    highlightedIndex.value = 0
    if (searchValue.value.trim() && filteredRoutes.value.length === 0) {
      showNoMatch.value = true
      showDropdown.value = false
    } else {
      showNoMatch.value = false
      showDropdown.value = filteredRoutes.value.length > 0
    }
  }, 300)
}

const handleKeydown = (e) => {
  if (e.key === 'Escape') {
    showDropdown.value = false
    showNoMatch.value = false
    inputRef.value?.blur()
    return
  }
  
  if (e.key === 'Enter') {
    e.preventDefault()
    if (filteredRoutes.value.length > 0 && highlightedIndex.value < filteredRoutes.value.length) {
      selectItem(filteredRoutes.value[highlightedIndex.value])
    }
    return
  }
  
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    if (filteredRoutes.value.length > 0) {
      highlightedIndex.value = (highlightedIndex.value + 1) % filteredRoutes.value.length
    }
    return
  }
  
  if (e.key === 'ArrowUp') {
    e.preventDefault()
    if (filteredRoutes.value.length > 0) {
      highlightedIndex.value = (highlightedIndex.value - 1 + filteredRoutes.value.length) % filteredRoutes.value.length
    }
  }
}

const handleBlur = () => {
  setTimeout(() => {
    isFocused.value = false
    showDropdown.value = false
    showNoMatch.value = false
  }, 200)
}

const selectItem = (item) => {
  searchValue.value = ''
  showDropdown.value = false
  showNoMatch.value = false
  emit('select', item)
  router.push(item.path)
}

const clearSearch = () => {
  searchValue.value = ''
  showDropdown.value = false
  showNoMatch.value = false
  inputRef.value?.focus()
}

const focusSearch = () => {
  inputRef.value?.focus()
}

const handleGlobalKeydown = (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault()
    focusSearch()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleGlobalKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleGlobalKeydown)
  if (debounceTimer.value) {
    clearTimeout(debounceTimer.value)
  }
})

defineExpose({
  focusSearch
})
</script>

<style scoped>
.search-bar {
  position: relative;
  width: 100%;
  max-width: 480px;
  z-index: 1000;
}

.search-input-wrapper {
  position: relative;
  width: 100%;
  background: rgba(0, 20, 40, 0.6);
  border: 1px solid rgba(0, 212, 255, 0.25);
  border-radius: 50px;
  padding: 10px 18px;
  display: flex;
  align-items: center;
  gap: 12px;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
}

.search-input-wrapper.focused {
  border-color: rgba(0, 212, 255, 0.6);
  box-shadow: 0 0 30px rgba(0, 212, 255, 0.2), inset 0 0 20px rgba(0, 212, 255, 0.05);
  background: rgba(0, 20, 40, 0.8);
}

.search-icon {
  width: 20px;
  height: 20px;
  color: rgba(0, 212, 255, 0.7);
  flex-shrink: 0;
  transition: color 0.3s;
}

.search-input-wrapper.focused .search-icon {
  color: #00d4ff;
}

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: #fff;
  font-size: 15px;
  font-family: inherit;
  line-height: 1.5;
}

.search-input::placeholder {
  color: rgba(255, 255, 255, 0.4);
}

.clear-btn {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: rgba(255, 255, 255, 0.5);
  transition: color 0.3s;
  flex-shrink: 0;
}

.clear-btn:hover {
  color: #00d4ff;
}

.clear-btn svg {
  width: 16px;
  height: 16px;
}

.search-dropdown {
  position: absolute;
  top: calc(100% + 12px);
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  min-width: 520px;
  background: rgba(10, 31, 68, 0.98);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5), 0 0 40px rgba(0, 212, 255, 0.1);
  backdrop-filter: blur(20px);
}

.search-dropdown::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.6), transparent);
}

.dropdown-list {
  max-height: 360px;
  overflow-y: auto;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 20px;
  cursor: pointer;
  transition: all 0.2s ease;
  border-bottom: 1px solid rgba(0, 212, 255, 0.08);
}

.dropdown-item:last-of-type {
  border-bottom: none;
}

.dropdown-item:hover,
.dropdown-item.active {
  background: rgba(0, 212, 255, 0.12);
}

.dropdown-item.active {
  background: rgba(0, 212, 255, 0.18);
  box-shadow: inset 3px 0 0 #00d4ff;
}

.item-icon {
  font-size: 24px;
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 212, 255, 0.1);
  border-radius: 10px;
}

.item-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.item-name {
  font-size: 15px;
  font-weight: 500;
  color: #fff;
}

.item-keywords {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.keyword-tag {
  font-size: 11px;
  padding: 2px 8px;
  background: rgba(0, 212, 255, 0.1);
  color: rgba(0, 212, 255, 0.8);
  border-radius: 10px;
  border: 1px solid rgba(0, 212, 255, 0.2);
}

.item-shortcut {
  font-size: 11px;
  padding: 4px 8px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.5);
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  font-family: monospace;
  flex-shrink: 0;
}

.dropdown-tip {
  padding: 10px 20px;
  background: rgba(0, 0, 0, 0.25);
  border-top: 1px solid rgba(0, 212, 255, 0.1);
  text-align: center;
}

.dropdown-tip span {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

.no-match {
  padding: 40px 20px;
}

.no-match-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.no-match-content svg {
  width: 48px;
  height: 48px;
  opacity: 0.6;
}

.no-match-content span {
  font-size: 14px;
}

.fade-enter-active,
.fade-leave-active {
  transition: all 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-8px);
}

.dropdown-list::-webkit-scrollbar {
  width: 6px;
}

.dropdown-list::-webkit-scrollbar-track {
  background: transparent;
}

.dropdown-list::-webkit-scrollbar-thumb {
  background: rgba(0, 212, 255, 0.3);
  border-radius: 3px;
}

.dropdown-list::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 212, 255, 0.5);
}

@media (max-width: 768px) {
  .search-bar {
    max-width: 320px;
  }
  
  .search-dropdown {
    min-width: 360px;
  }
  
  .item-keywords {
    display: none;
  }
}
</style>
