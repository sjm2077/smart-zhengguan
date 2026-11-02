<template>
  <div class="intelligent-page" v-loading="pageLoading" element-loading-text="正在加载预测数据…">
    <div class="filter-bar section-card">
      <div class="filter-header">
        <div class="brand-wrap">
          <div class="brand-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 3v4" />
              <path d="M12 17v4" />
              <path d="M4.93 4.93l2.83 2.83" />
              <path d="M16.24 16.24l2.83 2.83" />
              <path d="M3 12h4" />
              <path d="M17 12h4" />
              <path d="M4.93 19.07l2.83-2.83" />
              <path d="M16.24 7.76l2.83-2.83" />
              <circle cx="12" cy="12" r="4" />
            </svg>
          </div>
          <div>
            <div class="brand-title">{{ pageTitle }}</div>
            <div class="brand-caption">
              <span>{{ pageSubtitle }}</span>
              <el-tag size="small" effect="plain" type="primary">{{ businessScope.audience }}</el-tag>
            </div>
          </div>
        </div>
      </div>

      <div class="filter-toolbar">
        <div class="filter-items">
          <div class="filter-item filter-item-scope">
            <span class="filter-label">业务范围：</span>
            <div class="scope-badges">
              <span class="scope-badge">{{ businessScope.university }}</span>
              <span class="scope-badge scope-badge-strong">{{ businessScope.college }}</span>
            </div>
          </div>

          <div class="filter-item">
            <span class="filter-label">专业：</span>
            <el-select v-model="filters.major" class="filter-select">
              <el-option
                v-for="item in majorOptions"
                :key="item"
                :label="item"
                :value="item"
              />
            </el-select>
          </div>
          <div class="filter-item">
            <span class="filter-label">年级：</span>
            <el-select v-model="filters.grade" class="filter-select">
              <el-option
                v-for="item in gradeOptions"
                :key="item"
                :label="item"
                :value="item"
              />
            </el-select>
          </div>
          <div class="filter-item">
            <span class="filter-label">时间范围：</span>
            <el-select v-model="filters.range" class="filter-select">
              <el-option
                v-for="item in rangeOptions"
                :key="item"
                :label="item"
                :value="item"
              />
            </el-select>
          </div>
          <div class="filter-item">
            <span class="filter-label">风险类型：</span>
            <el-select v-model="filters.riskType" class="filter-select">
              <el-option
                v-for="item in riskTypeOptions"
                :key="item"
                :label="item"
                :value="item"
              />
            </el-select>
          </div>
        </div>

        <div class="filter-actions">
          <el-button type="primary" :loading="pageLoading" @click="handleRefresh">刷新分析</el-button>
          <el-button type="success" @click="handleExport">导出报告</el-button>
        </div>
      </div>
    </div>

    <el-alert
      v-if="pageLoadError"
      type="error"
      :closable="false"
      show-icon
      class="page-alert"
      :title="pageLoadError"
    />

    <div class="section-heading">学生发展趋势分析</div>
    <div class="top-grid">
      <div class="section-card chart-shell trend-card">
        <div class="card-head">
          <div class="card-title">学生发展趋势预测</div>
          <div class="card-subtitle">
            结合学院研究生发展指数，观察历史、预测与同年级平均变化趋势。
          </div>
        </div>
        <ChartCard :chart-options="trendChartOptions" chart-height="100%" />
      </div>

      <div class="section-card chart-shell radar-card">
        <div class="card-head card-head-inline">
          <div>
            <div class="card-title">学生综合发展雷达图</div>
            <div class="card-subtitle">
              从课程、科研、活动、导师评价等维度评估学院研究生综合状态。
            </div>
          </div>
          <el-radio-group v-model="radarMode" size="small">
            <el-radio-button label="student">单个学生</el-radio-button>
            <el-radio-button label="major">某个专业</el-radio-button>
            <el-radio-button label="grade">某一级</el-radio-button>
          </el-radio-group>
        </div>
        <div class="radar-filter-panel">
          <div class="radar-filter-grid">
            <el-select v-model="radarFilters.degreeType" placeholder="选择类别">
              <el-option
                v-for="item in radarDegreeOptions"
                :key="item"
                :label="item"
                :value="item"
              />
            </el-select>
            <el-select
              v-model="radarFilters.grade"
              placeholder="选择年级"
              :disabled="!radarFilters.degreeType"
            >
              <el-option
                v-for="item in radarGradeOptions"
                :key="item"
                :label="item"
                :value="item"
              />
            </el-select>
            <el-select
              v-model="radarFilters.major"
              placeholder="选择专业"
              :disabled="!radarFilters.grade || radarMode === 'grade'"
            >
              <el-option
                v-for="item in radarMajorOptions"
                :key="item"
                :label="item"
                :value="item"
              />
            </el-select>
            <el-select
              v-model="radarFilters.name"
              placeholder="选择姓名"
              filterable
              :disabled="!radarFilters.major || radarMode !== 'student'"
            >
              <el-option
                v-for="item in radarNameOptions"
                :key="item.id"
                :label="item.name"
                :value="item.id"
              />
            </el-select>
            <el-button type="primary" :disabled="!radarCanApply" @click="applyRadarFilters">
              查看雷达图
            </el-button>
          </div>
          <div class="radar-filter-hint">{{ radarFilterHint }}</div>
        </div>

        <div class="radar-chart-block">
          <div v-if="radarAppliedMeta" class="radar-summary">
            <span class="radar-summary-badge" :style="{ backgroundColor: radarAppliedMeta.color }">
              {{ radarAppliedMeta.label }}
            </span>
            <span class="radar-summary-text">{{ radarAppliedMeta.scope }}</span>
            <span class="radar-summary-text">样本数：{{ radarAppliedMeta.count }}</span>
          </div>
          <div v-else class="radar-summary radar-summary-placeholder">
            <span class="radar-summary-text">当前为默认空白雷达图，完成筛选后显示对应结果</span>
          </div>
          <ChartCard :chart-options="radarChartOptions" chart-height="100%" />
        </div>
      </div>
    </div>

    <div class="analysis-workspace">
        <aside class="target-filter-panel">
          <div class="target-filter-head">
            <div class="subcard-title">选择预测对象</div>
            <div class="target-filter-count">当前可选 {{ forecastNameOptions.length }} 人</div>
          </div>
          <div class="target-filter-grid">
            <label class="target-field"><span>学位类型</span><el-select v-model="forecastFilters.degreeType" placeholder="选择学位">
              <el-option
                v-for="item in forecastDegreeOptions"
                :key="item"
                :label="item"
                :value="item"
              />
            </el-select></label>
            <label class="target-field"><span>年级</span><el-select v-model="forecastFilters.grade" placeholder="选择年级">
              <el-option
                v-for="item in forecastGradeOptions"
                :key="item"
                :label="item"
                :value="item"
              />
            </el-select></label>
            <label class="target-field"><span>专业</span><el-select v-model="forecastFilters.major" placeholder="选择专业">
              <el-option
                v-for="item in forecastMajorOptions"
                :key="item"
                :label="item"
                :value="item"
              />
            </el-select></label>
            <label class="target-field"><span>姓名</span><el-select v-model="forecastFilters.name" placeholder="选择姓名" filterable>
              <el-option
                v-for="item in forecastNameOptions"
                :key="item.id"
                :label="item.name"
                :value="item.id"
              >
                <span>{{ item.name }}</span>
              </el-option>
            </el-select></label>
            <el-button type="primary" :disabled="!forecastFilters.name" @click="applyTargetFilters">确定并分析</el-button>
          </div>
          <div class="selected-target-card" v-if="hasCurrentTarget">
            <div class="selected-target-label">当前分析对象</div>
            <strong>{{ currentTarget.name }}</strong>
            <span>{{ currentTarget.degreeType }} · {{ currentTarget.grade }}</span>
            <span>{{ currentTarget.major }}</span>
            <span class="selected-target-label">学号 {{ currentTarget.studentId }}</span>
            <el-tag size="small" :type="currentTarget.riskType">{{ currentTarget.riskLevel }}</el-tag>
          </div>
          <p class="target-selection-help">确认对象后，右侧解读、AI对话和下方趋势预测同步切换。也可点击风险指标名称，从明细中选择学生。</p>
        </aside>
      <div class="analysis-workspace-main">
    <div class="section-heading">风险预警与治理</div>
    <div class="governance-scope">
      统计范围：{{ filters.grade || '全部年级' }} · {{ filters.major || '全部专业' }} · {{ filters.riskType || '全部' }}风险类型，
      共 {{ governanceStudents.length }} 名导入样本（当前快照，不含自动推算样本）。
    </div>
    <div class="risk-grid">
      <div class="gauge-grid">
        <div v-for="gauge in gauges" :key="gauge.key" class="section-card gauge-card"
          :style="{ '--gauge-accent': gauge.color }"
          >
          <button type="button" class="card-title gauge-title" :aria-label="`${gauge.title}，查看学生明细`"
            @click="openGovernanceDetails(gauge.key)">{{ gauge.title }}</button>
          <ChartCard :chart-options="buildGaugeOptions(gauge)" chart-height="148px" />
          <div class="governance-count">{{ gauge.status }}</div>
          <div class="governance-rule">{{ gauge.rule }}</div>
        </div>
      </div>

      <div class="section-card ai-card">
        <div class="card-head card-head-inline">
          <div>
            <div class="card-title">AI 智能解读与治理建议</div>
            <div class="insight-target" v-if="hasCurrentTarget">
              正在解读：{{ currentTarget.name }} · {{ currentTarget.grade }} · {{ currentTarget.major }}
            </div>
            <div class="card-subtitle">
              从明细中选择学生，联动查看趋势、风险与治理建议。
            </div>
            <div class="trace-row">
              <el-tag size="small" effect="plain" :type="capabilityTagType">{{ analysisTraceLabel }}</el-tag>
              <span class="trace-text">当前模式：{{ capabilityDescription }}</span>
            </div>
          </div>
          <div class="tab-strip">
            <el-button type="primary" plain :disabled="!hasCurrentTarget" @click="handleDeepAnalysis">查看完整解读</el-button>
            <button
              v-for="item in insightTabs"
              :key="item.value"
              type="button"
              class="tab-btn"
              :class="{ active: insightTab === item.value }"
              @click="insightTab = item.value"
            >
              {{ item.label }}
            </button>
          </div>
        </div>

        <div class="ai-layout">
          <div class="ai-content">
            <div v-if="insightAnalysisLoading" class="insight-block insight-loading">
              正在生成当前对象的分析解读...
            </div>
            <div v-else-if="insightAnalysisError" class="insight-block insight-error">
              {{ insightAnalysisError }}
            </div>
            <div v-else-if="!activeInsightSections.length" class="insight-block insight-empty">
              当前没有可展示的分析内容，请先检查预测对象和分析接口状态。
            </div>
            <div v-for="section in activeInsightSections" :key="section.title" class="insight-block">
              <div class="insight-title">{{ section.title }}</div>
              <div class="insight-body">{{ section.content }}</div>
            </div>
          </div>

          <div class="assistant-panel">
            <div class="assistant-header">
              <div class="assistant-figure">
                <svg viewBox="0 0 120 120" fill="none">
                  <circle cx="60" cy="60" r="48" fill="#EEF4FF" />
                  <rect x="32" y="34" width="56" height="40" rx="18" fill="#165DFF" />
                  <rect x="38" y="40" width="44" height="24" rx="12" fill="#0A2463" />
                  <circle cx="50" cy="52" r="5" fill="#6FD6FF" />
                  <circle cx="70" cy="52" r="5" fill="#6FD6FF" />
                  <path
                    d="M48 65c4 3 20 3 24 0"
                    stroke="#ffffff"
                    stroke-width="4"
                    stroke-linecap="round"
                  />
                  <path d="M44 28l6 10" stroke="#98A2B3" stroke-width="4" stroke-linecap="round" />
                  <path d="M76 28l-6 10" stroke="#98A2B3" stroke-width="4" stroke-linecap="round" />
                  <path d="M60 74v18" stroke="#165DFF" stroke-width="5" stroke-linecap="round" />
                  <path d="M44 90h32" stroke="#165DFF" stroke-width="5" stroke-linecap="round" />
                </svg>
              </div>
              <div class="assistant-name">AI 助手</div>
              <div class="assistant-desc">个人问题分析当前对象；群体问题比较全院实测学生</div>
            </div>

            <div ref="assistantChatRef" class="assistant-chat" @scroll="handleChatScroll">
              <div
                v-for="message in chatMessages"
                :key="message.id"
                class="chat-bubble"
                :class="message.role"
              >
                <template v-if="message.text">{{ message.text }}</template>
                <span v-else-if="message.streaming" class="chat-thinking-hint">
                  {{ chatProgress || '正在分析…' }}
                </span>
                <span v-if="message.streaming && message.text" class="chat-caret">▌</span>
              </div>
            </div>

            <div v-if="chatSubmitting && chatProgress" class="assistant-progress">
              <span class="assistant-progress-text">{{ chatProgress }}</span>
              <span
                v-for="(item, index) in chatProgressTools"
                :key="`${item.tool}-${index}`"
                class="assistant-progress-chip"
                :class="{ 'is-done': item.ok === true, 'is-failed': item.ok === false }"
              >
                {{ item.label }}<template v-if="item.hitCount != null">（{{ item.hitCount }}）</template>
              </span>
            </div>

            <div class="assistant-input-box">
              <el-input
                v-model.trim="chatInput"
                type="textarea"
                :rows="3"
                :disabled="chatSubmitting"
                resize="none"
                placeholder="您可以继续提问，例如：哪些学生需要优先干预？"
                @keydown.ctrl.enter.prevent="submitQuestion"
              />
              <div class="assistant-actions">
                <span class="assistant-tip">按 `Ctrl + Enter` 可快速发送</span>
                <el-button type="primary" @click="submitQuestion">发送</el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="bottom-grid">
      <div class="section-card forecast-card">
        <div class="card-head card-head-inline">
          <div>
            <div class="card-title">学生趋势预测与情景对比</div>
            <div class="card-subtitle">
              {{ currentTarget.name || '当前对象' }} · 查看未来3个月的指数变化、主要短板与跟进建议。
            </div>
          </div>
          <div class="tab-strip">
            <button
              v-for="item in forecastTabs"
              :key="item.value"
              type="button"
              class="tab-btn"
              :class="{ active: forecastTab === item.value }"
              @click="forecastTab = item.value"
            >
              {{ item.label }}
            </button>
          </div>
        </div>

        <div class="forecast-layout">
          <div class="forecast-left">
            <div class="forecast-method-note">{{ forecastMethodDescription }} 参考上界用于展示变化范围，不是统计置信区间。</div>
            <ChartCard :chart-options="forecastChartOptions" chart-height="270px" />
          </div>

          <div class="forecast-right">
            <div class="plain-subcard factor-card">
              <div class="subcard-title">关键影响因素（Top5）</div>
              <div class="factor-list">
                <div
                  v-for="(item, index) in currentTargetFactors"
                  :key="item.label"
                  class="factor-item"
                  :class="{ 'factor-item-placeholder': item.isPlaceholder }"
                >
                  <span class="factor-name"><span class="factor-rank">{{ index + 1 }}</span>{{ item.label }}</span>
                  <span class="factor-value">{{ item.value }}</span>
                </div>
              </div>
            </div>

          </div>
        </div>
        <div class="prediction-conclusions">
          <div class="conclusion-header">
            <div>
              <div class="subcard-title">预测结论与跟进建议</div>
              <p class="conclusion-caption">{{ currentTarget.name || '当前对象' }} · 结合近期表现，明确下一步跟进方向</p>
            </div>
            <el-button type="primary" :disabled="!hasCurrentTarget" @click="handleDeepAnalysis">查看完整解读 →</el-button>
          </div>
          <div class="prediction-conclusion-grid">
            <section v-for="(section, index) in forecastConclusionSections" :key="section.title" class="prediction-conclusion-section">
              <h4><span class="conclusion-index">0{{ index + 1 }}</span>{{ section.title }}</h4>
              <p>{{ section.content }}</p>
            </section>
          </div>
        </div>
      </div>

    </div>

      </div>
    </div>

    <el-dialog v-model="riskDialogVisible" :title="`${activeGovernanceGauge?.title || '风险'} · 学生明细`" width="1120px" class="governance-dialog">
      <div class="governance-dialog-toolbar">
        <div>
          <div>{{ filters.grade }} · {{ filters.major }} · 共 {{ governanceDetailStudents.length }} 人</div>
          <div class="governance-rule">{{ activeGovernanceGauge?.rule }}</div>
        </div>
        <el-input v-model="governanceSearch" clearable placeholder="搜索姓名或学号" style="width: 240px" @input="governancePage = 1" />
      </div>
      <el-table :data="pagedGovernanceStudents" stripe height="420" size="small" class="compact-table" empty-text="当前范围内没有符合条件的学生">
        <el-table-column prop="name" label="姓名" width="100" fixed="left" />
        <el-table-column prop="studentId" label="学号" width="120" />
        <el-table-column prop="grade" label="年级" width="100" />
        <el-table-column prop="major" label="专业" min-width="130" />
        <el-table-column prop="degreeType" label="学位类型" width="110" />
        <el-table-column v-if="governanceDetailKey === 'overdue'" prop="currentSnapshot.overdueTasksCount" label="任务逾期次数" width="115" sortable />
        <el-table-column v-if="governanceDetailKey === 'training'" label="培养节点" width="115">
          <template #default><el-tag type="warning" size="small">尚未完成</el-tag></template>
        </el-table-column>
        <el-table-column v-if="governanceDetailKey === 'communication'" prop="currentSnapshot.advisorMeetingCount60d" label="导师沟通次数" width="115" sortable />
        <el-table-column prop="currentSnapshot.courseAverage" label="课程成绩" width="90" />
        <el-table-column prop="riskScore" label="风险分" width="90" />
        <el-table-column prop="riskLevel" label="风险等级" width="100">
          <template #default="{ row }">
            <el-tag :type="row.riskType" size="small">{{ row.riskLevel }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="riskField" label="主要风险领域" min-width="150" />
        <el-table-column prop="suggestion" label="建议动作" min-width="150" />
        <el-table-column label="操作" fixed="right" width="100">
          <template #default="{ row }"><el-button link type="primary" @click="analyzeGovernanceStudent(row)">查看分析</el-button></template>
        </el-table-column>
      </el-table>
      <el-pagination v-model:current-page="governancePage" :page-size="20" :total="governanceDetailStudents.length" layout="total, prev, pager, next" class="governance-pagination" />
    </el-dialog>

    <el-dialog v-model="detailDialogVisible" title="完整解读与学生详情" width="min(860px, 94vw)" class="interpretation-dialog">
      <div class="detail-grid">
        <div v-for="item in detailOverviewItems" :key="item.label" class="detail-item">
          <span class="detail-label">{{ item.label }}</span>
          <span class="detail-value">{{ item.value }}</span>
        </div>
      </div>

      <div class="detail-section">
        <div class="detail-section-title">AI 智能解读</div>
        <div v-if="insightAnalysisLoading" class="detail-section-body">正在生成当前对象的分析解读...</div>
        <div v-else-if="insightAnalysisError" class="detail-section-body">{{ insightAnalysisError }}</div>
        <div v-else-if="!activeInsightSections.length" class="detail-section-body">当前暂无解读内容，请先选择对象并分析。</div>
        <section v-for="section in activeInsightSections" :key="section.title" class="full-insight-section">
          <h4>{{ section.title }}</h4>
          <div class="detail-section-body">{{ section.content }}</div>
        </section>
      </div>

      <div class="detail-section">
        <div class="detail-section-title">预测结论与跟进建议</div>
        <section v-for="section in forecastConclusionSections" :key="section.title" class="full-insight-section">
          <h4>{{ section.title }}</h4>
          <div class="detail-section-body">{{ section.content }}</div>
        </section>
      </div>

      <div class="detail-section">
        <div class="detail-section-title">趋势与预测序列</div>
        <div class="detail-grid">
          <div v-for="item in detailTrendItems" :key="item.label" class="detail-item">
            <span class="detail-label">{{ item.label }}</span>
            <span class="detail-value">{{ item.value }}</span>
          </div>
        </div>
      </div>

      <div class="detail-section">
        <div class="detail-section-title">指标与预警</div>
        <div class="detail-grid">
          <div v-for="item in detailMetricItems" :key="item.label" class="detail-item">
            <span class="detail-label">{{ item.label }}</span>
            <span class="detail-value">{{ item.value }}</span>
          </div>
        </div>
      </div>

      <div class="detail-section">
        <div class="detail-section-title">关键影响因素</div>
        <div class="detail-section-body">{{ detailFactorsText }}</div>
      </div>

      <div class="detail-section">
        <div class="detail-section-title">AI预测结论</div>
        <div class="detail-section-body">{{ insightAnalysisData.summary || currentTarget.summary || '暂无摘要' }}</div>
      </div>

      <div class="detail-section">
        <div class="detail-section-title">当前模式</div>
        <div class="detail-section-body">
          分析来源：{{ analysisTraceLabel }}；对话来源：{{ chatTraceLabel }}；提供方：{{ providerDisplayName }}；接口：{{ apiStyleDisplayName }}；模型：{{ aiModelDisplay }}
        </div>
      </div>

      <div class="detail-section">
        <div class="detail-section-title">分析证据</div>
        <div v-if="currentInsightEvidence.length" class="detail-evidence-list">
          <div v-for="item in currentInsightEvidence" :key="`${item.label || item.title}-${item.value || item.snippet}`" class="detail-evidence-item">
            <div class="detail-evidence-title">{{ item.label || item.title }}</div>
            <div class="detail-evidence-body">{{ item.value || item.snippet }}</div>
          </div>
        </div>
        <div v-else class="detail-section-body">当前分析接口未返回额外证据。</div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ElMessage } from 'element-plus'
import ChartCard from '../components/ChartCard.vue'
import { buildGovernanceGauges, isImportedPredictionStudent } from '../utils/riskGovernance'
import {
  getIntelligentPredictionAnalysis,
  getIntelligentPredictionChat,
  getIntelligentPredictionData,
  streamIntelligentPredictionChat,
} from '../services/mockDataService'

function uniqueValues(list, field) {
  return Array.from(new Set(list.map((item) => item[field])))
}

const DEFAULT_RADAR_INDICATORS = [
  { name: '学业投入与掌握', max: 100 },
  { name: '科研训练与创新', max: 100 },
  { name: '自我管理与学习策略', max: 100 },
  { name: '导师支持与学术互动', max: 100 },
  { name: '学术共同体融入', max: 100 },
  { name: '实践参与与公共服务', max: 100 },
  { name: '身心健康与持续发展', max: 100 },
]

const DEFAULT_BUSINESS_SCOPE = {
  university: '山东大学',
  college: '政治学与公共管理学院',
  audience: '山东大学政治学与公共管理学院研究生',
}

const EMPTY_PAGE_DATA = {
  businessScope: DEFAULT_BUSINESS_SCOPE,
  filters: {
    default: {
      college: DEFAULT_BUSINESS_SCOPE.college,
      major: '',
      grade: '',
      range: '',
      riskType: '',
    },
    colleges: [],
    majors: [],
    grades: [],
    ranges: [],
    riskTypes: [],
  },
  radarIndicators: [],
  students: [],
}

const EMPTY_TARGET = {
  id: '',
  studentId: '',
  name: '',
  degreeType: '',
  type: '',
  college: '',
  major: '',
  grade: '',
  advisorName: '',
  currentStatus: '',
  riskCategory: '',
  riskScore: 0,
  riskLevel: '',
  riskType: '',
  tagType: '',
  riskField: '',
  suggestion: '',
  aiConclusion: '',
  capturedAt: '',
  updatedAt: '',
  monthlyRecords: [],
  trendActual: [],
  trendForecast: [],
  peerTrend: [],
  trendPeer: [],
  radar: [],
  radarValues: [],
  historicalTrend: [],
  predictedTrend: [],
  peerAverageTrend: [],
  forecastTrend: [],
  forecastScenario: [],
  forecastUpperTrend: [],
  forecastUpperScenario: [],
  forecastTrendValues: [],
  scenarioValues: [],
  trendUpperBound: [],
  scenarioUpperBound: [],
  factors: [],
  keyFactors: [],
  keyFactorsText: '',
  historicalTrendText: '',
  predictedTrendText: '',
  peerAverageTrendText: '',
  radarValuesText: '',
  forecastTrendValuesText: '',
  scenarioValuesText: '',
  trendUpperBoundText: '',
  scenarioUpperBoundText: '',
  summary: '',
  period: '',
  graduationWarning: 0,
  trainingLag: 0,
  feedbackDelay: 0,
  riskRate: 0,
  gauges: { graduation: 0, training: 0, feedback: 0, risk: 0 },
}

const EMPTY_INSIGHT_ANALYSIS = {
  studentId: '',
  tab: 'trend',
  summary: '',
  sections: [],
  evidence: [],
  trace: null,
  promptPackage: null,
}

const RADAR_MODE_META = {
  student: {
    label: '个人雷达图',
    color: '#1677FF',
    areaColor: 'rgba(22,119,255,0.18)',
  },
  major: {
    label: '专业雷达图',
    color: '#12B76A',
    areaColor: 'rgba(18,183,106,0.18)',
  },
  grade: {
    label: '年级雷达图',
    color: '#F79009',
    areaColor: 'rgba(247,144,9,0.18)',
  },
}

const RADAR_ALL_DEGREE = '全部类别'

const FACTOR_CATEGORY_MAP = {
  学业投入与掌握: '学业风险',
  科研训练与创新: '科研风险',
  自我管理与学习策略: '培养风险',
  导师支持与学术互动: '支持风险',
  学术共同体融入: '培养风险',
  实践参与与公共服务: '培养风险',
  身心健康与持续发展: '支持风险',
}

const RISK_SUGGESTION_MAP = {
  学业风险: '补强课程学习投入并开展阶段学业督导',
  培养风险: '复核培养环节参与情况并制定阶段提升计划',
  科研风险: '跟进科研任务、项目参与与成果产出节奏',
  支持风险: '强化导师沟通、支持服务与身心关怀',
}

export default {
  components: { ChartCard },
  data() {
    return {
      pageData: EMPTY_PAGE_DATA,
      filters: {
        college: '',
        major: '',
        grade: '',
        range: '',
        riskType: '',
      },
      collegeOptions: [],
      majorOptions: [],
      gradeOptions: [],
      rangeOptions: [],
      riskTypeOptions: [],
      radarMode: 'student',
      radarFilters: {
        degreeType: RADAR_ALL_DEGREE,
        grade: '',
        major: '',
        name: '',
      },
      appliedRadarQuery: null,
      forecastTab: 'trend',
      insightTab: 'trend',
      selectedTargetId: '',
      forecastTabs: [
        { label: '趋势预测', value: 'trend' },
        { label: '保守情景', value: 'scenario' },
      ],
      insightTabs: [
        { label: '趋势解读', value: 'trend' },
        { label: '风险解读', value: 'risk' },
        { label: '治理建议', value: 'governance' },
      ],
      forecastFilters: {
        degreeType: '全部学位',
        grade: '全部年级',
        major: '全部专业',
        name: '',
      },
      aiRuntimeOptions: {
        experimentKey: 'default',
        preferredModel: '',
        apiStyle: '',
        thinkingType: '',
        reasoningEffort: '',
        temperature: '',
        useLlmWhenAvailable: true,
      },
      pageLoadError: '',
      pageLoading: false,
      insightAnalysisError: '',
      riskDialogVisible: false,
      governanceDetailKey: 'risk',
      governanceSearch: '',
      governancePage: 1,
      syncingForecastFilters: false,
      detailDialogVisible: false,
      chatInput: '',
      insightAnalysisLoading: false,
      insightAnalysisData: EMPTY_INSIGHT_ANALYSIS,
      lastChatTrace: null,
      chatSubmitting: false,
      // 流式问答的实时进度：Agent 要 10~40s，没有这个界面会像卡住
      chatProgress: '',
      chatProgressTools: [],
      // 思考增量的滚动预览，以及当前正在流式改写的那条消息
      chatThinking: '',
      streamingMessageId: '',
      chatStickToBottom: true,
      chatMessages: [
        {
          id: 'assistant-init',
          role: 'assistant',
          text: '您好，可以询问当前学生的情况，也可以提问“哪些学生需要优先干预？”来比较全院有数据快照的学生。',
        },
      ],
    }
  },
  computed: {
    studentPool() {
      return (this.pageData.students || []).map((student) => this.decorateStudent(student))
    },
    aiCapabilities() {
      return this.pageData.aiCapabilities || {
        llmEnabled: false,
        provider: '',
        apiStyle: '',
        model: '',
        chatMode: 'rule_based_rag',
        retrievalEnabled: false,
        debugEnabled: false,
        runtimeOptions: {},
        endpoints: {},
      }
    },
    providerDisplayName() {
      const provider = String(this.aiCapabilities.provider || '').trim().toLowerCase()
      if (!provider) return '未启用外部模型'
      if (provider === 'deepseek') return 'DeepSeek'
      if (provider === 'openai') return 'OpenAI'
      if (provider === 'aiohub') return 'AIOHub'
      return provider
    },
    defaultApiStyle() {
      if (this.aiCapabilities.apiStyle) return this.aiCapabilities.apiStyle
      if (String(this.aiCapabilities.provider || '').trim().toLowerCase() === 'deepseek') {
        return 'chat_completions'
      }
      return ''
    },
    defaultThinkingType() {
      const provider = String(this.aiCapabilities.provider || '').trim().toLowerCase()
      if (provider === 'deepseek' && this.aiCapabilities.llmEnabled) {
        return 'enabled'
      }
      return ''
    },
    apiStyleDisplayName() {
      const apiStyle = this.normalizedRuntimeOptions.apiStyle || this.defaultApiStyle
      if (apiStyle === 'chat_completions') return 'Chat Completions'
      if (apiStyle === 'responses') return 'Responses API'
      return apiStyle || '规则分析'
    },
    thinkingTypeDisplayName() {
      const thinkingType = this.normalizedRuntimeOptions.thinkingType || this.defaultThinkingType
      if (thinkingType === 'enabled') return '深度思考'
      if (thinkingType === 'disabled') return '关闭思考'
      return thinkingType || ''
    },
    aiModelDisplay() {
      if (!this.aiCapabilities.llmEnabled) return '未启用外部模型'
      const provider = this.providerDisplayName
      const model = this.aiCapabilities.model || '后端默认模型'
      return provider ? `${provider} / ${model}` : model
    },
    businessScope() {
      return {
        university: this.pageData.businessScope?.university || DEFAULT_BUSINESS_SCOPE.university,
        college: this.pageData.businessScope?.college || DEFAULT_BUSINESS_SCOPE.college,
        audience: this.pageData.businessScope?.audience || DEFAULT_BUSINESS_SCOPE.audience,
      }
    },
    pageTitle() {
      return `${this.businessScope.audience}智能分析与预测平台`
    },
    pageSubtitle() {
      return this.pageData.subtitle || '围绕学生发展趋势、风险预警与治理建议构建学院级研究生智能预测闭环。'
    },
    scopePlaceholderPrefix() {
      return `当前筛选条件下，${this.businessScope.audience}`
    },
    capabilityTagType() {
      return this.aiCapabilities.llmEnabled ? 'success' : 'warning'
    },
    capabilityLabel() {
      return this.aiCapabilities.llmEnabled ? `${this.providerDisplayName} 已接入` : '规则分析 + 知识检索'
    },
    capabilityDescription() {
      if (this.aiCapabilities.llmEnabled) {
        const modelLabel = this.aiCapabilities.model || '后端默认模型'
        const thinkingSuffix = this.thinkingTypeDisplayName ? `，思考模式为${this.thinkingTypeDisplayName}` : ''
        return `当前已启用 ${this.providerDisplayName} 模型推理（${modelLabel} / ${this.apiStyleDisplayName}）${thinkingSuffix}。`
      }
      return '当前未启用外部大模型，分析结果基于预测样本、规则推导和本地制度知识库生成。'
    },
    parsedTemperature() {
      if (this.aiRuntimeOptions.temperature === '') return null
      const numeric = Number(this.aiRuntimeOptions.temperature)
      return Number.isFinite(numeric) ? numeric : null
    },
    normalizedRuntimeOptions() {
      const runtimeOptions = {
        useLlmWhenAvailable: this.aiRuntimeOptions.useLlmWhenAvailable,
      }
      const preferredModel = String(this.aiRuntimeOptions.preferredModel || this.aiCapabilities.model || '').trim()
      const apiStyle = String(this.aiRuntimeOptions.apiStyle || this.defaultApiStyle || '').trim()
      const thinkingType = String(this.aiRuntimeOptions.thinkingType || this.defaultThinkingType || '').trim()
      const reasoningEffort = String(this.aiRuntimeOptions.reasoningEffort || '').trim()

      if (preferredModel) runtimeOptions.preferredModel = preferredModel
      if (apiStyle) runtimeOptions.apiStyle = apiStyle
      if (thinkingType) runtimeOptions.thinkingType = thinkingType
      if (reasoningEffort) runtimeOptions.reasoningEffort = reasoningEffort
      if (Number.isFinite(this.parsedTemperature)) runtimeOptions.temperature = this.parsedTemperature

      return runtimeOptions
    },
    aiRuntimeSummary() {
      const model = this.normalizedRuntimeOptions.preferredModel || '后端默认模型'
      const apiStyle = this.apiStyleDisplayName
      const thinking = this.thinkingTypeDisplayName || '后端默认思考模式'
      const reasoning = this.normalizedRuntimeOptions.reasoningEffort || '后端默认推理强度'
      const hasTemperature = Object.prototype.hasOwnProperty.call(this.normalizedRuntimeOptions, 'temperature')
      const temperature = hasTemperature ? this.normalizedRuntimeOptions.temperature : '后端默认温度'
      const mode = this.normalizedRuntimeOptions.useLlmWhenAvailable ? '可用时优先走外部模型' : '强制走规则分析 / 规则问答'
      return `当前配置：${mode}；模型=${model}；接口=${apiStyle}；思考模式=${thinking}；推理强度=${reasoning}；温度=${temperature}`
    },
    analysisTraceLabel() {
      const trace = this.insightAnalysisData.trace || {}
      const mode = trace.generationMode || ''
      if (mode === 'chat_completions') return 'AI 分析'
      if (mode === 'responses_api') return 'AI 分析'
      if (mode === 'fallback_after_llm_error') return '规则分析（模型异常后回退）'
      return '规则分析'
    },
    chatTraceLabel() {
      const trace = this.lastChatTrace || {}
      if (trace.generationMode === 'cohort_ranking') return '全院实测数据排序'
      if (trace.llmUsed) return 'AI 对话'
      if (trace.generationMode === 'fallback_after_llm_error') return '规则对话（模型异常后回退）'
      return '规则对话'
    },
    radarIndicators() {
      return this.pageData.radarIndicators?.length ? this.pageData.radarIndicators : DEFAULT_RADAR_INDICATORS
    },
    filteredStudents() {
      return this.studentPool.filter((student) => {
        const collegeMatch = !this.filters.college || student.college === this.filters.college
        const majorMatch = this.filters.major === '全部专业' || student.major === this.filters.major
        const gradeMatch = this.filters.grade === '全部年级' || student.grade === this.filters.grade
        const riskMatch = this.filters.riskType === '全部' || student.riskCategory === this.filters.riskType
        return collegeMatch && majorMatch && gradeMatch && riskMatch
      })
    },
    analysisStudents() {
      return this.filteredStudents
    },
    targetBaseStudents() {
      return this.filteredStudents.filter(isImportedPredictionStudent)
    },
    radarBaseStudents() {
      return this.studentPool
    },
    radarDegreeOptions() {
      return [RADAR_ALL_DEGREE, ...uniqueValues(this.radarBaseStudents, 'degreeType')]
    },
    radarStudentsByDegree() {
      if (!this.radarFilters.degreeType) return []
      if (this.radarFilters.degreeType === RADAR_ALL_DEGREE) return this.radarBaseStudents
      return this.radarBaseStudents.filter((student) => student.degreeType === this.radarFilters.degreeType)
    },
    radarGradeOptions() {
      return uniqueValues(this.radarStudentsByDegree, 'grade')
    },
    radarStudentsByGrade() {
      if (!this.radarFilters.degreeType || !this.radarFilters.grade) return []
      return this.radarStudentsByDegree.filter((student) => student.grade === this.radarFilters.grade)
    },
    radarMajorOptions() {
      return uniqueValues(this.radarStudentsByGrade, 'major')
    },
    radarStudentsByMajor() {
      if (!this.radarFilters.degreeType || !this.radarFilters.grade || !this.radarFilters.major) return []
      return this.radarStudentsByGrade.filter((student) => student.major === this.radarFilters.major)
    },
    radarNameOptions() {
      return this.radarStudentsByMajor
        .filter((student) => {
          // Imported summary rows use names such as 学生0624. These are
          // placeholders, not names suitable for individual selection.
          const name = String(student.name || '').trim()
          return name && !/^(?:学生\s*\d+|AUTO\d+|\d+)$/i.test(name)
            && name !== String(student.studentId || '').trim()
        })
        .map((student) => ({
          id: student.id,
          name: String(student.name).trim(),
        }))
    },
    radarCanApply() {
      if (!this.radarFilters.grade) return false
      if (this.radarMode === 'grade') return true
      if (!this.radarFilters.major) return false
      if (this.radarMode === 'major') return true
      return Boolean(this.radarFilters.name)
    },
    radarFilterHint() {
      if (this.radarMode === 'student') return '请先按类别（可选）、年级、专业、姓名完成筛选后再显示个人雷达图'
      if (this.radarMode === 'major') return '请先按类别（可选）、年级、专业完成筛选后再显示专业雷达图'
      return '请先按类别（可选）、年级完成筛选后再显示年级雷达图'
    },
    radarAppliedStudents() {
      return this.resolveRadarStudents(this.appliedRadarQuery)
    },
    radarAppliedMeta() {
      if (!this.appliedRadarQuery || !this.radarAppliedStudents.length) return null

      const modeMeta = RADAR_MODE_META[this.appliedRadarQuery.mode]
      const [firstStudent] = this.radarAppliedStudents

      if (this.appliedRadarQuery.mode === 'student') {
        return {
          ...modeMeta,
          name: firstStudent.name,
          scope: `${firstStudent.degreeType} / ${firstStudent.grade} / ${firstStudent.major}`,
          count: 1,
        }
      }

      if (this.appliedRadarQuery.mode === 'major') {
        const scope = this.appliedRadarQuery.degreeType === RADAR_ALL_DEGREE
          ? `${firstStudent.grade} / ${firstStudent.major}`
          : `${firstStudent.degreeType} / ${firstStudent.grade} / ${firstStudent.major}`
        return {
          ...modeMeta,
          name: `${firstStudent.major}平均`,
          scope,
          count: this.radarAppliedStudents.length,
        }
      }

      const scope = this.appliedRadarQuery.degreeType === RADAR_ALL_DEGREE
        ? firstStudent.grade
        : `${firstStudent.degreeType} / ${firstStudent.grade}`
      return {
        ...modeMeta,
        name: `${firstStudent.grade}平均`,
        scope,
        count: this.radarAppliedStudents.length,
      }
    },
    forecastDegreeOptions() {
      return ['全部学位', ...uniqueValues(this.targetBaseStudents, 'degreeType')]
    },
    targetStudentsByDegree() {
      if (this.forecastFilters.degreeType === '全部学位') return this.targetBaseStudents
      return this.targetBaseStudents.filter((student) => student.degreeType === this.forecastFilters.degreeType)
    },
    forecastGradeOptions() {
      return ['全部年级', ...uniqueValues(this.targetStudentsByDegree, 'grade')]
    },
    targetStudentsByGrade() {
      if (this.forecastFilters.grade === '全部年级') return this.targetStudentsByDegree
      return this.targetStudentsByDegree.filter((student) => student.grade === this.forecastFilters.grade)
    },
    forecastMajorOptions() {
      return ['全部专业', ...uniqueValues(this.targetStudentsByGrade, 'major')]
    },
    targetStudentsByMajor() {
      if (this.forecastFilters.major === '全部专业') return this.targetStudentsByGrade
      return this.targetStudentsByGrade.filter((student) => student.major === this.forecastFilters.major)
    },
    forecastNameOptions() {
      return this.targetStudentsByMajor.map((student) => ({
        id: student.id,
        name: student.name,
      }))
    },
    currentTarget() {
      return this.targetBaseStudents.find((item) => item.id === this.selectedTargetId) || this.targetBaseStudents[0] || EMPTY_TARGET
    },
    hasCurrentTarget() {
      return Boolean(this.currentTarget?.studentId)
    },
    rangeMonths() {
      if (this.filters.range === '近3个月') return 3
      if (this.filters.range === '近9个月') return 9
      return 6
    },
    monthLabels() {
      return this.sliceTail(this.currentTarget.monthlyRecords?.map((item) => item.month) || [], this.rangeMonths)
    },
    trendSeries() {
      const target = this.currentTarget
      return {
        actual: this.sliceTail(target.trendActual || [], this.rangeMonths),
        forecast: this.sliceTail(target.trendForecast || [], this.rangeMonths),
        peer: this.sliceTail(this.buildPeerTrendSeries(target), this.rangeMonths),
      }
    },
    hasTrendData() {
      if (!this.hasCurrentTarget || !this.monthLabels.length) return false
      return [this.trendSeries.actual, this.trendSeries.forecast, this.trendSeries.peer]
        .some((series) => Array.isArray(series) && series.some((value) => Number.isFinite(value)))
    },
    hasForecastData() {
      if (!this.hasCurrentTarget) return false
      const forecastSeries = [
        this.currentTarget.forecastTrend,
        this.currentTarget.forecastScenario,
        this.currentTarget.forecastUpperTrend,
        this.currentTarget.forecastUpperScenario,
      ]
      return forecastSeries.some((series) => Array.isArray(series) && series.some((value) => Number.isFinite(value)))
    },
    forecastMetaItems() {
      if (!this.hasCurrentTarget) {
        return [
          { label: '预测对象', value: '当前暂无可用研究生对象', isPlaceholder: true },
          { label: '学位类型', value: '待样本载入后自动识别', isPlaceholder: true },
          { label: '所属专业', value: '请调整专业或年级筛选条件', isPlaceholder: true },
          { label: '预测指标', value: '综合发展指数', isPlaceholder: false },
          { label: '预测周期', value: '未来 3 个月', isPlaceholder: false },
          { label: '业务范围', value: this.businessScope.college, isPlaceholder: false },
        ]
      }
      return [
        { label: '预测对象', value: this.currentTarget.name || '-', isPlaceholder: false },
        { label: '学位类型', value: this.currentTarget.degreeType || '-', isPlaceholder: false },
        { label: '所属专业', value: this.currentTarget.major || '-', isPlaceholder: false },
        { label: '预测指标', value: '综合发展指数', isPlaceholder: false },
        { label: '预测周期', value: this.currentTarget.period || '未来 3 个月', isPlaceholder: false },
        { label: '业务范围', value: this.businessScope.college, isPlaceholder: false },
      ]
    },
    currentTargetFactors() {
      if (Array.isArray(this.currentTarget.factors) && this.currentTarget.factors.length) {
        return this.currentTarget.factors.map((item) => ({ ...item, isPlaceholder: false }))
      }
      return [
        { label: '样本状态', value: '当前未锁定具体研究生对象', isPlaceholder: true },
        { label: '影响因子', value: '待筛选出可分析样本后自动计算', isPlaceholder: true },
        { label: '范围说明', value: `${this.businessScope.college}研究生专用预测模块`, isPlaceholder: true },
      ]
    },
    currentTargetSummary() {
      if (this.currentTarget.summary) return this.currentTarget.summary
      return `${this.scopePlaceholderPrefix}暂无可用于预测的研究生对象。系统已保留占位图表，待样本载入或调整筛选条件后自动更新。`
    },
    forecastMethodDescription() {
      return this.forecastTab === 'trend'
        ? '趋势预测：按最近4期指数的平均变化速度，估计未来3个月走势。'
        : '保守情景：将近期变化速度降至60%，观察上升或下降放缓后的走势；不表示实施了某项干预。'
    },
    forecastConclusionSections() {
      if (!this.hasCurrentTarget) return [{ title: '等待选择对象', content: '请先在左侧选择学生并确认，再查看完整预测与建议。' }]
      const target = this.currentTarget
      const series = this.forecastTab === 'trend' ? target.forecastTrend : target.forecastScenario
      const current = target.trendActual?.at(-1)
      const future = series?.at(-1)
      const hasValues = Number.isFinite(current) && Number.isFinite(future)
      const delta = hasValues ? Number((future - current).toFixed(1)) : null
      const peer = target.peerTrend?.at(-1)
      const factorNames = (target.factors || []).slice(0, 2).map((factor) => factor.label).join('、')
      return [
        { title: '三个月走势', content: hasValues
          ? `${target.name}当前综合发展指数为${current.toFixed(1)}分，${this.forecastTab === 'trend' ? '按近期趋势预测' : '在保守情景下'}，3个月后约为${future.toFixed(1)}分，${delta > 0 ? '上升' : delta < 0 ? '下降' : '变化'}${Math.abs(delta).toFixed(1)}分。结果是基于历史指标的估计。`
          : '当前缺少完整历史序列，暂不能估计三个月后的变化。' },
        { title: '当前风险与短板', content: `当前风险等级为“${target.riskLevel}”。${factorNames ? `指标短板主要集中在${factorNames}。` : ''}${target.riskField ? `需跟踪的领域包括${target.riskField}。` : ''}` },
        { title: '同年级对比', content: Number.isFinite(current) && Number.isFinite(peer)
          ? `最近一期同年级样本平均指数为${peer.toFixed(1)}分，当前学生${current > peer ? `高于该参考值${(current - peer).toFixed(1)}分` : current < peer ? `低于该参考值${(peer - current).toFixed(1)}分` : '与该参考值持平'}。可结合课程、科研与导师沟通记录持续观察变化。`
          : '当前没有可用于同年级比较的完整数据，可先结合个人历史变化进行观察。' },
        { title: '跟进建议', content: `${target.suggestion || '结合当前短板安排导师沟通与阶段复核。'}。建议明确待完成事项、责任人与复核时间，后续用新增记录检验变化。` },
      ]
    },
    detailOverviewItems() {
      if (!this.hasCurrentTarget) return []
      return [
        { label: '预测对象', value: this.currentTarget.name || '-' },
        { label: '样本编号', value: this.currentTarget.studentId || '-' },
        { label: '类别', value: this.currentTarget.degreeType || this.currentTarget.type || '-' },
        { label: '学院', value: this.currentTarget.college || '-' },
        { label: '专业', value: this.currentTarget.major || '-' },
        { label: '年级', value: this.currentTarget.grade || '-' },
        { label: '导师', value: this.currentTarget.advisorName || '-' },
        { label: '当前状态', value: this.currentTarget.currentStatus || '-' },
        { label: '风险类别', value: this.currentTarget.riskCategory || '-' },
        { label: '风险等级', value: this.currentTarget.riskLevel || '-' },
        { label: '标签类型', value: this.currentTarget.tagType || this.currentTarget.riskType || '-' },
        { label: '主要风险领域', value: this.currentTarget.riskField || '-' },
        { label: '建议动作', value: this.currentTarget.suggestion || '-' },
        { label: '预测周期', value: this.currentTarget.period || '未来 3 个月' },
      ]
    },
    detailTrendItems() {
      if (!this.hasCurrentTarget) return []
      const historicalTrend = Array.isArray(this.currentTarget.historicalTrend) && this.currentTarget.historicalTrend.length
        ? this.currentTarget.historicalTrend
        : this.currentTarget.trendActual
      const predictedTrend = Array.isArray(this.currentTarget.predictedTrend) && this.currentTarget.predictedTrend.length
        ? this.currentTarget.predictedTrend
        : this.currentTarget.trendForecast
      const peerTrend = Array.isArray(this.currentTarget.peerAverageTrend) && this.currentTarget.peerAverageTrend.length
        ? this.currentTarget.peerAverageTrend
        : Array.isArray(this.currentTarget.peerTrend) && this.currentTarget.peerTrend.length
          ? this.currentTarget.peerTrend
          : this.buildPeerTrendSeries(this.currentTarget)
      const forecastTrend = Array.isArray(this.currentTarget.forecastTrendValues) && this.currentTarget.forecastTrendValues.length
        ? this.currentTarget.forecastTrendValues
        : this.currentTarget.forecastTrend
      const forecastScenario = Array.isArray(this.currentTarget.scenarioValues) && this.currentTarget.scenarioValues.length
        ? this.currentTarget.scenarioValues
        : this.currentTarget.forecastScenario
      const trendUpperBound = Array.isArray(this.currentTarget.trendUpperBound) && this.currentTarget.trendUpperBound.length
        ? this.currentTarget.trendUpperBound
        : this.currentTarget.forecastUpperTrend
      const scenarioUpperBound = Array.isArray(this.currentTarget.scenarioUpperBound) && this.currentTarget.scenarioUpperBound.length
        ? this.currentTarget.scenarioUpperBound
        : this.currentTarget.forecastUpperScenario
      return [
        { label: '历史趋势', value: this.formatSeriesText(historicalTrend) },
        { label: '预测趋势', value: this.formatSeriesText(predictedTrend) },
        { label: '同年级均值', value: this.formatSeriesText(peerTrend) },
        { label: '预测趋势值', value: this.formatSeriesText(forecastTrend) },
        { label: '情景模拟值', value: this.formatSeriesText(forecastScenario) },
        { label: '趋势上界', value: this.formatSeriesText(trendUpperBound) },
        { label: '情景上界', value: this.formatSeriesText(scenarioUpperBound) },
      ]
    },
    detailMetricItems() {
      if (!this.hasCurrentTarget) return []
      const radarValues = Array.isArray(this.currentTarget.radarValues) && this.currentTarget.radarValues.length
        ? this.currentTarget.radarValues
        : this.currentTarget.radar
      return [
        { label: '雷达指标', value: this.formatSeriesText(radarValues) },
        { label: '毕业预警', value: this.formatMetricValue(this.currentTarget.graduationWarning, this.currentTarget.gauges?.graduation) },
        { label: '培养滞后', value: this.formatMetricValue(this.currentTarget.trainingLag, this.currentTarget.gauges?.training) },
        { label: '反馈延迟', value: this.formatMetricValue(this.currentTarget.feedbackDelay, this.currentTarget.gauges?.feedback) },
        { label: '风险占比', value: this.formatMetricValue(this.currentTarget.riskRate, this.currentTarget.gauges?.risk) },
      ]
    },
    detailFactorsText() {
      if (!this.hasCurrentTarget) return '暂无关键影响因素。'
      return this.currentTarget.keyFactorsText || this.formatFactorsText(this.currentTarget.factors) || '暂无关键影响因素。'
    },
    gauges() {
      return buildGovernanceGauges(this.governanceStudents)
    },
    governanceStudents() {
      return this.filteredStudents.filter(isImportedPredictionStudent)
    },
    activeGovernanceGauge() {
      return this.gauges.find((gauge) => gauge.key === this.governanceDetailKey)
    },
    governanceDetailStudents() {
      const query = this.governanceSearch.trim().toLowerCase()
      return (this.activeGovernanceGauge?.students || [])
        .filter((student) => !query || `${student.name} ${student.studentId}`.toLowerCase().includes(query))
        .slice().sort(this.compareRiskStudents)
    },
    pagedGovernanceStudents() {
      return this.governanceDetailStudents.slice((this.governancePage - 1) * 20, this.governancePage * 20)
    },
    radarChartOptions() {
      if (!this.radarAppliedMeta) {
        return {
          tooltip: { show: false },
          radar: {
            radius: '68%',
            splitNumber: 5,
            axisName: { color: '#98A2B3' },
            splitLine: { lineStyle: { color: '#E4E7EC' } },
            splitArea: { areaStyle: { color: ['#FCFCFD', '#F9FAFB'] } },
            axisLine: { lineStyle: { color: '#D0D5DD' } },
            indicator: this.radarIndicators,
          },
          graphic: [
            {
              type: 'text',
              left: 'center',
              top: '46%',
              style: {
                text: '请筛选后查看结果',
                fill: '#98A2B3',
                fontSize: 14,
                fontWeight: 500,
              },
            },
          ],
          series: [
            {
              type: 'radar',
              silent: true,
              data: [
                {
                  value: this.radarIndicators.map(() => 0),
                  lineStyle: { color: '#D0D5DD', type: 'dashed', width: 1.5 },
                  areaStyle: { color: 'rgba(255,255,255,0)' },
                  itemStyle: { color: '#D0D5DD' },
                  symbolSize: 0,
                },
              ],
            },
          ],
        }
      }

      const modeMeta = RADAR_MODE_META[this.appliedRadarQuery.mode]
      const values = this.appliedRadarQuery.mode === 'student'
        ? this.radarAppliedStudents[0].radar
        : this.averageRadarValues(this.radarAppliedStudents)

      return {
        tooltip: {
          trigger: 'item',
          confine: true,
        },
        radar: {
          radius: '68%',
          splitNumber: 5,
          axisName: { color: '#344054' },
          splitLine: { lineStyle: { color: '#E4E7EC' } },
          splitArea: { areaStyle: { color: ['#FCFCFD', '#F9FAFB'] } },
          axisLine: { lineStyle: { color: '#D0D5DD' } },
          indicator: this.radarIndicators,
        },
        series: [
          {
            type: 'radar',
            data: [
              {
                name: this.radarAppliedMeta.name,
                value: values,
                lineStyle: { color: modeMeta.color, width: 2.5 },
                areaStyle: { color: modeMeta.areaColor },
                itemStyle: { color: modeMeta.color },
                symbolSize: 7,
              },
            ],
          },
        ],
      }
    },
    trendChartOptions() {
      if (!this.hasTrendData) {
        const placeholderAxis = this.monthLabels.length ? this.monthLabels : this.buildFallbackMonths(this.rangeMonths)
        return {
          tooltip: { show: false },
          grid: { left: '3%', right: '4%', top: 30, bottom: '3%', containLabel: true },
          xAxis: {
            type: 'category',
            data: placeholderAxis,
            axisLine: { lineStyle: { color: '#D0D5DD' } },
            axisLabel: { color: '#98A2B3' },
            axisTick: { show: false },
          },
          yAxis: {
            type: 'value',
            min: 20,
            max: 100,
            splitLine: { lineStyle: { color: '#EAECF0', type: 'dashed' } },
            axisLabel: { color: '#98A2B3' },
          },
          graphic: [
            {
              type: 'text',
              left: 'center',
              top: '45%',
              style: {
                text: `${this.scopePlaceholderPrefix}暂无可展示趋势对象`,
                fill: '#98A2B3',
                fontSize: 14,
                fontWeight: 500,
              },
            },
          ],
          series: [
            {
              type: 'line',
              silent: true,
              data: placeholderAxis.map(() => 60),
              symbol: 'none',
              lineStyle: { width: 2, color: '#D0D5DD', type: 'dashed' },
              areaStyle: { color: 'rgba(208, 213, 221, 0.12)' },
            },
          ],
        }
      }

      return {
        tooltip: { trigger: 'axis' },
        legend: {
          top: 0,
          textStyle: { color: '#475467', fontSize: 12 },
        },
        grid: { left: '3%', right: '4%', top: 44, bottom: '3%', containLabel: true },
        xAxis: {
          type: 'category',
          data: this.monthLabels,
          axisLine: { lineStyle: { color: '#D0D5DD' } },
          axisLabel: { color: '#667085' },
          axisTick: { show: false },
        },
        yAxis: {
          type: 'value',
          min: 20,
          max: 100,
          splitLine: { lineStyle: { color: '#EAECF0', type: 'dashed' } },
          axisLabel: { color: '#667085' },
        },
        series: [
          {
            name: '历史真实值',
            type: 'line',
            smooth: true,
            data: this.trendSeries.actual,
            symbolSize: 8,
            lineStyle: { width: 3, color: '#1677FF' },
            itemStyle: { color: '#1677FF' },
          },
          {
            name: '预测趋势值',
            type: 'line',
            smooth: true,
            data: this.trendSeries.forecast,
            symbolSize: 8,
            lineStyle: { width: 3, color: '#8B5CF6' },
            itemStyle: { color: '#8B5CF6' },
          },
          {
            name: '同年级平均值',
            type: 'line',
            smooth: true,
            data: this.trendSeries.peer,
            symbolSize: 8,
            lineStyle: { width: 3, color: '#22C55E' },
            itemStyle: { color: '#22C55E' },
          },
        ],
      }
    },
    forecastChartOptions() {
      const isTrend = this.forecastTab === 'trend'
      const forecastData = isTrend ? this.currentTarget.forecastTrend : this.currentTarget.forecastScenario
      const upperData = isTrend ? this.currentTarget.forecastUpperTrend : this.currentTarget.forecastUpperScenario

      if (!this.hasForecastData) {
        const placeholderAxis = ['当前', '1个月后', '2个月后', '3个月后']
        return {
          tooltip: { show: false },
          grid: { left: '3%', right: '4%', top: 24, bottom: '3%', containLabel: true },
          xAxis: {
            type: 'category',
            data: placeholderAxis,
            axisLine: { lineStyle: { color: '#D0D5DD' } },
            axisLabel: { color: '#98A2B3' },
            axisTick: { show: false },
          },
          yAxis: {
            type: 'value',
            min: 40,
            max: 100,
            splitLine: { lineStyle: { color: '#EAECF0', type: 'dashed' } },
            axisLabel: { color: '#98A2B3' },
          },
          graphic: [
            {
              type: 'text',
              left: 'center',
              top: '45%',
              style: {
                text: `${this.scopePlaceholderPrefix}暂无可生成预测曲线的对象`,
                fill: '#98A2B3',
                fontSize: 14,
                fontWeight: 500,
              },
            },
          ],
          series: [
            {
              type: 'line',
              silent: true,
              data: [58, 58, 59, 60],
              symbol: 'none',
              lineStyle: { width: 2, color: '#D0D5DD', type: 'dashed' },
            },
            {
              type: 'line',
              silent: true,
              data: [62, 63, 64, 65],
              symbol: 'none',
              lineStyle: { width: 1, color: '#E4E7EC' },
              areaStyle: { color: 'rgba(208, 213, 221, 0.12)' },
            },
          ],
        }
      }

      return {
        tooltip: { trigger: 'axis' },
        legend: {
          top: 0,
          textStyle: { color: '#475467', fontSize: 12 },
        },
        grid: { left: '3%', right: '4%', top: 34, bottom: '3%', containLabel: true },
        xAxis: {
          type: 'category',
          data: ['当前', '1个月后', '2个月后', '3个月后'],
          axisLine: { lineStyle: { color: '#D0D5DD' } },
          axisLabel: { color: '#667085' },
          axisTick: { show: false },
        },
        yAxis: {
          type: 'value',
          min: 40,
          max: 100,
          splitLine: { lineStyle: { color: '#EAECF0', type: 'dashed' } },
          axisLabel: { color: '#667085' },
        },
        series: [
          {
            name: isTrend ? '预测趋势' : '保守情景',
            type: 'line',
            smooth: true,
            data: forecastData,
            symbolSize: 8,
            lineStyle: { width: 3, color: '#1677FF' },
            itemStyle: { color: '#1677FF' },
          },
          {
            name: '参考上界',
            type: 'line',
            smooth: true,
            data: upperData,
            symbol: 'none',
            lineStyle: { width: 1, color: '#8B5CF6', type: 'dashed' },
          },
        ],
      }
    },
    fallbackInsightMap() {
      const target = this.currentTarget
      const primaryFactor = target.factors?.[0]?.label || '学业投入与掌握'
      const secondaryFactor = target.factors?.[1]?.label || '导师支持与学术互动'
      const riskField = target.riskField || '关键风险项'
      return {
        trend: [
          {
            title: '核心总结',
            content: `当前筛选条件下，${target.name} 所在群体的发展指数总体呈波动上升趋势，短期内仍有改善空间。`,
          },
          {
            title: '主要影响面',
            content: `${primaryFactor} 与 ${secondaryFactor} 是当前拉动变化的两项关键因素。`,
          },
          {
            title: '风险提示',
            content: `当前需要重点关注 ${riskField} 相关问题，避免其继续拖累后续发展指数。`,
          },
        ],
        risk: [
          {
            title: '高风险分布',
            content: `在当前筛选结果中，高风险学生主要集中在 ${this.filters.riskType === '全部' ? '学业、培养与支持' : this.filters.riskType} 维度。`,
          },
          {
            title: '异常信号',
            content: `${target.name} 在 ${riskField} 上出现持续波动，建议纳入本周重点跟踪。`,
          },
          {
            title: '处置优先级',
            content: '建议先处理高风险对象，再对预警对象开展分层沟通与动态复核。',
          },
        ],
        governance: [
          {
            title: '治理建议一',
            content: '加强导师与学生的沟通频率，建立定期反馈机制。',
          },
          {
            title: '治理建议二',
            content: '对培养计划滞后的学生进行一对一辅导，明确阶段节点与责任人。',
          },
          {
            title: '治理建议三',
            content: '优化学业支持、科研训练与实践参与策略，持续提升综合发展质量。',
          },
        ],
      }
    },
    activeInsightSections() {
      return this.insightAnalysisData.sections?.length ? this.insightAnalysisData.sections : []
    },
    currentInsightEvidence() {
      return this.insightAnalysisData.evidence || []
    },
  },
  watch: {
    targetBaseStudents: {
      immediate: true,
      handler() {
        this.ensureValidSelectedTarget()
      },
    },
    selectedTargetId() {
      this.fetchInsightAnalysis()
    },
    insightTab() {
      this.fetchInsightAnalysis()
    },
    radarMode(nextMode) {
      this.appliedRadarQuery = null
      if (nextMode === 'grade') {
        this.radarFilters.major = ''
        this.radarFilters.name = ''
        return
      }
      if (nextMode === 'major') {
        this.radarFilters.name = ''
      }
    },
    'radarFilters.degreeType'() {
      this.radarFilters.grade = ''
      this.radarFilters.major = ''
      this.radarFilters.name = ''
      this.appliedRadarQuery = null
    },
    'radarFilters.grade'() {
      this.radarFilters.major = ''
      this.radarFilters.name = ''
      this.appliedRadarQuery = null
    },
    'radarFilters.major'() {
      this.radarFilters.name = ''
      this.appliedRadarQuery = null
    },
    'radarFilters.name'() {
      this.appliedRadarQuery = null
    },
    'forecastFilters.degreeType'() {
      if (this.syncingForecastFilters) return
      this.forecastFilters.grade = '全部年级'
      this.forecastFilters.major = '全部专业'
      this.forecastFilters.name = ''
    },
    'forecastFilters.grade'() {
      if (this.syncingForecastFilters) return
      this.forecastFilters.major = '全部专业'
      this.forecastFilters.name = ''
    },
    'forecastFilters.major'() {
      if (this.syncingForecastFilters) return
      this.forecastFilters.name = ''
    },
    forecastNameOptions(newOptions) {
      if (!newOptions.length) {
        this.forecastFilters.name = ''
        return
      }
      const exists = newOptions.some((item) => item.id === this.forecastFilters.name)
      if (!exists) {
        this.forecastFilters.name = newOptions.length === 1 ? newOptions[0].id : ''
      }
    },
    'chatMessages.length'() {
      this.$nextTick(() => {
        this.scrollChatToBottom()
      })
    },
  },
  async mounted() {
    await this.loadPageData()
    this.scrollChatToBottom()
  },
  beforeUnmount() {
    cancelAnimationFrame(this._chatRenderFrame)
  },
  methods: {
    resetAiRuntimeOptions() {
      this.aiRuntimeOptions = {
        experimentKey: 'default',
        preferredModel: this.aiCapabilities.model || '',
        apiStyle: this.defaultApiStyle,
        thinkingType: this.defaultThinkingType,
        reasoningEffort: '',
        temperature: '',
        useLlmWhenAvailable: true,
      }
    },
    async loadPageData() {
      this.pageLoading = true
      this.pageLoadError = ''
      try {
        const data = await getIntelligentPredictionData()
        this.pageData = data || EMPTY_PAGE_DATA

        const filterData = this.pageData.filters || EMPTY_PAGE_DATA.filters
        this.filters = {
          ...EMPTY_PAGE_DATA.filters.default,
          ...(filterData.default || {}),
        }
        this.filters.college = this.filters.college || this.businessScope.college
        this.collegeOptions = filterData.colleges?.length ? filterData.colleges : [this.businessScope.college]
        this.majorOptions = filterData.majors || []
        this.gradeOptions = filterData.grades || []
        this.rangeOptions = filterData.ranges || []
        this.riskTypeOptions = filterData.riskTypes || []
        this.resetAiRuntimeOptions()

        if (this.studentPool.length) {
          const preferredTarget = this.pickPreferredTarget(this.studentPool)
          this.selectedTargetId = preferredTarget?.id || ''
          this.syncForecastFiltersToTarget(preferredTarget)
        } else {
          this.selectedTargetId = ''
          this.resetChatMessages(`${this.scopePlaceholderPrefix}暂无可用预测对象。`)
        }
      } catch (error) {
        console.error('智能预测数据加载失败', error)
        this.pageLoadError = '智能预测数据加载失败，请检查后端接口、数据库样本或服务状态。'
        this.pageData = EMPTY_PAGE_DATA
        this.filters.college = DEFAULT_BUSINESS_SCOPE.college
        this.selectedTargetId = ''
        ElMessage.error(this.pageLoadError)
      } finally {
        this.pageLoading = false
      }
    },
    buildLocalInsightAnalysis(studentId, tab = this.insightTab) {
      const target = this.currentTarget
      if (!target?.studentId) {
        return {
          ...EMPTY_INSIGHT_ANALYSIS,
          studentId,
          tab,
        }
      }

      const topFactors = (target.factors || [])
        .slice(0, 3)
        .map((item) => `${item.label}${item.value}`)
        .join('；')

      const latestTrend = Array.isArray(target.trendActual) && target.trendActual.length
        ? target.trendActual[target.trendActual.length - 1]
        : null
      const forecastTrend = Array.isArray(target.forecastTrend) && target.forecastTrend.length
        ? target.forecastTrend[target.forecastTrend.length - 1]
        : null

      const sectionsByTab = {
        trend: [
          {
            title: '趋势判断',
            content: target.summary || '当前对象已生成基础趋势判断，可结合图表继续查看历史与预测变化。',
          },
          {
            title: '阶段表现',
            content: latestTrend !== null
              ? `当前综合发展指数最近一期约为 ${latestTrend}，预测周期末约为 ${forecastTrend ?? latestTrend}。`
              : '当前缺少完整的趋势序列，建议先检查月度指标样本。',
          },
          {
            title: '主要影响因素',
            content: topFactors || '当前未提取到显著影响因素，可先检查预测样本字段完整性。',
          },
        ],
        risk: [
          {
            title: '风险等级',
            content: `${target.name} 当前风险等级为 ${target.riskLevel}，主要风险领域为 ${target.riskField || '待补充'}。`,
          },
          {
            title: '风险说明',
            content: target.summary || '当前对象存在一定波动，建议结合培养进度、课程和导师反馈进一步核查。',
          },
          {
            title: '关键证据',
            content: topFactors || '当前未提取到清晰证据链，建议检查学业、科研、培养参与和支持服务类指标。',
          },
        ],
        governance: [
          {
            title: '治理建议',
            content: target.suggestion || '建议先安排导师沟通，并对培养计划和阶段任务进行复核。',
          },
          {
            title: '优先动作',
            content: `优先围绕 ${target.riskField || '关键风险字段'} 制定干预动作，并持续跟踪月度变化。`,
          },
          {
            title: '跟踪重点',
            content: topFactors || '建议持续跟踪学业投入、科研训练、共同体融入与导师支持等维度变化。',
          },
        ],
      }

      return {
        ...EMPTY_INSIGHT_ANALYSIS,
        studentId,
        tab,
        summary: target.summary || '当前已使用本地预测样本生成基础分析摘要。',
        sections: sectionsByTab[tab] || sectionsByTab.trend,
        evidence: (target.factors || []).slice(0, 5).map((item) => ({
          title: item.label,
          content: String(item.value),
        })),
        trace: {
          mode: 'frontend_local_fallback',
        },
      }
    },
    async fetchInsightAnalysis() {
      const studentId = this.currentTarget?.studentId
      if (!studentId) {
        this.insightAnalysisData = EMPTY_INSIGHT_ANALYSIS
        this.insightAnalysisError = `${this.scopePlaceholderPrefix}没有可分析的预测对象。`
        return
      }

      this.insightAnalysisLoading = true
      this.insightAnalysisError = ''
      try {
        const data = await getIntelligentPredictionAnalysis({
          studentId,
          tab: this.insightTab,
          experimentKey: this.aiRuntimeOptions.experimentKey,
          runtimeOptions: this.normalizedRuntimeOptions,
        }, null)

        this.insightAnalysisData = data || {
          ...EMPTY_INSIGHT_ANALYSIS,
          studentId,
          tab: this.insightTab,
        }
      } catch (error) {
        console.error('智能预测分析内容加载失败', error)
        this.insightAnalysisData = this.buildLocalInsightAnalysis(studentId, this.insightTab)
        this.insightAnalysisError = ''
      } finally {
        this.insightAnalysisLoading = false
      }
    },
    formatChatAnswer(answer) {
      if (!answer) {
        return '智能问答未返回结构化结果，请检查后端预测问答接口或 AI 配置。'
      }

      const blocks = []
      if (answer.directAnswer) {
        blocks.push(answer.directAnswer)
      }
      if (Array.isArray(answer.reasoning) && answer.reasoning.length) {
        blocks.push(`判断依据：${answer.reasoning.join('；')}`)
      }
      if (Array.isArray(answer.actionPlan) && answer.actionPlan.length) {
        blocks.push(`建议动作：${answer.actionPlan.join('；')}`)
      }
      if (Array.isArray(answer.citations) && answer.citations.length) {
        const citationTitles = answer.citations
          .map((item) => item.title)
          .filter(Boolean)
          .slice(0, 2)
        if (citationTitles.length) {
          blocks.push(`依据来源：${citationTitles.join('；')}`)
        }
      }

      return blocks.filter(Boolean).join('\n\n')
    },
    buildChatFailureText() {
      return [
        '智能问答服务暂不可用，当前未生成新的回答。',
        '请优先检查预测问答接口、后端日志或 AI 配置后重试。',
      ].join('\n')
    },
    resetChatMessages(summary = '') {
      const text = summary || this.currentTarget.summary || (
        this.hasCurrentTarget
          ? '已根据当前对象生成最新分析摘要，可以继续提问。'
          : `${this.scopePlaceholderPrefix}暂无可分析对象，可调整筛选条件或等待样本载入。`
      )
      this.lastChatTrace = null
      this.chatMessages = [
        {
          id: `assistant-refresh-${Date.now()}`,
          role: 'assistant',
          text,
        },
      ]
    },
    clamp(value, min = 0, max = 100) {
      return Math.min(max, Math.max(min, Number(value || 0)))
    },
    sliceTail(list, count) {
      if (!Array.isArray(list)) return []
      if (!count || list.length <= count) return list.slice()
      return list.slice(-count)
    },
    buildFallbackMonths(count = 6) {
      const months = []
      const today = new Date()
      const total = (today.getFullYear() * 12) + today.getMonth()
      for (let offset = count - 1; offset >= 0; offset -= 1) {
        const value = total - offset
        const year = Math.floor(value / 12)
        const month = (value % 12) + 1
        months.push(`${year}-${String(month).padStart(2, '0')}`)
      }
      return months
    },
    buildFallbackMonthlyRecords(student, count = 6) {
      const snapshot = student?.currentSnapshot || {}
      const steps = Math.max(1, count - 1)
      const interpolate = (target, spread, index) => {
        const targetValue = Number(target || 0)
        const start = Math.max(0, targetValue - spread)
        return Number((start + (((targetValue - start) * index) / steps)).toFixed(1))
      }

      return this.buildFallbackMonths(count).map((month, index) => ({
        month,
        courseAverage: interpolate(snapshot.courseAverage, 8, index),
        creditCompletionRate: interpolate(snapshot.creditCompletionRate, 16, index),
        attendanceRate: interpolate(snapshot.attendanceRate, 5, index),
        researchTaskCompletionRate: interpolate(snapshot.researchTaskCompletionRate, 14, index),
        activityHours: Math.round(interpolate(snapshot.activityHours, 4, index)),
        practiceHours: Math.round(interpolate(snapshot.practiceHours, 3, index)),
        advisorMeetingCount: Math.round(interpolate(snapshot.advisorMeetingCount60d, 1, index)),
        advisorEvaluationScore: interpolate(snapshot.advisorEvaluationScore, 6, index),
        wellbeingScore: interpolate(snapshot.wellbeingScore, 5, index),
      }))
    },
    buildMonthlyRecords(student) {
      if (Array.isArray(student?.monthlyRecords) && student.monthlyRecords.length) {
        return student.monthlyRecords.map((record) => ({
          month: record.month,
          courseAverage: Number(record.courseAverage || 0),
          creditCompletionRate: Number(record.creditCompletionRate || 0),
          attendanceRate: Number(record.attendanceRate || 0),
          researchTaskCompletionRate: Number(record.researchTaskCompletionRate || 0),
          activityHours: Number(record.activityHours || 0),
          practiceHours: Number(record.practiceHours || 0),
          advisorMeetingCount: Number(record.advisorMeetingCount || 0),
          advisorEvaluationScore: Number(record.advisorEvaluationScore || 0),
          wellbeingScore: Number(record.wellbeingScore || 0),
        }))
      }
      const metrics = student.monthlyMetrics || {}
      const months = metrics.months || []
      const records = months.map((month, index) => ({
        month,
        courseAverage: Number(metrics.courseAverage?.[index] || 0),
        creditCompletionRate: Number(metrics.creditCompletionRate?.[index] || 0),
        attendanceRate: Number(metrics.attendanceRate?.[index] || 0),
        researchTaskCompletionRate: Number(metrics.researchTaskCompletionRate?.[index] || 0),
        activityHours: Number(metrics.activityHours?.[index] || 0),
        practiceHours: Number(metrics.practiceHours?.[index] || 0),
        advisorMeetingCount: Number(metrics.advisorMeetingCount?.[index] || 0),
        advisorEvaluationScore: Number(metrics.advisorEvaluationScore?.[index] || 0),
        wellbeingScore: Number(metrics.wellbeingScore?.[index] || 0),
      }))
      return records.length ? records : this.buildFallbackMonthlyRecords(student)
    },
    formatSeriesText(values) {
      if (typeof values === 'string') return values || '-'
      if (!Array.isArray(values) || !values.length) return '-'
      return values
        .map((value) => {
          if (value === null || value === undefined || value === '') return 'null'
          const numeric = Number(value)
          return Number.isFinite(numeric) ? String(numeric) : String(value)
        })
        .join(' | ')
    },
    formatFactorsText(factors) {
      if (typeof factors === 'string') return factors || '-'
      if (!Array.isArray(factors) || !factors.length) return '-'
      return factors
        .filter((item) => item?.label)
        .map((item) => `${item.label}=${item.value || '-'}`)
        .join(' | ')
    },
    formatMetricValue(primary, fallback) {
      const value = primary ?? fallback
      if (value === null || value === undefined || value === '') return '-'
      const numeric = Number(value)
      return Number.isFinite(numeric) ? String(numeric) : String(value)
    },
    scoreValue(snapshot, key) {
      const value = snapshot?.[key]
      return value === undefined || value === null || value === '' ? null : Number(value)
    },
    scaleScore(snapshot, key, maximum) {
      const value = this.scoreValue(snapshot, key)
      if (value === null || maximum <= 0) return null
      return this.clamp((value / maximum) * 100)
    },
    reverseScaleScore(snapshot, key, maximum) {
      const value = this.scoreValue(snapshot, key)
      if (value === null || maximum <= 0) return null
      return this.clamp(100 - ((value / maximum) * 100))
    },
    weightedScore(parts) {
      const availableParts = parts.filter(([, score]) => score !== null)
      if (!availableParts.length) return 0
      const totalWeight = availableParts.reduce((sum, [weight]) => sum + weight, 0)
      const weighted = availableParts.reduce((sum, [weight, score]) => sum + (weight * this.clamp(score)), 0)
      return Number((this.clamp(weighted / totalWeight)).toFixed(1))
    },
    computeAcademicScore(snapshot) {
      return this.weightedScore([
        [0.40, this.scoreValue(snapshot, 'courseAverage')],
        [0.30, this.scoreValue(snapshot, 'creditCompletionRate')],
        [0.15, this.scoreValue(snapshot, 'trainingPlanCompletionRate')],
        [0.15, this.scoreValue(snapshot, 'graduationProgressRate')],
      ])
    },
    computeResearchScore(snapshot) {
      return this.weightedScore([
        [0.40, this.scoreValue(snapshot, 'researchTaskCompletionRate')],
        [0.25, this.scaleScore(snapshot, 'researchOutputCount', 4)],
        [0.20, this.scaleScore(snapshot, 'projectParticipationCount', 4)],
        [0.15, this.scoreValue(snapshot, 'graduationProgressRate')],
      ])
    },
    computeSelfManagementScore(snapshot) {
      return this.weightedScore([
        [0.40, this.scoreValue(snapshot, 'attendanceRate')],
        [0.30, this.reverseScaleScore(snapshot, 'missedCheckins', 5)],
        [0.20, this.reverseScaleScore(snapshot, 'overdueTasksCount', 6)],
        [0.10, this.scoreValue(snapshot, 'creditCompletionRate')],
      ])
    },
    computeAdvisorSupportScore(snapshot) {
      return this.weightedScore([
        [0.50, this.scoreValue(snapshot, 'advisorEvaluationScore')],
        [0.30, this.scaleScore(snapshot, 'advisorMeetingCount60d', 5)],
        [0.30, this.scaleScore(snapshot, 'advisorMeetingCount', 5)],
        [0.20, this.reverseScaleScore(snapshot, 'advisorAvgResponseDays', 10)],
      ])
    },
    computeCommunityScore(snapshot) {
      return this.weightedScore([
        [0.35, this.scaleScore(snapshot, 'activityHours', 30)],
        [0.25, this.scaleScore(snapshot, 'activityCount', 6)],
        [0.20, this.scaleScore(snapshot, 'projectParticipationCount', 4)],
        [0.20, this.scaleScore(snapshot, 'advisorMeetingCount60d', 5)],
        [0.20, this.scaleScore(snapshot, 'advisorMeetingCount', 5)],
      ])
    },
    computePracticeServiceScore(snapshot) {
      return this.weightedScore([
        [0.50, this.scaleScore(snapshot, 'practiceHours', 30)],
        [0.30, this.scaleScore(snapshot, 'practiceReportCount', 4)],
        [0.20, this.scaleScore(snapshot, 'activityCount', 6)],
      ])
    },
    computeWellbeingDevelopmentScore(snapshot) {
      return this.weightedScore([
        [0.60, this.scoreValue(snapshot, 'wellbeingScore')],
        [0.20, this.reverseScaleScore(snapshot, 'missedCheckins', 5)],
        [0.20, this.reverseScaleScore(snapshot, 'overdueTasksCount', 6)],
      ])
    },
    computeCurrentRadar(snapshot) {
      return [
        this.computeAcademicScore(snapshot),
        this.computeResearchScore(snapshot),
        this.computeSelfManagementScore(snapshot),
        this.computeAdvisorSupportScore(snapshot),
        this.computeCommunityScore(snapshot),
        this.computePracticeServiceScore(snapshot),
        this.computeWellbeingDevelopmentScore(snapshot),
      ]
    },
    computeMonthlyIndex(record) {
      const radarValues = this.computeCurrentRadar(record)
      const weighted = (radarValues[0] * 0.20)
        + (radarValues[1] * 0.18)
        + (radarValues[2] * 0.16)
        + (radarValues[3] * 0.14)
        + (radarValues[4] * 0.12)
        + (radarValues[5] * 0.10)
        + (radarValues[6] * 0.10)
      return Number(this.clamp(weighted).toFixed(1))
    },
    buildHistoricalForecast(actualSeries) {
      if (!actualSeries.length) return []
      const startIndex = Math.max(2, actualSeries.length - 4)
      return actualSeries.map((_, index) => {
        if (index < startIndex) return null
        const base = actualSeries[index - 1] ?? actualSeries[index]
        const prev = actualSeries[Math.max(0, index - 2)] ?? base
        const slope = base - prev
        return Number(this.clamp(base + (slope * 0.8)).toFixed(1))
      })
    },
    buildProjection(actualSeries, mode = 'trend') {
      if (!actualSeries.length) return [0, 0, 0, 0]
      const recent = actualSeries.slice(-4)
      const current = recent[recent.length - 1]
      const slope = recent.length > 1 ? (recent[recent.length - 1] - recent[0]) / (recent.length - 1) : 0
      const factor = mode === 'scenario' ? 0.6 : 1
      return [0, 1, 2, 3].map((step) => Number(this.clamp(current + (slope * factor * step)).toFixed(1)))
    },
    buildUpperProjection(baseSeries, padding = 3.5) {
      return baseSeries.map((value, index) => Number(this.clamp(value + padding + (index * 1.2)).toFixed(1)))
    },
    buildFactorBreakdown(student, radarValues) {
      const deficitItems = [
        { label: '学业投入与掌握', gap: 100 - Number(radarValues[0] || 0) },
        { label: '科研训练与创新', gap: 100 - Number(radarValues[1] || 0) },
        { label: '自我管理与学习策略', gap: 100 - Number(radarValues[2] || 0) },
        { label: '导师支持与学术互动', gap: 100 - Number(radarValues[3] || 0) },
        { label: '学术共同体融入', gap: 100 - Number(radarValues[4] || 0) },
        { label: '实践参与与公共服务', gap: 100 - Number(radarValues[5] || 0) },
        { label: '身心健康与持续发展', gap: 100 - Number(radarValues[6] || 0) },
      ]
        .map((item) => ({ ...item, gap: Number(this.clamp(item.gap).toFixed(1)) }))
        .sort((left, right) => right.gap - left.gap)
        .slice(0, 5)

      const totalGap = deficitItems.reduce((sum, item) => sum + item.gap, 0) || 1
      return deficitItems.map((item) => ({
        label: item.label,
        value: `${((item.gap / totalGap) * 100).toFixed(1)}%`,
        gap: item.gap,
      }))
    },
    buildRiskProfile(student, factors) {
      const topFactor = factors[0]
      const secondFactor = factors[1]
      const topGap = Number(topFactor?.gap || 0)
      const avgGap = factors.length
        ? factors.reduce((sum, item) => sum + Number(item.gap || 0), 0) / factors.length
        : 0
      const riskScore = Number(((topGap * 0.55) + (avgGap * 0.45)).toFixed(1))
      let riskLevel = '关注'
      let riskType = 'info'
      if (riskScore >= 28) {
        riskLevel = '高风险'
        riskType = 'danger'
      } else if (riskScore >= 18) {
        riskLevel = '预警'
        riskType = 'warning'
      }

      const riskCategory = FACTOR_CATEGORY_MAP[topFactor?.label] || '培养风险'
      const riskField = [topFactor?.label, secondFactor?.label].filter(Boolean).join('、')
      const suggestion = RISK_SUGGESTION_MAP[riskCategory] || '纳入持续跟踪'

      return {
        riskScore,
        riskLevel,
        riskType,
        riskCategory,
        riskField,
        suggestion,
      }
    },
    compareRiskStudents(left, right) {
      const priority = {
        danger: 3,
        warning: 2,
        info: 1,
        success: 0,
      }
      const leftScore = priority[left?.riskType] ?? 0
      const rightScore = priority[right?.riskType] ?? 0
      if (rightScore !== leftScore) return rightScore - leftScore
      const numericGap = Number(right?.riskScore || 0) - Number(left?.riskScore || 0)
      if (numericGap !== 0) return numericGap
      return String(left?.studentId || '').localeCompare(String(right?.studentId || ''))
    },
    buildGauges(student, riskProfile) {
      const snapshot = student.currentSnapshot || {}
      return {
        graduation: Number(this.clamp(100 - Number(snapshot.graduationProgressRate || 0)).toFixed(1)),
        training: Number(this.clamp(100 - Number(snapshot.trainingPlanCompletionRate || 0)).toFixed(1)),
        feedback: Number(this.clamp(Number(snapshot.advisorAvgResponseDays || 0) * 8).toFixed(1)),
        risk: Number(this.clamp(riskProfile.riskScore * 2.2).toFixed(1)),
      }
    },
    buildSummary(student, riskProfile, forecastTrend) {
      const trendDelta = (forecastTrend[forecastTrend.length - 1] || 0) - (forecastTrend[0] || 0)
      if (riskProfile.riskLevel === '高风险') {
        return `当前主要风险集中在${riskProfile.riskField}，若不及时干预，未来 3 个月综合发展指数可能仅维持低位波动。`
      }
      if (trendDelta >= 4) {
        return `当前样本整体趋势向上，未来 3 个月仍有改善空间，但需要继续关注${riskProfile.riskField}。`
      }
      return `当前对象处于平稳波动区间，短板主要在${riskProfile.riskField}，建议通过阶段性督办提升后续走势。`
    },
    pickPreferredTarget(source = []) {
      if (!Array.isArray(source) || !source.length) return null
      return source.find((item) => Array.isArray(item.monthlyRecords) && item.monthlyRecords.length) || source[0]
    },
    decorateStudent(student) {
      const monthlyRecords = this.buildMonthlyRecords(student)
      const radar = Array.isArray(student.radar) && student.radar.length
        ? student.radar.map((value) => Number(value || 0))
        : Array.isArray(student.radarValues) && student.radarValues.length
          ? student.radarValues.map((value) => Number(value || 0))
          : this.computeCurrentRadar(student.currentSnapshot || {})
      const trendActual = Array.isArray(student.trendActual) && student.trendActual.length
        ? student.trendActual.map((value) => Number(value || 0))
        : Array.isArray(student.historicalTrend) && student.historicalTrend.length
          ? student.historicalTrend.map((value) => Number(value || 0))
          : monthlyRecords.map((record) => this.computeMonthlyIndex(record))
      const trendForecast = Array.isArray(student.trendForecast) && student.trendForecast.length
        ? student.trendForecast.map((value) => (value === null ? null : Number(value || 0)))
        : Array.isArray(student.predictedTrend) && student.predictedTrend.length
          ? student.predictedTrend.map((value) => (value === null ? null : Number(value || 0)))
          : this.buildHistoricalForecast(trendActual)
      const forecastTrend = Array.isArray(student.forecastTrend) && student.forecastTrend.length
        ? student.forecastTrend.map((value) => Number(value || 0))
        : Array.isArray(student.forecastTrendValues) && student.forecastTrendValues.length
          ? student.forecastTrendValues.map((value) => Number(value || 0))
          : this.buildProjection(trendActual, 'trend')
      const forecastScenario = Array.isArray(student.forecastScenario) && student.forecastScenario.length
        ? student.forecastScenario.map((value) => Number(value || 0))
        : Array.isArray(student.scenarioValues) && student.scenarioValues.length
          ? student.scenarioValues.map((value) => Number(value || 0))
          : this.buildProjection(trendActual, 'scenario')
      const forecastUpperTrend = Array.isArray(student.forecastUpperTrend) && student.forecastUpperTrend.length
        ? student.forecastUpperTrend.map((value) => Number(value || 0))
        : Array.isArray(student.trendUpperBound) && student.trendUpperBound.length
          ? student.trendUpperBound.map((value) => Number(value || 0))
          : this.buildUpperProjection(forecastTrend, 3.5)
      const forecastUpperScenario = Array.isArray(student.forecastUpperScenario) && student.forecastUpperScenario.length
        ? student.forecastUpperScenario.map((value) => Number(value || 0))
        : Array.isArray(student.scenarioUpperBound) && student.scenarioUpperBound.length
          ? student.scenarioUpperBound.map((value) => Number(value || 0))
          : this.buildUpperProjection(forecastScenario, 2.8)
      const factors = Array.isArray(student.factors) && student.factors.length
        ? student.factors.map((item) => ({
          label: item.label,
          value: item.value || '-',
          gap: Number(item.gap || 0),
        }))
        : Array.isArray(student.keyFactors) && student.keyFactors.length
          ? student.keyFactors.map((item) => ({
            label: item.label,
            value: item.value || '-',
            gap: Number(item.gap || 0),
          }))
          : this.buildFactorBreakdown(student, radar)
      const derivedRiskProfile = this.buildRiskProfile(student, factors)
      const riskProfile = {
        ...derivedRiskProfile,
        riskScore: student.riskScore ?? derivedRiskProfile.riskScore,
        riskCategory: student.riskCategory || derivedRiskProfile.riskCategory,
        riskLevel: student.riskLevel || derivedRiskProfile.riskLevel,
        riskType: student.riskType || derivedRiskProfile.riskType,
        riskField: student.riskField || derivedRiskProfile.riskField,
        suggestion: student.suggestion || derivedRiskProfile.suggestion,
      }
      const gauges = student.gauges || this.buildGauges(student, riskProfile)
      const summary = student.summary || student.aiConclusion || this.buildSummary(student, riskProfile, forecastTrend)

      return {
        ...student,
        monthlyRecords,
        radar,
        radarValues: Array.isArray(student.radarValues) && student.radarValues.length ? student.radarValues : radar,
        trendActual,
        historicalTrend: Array.isArray(student.historicalTrend) && student.historicalTrend.length ? student.historicalTrend : trendActual,
        trendForecast,
        predictedTrend: Array.isArray(student.predictedTrend) && student.predictedTrend.length ? student.predictedTrend : trendForecast,
        forecastTrend,
        forecastTrendValues: Array.isArray(student.forecastTrendValues) && student.forecastTrendValues.length ? student.forecastTrendValues : forecastTrend,
        forecastScenario,
        scenarioValues: Array.isArray(student.scenarioValues) && student.scenarioValues.length ? student.scenarioValues : forecastScenario,
        forecastUpperTrend,
        trendUpperBound: Array.isArray(student.trendUpperBound) && student.trendUpperBound.length ? student.trendUpperBound : forecastUpperTrend,
        forecastUpperScenario,
        scenarioUpperBound: Array.isArray(student.scenarioUpperBound) && student.scenarioUpperBound.length ? student.scenarioUpperBound : forecastUpperScenario,
        factors: factors.map(({ label, value, gap }) => ({ label, value, gap })),
        keyFactors: student.keyFactors || factors.map(({ label, value, gap }) => ({ label, value, gap })),
        riskScore: riskProfile.riskScore,
        riskCategory: riskProfile.riskCategory,
        riskLevel: riskProfile.riskLevel,
        riskType: riskProfile.riskType,
        tagType: student.tagType || riskProfile.riskType,
        riskField: riskProfile.riskField,
        suggestion: riskProfile.suggestion,
        gauges,
        summary,
        aiConclusion: student.aiConclusion || summary,
        period: student.period || '未来 3 个月',
        peerTrend: Array.isArray(student.peerTrend) && student.peerTrend.length ? student.peerTrend : Array.isArray(student.peerAverageTrend) ? student.peerAverageTrend : [],
        peerAverageTrend: Array.isArray(student.peerAverageTrend) && student.peerAverageTrend.length ? student.peerAverageTrend : Array.isArray(student.peerTrend) ? student.peerTrend : [],
        keyFactorsText: student.keyFactorsText || this.formatFactorsText(factors),
        graduationWarning: this.formatMetricValue(student.graduationWarning, gauges.graduation),
        trainingLag: this.formatMetricValue(student.trainingLag, gauges.training),
        feedbackDelay: this.formatMetricValue(student.feedbackDelay, gauges.feedback),
        riskRate: this.formatMetricValue(student.riskRate, gauges.risk),
        historicalTrendText: student.historicalTrendText || this.formatSeriesText(student.historicalTrend || trendActual),
        predictedTrendText: student.predictedTrendText || this.formatSeriesText(student.predictedTrend || trendForecast),
        peerAverageTrendText: student.peerAverageTrendText || this.formatSeriesText(student.peerAverageTrend || student.peerTrend),
        radarValuesText: student.radarValuesText || this.formatSeriesText(student.radarValues || radar),
        forecastTrendValuesText: student.forecastTrendValuesText || this.formatSeriesText(student.forecastTrendValues || forecastTrend),
        scenarioValuesText: student.scenarioValuesText || this.formatSeriesText(student.scenarioValues || forecastScenario),
        trendUpperBoundText: student.trendUpperBoundText || this.formatSeriesText(student.trendUpperBound || forecastUpperTrend),
        scenarioUpperBoundText: student.scenarioUpperBoundText || this.formatSeriesText(student.scenarioUpperBound || forecastUpperScenario),
      }
    },
    buildPeerTrendSeries(target) {
      if (Array.isArray(target?.peerTrend) && target.peerTrend.length) {
        return target.peerTrend.map((value) => (value === null ? null : Number(value || 0)))
      }
      if (Array.isArray(target?.peerAverageTrend) && target.peerAverageTrend.length) {
        return target.peerAverageTrend.map((value) => (value === null ? null : Number(value || 0)))
      }
      if (!target?.id) return []
      const peers = this.studentPool.filter((student) => (
        student.degreeType === target.degreeType
        && student.grade === target.grade
      ))
      if (!peers.length) return []
      const maxLength = Math.max(...peers.map((item) => item.trendActual.length))
      return Array.from({ length: maxLength }, (_, index) => {
        const values = peers
          .map((item) => item.trendActual[index])
          .filter((value) => Number.isFinite(value))
        if (!values.length) return null
        return Number((values.reduce((sum, value) => sum + value, 0) / values.length).toFixed(1))
      })
    },
    buildGaugeOptions(gauge) {
      return {
        series: [
          {
            type: 'gauge',
            startAngle: 210,
            endAngle: -30,
            min: 0,
            max: 100,
            progress: {
              show: true,
              roundCap: true,
              width: 10,
              itemStyle: { color: gauge.color },
            },
            pointer: {
              show: false,
              icon: 'path://M2 0 L-2 0 L0 -48 Z',
              length: '55%',
              width: 6,
              itemStyle: { color: gauge.color },
            },
            axisLine: {
              lineStyle: {
                width: 10,
                color: [[1, '#E4E7EC']],
              },
            },
            axisTick: { show: false },
            splitLine: { show: false },
            axisLabel: { show: false },
            anchor: { show: false },
            title: { show: false },
            detail: {
              valueAnimation: false,
              offsetCenter: [0, '0%'],
              rich: {
                value: { fontSize: 20, fontWeight: 700, color: gauge.color },
                status: { fontSize: 14, fontWeight: 600, color: '#344054', padding: [6, 0, 0, 0] },
                trend: { fontSize: 12, color: '#667085', padding: [6, 0, 0, 0] },
              },
              formatter: () => `{value|${gauge.value}%}`,
            },
            data: [{ value: gauge.value }],
          },
        ],
      }
    },
    resolveRadarStudents(query) {
      if (!query) return []

      return this.studentPool.filter((student) => {
        if (query.degreeType && query.degreeType !== RADAR_ALL_DEGREE && student.degreeType !== query.degreeType) return false
        if (student.grade !== query.grade) return false

        if (query.mode === 'grade') return true
        if (student.major !== query.major) return false

        if (query.mode === 'major') return true
        return student.id === query.name
      })
    },
    averageRadarValues(students) {
      if (!students.length) return []

      return this.radarIndicators.map((_, index) => {
        const total = students.reduce((sum, student) => sum + Number(student.radar[index] || 0), 0)
        return Number((total / students.length).toFixed(1))
      })
    },
    applyRadarFilters() {
      if (!this.radarCanApply) {
        ElMessage.warning(this.radarFilterHint)
        return
      }

      const nextQuery = {
        mode: this.radarMode,
        degreeType: this.radarFilters.degreeType,
        grade: this.radarFilters.grade,
        major: this.radarMode === 'grade' ? '' : this.radarFilters.major,
        name: this.radarMode === 'student' ? this.radarFilters.name : '',
      }

      const matchedStudents = this.resolveRadarStudents(nextQuery)
      if (!matchedStudents.length) {
        ElMessage.warning('当前筛选条件下没有可展示的雷达图数据')
        return
      }

      this.appliedRadarQuery = nextQuery
      ElMessage.success(`已生成${RADAR_MODE_META[this.radarMode].label}`)
    },
    ensureValidSelectedTarget() {
      const source = this.targetBaseStudents
      const exists = source.some((item) => item.id === this.selectedTargetId)
      if (!exists && source.length) {
        const preferredTarget = this.pickPreferredTarget(source)
        this.selectedTargetId = preferredTarget?.id || ''
        this.syncForecastFiltersToTarget(preferredTarget)
      } else if (!source.length) {
        this.selectedTargetId = ''
      }
    },
    syncForecastFiltersToTarget(target) {
      if (!target) return
      this.syncingForecastFilters = true
      this.forecastFilters.degreeType = target.degreeType
      this.forecastFilters.grade = target.grade
      this.forecastFilters.major = target.major
      this.forecastFilters.name = target.id
      this.$nextTick(() => { this.syncingForecastFilters = false })
    },
    applyTargetFilters() {
      if (!this.forecastNameOptions.length) {
        ElMessage.warning('当前筛选条件下没有可选预测对象')
        return
      }
      if (!this.forecastFilters.name) {
        ElMessage.warning('请先选择姓名后再确定预测对象')
        return
      }
      this.selectedTargetId = this.forecastFilters.name
      ElMessage.success(`已切换到 ${this.currentTarget.name} 的预测结果`)
    },
    async handleRefresh() {
      if (this.pageLoadError || !this.studentPool.length) {
        await this.loadPageData()
        if (this.pageLoadError || !this.studentPool.length) return
      }
      await this.fetchInsightAnalysis()
      this.resetChatMessages(this.insightAnalysisData.summary)
      ElMessage.success('智能分析结果已刷新')
    },
    handleExport() {
      if (!this.currentTarget?.studentId) {
        ElMessage.warning('当前没有可导出的预测对象')
        return
      }
      const payload = {
        exportedAt: new Date().toISOString(),
        target: this.currentTarget,
        insightTab: this.insightTab,
        insightSummary: this.insightAnalysisData.summary,
        insightSections: this.activeInsightSections,
        evidence: this.currentInsightEvidence,
        capabilities: this.aiCapabilities,
        analysisTrace: this.insightAnalysisData.trace || null,
        chatTrace: this.lastChatTrace,
        runtimeOptions: this.normalizedRuntimeOptions,
      }
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${this.currentTarget.studentId}-prediction-report.json`
      link.click()
      URL.revokeObjectURL(url)
      ElMessage.success('预测报告已导出')
    },
    openGovernanceDetails(key) {
      this.governanceDetailKey = key
      this.governanceSearch = ''
      this.governancePage = 1
      this.riskDialogVisible = true
    },
    analyzeGovernanceStudent(student) {
      this.selectedTargetId = student.id
      this.syncForecastFiltersToTarget(student)
      this.riskDialogVisible = false
      this.$nextTick(() => document.querySelector('.risk-grid .ai-card')?.scrollIntoView({ behavior: 'smooth', block: 'center' }))
    },
    handleDeepAnalysis() {
      if (!this.currentTarget?.studentId) {
        ElMessage.warning('当前没有可查看的详细分析对象')
        return
      }
      this.detailDialogVisible = true
    },
    normalizeChatHistoryPayload(messages = []) {
      return messages
        .slice(-4)
        .map((message) => ({
          role: message.role,
          content: String(message.text || '').trim().slice(0, 480),
        }))
        .filter((message) => message.role && message.content)
    },
    resolveChatErrorMessage(error) {
      const detail = error?.message || ''
      if (detail.includes('temperature')) {
        return '当前问答参数中的温度值格式无效。系统已改为走后端默认配置，请刷新页面后重试。'
      }
      if (detail.includes('chatHistory')) {
        return '当前上下文消息格式不符合后端要求，请直接重试一次。'
      }
      if (detail.includes('question')) {
        return '当前问题内容不符合后端要求，请缩短到 500 字以内后重试。'
      }
      if (detail.includes('400')) {
        return '当前问题已发出，但请求参数未通过后端校验，请刷新页面后重试。'
      }
      return this.buildChatFailureText()
    },
    async submitQuestion() {
      if (!this.currentTarget?.studentId) {
        ElMessage.warning('当前没有可提问的预测对象')
        return
      }
      const question = String(this.chatInput || '').trim()
      if (!question) {
        ElMessage.warning('请输入问题后再发送')
        return
      }
      if (question.length > 500) {
        ElMessage.warning('问题长度不能超过 500 个字符')
        return
      }

      const chatHistory = this.normalizeChatHistoryPayload(this.chatMessages)
      const timeId = Date.now()

      this.chatMessages.push({
        id: `user-${timeId}`,
        role: 'user',
        text: question,
      })

      this.chatInput = ''
      this.chatStickToBottom = true
      this.chatSubmitting = true
      this.chatProgress = '正在分析…'
      this.chatProgressTools = []
      this.chatThinking = ''

      // 先占位一条助手消息，流式过程中就地改写它的 text，
      // 这样答案是"逐字长出来"的，而不是等全部结束才整段出现。
      const assistantId = `assistant-${timeId}`
      this.streamingMessageId = assistantId
      this.chatMessages.push({
        id: assistantId,
        role: 'assistant',
        text: '',
        streaming: true,
      })

      const requestPayload = {
        studentId: this.currentTarget.studentId,
        question,
        experimentKey: this.aiRuntimeOptions.experimentKey,
        runtimeOptions: this.normalizedRuntimeOptions,
        chatHistory,
      }

      try {
        let data
        try {
          data = await streamIntelligentPredictionChat(requestPayload, (event) => {
            this.handleChatStreamEvent(event)
          })
        } catch (streamError) {
          const partial = this.chatMessages.find((item) => item.id === assistantId)?.text
          if (partial || this._pendingChatText) {
            throw streamError
          }
          // 流式不可用（反代不支持 SSE、浏览器不支持 ReadableStream 等）
          // 时退回一次性请求，保证功能仍然可用
          console.warn('流式问答不可用，回退为一次性请求', streamError)
          this.chatProgress = '正在生成回答…'
          data = await getIntelligentPredictionChat(requestPayload, null)
        }

        this.lastChatTrace = data?.trace || null
        // 收尾：用结构化答案（含推理、建议、引用）替换流式期间的纯文本
        this.replaceStreamingMessage(assistantId, this.formatChatAnswer(data?.answer))
      } catch (error) {
        console.error('智能预测对话生成失败', error)
        this.lastChatTrace = null
        const partial = this._pendingChatText || this.chatMessages.find((item) => item.id === assistantId)?.text
        this.replaceStreamingMessage(assistantId, partial
          ? `${partial}\n\n（连接中断，以上为已收到的内容，可继续追问。）`
          : this.resolveChatErrorMessage(error))
      } finally {
        this.chatSubmitting = false
        this.chatProgress = ''
        this.chatProgressTools = []
        this.chatThinking = ''
        this.streamingMessageId = ''
      }
    },

    replaceStreamingMessage(messageId, text) {
      cancelAnimationFrame(this._chatRenderFrame)
      this._chatRenderFrame = null
      this._pendingChatText = ''
      const target = this.chatMessages.find((item) => item.id === messageId)
      if (target) {
        target.text = text
        target.streaming = false
        this.scrollChatToBottom()
        return
      }
      this.chatMessages.push({ id: messageId, role: 'assistant', text })
    },

    handleChatStreamEvent(event) {
      const toolLabels = {
        search_policy: '检索制度文件',
        get_student_snapshot: '读取学生画像',
        compare_peers: '对比同群体水位',
        list_warnings: '查询预警记录',
      }

      if (event.type === 'status') {
        this.chatProgress = event.message || (event.stage === 'finalizing' ? '正在整理答案…' : '正在分析…')
        return
      }
      if (event.type === 'reasoning') {
        // 思考增量占了整轮大部分时间（实测 1.8s~13s）。
        // 不消费它的话，界面会一直停在"正在分析…"看起来像卡死。
        this.chatThinking = (this.chatThinking + event.text).slice(-160)
        return
      }
      if (event.type === 'tool_start') {
        const label = toolLabels[event.tool] || event.tool
        const query = event.arguments?.query
        this.chatProgress = query ? `${label}：${query}` : `${label}…`
        this.chatProgressTools.push({ tool: event.tool, label, ok: null })
        this.chatThinking = ''
        return
      }
      if (event.type === 'tool_result') {
        const last = [...this.chatProgressTools]
          .reverse()
          .find((item) => item.tool === event.tool && item.ok === null)
        if (last) {
          last.ok = event.ok
          last.hitCount = event.hitCount
        }
        return
      }
      if (event.type === 'answer_text' || event.type === 'answer_sections') {
        // 后端已从半截 JSON 里抽出 directAnswer 的当前内容，可直接展示
        this.chatProgress = '正在生成回答…'
        this.chatThinking = ''
        this._pendingChatText = event.text
        if (!this._chatRenderFrame) {
          this._chatRenderFrame = requestAnimationFrame(() => {
            this._chatRenderFrame = null
            const target = this.chatMessages.find((item) => item.id === this.streamingMessageId)
            if (target) target.text = this._pendingChatText
            this.scrollChatToBottom()
          })
        }
      }
    },

    handleChatScroll(event) {
      const el = event.target
      this.chatStickToBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 48
    },
    scrollChatToBottom() {
      this.$nextTick(() => {
        const box = this.$refs.assistantChatRef
        const el = Array.isArray(box) ? box[0] : box
        if (this.chatStickToBottom && el && typeof el.scrollTop === 'number') {
          el.scrollTop = el.scrollHeight
        }
      })
    },
  },
}
</script>

<style scoped>
.intelligent-page {
  background: #fff;
  color: #1d2939;
  min-height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

.section-card {
  background: #fff;
  border: none;
  border-radius: 12px;
  padding: 18px 20px;
  box-shadow: none;
}

.filter-bar {
  display: grid;
  gap: 18px;
  margin-bottom: 18px;
}

.filter-header {
  display: flex;
  justify-content: flex-start;
}

.filter-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  flex-wrap: wrap;
}

.page-alert {
  margin-bottom: 18px;
}

.ai-config-card {
  margin-bottom: 18px;
}

.ai-config-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.ai-config-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.ai-config-field {
  display: grid;
  gap: 8px;
}

.ai-config-label {
  font-size: 13px;
  color: #475467;
}

.ai-config-alert {
  margin-top: 14px;
}

.brand-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
  width: 100%;
}

.brand-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(135deg, #eaf2ff 0%, #d8e8ff 100%);
  color: #1677ff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-icon svg {
  width: 22px;
  height: 22px;
}

.brand-title {
  font-size: 28px;
  font-weight: 700;
  color: #1d2939;
}

.brand-caption {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
  font-size: 13px;
  color: #667085;
  flex-wrap: wrap;
}

.filter-items {
  display: flex;
  align-items: center;
  gap: 18px;
  flex-wrap: wrap;
  flex: 1;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.filter-item-scope {
  align-items: center;
}

.filter-label {
  font-size: 14px;
  color: #475467;
  white-space: nowrap;
}

.scope-badges {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: nowrap;
}

.scope-badge {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  background: #f5f8ff;
  border: 1px solid #dbe7ff;
  color: #475467;
  font-size: 13px;
}

.scope-badge-strong {
  background: #eff6ff;
  border-color: #bfd4ff;
  color: #1677ff;
  font-weight: 600;
}

.filter-select {
  width: 148px;
}

.filter-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.radar-filter-panel {
  margin-bottom: 14px;
  padding: 14px 16px;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid #e4e7ec;
}

.radar-filter-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}

.radar-filter-hint {
  margin-top: 10px;
  font-size: 12px;
  color: #667085;
}

.radar-chart-block {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.radar-summary {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.radar-summary-placeholder {
  min-height: 28px;
}

.radar-summary-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  padding: 0 12px;
  border-radius: 999px;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
}

.radar-summary-text {
  font-size: 13px;
  color: #475467;
}

.section-heading {
  font-size: 20px;
  font-weight: 700;
  color: #1d2939;
  margin: 20px 0 14px;
  padding-left: 12px;
  border-left: 4px solid #1677ff;
}

.governance-scope {
  margin: -4px 0 16px;
  color: #475467;
  font-size: 13px;
  line-height: 1.7;
}

.governance-rule {
  color: #667085;
  font-size: 12px;
  text-align: center;
  line-height: 1.5;
}

.risk-student-id {
  margin-top: 4px;
  font-size: 11px;
  font-weight: 400;
  color: #667085;
}

.risk-table-row .risk-table-cell-name,
.risk-table-row .risk-student-scope {
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
}

.top-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 16px;
  align-items: stretch;
}

.top-grid > .chart-shell {
  display: flex;
  flex-direction: column;
  min-height: 540px;
  height: 100%;
  min-width: 0;
}

.risk-grid {
  display: grid;
  grid-template-columns: minmax(285px, 0.65fr) minmax(0, 1.55fr);
  gap: 16px;
  align-items: stretch;
}

.gauge-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  grid-template-rows: repeat(2, minmax(0, 1fr));
  gap: 14px;
  align-content: start;
  height: 100%;
}

.bottom-grid {
  --bottom-panel-height: 520px;
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
  margin-top: 16px;
  align-items: stretch;
  flex: 1;
  min-height: 0;
}

.forecast-card,
.ai-card {
  display: flex;
  flex-direction: column;
  height: var(--bottom-panel-height);
  min-height: 0;
  overflow: hidden;
}

.forecast-layout,
.ai-layout {
  flex: 1 1 auto;
  min-height: 0;
  align-items: stretch;
}

.forecast-left,
.ai-content {
  min-height: 0;
}

.forecast-right {
  min-height: 0;
}

.trend-card,
.radar-card {
  min-width: 0;
}

.top-grid .card-head,
.radar-filter-panel {
  flex-shrink: 0;
}

.top-grid .chart-shell :deep(.chart-card) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.top-grid .chart-shell :deep(.chart-box) {
  flex: 1;
  min-height: 0;
}

.card-head {
  margin-bottom: 12px;
}

.card-head-inline {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.card-title {
  font-size: 18px;
  font-weight: 700;
  color: #1d2939;
}

.card-subtitle {
  font-size: 13px;
  color: #667085;
  margin-top: 4px;
  line-height: 1.6;
}

.trace-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 10px;
}

.trace-row-center {
  justify-content: center;
}

.trace-text {
  font-size: 12px;
  color: #667085;
}

.gauge-title {
  font-size: 16px;
  padding: 0;
  border: none;
  background: transparent;
  text-align: center;
  cursor: pointer;
  text-decoration: underline;
  text-decoration-color: #c0d4f5;
  text-underline-offset: 5px;
}

.gauge-title:hover, .gauge-title:focus-visible { color: #1677ff; }

.gauge-card {
  padding: 12px 14px 8px;
  min-height: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  border: 1px solid #e4eaf3;
  border-top: 3px solid var(--gauge-accent);
  border-radius: 14px;
  background: linear-gradient(180deg, #fff 65%, #f8faff 100%);
  transition: box-shadow 0.2s, transform 0.2s;
}

.gauge-card:focus-within {
  outline: 2px solid #91baff;
  outline-offset: 2px;
  box-shadow: 0 8px 24px #102b6012;
  transform: translateY(-2px);
}


.governance-count {
  text-align: center;
  color: #344054;
  font-size: 14px;
  font-weight: 600;
  margin: -12px 0 6px;
}

.risk-grid .ai-card .tab-strip { flex-shrink: 0; flex-wrap: nowrap; }

.risk-grid .assistant-header {
  display: grid;
  grid-template-columns: 36px 1fr;
  column-gap: 8px;
  align-items: center;
  text-align: left;
}

.risk-grid .assistant-figure { grid-row: span 2; }
.risk-grid .assistant-figure svg { width: 36px; height: 36px; }
.risk-grid .assistant-name { margin: 0; }
.risk-grid .assistant-chat { min-height: 40px; max-height: none; }

.insight-target {
  margin-top: 8px;
  color: #1d4ed8;
  font-size: 13px;
  font-weight: 600;
}

.risk-grid .ai-card {
  height: 600px;
  border: 1px solid #e4eaf3;
  border-radius: 14px;
  background: #fff;
}

.bottom-grid .forecast-card { height: auto; min-height: 380px; }

.governance-dialog-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 18px;
  line-height: 1.8;
}

.governance-dialog { max-width: calc(100vw - 32px); }

.governance-dialog-toolbar .governance-rule { text-align: left; }
.governance-pagination { justify-content: flex-end; margin-top: 18px; }

.gauge-card .gauge-title {
  margin-bottom: 2px;
}

.chart-shell :deep(.chart-card),
.gauge-card :deep(.chart-card),
.forecast-left :deep(.chart-card) {
  padding: 0;
  background: transparent;
  border-radius: 0;
}

.chart-shell :deep(.chart-title),
.gauge-card :deep(.chart-title),
.forecast-left :deep(.chart-title) {
  display: none;
}

.trend-card {
  border: none;
}

.tab-strip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.tab-btn {
  border: 1px solid #d0d5dd;
  background: #fff;
  color: #475467;
  padding: 6px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
}

.tab-btn.active {
  border-color: #1677ff;
  color: #1677ff;
  background: #eff6ff;
}

.risk-table-card {
  padding: 16px 18px 12px;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.risk-table-card .card-head {
  flex-shrink: 0;
  margin-bottom: 10px;
}

.risk-table-shell {
  flex: 1;
  min-height: 0;
  display: flex;
  overflow: hidden;
}

.risk-student-table {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  border: 1px solid #e4e7ec;
  border-radius: 12px;
  background: #fff;
  overflow: hidden;
}

.risk-table-header,
.risk-table-row {
  display: grid;
  grid-template-columns: 128px minmax(95px, 0.9fr) 72px minmax(110px, 1fr) minmax(130px, 1.1fr);
  column-gap: 14px;
}

.risk-table-header {
  flex-shrink: 0;
  padding: 10px 14px;
  align-items: center;
  background: #f8fafc;
  border-bottom: 1px solid #e4e7ec;
}

.risk-table-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.risk-table-empty {
  flex: 1;
  min-height: 110px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  color: #98a2b3;
  font-size: 13px;
  text-align: center;
}

.risk-table-row {
  flex: 1;
  min-height: 0;
  padding: 0 14px;
  align-items: stretch;
  border-bottom: 1px solid #e4e7ec;
}

.risk-table-row:last-child {
  border-bottom: none;
}

.risk-table-cell {
  min-width: 0;
  display: flex;
  align-items: center;
  font-size: 13px;
  color: #344054;
  line-height: 1.65;
  word-break: break-word;
}

.risk-table-header .risk-table-cell {
  font-size: 13px;
  font-weight: 600;
  color: #344054;
}

.risk-table-cell-id,
.risk-table-cell-name,
.risk-table-cell-level {
  white-space: nowrap;
}

.risk-table-cell-level {
  align-items: center;
}

.risk-table-cell-field,
.risk-table-cell-suggestion {
  white-space: normal;
  align-self: stretch;
  padding: 8px 0;
}

.target-filter-panel {
  position: sticky;
  top: 16px;
  align-self: start;
  box-sizing: border-box;
  max-height: calc(100dvh - 112px);
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-gutter: stable;
  z-index: 2;
  border: 1px solid #e1e9f5;
  border-radius: 14px;
  padding: 18px 14px;
  background: linear-gradient(180deg, #f4f8ff, #fff);
  box-shadow: 0 6px 22px #183b6b08;
}

.target-filter-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
  flex-direction: column;
  align-items: flex-start;
}

.target-filter-count {
  font-size: 12px;
  color: #667085;
}

.target-filter-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}

.analysis-workspace { display: grid; grid-template-columns: 220px minmax(0, 1fr); gap: 18px; align-items: start; margin-top: 26px; }
.analysis-workspace-main { min-width: 0; }
.analysis-workspace-main > .section-heading { margin-top: 0; }
.target-field { display: grid; gap: 7px; min-width: 0; font-size: 12px; color: #475467; }
.target-filter-grid .el-select { width: 100%; }
.selected-target-card { display: grid; gap: 8px; margin-top: 20px; padding: 14px 10px; border-radius: 10px; border: 1px solid #dce7fb; background: #fff; color: #344054; font-size: 12px; line-height: 1.6; }
.selected-target-card strong { font-size: 19px; color: #123b7b; }
.selected-target-card .el-tag { justify-self: start; }
.selected-target-label { color: #667085; font-size: 11px; }
.target-selection-help { margin: 14px 0 0; color: #667085; font-size: 12px; line-height: 1.8; }
.forecast-method-note { padding: 10px 12px; background: #f4f7ff; border-radius: 8px; font-size: 12px; line-height: 1.8; color: #475467; }
.prediction-conclusions { border: 1px solid #e4eaf3; border-radius: 14px; padding: 20px; margin-top: 18px; background: linear-gradient(135deg, #f3f7ff, #f8fafc); }
.conclusion-header { display: flex; justify-content: space-between; align-items: center; gap: 16px; margin-bottom: 18px; }
.conclusion-caption { margin: 6px 0 0; font-size: 12px; line-height: 1.7; color: #667085; }
.prediction-conclusion-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.prediction-conclusion-section { background: #fff; border: 1px solid #e5ebf5; border-radius: 12px; padding: 18px; box-shadow: 0 3px 12px #183b6b04; }
.prediction-conclusion-section h4 { display: flex; align-items: center; gap: 10px; margin: 0 0 12px; color: #183b6b; font-size: 14px; }
.conclusion-index { display: inline-grid; place-items: center; width: 28px; height: 28px; flex-shrink: 0; border-radius: 8px; color: #3264cc; background: #edf3ff; font-size: 12px; }
.prediction-conclusion-section:nth-child(2) .conclusion-index { color: #b56a18; background: #fff5e7; }
.prediction-conclusion-section:nth-child(3) .conclusion-index { color: #6c54b5; background: #f2efff; }
.prediction-conclusion-section:nth-child(4) .conclusion-index { color: #16816e; background: #eaf8f3; }
.prediction-conclusion-section p { margin: 0; font-size: 13px; line-height: 1.95; color: #475467; overflow-wrap: anywhere; }
.full-insight-section { margin-top: 14px; padding: 14px 16px; background: #f8faff; border-radius: 10px; }
.full-insight-section h4 { margin: 0 0 8px; color: #183b6b; font-size: 14px; }
.interpretation-dialog :deep(.el-dialog__body) { max-height: 72vh; overflow-y: auto; }

.forecast-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(240px, 0.7fr);
  gap: 12px;
}

.forecast-meta {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  column-gap: 14px;
  row-gap: 6px;
  margin-bottom: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  background: #f8fafc;
  font-size: 13px;
  color: #475467;
}

.forecast-meta-item {
  display: grid;
  gap: 4px;
}

.forecast-meta-label {
  font-size: 12px;
  color: #667085;
}

.forecast-meta-value {
  font-size: 13px;
  color: #1d2939;
  line-height: 1.6;
}

.forecast-meta-value.is-placeholder {
  color: #98a2b3;
}

.forecast-left {
  display: grid;
  gap: 10px;
  align-content: start;
}

.forecast-right {
  display: flex;
  min-width: 0;
}

.factor-card { flex: 1; display: flex; flex-direction: column; min-width: 0; border: 1px solid #e4eaf3 !important; background: linear-gradient(180deg, #f8faff, #fff) !important; }
.factor-card .subcard-title { padding-bottom: 12px; border-bottom: 1px solid #e4eaf3; }
.factor-card .factor-list { flex: 1; grid-template-rows: repeat(5, minmax(0, 1fr)); gap: 0; }
.factor-card .factor-item { align-items: center; padding: 10px 0; }
.factor-card .factor-item:last-child { border-bottom: none; }
.factor-name { display: flex; align-items: center; gap: 9px; min-width: 0; }
.factor-rank { display: inline-grid; place-items: center; width: 24px; height: 24px; flex-shrink: 0; border-radius: 7px; background: #edf1f7; color: #667085; font-size: 12px; font-weight: 600; }
.factor-item:nth-child(-n+3) .factor-rank { background: #e8efff; color: #3264cc; }
.factor-value { font-weight: 600; color: #183b6b; text-align: right; }

.plain-subcard {
  border: none;
  border-radius: 10px;
  padding: 12px 14px;
  background: #fff;
}

.subcard-title {
  font-size: 15px;
  font-weight: 700;
  color: #1d2939;
  margin-bottom: 8px;
}

.factor-list {
  display: grid;
  gap: 6px;
}

.factor-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
  color: #344054;
  padding-bottom: 6px;
  border-bottom: 1px dashed #eaecef;
}

.factor-item-placeholder {
  color: #98a2b3;
}

.summary-card {
  display: grid;
  gap: 8px;
  align-content: start;
}

.summary-card p {
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
  color: #475467;
}

.detail-link {
  border: none;
  background: transparent;
  color: #1677ff;
  cursor: pointer;
  padding: 0;
  font-size: 13px;
  font-weight: 600;
}

.detail-link.disabled {
  color: #98a2b3;
  cursor: not-allowed;
}

.ai-layout {
  display: grid;
  grid-template-columns: minmax(0, 0.8fr) minmax(0, 1.2fr);
  gap: 10px;
  align-items: stretch;
  min-height: 0;
  height: 100%;
}

.ai-card .card-head {
  margin-bottom: 8px;
}

.ai-card .card-subtitle {
  line-height: 1.45;
}

.ai-card .trace-row {
  margin-top: 6px;
}

.ai-content {
  display: grid;
  gap: 10px;
  align-content: start;
  grid-auto-rows: max-content;
  min-height: 0;
  height: 100%;
  overflow-y: auto;
  padding: 10px 12px 10px 4px;
  border-radius: 12px;
  background: linear-gradient(180deg, #fcfdff 0%, #f8fbff 100%);
  border: 1px solid #e4e7ec;
  scrollbar-gutter: stable;
  overscroll-behavior: contain;
  box-sizing: border-box;
}

.insight-block {
  border: none;
  border-radius: 10px;
  padding: 12px 14px;
  background: #fff;
}

.insight-loading {
  color: #667085;
  font-size: 14px;
}

.insight-error {
  color: #b42318;
  background: #fef3f2;
}

.insight-empty {
  color: #667085;
  background: #f8fafc;
}

.insight-title {
  font-size: 15px;
  font-weight: 700;
  color: #1d2939;
  margin-bottom: 8px;
}

.insight-body {
  font-size: 14px;
  line-height: 1.8;
  color: #475467;
}

.assistant-panel {
  border: none;
  border-radius: 12px;
  background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  height: 100%;
  min-height: 0;
  box-sizing: border-box;
}

.assistant-header {
  text-align: center;
  flex-shrink: 0;
  padding-bottom: 4px;
}

.assistant-figure svg {
  width: 56px;
  height: 56px;
}

.assistant-name {
  font-size: 15px;
  font-weight: 700;
  color: #1d2939;
  margin-top: 2px;
}

.assistant-desc {
  font-size: 11px;
  color: #667085;
  margin-top: 2px;
  line-height: 1.35;
}

.assistant-chat {
  flex: 1 1 auto;
  min-height: 96px;
  max-height: 188px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-right: 4px;
  overscroll-behavior: contain;
}

.chat-bubble {
  flex-shrink: 0;
  max-width: 100%;
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 13px;
  line-height: 1.7;
  word-break: break-word;
  white-space: pre-wrap;
}

.chat-bubble.assistant {
  background: #f3f8ff;
  color: #344054;
  align-self: flex-start;
}

.chat-bubble.user {
  background: #1677ff;
  color: #fff;
  align-self: flex-end;
}

.chat-thinking-hint {
  color: #98a2b3;
  font-size: 12px;
  font-style: italic;
  word-break: break-all;
}

.chat-caret {
  display: inline-block;
  margin-left: 2px;
  color: #165dff;
  animation: chat-caret-blink 1s step-end infinite;
}

@keyframes chat-caret-blink {
  50% {
    opacity: 0;
  }
}

.option-tag-virtual {
  float: right;
  margin-left: 10px;
  padding: 0 6px;
  border-radius: 8px;
  background: #fef0c7;
  color: #b54708;
  font-size: 11px;
  line-height: 20px;
}

.assistant-progress {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  padding: 6px 10px;
  border-radius: 8px;
  background: #f2f4f7;
  font-size: 12px;
  color: #475467;
  flex-shrink: 0;
}

.assistant-progress-text {
  color: #344054;
}

.assistant-progress-chip {
  padding: 1px 8px;
  border-radius: 10px;
  background: #e4e7ec;
  color: #475467;
}

.assistant-progress-chip.is-done {
  background: #e6f4ea;
  color: #1e7b4f;
}

.assistant-progress-chip.is-failed {
  background: #fde8e8;
  color: #b42318;
}

.assistant-input-box {
  margin-top: auto;
  border-top: 1px solid #e4e7ec;
  padding-top: 8px;
  flex-shrink: 0;
}

.assistant-input-box :deep(.el-textarea__inner) {
  min-height: 72px !important;
  line-height: 1.6;
}

.assistant-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: 4px;
}

.assistant-tip {
  font-size: 11px;
  color: #667085;
  line-height: 1.5;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.detail-item {
  display: grid;
  gap: 6px;
  padding: 12px 14px;
  border: 1px solid #e4e7ec;
  border-radius: 10px;
  background: #f8fafc;
}

.detail-label {
  font-size: 12px;
  color: #667085;
}

.detail-value {
  font-size: 14px;
  color: #1d2939;
  line-height: 1.7;
}

.detail-section {
  margin-top: 16px;
}

.detail-section-title {
  font-size: 15px;
  font-weight: 700;
  color: #1d2939;
  margin-bottom: 10px;
}

.detail-section-body {
  font-size: 14px;
  line-height: 1.8;
  color: #475467;
}

.detail-evidence-list {
  display: grid;
  gap: 10px;
}

.detail-evidence-item {
  padding: 12px 14px;
  border-radius: 10px;
  background: #f8fafc;
  border: 1px solid #e4e7ec;
}

.detail-evidence-title {
  font-size: 13px;
  font-weight: 600;
  color: #1d2939;
  margin-bottom: 6px;
}

.detail-evidence-body {
  font-size: 13px;
  color: #475467;
  line-height: 1.7;
}

@media (max-width: 1400px) {
  .top-grid,
  .bottom-grid {
    grid-template-columns: 1fr;
  }

  .gauge-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .ai-config-grid,
  .radar-filter-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .ai-content,
  .assistant-panel {
    height: auto;
    min-height: 0;
    max-height: none;
  }

  .forecast-card,
  .ai-card {
    height: auto;
  }
}

@media (max-width: 1550px) {
  .risk-grid { grid-template-columns: 1fr; }
  .gauge-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); grid-template-rows: 1fr; height: auto; }
  .gauge-card { height: auto; min-height: 230px; }
  .risk-grid .ai-card { height: 560px; }
}

.risk-grid .ai-content, .risk-grid .assistant-panel { height: 100%; min-height: 0; }
.risk-grid .ai-layout { grid-template-columns: minmax(0, 0.8fr) minmax(0, 1.2fr); }

@media (max-width: 1100px) {
  .analysis-workspace { grid-template-columns: 1fr; }
  .target-filter-panel { position: static; max-height: none; overflow: visible; }
  .target-filter-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
  .selected-target-card { grid-template-columns: repeat(3, minmax(0, 1fr)); align-items: center; }
  .risk-grid { grid-template-columns: 1fr; }
  .risk-grid .assistant-chat { max-height: 250px; }
}

@media (max-width: 900px) {
  .brand-title {
    font-size: 22px;
  }

  .gauge-grid,
  .ai-config-grid,
  .assistant-meta-grid,
  .radar-filter-grid,
  .target-filter-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .forecast-layout, .prediction-conclusion-grid { grid-template-columns: 1fr; }
  .conclusion-header { align-items: flex-start; flex-direction: column; }
  .risk-grid .ai-layout { grid-template-columns: 1fr; }
  .risk-grid .ai-card { height: auto; }
  .risk-grid .ai-content { height: auto; max-height: 440px; }
  .risk-grid .assistant-panel { height: 400px; }

  .card-head-inline,
  .filter-toolbar,
  .ai-config-actions,
  .assistant-actions,
  .target-filter-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .scope-badges {
    flex-wrap: wrap;
  }

  .filter-select {
    width: 100%;
  }

  .forecast-meta {
    grid-template-columns: 1fr;
  }
  
  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>

