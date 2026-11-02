/**
 * R07: 预警规则引擎服务
 */
import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000/api/v1'

const warningService = {
  /**
   * 获取预警规则列表
   */
  async getWarningRules(params = {}) {
    const response = await axios.get(`${API_BASE_URL}/warning/rules/`, { params })
    return response.data
  },

  /**
   * 获取规则详情
   */
  async getWarningRuleDetail(ruleId) {
    const response = await axios.get(`${API_BASE_URL}/warning/rules/${ruleId}/`)
    return response.data
  },

  /**
   * 创建预警规则
   */
  async createWarningRule(data) {
    const response = await axios.post(`${API_BASE_URL}/warning/rules/`, data)
    return response.data
  },

  /**
   * 修改预警规则
   */
  async updateWarningRule(ruleId, data) {
    const response = await axios.put(`${API_BASE_URL}/warning/rules/${ruleId}/`, data)
    return response.data
  },

  /**
   * 启停规则
   */
  async toggleWarningRule(ruleId, isActive) {
    const response = await axios.patch(`${API_BASE_URL}/warning/rules/${ruleId}/`, {
      is_active: isActive,
    })
    return response.data
  },

  /**
   * 触发扫描
   */
  async runScan(dryRun = false, ruleIds = null) {
    const response = await axios.post(`${API_BASE_URL}/warning/scan/`, {
      dry_run: dryRun,
      rule_ids: ruleIds,
    })
    return response.data
  },

  /**
   * 获取预警实例列表
   */
  async getWarningInstances(params = {}) {
    const response = await axios.get(`${API_BASE_URL}/warning/instances/`, { params })
    return response.data
  },

  /**
   * 获取预警详情
   */
  async getWarningInstanceDetail(instanceId, generateExplanation = false) {
    const response = await axios.get(`${API_BASE_URL}/warning/instances/${instanceId}/`, {
      params: { generate_explanation: generateExplanation },
    })
    return response.data
  },

  /**
   * 处理预警
   */
  async treatWarning(instanceId, action, note = '', assigneeId = null) {
    const data = { action, note }
    if (assigneeId) {
      data.assignee_id = assigneeId
    }

    const response = await axios.post(
      `${API_BASE_URL}/warning/instances/${instanceId}/treat/`,
      data
    )
    return response.data
  },

  /**
   * 获取预警统计
   */
  async getWarningStats() {
    const response = await axios.get(`${API_BASE_URL}/warning/stats/`)
    return response.data
  },
}

export default warningService
