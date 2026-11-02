<template>
  <el-dialog
    v-model="visible"
    title="自定义学生名单导出"
    width="80%"
    @close="handleClose"
  >
    <div class="export-dialog">
      <!-- 筛选条件区 -->
      <el-card class="section-card" shadow="never">
        <template #header>
          <span>筛选条件</span>
        </template>
        <el-form :model="exportForm" label-width="100px">
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="年级">
                <el-select v-model="exportForm.filters.grade" placeholder="请选择年级" clearable>
                  <el-option label="2021级" value="2021级" />
                  <el-option label="2022级" value="2022级" />
                  <el-option label="2023级" value="2023级" />
                  <el-option label="2024级" value="2024级" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="学院">
                <el-input v-model="exportForm.filters.college" placeholder="请输入学院" clearable />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="专业">
                <el-input v-model="exportForm.filters.major" placeholder="请输入专业" clearable />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="培养层次">
                <el-select v-model="exportForm.filters.degree_type" placeholder="请选择" clearable>
                  <el-option label="学术硕士" value="academic_master" />
                  <el-option label="专业硕士" value="professional_master" />
                  <el-option label="博士" value="doctoral" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="学籍状态">
                <el-select v-model="exportForm.filters.current_status" placeholder="请选择" clearable>
                  <el-option label="在读" value="active" />
                  <el-option label="休学" value="suspended" />
                  <el-option label="退学" value="withdrawn" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="导师">
                <el-input v-model="exportForm.filters.advisor_name" placeholder="请输入导师姓名" clearable />
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </el-card>

      <!-- 字段选择区 -->
      <el-card class="section-card" shadow="never">
        <template #header>
          <span>字段选择</span>
        </template>
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="field-list-header">可选字段</div>
            <el-input
              v-model="fieldSearchText"
              placeholder="搜索字段"
              clearable
              style="margin-bottom: 10px"
            />
            <div class="field-list">
              <el-tree
                ref="fieldTreeRef"
                :data="availableFieldsTree"
                show-checkbox
                node-key="id"
                :default-checked-keys="selectedFieldIds"
                @check="handleFieldCheck"
              >
                <template #default="{ node, data }">
                  <span class="custom-tree-node">
                    <span>{{ node.label }}</span>
                    <el-tag v-if="data.data_granularity" size="small" type="info" style="margin-left: 5px">
                      {{ data.data_granularity }}
                    </el-tag>
                  </span>
                </template>
              </el-tree>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="field-list-header">已选字段（可拖拽排序）</div>
            <div class="selected-fields">
              <el-empty v-if="exportForm.fields.length === 0" description="请从左侧选择字段" />
              <draggable
                v-else
                v-model="exportForm.fields"
                item-key="field_code"
                class="draggable-list"
              >
                <template #item="{ element, index }">
                  <div class="selected-field-item">
                    <span class="field-name">{{ element.field_name_cn }}</span>
                    <el-tag v-if="element.data_granularity !== 'student'" size="small" type="warning">
                      {{ element.data_granularity }}
                    </el-tag>
                    <el-select
                      v-if="element.data_granularity !== 'student'"
                      v-model="exportForm.one_to_many_strategies[element.field_code]"
                      placeholder="处理策略"
                      size="small"
                      style="width: 150px; margin-left: 10px"
                    >
                      <el-option label="取最新一条" value="latest" />
                      <el-option label="记录数量" value="aggregate_count" />
                      <el-option label="金额合计" value="aggregate_sum" />
                      <el-option label="合并文本" value="merge_text" />
                      <el-option label="展开多行" value="expand_rows" />
                    </el-select>
                    <el-input
                      v-model="exportForm.field_aliases[element.field_code]"
                      placeholder="自定义表头"
                      size="small"
                      style="width: 120px; margin-left: 10px"
                    />
                    <el-button
                      type="danger"
                      size="small"
                      @click="removeField(index)"
                      style="margin-left: 10px"
                    >
                      删除
                    </el-button>
                  </div>
                </template>
              </draggable>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 预览区 -->
      <el-card class="section-card" shadow="never">
        <template #header>
          <span>导出预览</span>
        </template>
        <el-descriptions :column="3" border>
          <el-descriptions-item label="预计人数">
            <el-tag>{{ previewData.estimated_count }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="导出列数">
            <el-tag>{{ exportForm.fields.length }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="数据截止时间">
            {{ currentDateTime }}
          </el-descriptions-item>
        </el-descriptions>

        <el-alert
          v-if="exportForm.fields.length === 0"
          title="请至少选择一个字段"
          type="warning"
          :closable="false"
          style="margin-top: 10px"
        />
      </el-card>
    </div>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" :disabled="exportForm.fields.length === 0" @click="handleExport">
          导出
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import draggable from 'vuedraggable'
import exportService from '@/services/exportService'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  initialFilters: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue', 'export-success'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 表单数据
const exportForm = ref({
  filters: {},
  fields: [],
  one_to_many_strategies: {},
  field_aliases: {}
})

// 可选字段树
const availableFieldsTree = ref([])
const fieldSearchText = ref('')
const selectedFieldIds = ref([])

// 预览数据
const previewData = ref({
  estimated_count: 0
})

// 当前时间
const currentDateTime = computed(() => {
  return new Date().toLocaleString('zh-CN')
})

// 加载可选字段
const loadAvailableFields = async () => {
  try {
    const response = await exportService.getExportableFields()
    const fieldsData = response.fields

    // 转换为树形结构
    availableFieldsTree.value = fieldsData.map(module => ({
      id: module.module,
      label: module.module,
      children: module.fields.map(field => ({
        id: field.field_code,
        label: field.field_name_cn,
        field_code: field.field_code,
        field_name_cn: field.field_name_cn,
        data_granularity: field.data_granularity,
        is_sensitive: field.is_sensitive
      }))
    }))
  } catch (error) {
    ElMessage.error('加载字段列表失败: ' + error.message)
  }
}

// 字段选择处理
const handleFieldCheck = (data, checked) => {
  const checkedNodes = checked.checkedNodes.filter(node => node.field_code)
  exportForm.value.fields = checkedNodes.map(node => ({
    field_code: node.field_code,
    field_name_cn: node.field_name_cn,
    data_granularity: node.data_granularity,
    is_sensitive: node.is_sensitive
  }))

  // 为非学生级字段设置默认策略
  checkedNodes.forEach(node => {
    if (node.data_granularity !== 'student') {
      if (!exportForm.value.one_to_many_strategies[node.field_code]) {
        exportForm.value.one_to_many_strategies[node.field_code] = 'latest'
      }
    }
  })
}

// 移除字段
const removeField = (index) => {
  const field = exportForm.value.fields[index]
  exportForm.value.fields.splice(index, 1)

  // 从树中取消勾选
  const fieldTreeRef = ref(null)
  if (fieldTreeRef.value) {
    fieldTreeRef.value.setChecked(field.field_code, false)
  }
}

// 导出
const handleExport = async () => {
  try {
    const requestData = {
      fields: exportForm.value.fields.map(f => f.field_code),
      filters: exportForm.value.filters,
      one_to_many_strategies: exportForm.value.one_to_many_strategies,
      field_aliases: exportForm.value.field_aliases
    }

    const response = await exportService.exportStudentList(requestData)

    if (response.status === 'completed') {
      ElMessage.success('导出成功')
      emit('export-success', response)
      handleClose()
    } else {
      ElMessage.info('导出任务已创建，请稍后在导出记录中查看')
      handleClose()
    }
  } catch (error) {
    ElMessage.error('导出失败: ' + error.message)
  }
}

// 关闭对话框
const handleClose = () => {
  visible.value = false
}

// 监听初始筛选条件
watch(() => props.initialFilters, (newFilters) => {
  exportForm.value.filters = { ...newFilters }
}, { immediate: true })

onMounted(() => {
  loadAvailableFields()
})
</script>

<style scoped>
.export-dialog {
  max-height: 70vh;
  overflow-y: auto;
}

.section-card {
  margin-bottom: 20px;
}

.field-list-header {
  font-weight: bold;
  margin-bottom: 10px;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.field-list {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 10px;
}

.selected-fields {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 10px;
}

.draggable-list {
  min-height: 100px;
}

.selected-field-item {
  display: flex;
  align-items: center;
  padding: 10px;
  margin-bottom: 8px;
  background-color: #f5f7fa;
  border-radius: 4px;
  cursor: move;
}

.field-name {
  flex: 1;
  font-weight: 500;
}

.custom-tree-node {
  display: flex;
  align-items: center;
  width: 100%;
}
</style>
