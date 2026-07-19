import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useDashboardStore = defineStore('dashboard', () => {
  const students = ref(1320)
  const staff = ref(93)
  const projects = ref(307)
  const funding = ref(4000)
  const budget = ref(910)
  const maleRatio = ref(38.03)
  const femaleRatio = ref(61.97)

  const updateData = (data) => {
    if (data.students !== undefined) students.value = data.students
    if (data.staff !== undefined) staff.value = data.staff
    if (data.projects !== undefined) projects.value = data.projects
    if (data.funding !== undefined) funding.value = data.funding
    if (data.budget !== undefined) budget.value = data.budget
    if (data.maleRatio !== undefined) maleRatio.value = data.maleRatio
    if (data.femaleRatio !== undefined) femaleRatio.value = data.femaleRatio
  }

  return {
    students,
    staff,
    projects,
    funding,
    budget,
    maleRatio,
    femaleRatio,
    updateData
  }
})