<template>
  <div v-if="pageData" class="password-page">
    <div class="page-header">
      <div class="header-left">
        <span class="page-title">{{ pageData.title }}</span>
        <span class="page-subtitle">{{ pageData.subtitle }}</span>
      </div>
    </div>

    <el-row :gutter="16" class="chart-row">
      <el-col :span="14">
        <div class="section-card">
          <div class="card-header">
            <span class="card-title">密码更新</span>
          </div>
          <el-form ref="passwordFormRef" :model="form" label-width="96px" class="password-form">
            <el-form-item label="当前密码">
              <el-input v-model="form.currentPassword" type="password" show-password placeholder="请输入当前密码" />
            </el-form-item>
            <el-form-item label="新密码">
              <el-input v-model="form.newPassword" type="password" show-password placeholder="请输入新密码" />
            </el-form-item>
            <el-form-item label="确认新密码">
              <el-input v-model="form.confirmPassword" type="password" show-password placeholder="请再次输入新密码" />
            </el-form-item>
            <el-form-item>
              <div class="form-actions">
                <el-button @click="resetForm">重置</el-button>
                <el-button type="primary" class="primary-btn" @click="submitPassword">确认修改</el-button>
              </div>
            </el-form-item>
          </el-form>
        </div>
      </el-col>
      <el-col :span="10">
        <div class="section-card">
          <div class="card-header">
            <span class="card-title">安全提示</span>
          </div>
          <div class="tips-list">
            <div v-for="tip in pageData.securityTips" :key="tip.title" class="tip-item">
              <div class="tip-title">{{ tip.title }}</div>
              <div class="tip-desc">{{ tip.desc }}</div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="bottom-row">
      <el-col :span="24">
        <div class="section-card">
          <div class="card-header">
            <span class="card-title">最近密码相关记录</span>
          </div>
          <el-table :data="pageData.passwordLogs" stripe size="small" class="compact-table">
            <el-table-column prop="time" label="时间" width="160" />
            <el-table-column prop="action" label="操作" min-width="200" />
            <el-table-column prop="device" label="设备" min-width="160" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.statusType" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { getChangePasswordData } from '../services/mockDataService'

export default {
  data() {
    return {
      pageData: null,
      form: {
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
      },
    }
  },
  async mounted() {
    this.pageData = await getChangePasswordData()
  },
  methods: {
    resetForm() {
      this.form = {
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
      }
    },
    submitPassword() {
      const storedPassword = localStorage.getItem('mock-password') || '123456'
      if (!this.form.currentPassword || !this.form.newPassword || !this.form.confirmPassword) {
        this.$message.warning('请完整填写密码信息')
        return
      }
      if (this.form.currentPassword !== storedPassword) {
        this.$message.error('当前密码不正确')
        return
      }
      if (this.form.newPassword.length < 6) {
        this.$message.warning('新密码长度不能少于 6 位')
        return
      }
      if (this.form.newPassword !== this.form.confirmPassword) {
        this.$message.warning('两次输入的新密码不一致')
        return
      }
      localStorage.setItem('mock-password', this.form.newPassword)
      localStorage.removeItem('token')
      this.$message.success('密码修改成功，请重新登录')
      this.$router.push({ path: '/login', query: { changed: '1' } })
    },
  },
}
</script>

<style scoped>
.password-page { color: #333; }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  background: #fff;
  border-radius: 8px;
  padding: 16px 20px;
}
.header-left {
  display: flex;
  align-items: baseline;
  gap: 12px;
  flex-wrap: wrap;
}
.page-title { font-size: 20px; font-weight: 600; color: #333; }
.page-subtitle { font-size: 13px; color: #86909C; }
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
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #F0F0F0;
}
.card-title { font-size: 16px; font-weight: 600; color: #1D2939; }
.password-form { max-width: 560px; }
.form-actions { display: flex; gap: 8px; }
.primary-btn { background: #0A2463 !important; border-color: #0A2463 !important; }
.tips-list { display: flex; flex-direction: column; gap: 12px; }
.tip-item {
  padding: 14px;
  border-radius: 8px;
  background: #F8FAFC;
  border: 1px solid #EEF2F6;
}
.tip-title { font-size: 14px; font-weight: 600; color: #1D2939; }
.tip-desc { margin-top: 6px; font-size: 13px; color: #667085; line-height: 1.6; }
.compact-table :deep(.el-table__header th) {
  background: #F8FAFC;
  color: #344054;
  font-weight: 600;
  font-size: 13px;
}
</style>
