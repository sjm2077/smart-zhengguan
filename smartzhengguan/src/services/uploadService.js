/**
 * R05: 数据上传服务
 */
import axios from 'axios'

export const UPLOAD_API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/$/, '')
const API_BASE_URL = UPLOAD_API_BASE_URL

const uploadService = {
  /**
   * 上传文件
   */
  async uploadFile(file) {
    const formData = new FormData()
    formData.append('file', file)

    const response = await axios.post(`${API_BASE_URL}/upload/file/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  /**
   * Sheet 识别
   */
  async identifySheets(batchId, manualModule = null) {
    const response = await axios.post(`${API_BASE_URL}/upload/identify/`, {
      batch_id: batchId,
      manual_module: manualModule,
    })
    return response.data
  },

  /**
   * 保存字段映射
   */
  async saveMapping(batchId, sheetName, mapping) {
    const response = await axios.post(`${API_BASE_URL}/upload/mapping/`, {
      batch_id: batchId,
      sheet_name: sheetName,
      mapping: mapping,
    })
    return response.data
  },

  /**
   * 获取映射状态
   */
  async getMappingStatus(batchId) {
    const response = await axios.get(`${API_BASE_URL}/upload/mapping/`, {
      params: { batch_id: batchId },
    })
    return response.data
  },

  /**
   * 校验和预览
   */
  async validateAndPreview(batchId, strategy) {
    const response = await axios.post(`${API_BASE_URL}/upload/validate-preview/`, {
      batch_id: batchId,
      strategy: strategy,
    })
    return response.data
  },

  /**
   * 确认导入
   */
  async confirmImport(batchId, strategy) {
    const response = await axios.post(`${API_BASE_URL}/upload/confirm/`, {
      batch_id: batchId,
      strategy: strategy,
    })
    return response.data
  },

  /**
   * 获取批次列表
   */
  async getBatchList(page = 1, pageSize = 20, status = null) {
    const params = { page, page_size: pageSize }
    if (status) {
      params.status = status
    }

    const response = await axios.get(`${API_BASE_URL}/upload/batches/`, { params })
    return response.data
  },

  /**
   * 获取批次详情
   */
  async getBatchDetail(batchId) {
    const response = await axios.get(`${API_BASE_URL}/upload/batches/${batchId}/`)
    return response.data
  },

  /**
   * 撤销批次
   */
  async revertBatch(batchId) {
    const response = await axios.post(`${API_BASE_URL}/upload/revert/`, {
      batch_id: batchId,
    })
    return response.data
  },

  /**
   * 获取模板列表
   */
  async getTemplateList() {
    const response = await axios.get(`${API_BASE_URL}/upload/templates/`)
    return response.data
  },

  /**
   * 保存模板
   */
  async saveTemplate(name, targetModule, mapping) {
    const response = await axios.post(`${API_BASE_URL}/upload/templates/`, {
      name: name,
      target_module: targetModule,
      mapping: mapping,
    })
    return response.data
  },

  /**
   * 删除模板
   */
  async deleteTemplate(templateId) {
    const response = await axios.delete(`${API_BASE_URL}/upload/templates/`, {
      params: { id: templateId },
    })
    return response.data
  },
}

export default uploadService
