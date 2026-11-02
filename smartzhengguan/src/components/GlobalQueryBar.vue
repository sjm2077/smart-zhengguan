<template>
  <div class="section-card global-query-card">
    <div class="filter-row">
      <div class="filter-items">
        <div class="query-intro">
          <div class="query-title">跨模块查询</div>
          <div class="query-subtitle">只选年级看该年级全部专业，只选专业看该专业跨年级对比</div>
        </div>
        <el-select v-model="filters.grade" placeholder="选择年级" clearable>
          <el-option v-for="item in gradeOptions" :key="item" :label="item" :value="item" />
        </el-select>
        <el-select v-model="filters.major" placeholder="选择专业" clearable>
          <el-option v-for="item in majorOptions" :key="item" :label="item" :value="item" />
        </el-select>
      </div>
      <div class="filter-actions">
        <el-button @click="resetFilters">重置</el-button>
        <el-button type="primary" class="query-btn" @click="submitQuery">查询汇总</el-button>
      </div>
    </div>
    <div class="filter-meta">
      <span class="summary-text">{{ metaText }}</span>
      <span class="update-time">结果页会自动切换为“年级内专业画像”或“专业跨年级对比”</span>
    </div>
  </div>
</template>

<script>
import { gradeOptions, majorOptions, getQueryPlaceholderText, normalizeQueryFilters } from '../utils/queryData'
import { getSharedOptions } from '../services/mockDataService'

export default {
  data() {
    return {
      gradeOptions: [...gradeOptions],
      majorOptions: [...majorOptions],
      filters: {
        grade: '',
        major: '',
      },
    }
  },
  computed: {
    metaText() {
      return `当前条件：${getQueryPlaceholderText(this.filters)}`
    },
  },
  watch: {
    '$route.query': {
      immediate: true,
      deep: true,
      handler() {
        this.syncFromRoute()
      },
    },
  },
  mounted() {
    this.fetchOptions()
  },
  methods: {
    async fetchOptions() {
      const response = await getSharedOptions()
      if (Array.isArray(response?.grades) && response.grades.length) {
        this.gradeOptions = response.grades
      }
      if (Array.isArray(response?.majors) && response.majors.length) {
        this.majorOptions = response.majors
      }
    },
    syncFromRoute() {
      const query = normalizeQueryFilters(this.$route.query)
      this.filters = {
        grade: query.grade,
        major: query.major,
      }
    },
    buildQuery() {
      const query = {}
      if (this.filters.grade) query.grade = this.filters.grade
      if (this.filters.major) query.major = this.filters.major
      return query
    },
    submitQuery() {
      if (!this.filters.grade && !this.filters.major) {
        this.$message.warning('请至少选择一个筛选条件')
        return
      }

      this.$router.push({
        path: '/query-results',
        query: this.buildQuery(),
      })
    },
    resetFilters() {
      this.filters = {
        grade: '',
        major: '',
      }

      if (this.$route.path === '/query-results') {
        this.$router.push({ path: '/query-results' })
      }
    },
  },
}
</script>

<style scoped>
.global-query-card {
  margin-bottom: 16px;
  padding: 16px 20px;
}

.filter-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.filter-items {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  min-width: 0;
}

.query-intro {
  min-width: 280px;
  margin-right: 8px;
}

.query-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  line-height: 1.2;
}

.query-subtitle {
  font-size: 13px;
  color: #667085;
  margin-top: 4px;
  line-height: 1.5;
}

.filter-items :deep(.el-select) {
  width: 180px;
}

.filter-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.query-btn {
  background: #0A2463 !important;
  border-color: #0A2463 !important;
}

.filter-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-top: 14px;
  color: #667085;
  font-size: 13px;
  flex-wrap: wrap;
}

.summary-text {
  color: #344054;
}

.update-time {
  color: #667085;
}

@media (max-width: 1200px) {
  .query-intro {
    min-width: 100%;
    margin-right: 0;
  }
}

@media (max-width: 768px) {
  .filter-row,
  .filter-meta {
    flex-direction: column;
    align-items: flex-start;
  }

  .filter-items {
    width: 100%;
  }

  .filter-items :deep(.el-select) {
    width: 100%;
  }

  .filter-actions {
    width: 100%;
  }
}
</style>
