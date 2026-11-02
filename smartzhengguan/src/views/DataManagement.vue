<template>
  <div class="data-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>数据管理</span>
        </div>
      </template>

      <el-tabs v-model="activeTab" type="border-card">
        <!-- 数据导入 Tab -->
        <el-tab-pane label="数据导入" name="import">
          <div class="import-wizard">
            <el-steps :active="currentStep" align-center finish-status="success">
              <el-step title="文件上传" />
              <el-step title="Sheet识别" />
              <el-step title="字段映射" />
              <el-step title="更新策略" />
              <el-step title="校验预览" />
              <el-step title="确认导入" />
            </el-steps>

            <!-- 步骤1: 文件上传 -->
            <div v-if="currentStep === 0" class="step-content">
              <el-upload
                ref="uploadRef"
                class="upload-demo"
                drag
                :action="uploadUrl"
                :headers="uploadHeaders"
                :on-success="handleUploadSuccess"
                :on-error="handleUploadError"
                :before-upload="beforeUpload"
                :auto-upload="true"
                accept=".xlsx,.xls,.csv"
              >
                <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                <div class="el-upload__text">
                  拖拽文件到此处或 <em>点击上传</em>
                </div>
                <template #tip>
                  <div class="el-upload__tip">
                    支持 xlsx、xls、csv 格式，文件大小不超过 50MB
                  </div>
                </template>
              </el-upload>
            </div>

            <!-- 步骤2: Sheet识别 -->
            <div v-if="currentStep === 1" class="step-content">
              <el-table :data="identificationResults" border style="width: 100%">
                <el-table-column prop="sheet_name" label="Sheet名称" width="150" />
                <el-table-column prop="row_count" label="数据行数" width="100" />
                <el-table-column prop="best_match" label="识别模块" width="150" />
                <el-table-column prop="confidence" label="置信度" width="100">
                  <template #default="scope">
                    {{ (scope.row.confidence * 100).toFixed(0) }}%
                  </template>
                </el-table-column>
                <el-table-column label="候选模块">
                  <template #default="scope">
                    <el-tag
                      v-for="candidate in scope.row.candidate_modules"
                      :key="candidate.module"
                      style="margin-right: 5px"
                    >
                      {{ candidate.module }} ({{ (candidate.score * 100).toFixed(0) }}%)
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="手动选择" width="200">
                  <template #default="scope">
                    <el-select v-model="scope.row.best_match" placeholder="选择模块">
                      <el-option label="学生信息" value="student" />
                      <el-option label="奖学金" value="scholarship" />
                      <el-option label="就业信息" value="employment" />
                      <el-option label="课程成绩（暂不支持导入）" value="course_grade" />
                      <el-option label="不支持的 Sheet" value="unsupported" />
                    </el-select>
                  </template>
                </el-table-column>
              </el-table>

              <div class="step-actions">
                <el-button @click="currentStep--">上一步</el-button>
                <el-button type="primary" @click="confirmIdentification">下一步</el-button>
              </div>
            </div>

            <!-- 步骤3: 字段映射 -->
            <div v-if="currentStep === 2" class="step-content">
              <div class="mapping-container">
                <el-alert
                  title="提示：将左侧文件列映射到右侧系统字段，必填项标红"
                  type="info"
                  :closable="false"
                  style="margin-bottom: 20px"
                />

                <el-table :data="mappingData" border style="width: 100%">
                  <el-table-column prop="sheet_name" label="Sheet" width="140" />
                  <el-table-column prop="file_column" label="文件列名" width="200" />
                  <el-table-column label="样例值" width="150">
                    <template #default="scope">
                      {{ scope.row.sample_value }}
                    </template>
                  </el-table-column>
                  <el-table-column label="映射到系统字段" width="250">
                    <template #default="scope">
                      <el-select
                        v-model="scope.row.target_field"
                        placeholder="选择字段"
                        filterable
                      >
                        <el-option
                          v-for="field in fieldsForSheet(scope.row.sheet_name)"
                          :key="field.field_code"
                          :label="field.field_name_cn"
                          :value="field.field_code"
                        />
                      </el-select>
                    </template>
                  </el-table-column>
                  <el-table-column label="自定义表头" width="150">
                    <template #default="scope">
                      <el-input
                        v-model="scope.row.custom_header"
                        placeholder="可选"
                        size="small"
                      />
                    </template>
                  </el-table-column>
                </el-table>
              </div>

              <div class="step-actions">
                <el-button @click="currentStep--">上一步</el-button>
                <el-button type="primary" @click="confirmMapping">下一步</el-button>
              </div>
            </div>

            <!-- 步骤4: 更新策略 -->
            <div v-if="currentStep === 3" class="step-content">
              <div class="strategy-header">
                <h3>选择数据更新策略</h3>
                <p class="strategy-subtitle">根据您的需求选择合适的数据处理方式</p>
              </div>

              <div class="strategy-grid">
                <div
                  v-for="strategy in strategies"
                  :key="strategy.value"
                  class="strategy-card-wrapper"
                  :class="{ active: updateStrategy === strategy.value }"
                  @click="updateStrategy = strategy.value"
                >
                  <div class="strategy-card-new">
                    <div class="strategy-icon-new" :style="{ background: strategy.iconBg }">
                      <el-icon :size="28" :color="strategy.iconColor">
                        <CirclePlus v-if="strategy.icon === 'CirclePlus'" />
                        <Edit v-else-if="strategy.icon === 'Edit'" />
                        <RefreshRight v-else-if="strategy.icon === 'RefreshRight'" />
                        <CircleCheck v-else-if="strategy.icon === 'CircleCheck'" />
                      </el-icon>
                    </div>
                    <div class="strategy-content-new">
                      <div class="strategy-title-new">{{ strategy.title }}</div>
                      <div class="strategy-desc-new">{{ strategy.desc }}</div>
                      <div class="strategy-tags">
                        <el-tag
                          v-for="tag in strategy.tags"
                          :key="tag.text"
                          size="small"
                          :type="tag.type"
                        >
                          {{ tag.text }}
                        </el-tag>
                      </div>
                    </div>
                    <div class="strategy-check">
                      <el-icon v-if="updateStrategy === strategy.value" :size="24" color="#409eff">
                        <CircleCheck />
                      </el-icon>
                    </div>
                  </div>
                </div>
              </div>

              <div class="step-actions">
                <el-button @click="currentStep--" size="large">
                  <el-icon><ArrowLeft /></el-icon>
                  上一步
                </el-button>
                <el-button type="primary" @click="openPreview" size="large">
                  下一步
                  <el-icon><ArrowRight /></el-icon>
                </el-button>
              </div>
            </div>

            <!-- 步骤5: 校验预览 -->
            <div v-if="currentStep === 4" class="step-content">
              <el-alert v-if="!previewReady" :title="previewLoading ? '正在读取文件并校验，请稍候…' : (previewError || '尚未执行预览，统计结果暂不可用')" :type="previewError ? 'error' : 'info'" :closable="false" style="margin-bottom: 16px" />
              <el-descriptions title="预览摘要" :column="3" border>
                <el-descriptions-item label="新增记录">
                  <el-tag type="success">{{ previewReady ? previewResult.new_count : '—' }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="更新记录">
                  <el-tag type="warning">{{ previewReady ? previewResult.update_count : '—' }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="不变记录">
                  <el-tag type="info">{{ previewReady ? previewResult.unchanged_count : '—' }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="错误记录">
                  <el-tag type="danger">{{ previewReady ? previewResult.error_count : '—' }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="跳过记录">
                  <el-tag>{{ previewReady ? previewResult.skipped_count : '—' }}</el-tag>
                </el-descriptions-item>
              </el-descriptions>
              <template v-if="previewReady">
                <p>读取数据共 {{ previewResult.total_rows }} 行，以下为各 Sheet 的实际处理结果：</p>
                <el-alert v-for="warning in validationWarnings" :key="warning.sheet + warning.message" :title="warning.message" type="warning" :closable="false" style="margin-bottom: 10px" />
                <el-table :data="previewResult.sheets" border>
                  <el-table-column prop="sheet_name" label="Sheet" />
                  <el-table-column prop="row_count" label="读取行数" />
                  <el-table-column prop="new_count" label="新增" />
                  <el-table-column prop="update_count" label="更新" />
                  <el-table-column prop="unchanged_count" label="不变" />
                  <el-table-column prop="error_count" label="错误" />
                  <el-table-column prop="skipped_count" label="跳过" />
                </el-table>
              </template>

              <div v-if="validationErrors.length > 0" style="margin-top: 20px">
                <el-alert
                  title="发现数据错误"
                  type="error"
                  :closable="false"
                  style="margin-bottom: 10px"
                >
                  <div>
                    共 {{ validationErrors.length }} 条错误，请修正后重新上传
                  </div>
                </el-alert>

                <el-table :data="validationErrors" border style="width: 100%" max-height="300">
                  <el-table-column prop="sheet" label="Sheet" width="140" />
                  <el-table-column prop="row" label="行号" width="80" />
                  <el-table-column prop="field" label="字段" width="150" />
                  <el-table-column prop="message" label="错误信息" />
                </el-table>
              </div>

              <div class="step-actions">
                <el-button @click="currentStep--">上一步</el-button>
                <el-button
                  type="primary"
                  :loading="previewLoading"
                  @click="validateAndPreview"
                >
                  {{ previewReady ? '重新预览' : '执行预览' }}
                </el-button>
                <el-button
                  v-if="previewReady && !previewLoading && !validationErrors.length && (previewResult.new_count > 0 || previewResult.update_count > 0 || updateStrategy === 'validate_only')"
                  type="success"
                  @click="currentStep++"
                >
                  确认导入
                </el-button>
              </div>
            </div>

            <!-- 步骤6: 确认导入 -->
            <div v-if="currentStep === 5" class="step-content">
              <el-result
                icon="warning"
                title="确认导入"
                sub-title="即将导入数据到正式环境，请再次确认"
              >
                <template #extra>
                  <el-button @click="currentStep--">返回修改</el-button>
                  <el-button type="primary" @click="confirmImport">确认导入</el-button>
                </template>
              </el-result>
            </div>
          </div>
        </el-tab-pane>

        <!-- 导入批次 Tab -->
        <el-tab-pane label="导入批次" name="batches">
          <el-table :data="batchList" border style="width: 100%">
            <el-table-column prop="file_name" label="文件名" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="scope">
                <el-tag :type="getBatchStatusType(scope.row.status)">
                  {{ scope.row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="total_rows" label="总行数" width="100" />
            <el-table-column prop="new_count" label="新增" width="80" />
            <el-table-column prop="update_count" label="更新" width="80" />
            <el-table-column prop="error_count" label="错误" width="80" />
            <el-table-column prop="operator" label="操作人" width="120" />
            <el-table-column prop="created_at" label="创建时间" width="180" />
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="scope">
                <el-button size="small" @click="viewBatchDetail(scope.row)">
                  查看
                </el-button>
                <el-button
                  size="small"
                  type="danger"
                  :disabled="scope.row.status !== 'completed'"
                  @click="revertBatch(scope.row)"
                >
                  撤销
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-model:current-page="batchPage"
            v-model:page-size="batchPageSize"
            :total="batchTotal"
            layout="total, sizes, prev, pager, next, jumper"
            @current-change="loadBatchList"
            @size-change="loadBatchList"
          />
        </el-tab-pane>

        <!-- 映射模板 Tab -->
        <el-tab-pane label="映射模板" name="templates">
          <el-button type="primary" @click="saveAsTemplate">保存当前映射为模板</el-button>

          <el-table :data="templateList" border style="width: 100%; margin-top: 20px">
            <el-table-column prop="name" label="模板名称" />
            <el-table-column prop="target_module" label="目标模块" width="150" />
            <el-table-column prop="version" label="版本" width="80" />
            <el-table-column prop="is_public" label="公开" width="80">
              <template #default="scope">
                <el-tag v-if="scope.row.is_public" type="success">是</el-tag>
                <el-tag v-else type="info">否</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="180" />
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="scope">
                <el-button size="small" type="danger" @click="deleteTemplate(scope.row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 导出记录 Tab -->
        <el-tab-pane label="导出记录" name="export-records">
          <el-table :data="exportRecordList" border style="width: 100%">
            <el-table-column prop="file_name" label="文件名" />
            <el-table-column prop="export_type" label="导出类型" width="120">
              <template #default="scope">
                <el-tag v-if="scope.row.export_type === 'student_list'" type="primary">
                  学生名单
                </el-tag>
                <el-tag v-else type="success">汇总表</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="scope">
                <el-tag :type="getExportStatusType(scope.row.status)">
                  {{ scope.row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="row_count" label="行数" width="80" />
            <el-table-column prop="created_at" label="创建时间" width="180" />
            <el-table-column prop="expires_at" label="过期时间" width="180" />
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="scope">
                <el-button
                  v-if="!scope.row.is_expired"
                  size="small"
                  type="primary"
                  @click="downloadExportFile(scope.row)"
                >
                  下载
                </el-button>
                <el-tag v-else type="info">已过期</el-tag>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-model:current-page="exportRecordPage"
            v-model:page-size="exportRecordPageSize"
            :total="exportRecordTotal"
            layout="total, sizes, prev, pager, next, jumper"
            @current-change="loadExportRecords"
            @size-change="loadExportRecords"
          />
        </el-tab-pane>

        <!-- 导出模板 Tab -->
        <el-tab-pane label="导出模板" name="export-templates">
          <el-button type="primary" @click="showSaveExportTemplate">保存导出配置为模板</el-button>

          <el-table :data="exportTemplateList" border style="width: 100%; margin-top: 20px">
            <el-table-column prop="name" label="模板名称" />
            <el-table-column prop="version" label="版本" width="80" />
            <el-table-column prop="is_public" label="公开" width="80">
              <template #default="scope">
                <el-tag v-if="scope.row.is_public" type="success">是</el-tag>
                <el-tag v-else type="info">否</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="字段数量" width="100">
              <template #default="scope">
                {{ scope.row.fields.length }}
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="180" />
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="scope">
                <el-button size="small" @click="useExportTemplate(scope.row)">
                  使用
                </el-button>
                <el-button size="small" type="danger" @click="deleteExportTemplate(scope.row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled, CirclePlus, Edit, RefreshRight, CircleCheck, ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import uploadService, { UPLOAD_API_BASE_URL } from '@/services/uploadService'
import exportService from '@/services/exportService'

// 当前激活的 Tab
const activeTab = ref('import')

// 导入向导当前步骤
const currentStep = ref(0)

// 上传相关
const uploadUrl = ref(`${UPLOAD_API_BASE_URL}/upload/file/`)
const uploadHeaders = ref({
  // Authorization: `Bearer ${localStorage.getItem('token')}`
})

// 批次ID
const batchId = ref('')

// Sheet 识别结果
const identificationResults = ref([])

// 字段映射数据
const mappingData = ref([])
const availableFields = ref([])
const fieldsForSheet = (name) => availableFields.value[name] || []

// 更新策略
const updateStrategy = ref('create_only')

// 策略选项配置
const strategies = [
  {
    value: 'create_only',
    title: '仅新增',
    desc: '只创建不存在的记录，已存在的记录将被跳过',
    icon: 'CirclePlus',
    iconColor: '#4caf50',
    iconBg: '#e8f5e9',
    tags: [
      { text: '推荐', type: 'success' },
      { text: '安全', type: 'info' }
    ]
  },
  {
    value: 'update_empty',
    title: '更新空值',
    desc: '更新已存在记录的空字段，非空字段保持不变',
    icon: 'Edit',
    iconColor: '#ff9800',
    iconBg: '#fff3e0',
    tags: [
      { text: '常用', type: 'warning' }
    ]
  },
  {
    value: 'overwrite',
    title: '覆盖现值',
    desc: '完全覆盖已存在的记录，旧数据将被替换',
    icon: 'RefreshRight',
    iconColor: '#f44336',
    iconBg: '#ffebee',
    tags: [
      { text: '谨慎使用', type: 'danger' }
    ]
  },
  {
    value: 'validate_only',
    title: '仅校验',
    desc: '只检查数据有效性，不实际导入数据',
    icon: 'CircleCheck',
    iconColor: '#2196f3',
    iconBg: '#e3f2fd',
    tags: [
      { text: '测试', type: 'info' }
    ]
  }
]


// 校验和预览结果
const validationErrors = ref([])
const validationWarnings = ref([])
const previewReady = ref(false)
const previewLoading = ref(false)
const previewError = ref('')
watch(updateStrategy, () => { previewReady.value = false })
const previewResult = ref({
  new_count: 0,
  update_count: 0,
  unchanged_count: 0,
  error_count: 0,
  skipped_count: 0,
  sample_changes: []
})

// 批次列表
const batchList = ref([])
const batchPage = ref(1)
const batchPageSize = ref(20)
const batchTotal = ref(0)

// 模板列表
const templateList = ref([])

// 导出记录列表
const exportRecordList = ref([])
const exportRecordPage = ref(1)
const exportRecordPageSize = ref(20)
const exportRecordTotal = ref(0)

// 导出模板列表
const exportTemplateList = ref([])

// 文件上传前验证
const beforeUpload = (file) => {
  const isValidType = ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                       'application/vnd.ms-excel',
                       'text/csv'].includes(file.type)
  const isLt50M = file.size / 1024 / 1024 < 50

  if (!isValidType) {
    ElMessage.error('只能上传 xlsx、xls 或 csv 格式的文件')
    return false
  }
  if (!isLt50M) {
    ElMessage.error('文件大小不能超过 50MB')
    return false
  }
  return true
}

// 文件上传成功
const handleUploadSuccess = (response) => {
  previewReady.value = false
  previewError.value = ''
  validationErrors.value = []
  validationWarnings.value = []
  ElMessage.success('文件上传成功')
  batchId.value = response.batch_id

  // 自动进行 Sheet 识别
  identifySheets()
}

// 文件上传失败
const handleUploadError = (error) => {
  ElMessage.error('文件上传失败: ' + error.message)
}

// Sheet 识别
const identifySheets = async () => {
  try {
    const response = await uploadService.identifySheets(batchId.value)
    identificationResults.value = response.identification_results
    currentStep.value = 1
  } catch (error) {
    ElMessage.error('Sheet 识别失败: ' + error.message)
  }
}

// 确认识别结果
const confirmIdentification = async () => {
  try {
    await uploadService.identifySheets(batchId.value, Object.fromEntries(identificationResults.value.map(item => [item.sheet_name, item.best_match])))
    const response = await uploadService.getMappingStatus(batchId.value)
    availableFields.value = Object.fromEntries(response.sheets.map(sheet => [sheet.sheet_name, sheet.fields]))
    mappingData.value = response.sheets.flatMap(sheet => sheet.headers.map((header, index) => ({
      sheet_name: sheet.sheet_name, file_column: header,
      sample_value: sheet.sample_values[index] || '',
      target_field: sheet.mapping[header] || '', custom_header: '',
    })).filter(item => item.file_column))
    currentStep.value = 2
  } catch (error) {
    ElMessage.error('确认识别失败: ' + error.message)
  }
}

// 确认字段映射
const confirmMapping = async () => {
  try {
    for (const sheet of identificationResults.value) {
      const mapping = Object.fromEntries(mappingData.value.filter(item => item.sheet_name === sheet.sheet_name && item.target_field).map(item => [item.file_column, item.target_field]))
      await uploadService.saveMapping(batchId.value, sheet.sheet_name, mapping)
    }
    previewReady.value = false
    ElMessage.success('字段映射保存成功')
    currentStep.value = 3
  } catch (error) {
    ElMessage.error('保存映射失败: ' + error.message)
  }
}

// 校验和预览
const validateAndPreview = async () => {
  if (previewLoading.value) return
  previewLoading.value = true
  previewReady.value = false
  previewError.value = ''
  validationErrors.value = []
  validationWarnings.value = []
  try {
    const response = await uploadService.validateAndPreview(batchId.value, updateStrategy.value)
    validationErrors.value = response.validation.errors
    validationWarnings.value = response.validation.warnings || []
    previewResult.value = response.preview
    previewReady.value = true
    ElMessage.success('校验预览完成')
  } catch (error) {
    previewError.value = error.response?.data?.error || error.message
    ElMessage.error('校验预览失败: ' + previewError.value)
  } finally {
    previewLoading.value = false
  }
}
const openPreview = () => {
  currentStep.value = 4
  validateAndPreview()
}

// 确认导入
const confirmImport = async () => {
  try {
    await ElMessageBox.confirm('确认导入数据到正式环境？', '警告', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning',
    })

    const response = await uploadService.confirmImport(batchId.value, updateStrategy.value)
    ElMessage.success('导入成功')

    // 重置向导
    currentStep.value = 0
    batchId.value = ''

    // 刷新批次列表
    activeTab.value = 'batches'
    loadBatchList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('导入失败: ' + error.message)
    }
  }
}

// 加载批次列表
const loadBatchList = async () => {
  try {
    const response = await uploadService.getBatchList(batchPage.value, batchPageSize.value)
    batchList.value = response.results
    batchTotal.value = response.total
  } catch (error) {
    ElMessage.error('加载批次列表失败: ' + error.message)
  }
}

// 查看批次详情
const viewBatchDetail = (batch) => {
  ElMessage.info('查看批次详情: ' + batch.batch_id)
}

// 撤销批次
const revertBatch = async (batch) => {
  try {
    await ElMessageBox.confirm('确认撤销此批次的导入？', '警告', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning',
    })

    await uploadService.revertBatch(batch.batch_id)
    ElMessage.success('批次撤销成功')
    loadBatchList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('撤销失败: ' + error.message)
    }
  }
}

// 保存为模板
const saveAsTemplate = () => {
  ElMessage.info('保存为模板功能待实现')
}

// 删除模板
const deleteTemplate = (template) => {
  ElMessage.info('删除模板: ' + template.name)
}

// 加载导出记录
const loadExportRecords = async () => {
  try {
    const response = await exportService.getExportRecords(exportRecordPage.value, exportRecordPageSize.value)
    exportRecordList.value = response.results
    exportRecordTotal.value = response.total
  } catch (error) {
    ElMessage.error('加载导出记录失败: ' + error.message)
  }
}

// 下载导出文件
const downloadExportFile = (record) => {
  const downloadUrl = exportService.getDownloadUrl(record.record_id)
  window.open(downloadUrl, '_blank')
}

// 获取导出状态类型
const getExportStatusType = (status) => {
  const typeMap = {
    'completed': 'success',
    'failed': 'danger',
    'pending': 'warning',
    'expired': 'info',
  }
  return typeMap[status] || 'info'
}

// 加载导出模板列表
const loadExportTemplates = async () => {
  try {
    const response = await exportService.getExportTemplates()
    exportTemplateList.value = response.results
  } catch (error) {
    ElMessage.error('加载导出模板失败: ' + error.message)
  }
}

// 显示保存导出模板对话框
const showSaveExportTemplate = () => {
  ElMessage.info('保存导出模板功能待实现')
}

// 使用导出模板
const useExportTemplate = (template) => {
  ElMessage.info('使用模板: ' + template.name)
}

// 删除导出模板
const deleteExportTemplate = async (template) => {
  try {
    await ElMessageBox.confirm('确认删除此模板？', '警告', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning',
    })

    await exportService.deleteExportTemplate(template.id)
    ElMessage.success('模板删除成功')
    loadExportTemplates()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + error.message)
    }
  }
}

// 获取批次状态类型
const getBatchStatusType = (status) => {
  const typeMap = {
    'completed': 'success',
    'failed': 'danger',
    'draft': 'info',
    'parsing': 'warning',
    'mapping': 'warning',
    'validating': 'warning',
    'previewing': 'warning',
  }
  return typeMap[status] || 'info'
}

onMounted(() => {
  // 暂时不加载数据，避免后端未启动时的错误提示
  // 如果需要启用这些功能，请先启动后端服务器：cd backend && python manage.py runserver
  // loadBatchList()
  // loadExportRecords()
  // loadExportTemplates()
})
</script>

<style scoped>
.data-management {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.import-wizard {
  padding: 20px;
}

.step-content {
  margin-top: 40px;
  min-height: 400px;
}

.step-actions {
  margin-top: 30px;
  text-align: center;
}

.upload-demo {
  width: 100%;
}

.strategy-header {
  text-align: center;
  margin-bottom: 32px;
}

.strategy-header h3 {
  font-size: 22px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.strategy-subtitle {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.strategy-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 40px;
}

.strategy-card-wrapper {
  cursor: pointer;
  transition: all 0.3s ease;
}

.strategy-card-new {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 24px;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  background: #ffffff;
  transition: all 0.3s ease;
  height: 100%;
  position: relative;
}

.strategy-card-wrapper:hover .strategy-card-new {
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
  transform: translateY(-2px);
}

.strategy-card-wrapper.active .strategy-card-new {
  border-color: #409eff;
  background: #f0f7ff;
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.25);
}

.strategy-icon-new {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.strategy-content-new {
  flex: 1;
  min-width: 0;
}

.strategy-title-new {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.strategy-desc-new {
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 12px;
}

.strategy-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.strategy-check {
  position: absolute;
  top: 20px;
  right: 20px;
}

.strategy-group {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 24px;
}

.strategy-radio {
  width: 100%;
  margin-right: 0 !important;
  display: flex;
  align-items: flex-start;
}

.strategy-radio :deep(.el-radio__input) {
  margin-top: 24px;
}

.strategy-radio :deep(.el-radio__label) {
  width: 100%;
  padding: 0;
  padding-left: 12px;
}

.strategy-card {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 20px;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  background: #ffffff;
  transition: all 0.3s ease;
  cursor: pointer;
  width: 100%;
}

.strategy-card:hover {
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
  transform: translateY(-2px);
}

.strategy-radio.is-checked .strategy-card {
  border-color: #409eff;
  background: #f0f7ff;
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.2);
}

.strategy-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.strategy-content {
  flex: 1;
}

.strategy-option {
  margin-left: 10px;
}

.strategy-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.strategy-desc {
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 8px;
}

.strategy-tag {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.mapping-container {
  max-height: 500px;
  overflow-y: auto;
}
</style>
