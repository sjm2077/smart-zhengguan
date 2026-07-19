<template>
  <div class="search-container" ref="containerRef">
    <div class="search-wrapper">
      <div class="search-input-wrapper" :class="{ focused: isFocused }">
        <span class="search-icon">🔍</span>
        <input
          ref="inputRef"
          v-model="searchQuery"
          type="text"
          class="search-input"
          placeholder="搜索课程/科研项目/专业/招生信息..."
          @focus="handleFocus"
          @input="handleInput"
          @keydown.enter="handleSearch"
          @keydown.esc="closeSearch"
        />
        <button v-if="searchQuery" class="clear-btn" @click="clearSearch">✕</button>
        <button class="search-btn" @click="handleSearch">
          <span class="search-btn-icon">→</span>
        </button>
      </div>

      <div class="hot-search-section">
        <span class="hot-label">🔥 热门搜索：</span>
        <div class="hot-tags">
          <span
            v-for="(item, index) in hotSearchList"
            :key="index"
            class="hot-tag"
            :class="{ top: index < 3 }"
            @click="selectHotSearch(item)"
          >
            {{ item.title }}
          </span>
        </div>
      </div>

      <transition name="dropdown">
        <div v-if="showDropdown" class="search-dropdown">
          <div v-if="searchQuery && suggestions.length > 0" class="suggestion-list">
            <div
              v-for="(suggestion, index) in suggestions"
              :key="index"
              class="suggestion-item"
              :class="{ active: currentSuggestionIndex === index }"
              @click="selectSuggestion(suggestion)"
              @mouseenter="currentSuggestionIndex = index"
            >
              <span class="suggestion-icon">{{ getSuggestionIcon(suggestion.type) }}</span>
              <div class="suggestion-content">
                <div class="suggestion-title" v-html="highlightText(suggestion.title)"></div>
                <div class="suggestion-meta">
                  <span class="suggestion-type">{{ getSuggestionTypeName(suggestion.type) }}</span>
                  <span v-if="suggestion.department" class="suggestion-dept">{{ suggestion.department }}</span>
                </div>
              </div>
            </div>
          </div>

          <div v-if="searchQuery && suggestions.length === 0 && !isSearching" class="no-results">
            <span class="no-results-icon">🔍</span>
            <span class="no-results-text">未找到相关结果</span>
          </div>

          <div v-if="isSearching" class="loading-state">
            <div class="loading-spinner"></div>
            <span>搜索中...</span>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const emit = defineEmits(['search', 'select'])
const router = useRouter()

const searchQuery = ref('')
const isFocused = ref(false)
const showDropdown = ref(false)
const isSearching = ref(false)
const suggestions = ref([])
const currentSuggestionIndex = ref(-1)
const inputRef = ref(null)
const containerRef = ref(null)

const SEARCH_DEBOUNCE = 300
let debounceTimer = null

const handleClickOutside = (event) => {
  if (containerRef.value && !containerRef.value.contains(event.target)) {
    closeSearch()
  }
}

const mockDatabase = {
  projects: [
    { id: 6, title: '数字政府治理研究', type: 'project', department: '公共管理系', level: '国家级' },
    { id: 7, title: '基层社会治理创新', type: 'project', department: '行政管理系', level: '省部级' },
    { id: 26, title: '中国政治学理论前沿研究', type: 'project', department: '政治学系', level: '国家级' },
    { id: 27, title: '全球治理与中国外交战略', type: 'project', department: '国际政治系', level: '省部级' },
    { id: 28, title: '公共政策评估理论与实践', type: 'project', department: '公共管理系', level: '国家级' },
    { id: 32, title: '人工智能与政府治理现代化', type: 'project', department: '行政管理系', level: '国家级' },
    { id: 30, title: '全球气候治理与国际合作', type: 'project', department: '国际政治系', level: '国家级' },
    { id: 29, title: '新时代政党政治与国家治理', type: 'project', department: '政治学系', level: '省部级' }
  ],
  courses: [
    { id: 8, title: '公共管理学', type: 'course', department: '公共管理系', credit: '3学分' },
    { id: 9, title: '政治学原理', type: 'course', department: '政治学系', credit: '4学分' },
    { id: 34, title: '行政管理学', type: 'course', department: '行政管理系', credit: '3学分' },
    { id: 35, title: '国际政治学', type: 'course', department: '国际政治系', credit: '4学分' },
    { id: 36, title: '公共政策分析', type: 'course', department: '公共管理系', credit: '3学分' },
    { id: 37, title: '西方政治思想史', type: 'course', department: '政治学系', credit: '4学分' },
    { id: 38, title: '中国政府与政治', type: 'course', department: '政治学系', credit: '3学分' },
    { id: 43, title: '行政法学', type: 'course', department: '行政管理系', credit: '3学分' }
  ],
  departments: [
    { id: 10, title: '行政管理系', type: 'department', teacherCount: 28 },
    { id: 11, title: '政治学系', type: 'department', teacherCount: 22 },
    { id: 44, title: '国际政治系', type: 'department', teacherCount: 18 },
    { id: 45, title: '公共管理系', type: 'department', teacherCount: 25 },
    { id: 46, title: '政治学与行政学系', type: 'department', teacherCount: 20 }
  ],
  programs: [
    { id: 47, title: '行政管理', type: 'program', level: '本科', category: '热门专业' },
    { id: 48, title: '政治学与行政学', type: 'program', level: '本科', category: '热门专业' },
    { id: 49, title: '国际政治', type: 'program', level: '本科', category: '特色专业' },
    { id: 50, title: '公共管理硕士(MPA)', type: 'program', level: '研究生', category: '热门专业' },
    { id: 51, title: '政治学理论', type: 'program', level: '研究生', category: '重点学科' },
    { id: 53, title: '国际关系', type: 'program', level: '研究生', category: '特色专业' },
    { id: 54, title: '公共政策', type: 'program', level: '研究生', category: '热门专业' },
    { id: 55, title: '社会保障', type: 'program', level: '研究生', category: '特色专业' }
  ],
  admissions: [
    { id: 57, title: '研究生招生简章', type: 'admission', year: '2025' },
    { id: 58, title: '推免生招生简章', type: 'admission', year: '2025' },
    { id: 59, title: '博士研究生招生', type: 'admission', year: '2025' },
    { id: 60, title: 'MPA招生简章', type: 'admission', year: '2025' },
    { id: 62, title: '历年分数线', type: 'admission', year: '2025' },
    { id: 63, title: '复试安排', type: 'admission', year: '2025' }
  ]
}

const hotSearchList = [
  { title: '数字政府治理研究', type: 'project' },
  { title: '公共管理学', type: 'course' },
  { title: '行政管理', type: 'program' },
  { title: '研究生招生简章', type: 'admission' },
  { title: '政治学原理', type: 'course' },
  { title: '基层社会治理创新', type: 'project' },
  { title: '公共管理硕士(MPA)', type: 'program' },
  { title: '公共政策分析', type: 'course' },
  { title: '国际政治', type: 'program' },
  { title: '历年分数线', type: 'admission' }
]

const searchData = (query) => {
  if (!query.trim()) {
    suggestions.value = []
    return
  }

  const data = {
    projects: mockDatabase.projects,
    courses: mockDatabase.courses,
    departments: mockDatabase.departments,
    programs: mockDatabase.programs,
    admissions: mockDatabase.admissions
  }

  const results = []
  const lowerQuery = query.toLowerCase()

  Object.keys(data).forEach(key => {
    data[key].forEach(item => {
      if (item.title.toLowerCase().includes(lowerQuery) || 
          (item.department && item.department.toLowerCase().includes(lowerQuery))) {
        results.push(item)
      }
    })
  })

  suggestions.value = results.slice(0, 8)
}

const handleInput = () => {
  currentSuggestionIndex.value = -1
  
  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }

  if (!searchQuery.value) {
    suggestions.value = []
    isSearching.value = false
    return
  }

  isSearching.value = true
  
  debounceTimer = setTimeout(() => {
    searchData(searchQuery.value)
    isSearching.value = false
  }, SEARCH_DEBOUNCE)
}

const handleFocus = () => {
  isFocused.value = true
  showDropdown.value = true
}

const closeSearch = () => {
  showDropdown.value = false
  isFocused.value = false
  currentSuggestionIndex.value = -1
}

const handleSearch = () => {
  if (currentSuggestionIndex.value >= 0 && suggestions.value[currentSuggestionIndex.value]) {
    selectSuggestion(suggestions.value[currentSuggestionIndex.value])
    return
  }
  
  if (searchQuery.value.trim()) {
    emit('search', searchQuery.value)
    closeSearch()
  }
}

const selectSuggestion = (suggestion) => {
  searchQuery.value = suggestion.title
  emit('select', suggestion)
  closeSearch()
  
  if (suggestion.type === 'project') {
    router.push({ path: '/research', query: { keyword: suggestion.title } })
  } else if (suggestion.type === 'course') {
    router.push({ path: '/teaching', query: { keyword: suggestion.title } })
  } else if (suggestion.type === 'department') {
    router.push({ path: '/portrait', query: { type: 'department', name: suggestion.title } })
  } else if (suggestion.type === 'program') {
    router.push({ path: '/graduate', query: { keyword: suggestion.title } })
  } else if (suggestion.type === 'admission') {
    router.push({ path: '/graduate', query: { keyword: suggestion.title } })
  }
}

const selectHotSearch = (item) => {
  searchQuery.value = item.title
  handleSearch()
}

const clearSearch = () => {
  searchQuery.value = ''
  suggestions.value = []
  inputRef.value?.focus()
}

const getSuggestionIcon = (type) => {
  const icons = {
    project: '🔬',
    course: '📚',
    department: '🏢',
    program: '🎓',
    admission: '📋'
  }
  return icons[type] || '📌'
}

const getSuggestionTypeName = (type) => {
  const names = {
    project: '科研项目',
    course: '课程',
    department: '院系',
    program: '专业',
    admission: '招生'
  }
  return names[type] || '其他'
}

const highlightText = (text) => {
  if (!searchQuery.value) return text
  const regex = new RegExp(`(${searchQuery.value})`, 'gi')
  return text.replace(regex, '<em class="highlight">$1</em>')
}

watch(searchQuery, (newVal) => {
  if (!newVal) {
    suggestions.value = []
    isSearching.value = false
  }
})

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.search-container {
  position: relative;
  width: 100%;
  max-width: 650px;
}

.search-wrapper {
  position: relative;
  width: 100%;
}

.search-input-wrapper {
  display: flex;
  align-items: center;
  padding: 14px 20px;
  background: linear-gradient(135deg, rgba(0, 30, 60, 0.9) 0%, rgba(10, 40, 80, 0.85) 100%);
  backdrop-filter: blur(20px);
  border: 2px solid rgba(0, 212, 255, 0.3);
  border-radius: 40px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.search-input-wrapper:hover {
  border-color: rgba(0, 212, 255, 0.5);
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.4),
    0 0 20px rgba(0, 212, 255, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.search-input-wrapper.focused {
  background: linear-gradient(135deg, rgba(0, 40, 80, 0.95) 0%, rgba(15, 50, 100, 0.9) 100%);
  border-color: rgba(0, 212, 255, 0.8);
  box-shadow: 
    0 0 40px rgba(0, 212, 255, 0.3),
    0 8px 32px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
  transform: translateY(-2px);
}

.search-icon {
  font-size: 18px;
  margin-right: 12px;
  color: rgba(0, 212, 255, 0.7);
  transition: all 0.3s;
}

.search-input-wrapper.focused .search-icon {
  color: rgba(0, 212, 255, 1);
}

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: #fff;
  font-size: 16px;
  font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
  letter-spacing: 0.5px;
}

.search-input::placeholder {
  color: rgba(255, 255, 255, 0.4);
  font-size: 15px;
}

.clear-btn {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.6);
  width: 28px;
  height: 28px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.25s ease;
  font-size: 14px;
  margin-left: 8px;
}

.clear-btn:hover {
  background: rgba(255, 77, 79, 0.4);
  border-color: rgba(255, 77, 79, 0.6);
  color: #ff4d4f;
}

.search-btn {
  background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
  border: none;
  color: #001e3c;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  margin-left: 8px;
  box-shadow: 0 4px 15px rgba(0, 212, 255, 0.4);
}

.search-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 20px rgba(0, 212, 255, 0.6);
}

.search-btn:active {
  transform: scale(0.95);
}

.search-btn-icon {
  font-size: 16px;
  font-weight: bold;
}

.hot-search-section {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
  padding: 12px 20px;
  background: linear-gradient(135deg, rgba(0, 20, 40, 0.7) 0%, rgba(10, 30, 60, 0.6) 100%);
  backdrop-filter: blur(15px);
  border: 1px solid rgba(0, 212, 255, 0.15);
  border-radius: 16px;
  flex-wrap: wrap;
}

.hot-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 500;
}

.hot-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.hot-tag {
  padding: 6px 16px;
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(255, 100, 150, 0.05) 100%);
  border: 1px solid rgba(0, 212, 255, 0.25);
  border-radius: 20px;
  color: rgba(255, 255, 255, 0.85);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  letter-spacing: 0.3px;
}

.hot-tag:hover {
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.25) 0%, rgba(255, 100, 150, 0.15) 100%);
  border-color: rgba(0, 212, 255, 0.5);
  box-shadow: 0 0 15px rgba(0, 212, 255, 0.2);
  transform: translateY(-2px);
}

.hot-tag.top {
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.2) 0%, rgba(255, 100, 150, 0.1) 100%);
  border-color: rgba(0, 212, 255, 0.4);
  color: #00d4ff;
  font-weight: 500;
}

.search-dropdown {
  position: absolute;
  top: calc(100% + 12px);
  left: 0;
  right: 0;
  min-width: 450px;
  max-height: 400px;
  overflow-y: auto;
  background: rgba(5, 25, 55, 0.98);
  backdrop-filter: blur(25px);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 16px;
  box-shadow: 
    0 15px 50px rgba(0, 0, 0, 0.6),
    0 0 30px rgba(0, 212, 255, 0.1);
  z-index: 1000;
}

.search-dropdown::-webkit-scrollbar {
  width: 6px;
}

.search-dropdown::-webkit-scrollbar-track {
  background: rgba(0, 212, 255, 0.05);
  border-radius: 3px;
}

.search-dropdown::-webkit-scrollbar-thumb {
  background: rgba(0, 212, 255, 0.3);
  border-radius: 3px;
}

.search-dropdown::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 212, 255, 0.5);
}

.suggestion-list {
  display: flex;
  flex-direction: column;
}

.suggestion-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 20px;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 1px solid rgba(0, 212, 255, 0.05);
}

.suggestion-item:last-child {
  border-bottom: none;
}

.suggestion-item:hover,
.suggestion-item.active {
  background: linear-gradient(90deg, rgba(0, 212, 255, 0.15) 0%, transparent 100%);
}

.suggestion-icon {
  font-size: 26px;
  color: #00d4ff;
}

.suggestion-content {
  flex: 1;
}

.suggestion-title {
  color: #fff;
  font-size: 15px;
  margin-bottom: 5px;
  font-weight: 500;
}

.suggestion-title :deep(.highlight) {
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.4) 0%, rgba(255, 100, 150, 0.3) 100%);
  color: #00d4ff;
  padding: 0 4px;
  border-radius: 4px;
  font-style: normal;
  font-weight: 600;
}

.suggestion-meta {
  display: flex;
  gap: 14px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.suggestion-type {
  color: #00d4ff;
  padding: 2px 8px;
  background: rgba(0, 212, 255, 0.15);
  border-radius: 10px;
  font-size: 11px;
}

.no-results,
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 50px 20px;
  color: rgba(255, 255, 255, 0.5);
  gap: 14px;
}

.no-results-icon {
  font-size: 40px;
  opacity: 0.4;
}

.no-results-text {
  font-size: 14px;
}

.loading-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid rgba(0, 212, 255, 0.2);
  border-top-color: #00d4ff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-10px) scale(0.98);
}
</style>