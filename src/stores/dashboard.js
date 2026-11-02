import { defineStore } from 'pinia'
import { ref } from 'vue'

// 大屏 / AI 助手共享的全院口径数据
// 默认值即官网《学院简介》口径（在校生按官网年招生规模×标准学制换算，属估算口径）
export const useDashboardStore = defineStore('dashboard', () => {
  const students = ref(2420)   // 全院在校生（本科+硕士+博士+MPA+留学生）
  const undergrad = ref(600)   // 本科在校生（官网 150 人/年 × 4 年）
  const master = ref(1560)     // 硕士在校生（学硕 360 + MPA 1200）
  const doctor = ref(140)      // 博士在校生（官网 35 人/年 × 4 年）
  const staff = ref(93)        // 专任教师（学院官网）
  const funding = ref(6000)    // 近五年科研经费（学院官网，万元）
  const projects = ref(100)    // 近五年科研项目（学院官网）
  const budget = ref(0)        // 年度预算执行：官网未公布，接入财务系统前为 0
  const maleRatio = ref(null)  // 官网未公布全院男女比例
  const femaleRatio = ref(null)

  const updateData = (data) => {
    if (data.students !== undefined) students.value = data.students
    if (data.undergrad !== undefined) undergrad.value = data.undergrad
    if (data.master !== undefined) master.value = data.master
    if (data.doctor !== undefined) doctor.value = data.doctor
    if (data.staff !== undefined) staff.value = data.staff
    if (data.funding !== undefined) funding.value = data.funding
    if (data.projects !== undefined) projects.value = data.projects
    if (data.budget !== undefined) budget.value = data.budget
    if (data.maleRatio !== undefined) maleRatio.value = data.maleRatio
    if (data.femaleRatio !== undefined) femaleRatio.value = data.femaleRatio
  }

  return {
    students,
    undergrad,
    master,
    doctor,
    staff,
    funding,
    projects,
    budget,
    maleRatio,
    femaleRatio,
    updateData
  }
})
