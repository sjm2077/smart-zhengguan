<template>
  <div v-if="pageData" class="personal-page">
    <div class="page-header">
      <div class="header-left">
        <span class="page-title">{{ pageData.title }}</span>
        <span class="page-subtitle">{{ pageData.subtitle }}</span>
      </div>
      <div class="header-right">
        <span class="update-time">上次登录：{{ profile.lastLogin }}</span>
      </div>
    </div>

    <el-row :gutter="16" class="stat-row">
      <el-col :span="6" v-for="card in pageData.statCards" :key="card.title">
        <DashboardCard
          :title="card.title"
          :number="card.number"
          :icon="card.icon"
          :iconBg="card.iconBg"
          :changeLabel="card.changeLabel"
        />
      </el-col>
    </el-row>

    <el-row :gutter="16" class="chart-row">
      <el-col :span="14">
        <div class="section-card">
          <div class="card-header">
            <span class="card-title">个人资料</span>
            <div class="header-actions">
              <el-button @click="resetProfile">重置</el-button>
              <el-button type="primary" class="primary-btn" @click="saveProfile">保存资料</el-button>
            </div>
          </div>
          <el-form :model="profile" label-width="90px" class="profile-form">
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="姓名">
                  <el-input v-model="profile.name" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="角色">
                  <el-input v-model="profile.role" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="所属部门">
                  <el-input v-model="profile.department" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="工号">
                  <el-input v-model="profile.jobNo" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="手机号">
                  <el-input v-model="profile.phone" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="邮箱">
                  <el-input v-model="profile.email" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>
      </el-col>
      <el-col :span="10">
        <div class="section-card profile-side-card">
          <div class="profile-top">
            <el-avatar :size="64" class="profile-avatar">{{ profile.name.charAt(0) }}</el-avatar>
            <div class="profile-summary">
              <div class="profile-name">{{ profile.name }}</div>
              <div class="profile-role">{{ profile.role }}</div>
              <div class="profile-dept">{{ profile.department }}</div>
            </div>
          </div>
          <div class="profile-tags">
            <el-tag
              v-for="tag in pageData.profileTags"
              :key="tag.label"
              :type="tag.type"
              effect="plain"
            >
              {{ tag.label }}
            </el-tag>
          </div>
          <div class="quick-list">
            <div
              v-for="item in pageData.quickActions"
              :key="item.label"
              class="quick-item"
              @click="showComingSoon(item.label)"
            >
              <span class="quick-label">{{ item.label }}</span>
              <span class="quick-desc">{{ item.desc }}</span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="bottom-row">
      <el-col :span="14">
        <div class="section-card">
          <div class="card-header">
            <span class="card-title">最近操作记录</span>
          </div>
          <el-table :data="pageData.operationLogs" stripe size="small" class="compact-table">
            <el-table-column prop="time" label="时间" width="120" />
            <el-table-column prop="module" label="模块" width="110" />
            <el-table-column prop="action" label="操作内容" min-width="180" />
            <el-table-column prop="status" label="结果" width="90">
              <template #default="{ row }">
                <el-tag :type="row.statusType" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
      <el-col :span="10">
        <div class="section-card">
          <div class="card-header">
            <span class="card-title">常用入口</span>
          </div>
          <div class="shortcut-list">
            <div
              v-for="item in pageData.shortcuts"
              :key="item.label"
              class="shortcut-item"
              @click="$router.push(item.route)"
            >
              <span class="shortcut-label">{{ item.label }}</span>
              <span class="shortcut-arrow">进入 ></span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import DashboardCard from '../components/DashboardCard.vue'
import { getPersonalCenterData } from '../services/mockDataService'

export default {
  components: { DashboardCard },
  data() {
    return {
      pageData: null,
      baseProfile: null,
      profile: {
        name: '',
        role: '',
        department: '',
        jobNo: '',
        phone: '',
        email: '',
        lastLogin: '',
      },
    }
  },
  async mounted() {
    this.pageData = await getPersonalCenterData()
    this.baseProfile = { ...this.pageData.profile }
    this.profile = { ...this.pageData.profile }
    this.loadProfile()
  },
  methods: {
    loadProfile() {
      const storedUser = localStorage.getItem('mock-user')
      const storedProfile = localStorage.getItem('mock-user-profile')

      if (storedUser) {
        try {
          const user = JSON.parse(storedUser)
          this.profile = {
            ...this.profile,
            name: user.name || this.profile.name,
            role: user.role || this.profile.role,
          }
        } catch (error) {
          console.warn('用户信息读取失败', error)
        }
      }

      if (storedProfile) {
        try {
          this.profile = {
            ...this.profile,
            ...JSON.parse(storedProfile),
          }
        } catch (error) {
          console.warn('个人资料读取失败', error)
        }
      }
    },
    saveProfile() {
      localStorage.setItem('mock-user', JSON.stringify({
        name: this.profile.name,
        role: this.profile.role,
      }))
      localStorage.setItem('mock-user-profile', JSON.stringify(this.profile))
      window.dispatchEvent(new Event('mock-user-updated'))
      if (this.$message) this.$message.success('个人资料已保存')
    },
    resetProfile() {
      this.profile = { ...this.baseProfile }
      this.loadProfile()
    },
    showComingSoon(label) {
      if (this.$message) this.$message.info(`${label} 功能待补充`)
    },
  },
}
</script>

<style scoped>
.personal-page { color: #333; }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  background: #fff;
  border-radius: 8px;
  padding: 16px 20px;
  gap: 16px;
}
.header-left {
  display: flex;
  align-items: baseline;
  gap: 12px;
  flex-wrap: wrap;
}
.page-title { font-size: 20px; font-weight: 600; color: #333; }
.page-subtitle,
.update-time { font-size: 13px; color: #86909C; }
.stat-row,
.chart-row,
.bottom-row { margin-bottom: 16px; }
.section-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  height: 100%;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #F0F0F0;
}
.card-title { font-size: 16px; font-weight: 600; color: #1D2939; }
.header-actions { display: flex; gap: 8px; }
.primary-btn { background: #0A2463 !important; border-color: #0A2463 !important; }
.profile-form { padding-top: 4px; }
.profile-side-card { display: flex; flex-direction: column; gap: 16px; }
.profile-top { display: flex; align-items: center; gap: 16px; }
.profile-avatar { background: #165DFF; font-size: 26px; flex-shrink: 0; }
.profile-name { font-size: 20px; font-weight: 600; color: #1D2939; }
.profile-role,
.profile-dept { font-size: 13px; color: #667085; margin-top: 4px; }
.profile-tags { display: flex; gap: 8px; flex-wrap: wrap; }
.quick-list,
.shortcut-list { display: flex; flex-direction: column; gap: 10px; }
.quick-item,
.shortcut-item {
  padding: 12px 14px;
  border-radius: 8px;
  background: #F8FAFC;
  border: 1px solid #EEF2F6;
  cursor: pointer;
}
.quick-label,
.shortcut-label { font-size: 14px; font-weight: 500; color: #1D2939; }
.quick-desc,
.shortcut-arrow { display: block; font-size: 12px; color: #667085; margin-top: 4px; }
.compact-table :deep(.el-table__header th) {
  background: #F8FAFC;
  color: #344054;
  font-weight: 600;
  font-size: 13px;
}
</style>
