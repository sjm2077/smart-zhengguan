
<template>
  <div class="employment-page">
    <header class="page-header">
      <div>
        <div class="eyebrow">TEACHING MANAGEMENT</div>
        <h1>毕业生就业统计管理</h1>
        <p>维护各学院毕业生就业去向统计，数据保存后自动同步至首页。</p>
      </div>
      <button class="btn btn-secondary" :disabled="loading" @click="loadStats">
        {{ loading ? '正在查询...' : '刷新数据' }}
      </button>
    </header>

    <section class="summary-grid">
      <article class="summary-card">
        <span class="summary-label">当前统计学院</span>
        <strong>{{ currentCollegeName }}</strong>
        <small>按所选学院统计</small>
      </article>
      <article class="summary-card">
        <span class="summary-label">毕业年份</span>
        <strong>{{ year }} 届</strong>
        <small>可切换历史毕业年份</small>
      </article>
      <article class="summary-card">
        <span class="summary-label">毕业去向统计人数</span>
        <strong>{{ total.toLocaleString() }}</strong>
        <small>各去向汇总人数</small>
      </article>
    </section>

    <section class="panel">
      <div class="panel-heading">
        <div>
          <h2>统计范围</h2>
          <p>选择学院和毕业年份，查询对应统计数据。</p>
        </div>
      </div>

      <div class="filter-grid">
        <label class="field">
          <span>所属学院</span>
          <select v-model.number="collegeId">
            <option :value="0" disabled>请选择学院</option>
            <option v-for="college in colleges" :key="college.id" :value="college.id">
              {{ college.name }}
            </option>
          </select>
        </label>

        <label class="field">
          <span>毕业年份</span>
          <input v-model.number="year" type="number" min="2000" max="2100" />
        </label>

        <button class="btn btn-primary filter-button" :disabled="loading" @click="loadStats">
          查询统计
        </button>
      </div>
    </section>

    <section class="panel">
      <div class="panel-heading">
        <div>
          <h2>{{ editing ? '修改就业统计' : '登记就业统计' }}</h2>
          <p>请依据正式就业统计资料填写人数，不要使用估算或虚构数据。</p>
        </div>
        <span class="permission-tag">管理员 / 教务管理</span>
      </div>

      <form class="entry-form" @submit.prevent="saveRecord">
        <label class="field">
          <span>就业去向类别</span>
          <select v-model="form.destination_type" required>
            <option v-for="item in categories" :key="item.value" :value="item.value">
              {{ item.label }}
            </option>
          </select>
        </label>

        <label class="field">
          <span>统计人数</span>
          <input
            v-model.number="form.count"
            type="number"
            min="0"
            step="1"
            required
            placeholder="请输入实际统计人数"
          />
        </label>

        <div class="form-actions">
          <button class="btn btn-primary" type="submit" :disabled="saving || !collegeId">
            {{ saving ? '正在保存...' : editing ? '保存修改' : '保存统计' }}
          </button>
          <button v-if="editing" class="btn btn-secondary" type="button" @click="cancelEdit">
            取消修改
          </button>
        </div>
      </form>

      <div v-if="successMessage" class="feedback success">{{ successMessage }}</div>
      <div v-if="errorMessage" class="feedback error">{{ errorMessage }}</div>
    </section>

    <section class="panel">
      <div class="panel-heading">
        <div>
          <h2>就业去向明细</h2>
          <p>当前学院及毕业年份的统计结果。</p>
        </div>
        <span class="record-count">共 {{ categories.length }} 类</span>
      </div>

      <div v-if="loading" class="empty-state">正在加载统计数据...</div>
      <div v-else-if="loadError" class="empty-state error-text">
        统计数据加载失败，请检查接口或登录状态后重试。
      </div>
      <div v-else-if="!collegeId" class="empty-state">
        请先选择学院。
      </div>
      <div v-else class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>序号</th>
              <th>就业去向类别</th>
              <th class="number-cell">统计人数</th>
              <th>占当前汇总比例</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in categories" :key="item.value">
              <td>{{ index + 1 }}</td>
              <td>{{ item.label }}</td>
              <td class="number-cell">{{ getCount(item.value).toLocaleString() }}</td>
              <td>
                <div class="ratio-cell">
                  <div class="ratio-track">
                    <div
                      class="ratio-fill"
                      :style="{ width: getRatio(item.value) + '%' }"
                    ></div>
                  </div>
                  <span>{{ getRatio(item.value).toFixed(1) }}%</span>
                </div>
              </td>
              <td>
                <button class="text-button" @click="editRecord(item.value)">
                  编辑
                </button>
              </td>
            </tr>
          </tbody>
          <tfoot>
            <tr>
              <td colspan="2">汇总人数</td>
              <td class="number-cell">{{ total.toLocaleString() }}</td>
              <td colspan="2">仅统计已登记的去向类别</td>
            </tr>
          </tfoot>
        </table>
      </div>

      <p class="table-note">
        未登记的类别显示为 0，仅代表当前没有已登记的统计值，不代表该类别实际人数为零。
      </p>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import {
  getColleges,
  getGraduateEmploymentStats,
  saveGraduateEmploymentStat,
  type CollegeItem,
} from '@/api/dashboard'

const categories = [
  { value: 'employment', label: '协议 / 合同就业' },
  { value: 'further_study', label: '升学' },
  { value: 'civil_service', label: '考公考编' },
  { value: 'flexible', label: '灵活就业' },
  { value: 'entrepreneurship', label: '自主创业' },
  { value: 'unemployed', label: '待就业' },
  { value: 'other', label: '其他' },
]

interface EmploymentRow {
  name: string
  value: number
}

const colleges = ref<CollegeItem[]>([])
const collegeId = ref(0)
const year = ref(new Date().getFullYear())
const rows = ref<EmploymentRow[]>([])
const loading = ref(false)
const saving = ref(false)
const loadError = ref(false)
const successMessage = ref('')
const errorMessage = ref('')
const editing = ref(false)

type EmploymentDestination =
  | 'employment'
  | 'further_study'
  | 'civil_service'
  | 'flexible'
  | 'entrepreneurship'
  | 'unemployed'
  | 'other'

const form = reactive<{
  destination_type: EmploymentDestination
  count: number
}>({
  destination_type: 'employment',
  count: 0,
})

const currentCollegeName = computed(
  () => colleges.value.find(item => item.id === collegeId.value)?.name || '尚未选择',
)

const total = computed(() =>
  rows.value.reduce((sum, item) => sum + Number(item.value || 0), 0),
)

function getCount(type: string): number {
  const label = categories.find(item => item.value === type)?.label
  return Number(rows.value.find(item => item.name === label)?.value || 0)
}

function getRatio(type: string): number {
  return total.value > 0 ? (getCount(type) / total.value) * 100 : 0
}

function validateFilters(): boolean {
  if (!Number.isInteger(collegeId.value) || collegeId.value <= 0) {
    errorMessage.value = '请先选择有效的学院。'
    return false
  }
  if (!Number.isInteger(year.value) || year.value < 2000 || year.value > 2100) {
    errorMessage.value = '毕业年份必须为 2000 至 2100 之间的整数。'
    return false
  }
  return true
}

async function loadColleges(): Promise<void> {
  const response: unknown = await getColleges()
  const data = response as {
    results?: CollegeItem[]
  } | CollegeItem[]

  colleges.value = Array.isArray(data)
    ? data
    : Array.isArray(data?.results)
      ? data.results
      : []

  const firstCollege = colleges.value[0]

if (!collegeId.value && firstCollege) {
  collegeId.value = firstCollege.id
}
}

async function loadStats(): Promise<void> {
  successMessage.value = ''
  errorMessage.value = ''

  if (!validateFilters()) return

  loading.value = true
  loadError.value = false

  try {
    const response = await getGraduateEmploymentStats({
      year: year.value,
      college_id: collegeId.value,
    })
    rows.value = Array.isArray(response.data) ? response.data : []
  } catch (error: any) {
    rows.value = []
    loadError.value = true
    errorMessage.value =
      error?.response?.data?.detail || '统计查询失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

function editRecord(type: string): void {
  function editRecord(type: EmploymentDestination): void {
  form.destination_type = type
  form.count = getCount(type)
  editing.value = true
  successMessage.value = ''
  errorMessage.value = ''
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
  editing.value = true
  successMessage.value = ''
  errorMessage.value = ''
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function cancelEdit(): void {
  editing.value = false
  form.destination_type = 'employment'
  form.count = 0
  errorMessage.value = ''
}

async function saveRecord(): Promise<void> {
  successMessage.value = ''
  errorMessage.value = ''

  if (!validateFilters()) return

  if (!Number.isInteger(form.count) || form.count < 0) {
    errorMessage.value = '统计人数必须为大于或等于 0 的整数。'
    return
  }

  saving.value = true

  try {
    await saveGraduateEmploymentStat({
      year: year.value,
      college_id: collegeId.value,
      destination_type: form.destination_type,
      count: form.count,
    })

    successMessage.value = '就业统计保存成功，首页将在重新加载后显示更新数据。'
    editing.value = false
    form.destination_type = 'employment'
    form.count = 0

    await loadStats()
  } catch (error: any) {
    errorMessage.value =
      error?.response?.data?.detail || '保存失败，请检查权限和填写内容。'
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  try {
    await loadColleges()
    if (collegeId.value) {
      await loadStats()
    }
  } catch (error: any) {
    loadError.value = true
    errorMessage.value =
      error?.response?.data?.detail || '学院数据加载失败，请检查登录状态和接口。'
  }
})
</script>

<style scoped>
.employment-page {
  min-height: 100%;
  padding: 28px 32px 40px;
  color: #1e293b;
  background: #f5f7fb;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  margin-bottom: 26px;
}

.eyebrow {
  margin-bottom: 8px;
  color: #64748b;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1.5px;
}

.page-header h1 {
  margin: 0;
  font-size: 26px;
  font-weight: 700;
}

.page-header p,
.panel-heading p {
  margin: 9px 0 0;
  color: #64748b;
  font-size: 13px;
  line-height: 1.7;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
  margin-bottom: 20px;
}

.summary-card,
.panel {
  background: #fff;
  border: 1px solid #e7ebf2;
  border-radius: 12px;
  box-shadow: 0 3px 12px rgb(15 23 42 / 3%);
}

.summary-card {
  padding: 22px 24px;
}

.summary-label {
  display: block;
  color: #64748b;
  font-size: 13px;
}

.summary-card strong {
  display: block;
  margin: 12px 0 8px;
  font-size: 24px;
  font-weight: 700;
  overflow-wrap: anywhere;
}

.summary-card small {
  color: #94a3b8;
  font-size: 12px;
}

.panel {
  margin-bottom: 20px;
  padding: 24px;
}

.panel-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 22px;
}

.panel-heading h2 {
  margin: 0;
  font-size: 17px;
}

.filter-grid,
.entry-form {
  display: grid;
  grid-template-columns: minmax(180px, 1fr) minmax(180px, 1fr) auto;
  align-items: end;
  gap: 18px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 9px;
  min-width: 0;
}

.field span {
  color: #475569;
  font-size: 13px;
  font-weight: 600;
}

.field input,
.field select {
  width: 100%;
  min-height: 42px;
  padding: 0 12px;
  color: #334155;
  background: #fff;
  border: 1px solid #dbe2ea;
  border-radius: 7px;
  outline: none;
  font-size: 13px;
}

.field input:focus,
.field select:focus {
  border-color: #5378d8;
  box-shadow: 0 0 0 3px rgb(83 120 216 / 10%);
}

.btn {
  min-height: 40px;
  padding: 0 17px;
  border: 1px solid transparent;
  border-radius: 7px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}

.btn:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.btn-primary {
  color: #fff;
  background: #315fc5;
}

.btn-primary:hover:not(:disabled) {
  background: #254da7;
}

.btn-secondary {
  color: #475569;
  background: #fff;
  border-color: #dbe2ea;
}

.filter-button {
  min-width: 104px;
}

.permission-tag {
  padding: 7px 10px;
  color: #315fc5;
  background: #edf3ff;
  border-radius: 6px;
  font-size: 12px;
  white-space: nowrap;
}

.form-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.feedback {
  margin-top: 18px;
  padding: 12px 14px;
  border-radius: 7px;
  font-size: 13px;
}

.success {
  color: #166534;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
}

.error {
  color: #b91c1c;
  background: #fef2f2;
  border: 1px solid #fecaca;
}

.record-count {
  color: #64748b;
  font-size: 12px;
}

.table-wrap {
  width: 100%;
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  text-align: left;
}

th,
td {
  padding: 15px 12px;
  border-bottom: 1px solid #edf0f5;
  white-space: nowrap;
}

th {
  color: #64748b;
  background: #f8fafc;
  font-weight: 600;
}

td {
  color: #334155;
}

.number-cell {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.ratio-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ratio-track {
  width: 90px;
  height: 6px;
  overflow: hidden;
  background: #edf1f7;
  border-radius: 6px;
}

.ratio-fill {
  height: 100%;
  background: #5278d5;
  border-radius: 6px;
  transition: width 0.2s ease;
}

.ratio-cell span {
  min-width: 42px;
  color: #64748b;
  font-size: 12px;
}

.text-button {
  padding: 5px 8px;
  color: #315fc5;
  background: transparent;
  border: 0;
  cursor: pointer;
}

.text-button:hover {
  text-decoration: underline;
}

tfoot td {
  color: #1e293b;
  background: #f8fafc;
  font-weight: 700;
}

.empty-state {
  padding: 35px 15px;
  color: #64748b;
  text-align: center;
  font-size: 13px;
}

.error-text {
  color: #b91c1c;
}

.table-note {
  margin: 15px 0 0;
  color: #94a3b8;
  font-size: 12px;
  line-height: 1.7;
}

@media (max-width: 850px) {
  .employment-page {
    padding: 20px 16px;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }

  .filter-grid,
  .entry-form {
    grid-template-columns: 1fr;
  }

  .page-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .panel {
    padding: 18px;
  }
}
</style>
