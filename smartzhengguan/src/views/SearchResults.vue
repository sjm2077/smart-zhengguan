<template>
  <div class="search-results-page">
    <div class="page-header">
      <div class="header-left">
        <span class="page-title">全局搜索</span>
        <span class="page-subtitle">统一检索学生、学号、功能模块、通知待办和跨模块汇总信息。</span>
      </div>
      <div class="header-right">
        <el-tag v-if="keyword" type="primary" effect="plain">关键词：{{ keyword }}</el-tag>
        <el-button v-if="keyword" plain @click="clearSearch">清空搜索</el-button>
        <el-button type="primary" @click="$router.push('/home')">返回首页</el-button>
      </div>
    </div>

    <div v-if="!keyword" class="section-card">
      <div class="empty-title">从顶部搜索框输入关键词开始检索</div>
      <div class="empty-subtitle">推荐先试试这些高频关键词：</div>
      <div class="keyword-list">
        <button
          v-for="item in suggestionKeywords"
          :key="item"
          type="button"
          class="keyword-chip"
          @click="searchByKeyword(item)"
        >
          {{ item }}
        </button>
      </div>

      <div v-if="searchHistory.length" class="history-block">
        <div class="section-mini-title">最近搜索</div>
        <div class="keyword-list">
          <button
            v-for="item in searchHistory"
            :key="`history-${item}`"
            type="button"
            class="keyword-chip secondary"
            @click="searchByKeyword(item)"
          >
            {{ item }}
          </button>
        </div>
      </div>
    </div>

    <div v-else-if="!searchResult.total" class="section-card">
      <el-empty description="没有找到匹配结果，可以尝试换成学生姓名、学号、专业、年级或业务关键词。" />
      <div class="keyword-list empty-keywords">
        <button
          v-for="item in suggestionKeywords"
          :key="`empty-${item}`"
          type="button"
          class="keyword-chip"
          @click="searchByKeyword(item)"
        >
          {{ item }}
        </button>
      </div>
    </div>

    <template v-else>
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-number">{{ searchResult.total }}</div>
          <div class="stat-label">总结果数</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">{{ searchResult.modules.length }}</div>
          <div class="stat-label">功能入口</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">{{ searchResult.records.length }}</div>
          <div class="stat-label">业务记录</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">{{ searchResult.notices.length + searchResult.analysis.length }}</div>
          <div class="stat-label">通知与汇总</div>
        </div>
      </div>

      <div v-if="displayModules.length" class="section-card">
        <div class="section-header">
          <span class="section-title">功能入口</span>
          <span class="section-count">共 {{ searchResult.modules.length }} 条</span>
        </div>

        <div class="module-grid">
          <div v-for="item in displayModules" :key="item.route" class="module-card">
            <div class="module-top">
              <span class="module-title">{{ item.title }}</span>
              <span class="module-tag">{{ item.kindLabel }}</span>
            </div>
            <div class="module-summary">{{ item.summary }}</div>
            <div class="module-meta">{{ item.meta }}</div>
            <div class="tag-list">
              <span v-for="tag in item.tags.slice(0, 3)" :key="`${item.route}-${tag}`" class="mini-tag">{{ tag }}</span>
            </div>
            <div class="module-actions">
              <el-button type="primary" plain size="small" @click="openResult(item)">
                {{ item.actionLabel }}
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <div v-if="displayRecords.length" class="section-card">
        <div class="section-header">
          <span class="section-title">业务记录</span>
          <span class="section-count">
            共 {{ searchResult.records.length }} 条
            <template v-if="searchResult.records.length > displayRecords.length">，当前展示前 {{ displayRecords.length }} 条</template>
          </span>
        </div>

        <div class="result-list">
          <div v-for="item in displayRecords" :key="`${item.route}-${item.title}-${item.meta}`" class="result-card">
            <div class="result-top">
              <div>
                <div class="result-title">{{ item.title }}</div>
                <div class="result-summary">{{ item.summary }}</div>
              </div>
              <el-tag type="info" effect="plain" size="small">{{ item.moduleName }}</el-tag>
            </div>
            <div class="result-footer">
              <div class="result-meta">{{ item.meta }}</div>
              <div class="result-actions">
                <el-tag v-if="item.statusText" :type="item.statusType || 'info'" size="small">{{ item.statusText }}</el-tag>
                <el-button link type="primary" @click="openResult(item)">{{ item.actionLabel }}</el-button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="displayNotices.length" class="section-card">
        <div class="section-header">
          <span class="section-title">通知与待办</span>
          <span class="section-count">
            共 {{ searchResult.notices.length }} 条
            <template v-if="searchResult.notices.length > displayNotices.length">，当前展示前 {{ displayNotices.length }} 条</template>
          </span>
        </div>

        <div class="result-list">
          <div v-for="item in displayNotices" :key="`${item.route}-${item.title}-${item.meta}`" class="result-card compact">
            <div class="result-top">
              <div>
                <div class="result-title">{{ item.title }}</div>
                <div class="result-summary">{{ item.summary }}</div>
              </div>
              <el-tag type="warning" effect="plain" size="small">{{ item.kindLabel }}</el-tag>
            </div>
            <div class="result-footer">
              <div class="result-meta">{{ item.meta }}</div>
              <div class="result-actions">
                <el-button link type="primary" @click="openResult(item)">{{ item.actionLabel }}</el-button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="displayAnalysis.length" class="section-card">
        <div class="section-header">
          <span class="section-title">跨模块汇总</span>
          <span class="section-count">
            共 {{ searchResult.analysis.length }} 条
            <template v-if="searchResult.analysis.length > displayAnalysis.length">，当前展示前 {{ displayAnalysis.length }} 条</template>
          </span>
        </div>

        <div class="result-list">
          <div v-for="item in displayAnalysis" :key="`${item.route}-${item.title}-${item.summary}`" class="result-card">
            <div class="result-top">
              <div>
                <div class="result-title">{{ item.title }}</div>
                <div class="result-summary">{{ item.summary }}</div>
              </div>
              <el-tag type="primary" effect="plain" size="small">{{ item.moduleName }}</el-tag>
            </div>
            <div class="result-footer">
              <div class="result-meta">{{ item.meta }}</div>
              <div class="result-actions">
                <el-tag v-if="item.statusText" :type="item.statusType || 'info'" size="small">{{ item.statusText }}</el-tag>
                <el-button link type="primary" @click="openResult(item)">{{ item.actionLabel }}</el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import {
  DEFAULT_SEARCH_KEYWORDS,
  getSearchHistory,
} from '../utils/searchEngine'
import { getGlobalSearchResults } from '../services/mockDataService'

const SECTION_LIMITS = {
  modules: 8,
  records: 12,
  notices: 8,
  analysis: 12,
}

export default {
  name: 'SearchResults',
  data() {
    return {
      searchHistory: [],
      searchResult: {
        keyword: '',
        total: 0,
        modules: [],
        records: [],
        notices: [],
        analysis: [],
        flatResults: [],
      },
    }
  },
  watch: {
    '$route.query.q': {
      immediate: true,
      handler() {
        this.refreshSearchHistory()
        this.fetchSearchResult()
      },
    },
  },
  computed: {
    keyword() {
      return String(this.$route.query.q || '').trim()
    },
    suggestionKeywords() {
      return DEFAULT_SEARCH_KEYWORDS
    },
    displayModules() {
      return this.searchResult.modules.slice(0, SECTION_LIMITS.modules)
    },
    displayRecords() {
      return this.searchResult.records.slice(0, SECTION_LIMITS.records)
    },
    displayNotices() {
      return this.searchResult.notices.slice(0, SECTION_LIMITS.notices)
    },
    displayAnalysis() {
      return this.searchResult.analysis.slice(0, SECTION_LIMITS.analysis)
    },
  },
  mounted() {
    this.refreshSearchHistory()
  },
  methods: {
    async fetchSearchResult() {
      if (!this.keyword) {
        this.searchResult = {
          keyword: '',
          total: 0,
          modules: [],
          records: [],
          notices: [],
          analysis: [],
          flatResults: [],
        }
        return
      }

      this.searchResult = await getGlobalSearchResults(this.keyword)
    },
    refreshSearchHistory() {
      this.searchHistory = getSearchHistory()
    },
    clearSearch() {
      this.$router.push({ path: '/search' })
    },
    searchByKeyword(keyword) {
      this.$router.push({
        path: '/search',
        query: { q: keyword },
      })
    },
    openResult(item) {
      this.$router.push({
        path: item.route,
        query: item.routeQuery || {},
      })
    },
  },
}
</script>

<style scoped>
.search-results-page {
  color: #333;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  background: #fff;
  border-radius: 8px;
  padding: 16px 20px;
  gap: 16px;
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: 12px;
  flex-wrap: wrap;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.page-subtitle {
  font-size: 13px;
  color: #86909c;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.section-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: #1d2939;
}

.empty-subtitle {
  margin-top: 8px;
  font-size: 13px;
  color: #667085;
}

.history-block {
  margin-top: 18px;
}

.section-mini-title {
  font-size: 13px;
  color: #667085;
  margin-bottom: 10px;
}

.keyword-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
}

.keyword-chip {
  border: 1px solid #d0d5dd;
  background: #f8fafc;
  color: #344054;
  border-radius: 999px;
  padding: 7px 14px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.keyword-chip:hover {
  border-color: #bfd4ff;
  background: #eef4ff;
  color: #165dff;
}

.keyword-chip.secondary {
  background: #fff;
}

.empty-keywords {
  justify-content: center;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 18px 20px;
}

.stat-number {
  font-size: 28px;
  font-weight: 700;
  color: #0a2463;
}

.stat-label {
  margin-top: 6px;
  font-size: 13px;
  color: #667085;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1d2939;
}

.section-count {
  font-size: 12px;
  color: #86909c;
}

.module-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.module-card,
.result-card {
  border: 1px solid #eaecf0;
  border-radius: 12px;
  padding: 16px;
}

.module-top,
.result-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.module-title,
.result-title {
  font-size: 15px;
  font-weight: 600;
  color: #101828;
}

.module-tag {
  flex-shrink: 0;
  font-size: 11px;
  color: #165dff;
  background: #eef4ff;
  border-radius: 999px;
  padding: 3px 8px;
}

.module-summary,
.result-summary {
  margin-top: 8px;
  font-size: 13px;
  color: #475467;
  line-height: 1.6;
}

.module-meta,
.result-meta {
  margin-top: 10px;
  font-size: 12px;
  color: #98a2b3;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.mini-tag {
  font-size: 11px;
  color: #344054;
  background: #f2f4f7;
  border-radius: 999px;
  padding: 3px 8px;
}

.module-actions {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-footer {
  margin-top: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.result-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

@media (max-width: 1200px) {
  .stats-grid,
  .module-grid {
    grid-template-columns: 1fr 1fr;
  }

  .page-header,
  .section-header,
  .result-footer {
    flex-direction: column;
    align-items: flex-start;
  }

  .result-actions {
    flex-wrap: wrap;
  }
}

@media (max-width: 768px) {
  .stats-grid,
  .module-grid {
    grid-template-columns: 1fr;
  }

  .page-header {
    padding: 16px;
  }
}
</style>
