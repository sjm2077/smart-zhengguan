/**
 * R06: 导出服务
 */
import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000/api/v1'

const exportService = {
  /**
   * 获取可导出字段
   */
  async getExportableFields() {
    const response = await axios.get(`${API_BASE_URL}/export/fields/`)
    return response.data
  },

  /**
   * 导出学生名单
   */
  async exportStudentList(data) {
    const response = await axios.post(`${API_BASE_URL}/export/student-list/`, data)
    return response.data
  },

  /**
   * 导出汇总表
   */
  async exportSummaryTable(filters) {
    const response = await axios.post(`${API_BASE_URL}/export/summary-table/`, {
      filters: filters,
    })
    return response.data
  },

  /**
   * 获取导出记录列表
   */
  async getExportRecords(page = 1, pageSize = 20, status = null) {
    const params = { page, page_size: pageSize }
    if (status) {
      params.status = status
    }

    const response = await axios.get(`${API_BASE_URL}/export/records/`, { params })
    return response.data
  },

  /**
   * 下载导出文件
   */
  getDownloadUrl(recordId) {
    return `${API_BASE_URL}/export/download/${recordId}/`
  },

  /**
   * 获取导出模板列表
   */
  async getExportTemplates() {
    const response = await axios.get(`${API_BASE_URL}/export/templates/`)
    return response.data
  },

  /**
   * 保存导出模板
   */
  async saveExportTemplate(data) {
    const response = await axios.post(`${API_BASE_URL}/export/templates/`, data)
    return response.data
  },

  /**
   * 删除导出模板
   */
  async deleteExportTemplate(templateId) {
    const response = await axios.delete(`${API_BASE_URL}/export/templates/`, {
      params: { id: templateId },
    })
    return response.data
  },
}

export default exportService
