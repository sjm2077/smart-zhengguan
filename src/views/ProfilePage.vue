<template>
  <div class="profile-page">
    <!-- 顶部背景区域 -->
    <div class="profile-hero">
      <div class="hero-glow"></div>
      <div class="hero-particles">
        <span v-for="i in 20" :key="i" class="particle" :style="particleStyle(i)"></span>
      </div>
      <div class="hero-content">
        <div class="avatar-wrapper">
          <span class="avatar-emoji">{{ userInfo?.avatar }}</span>
          <div class="avatar-ring"></div>
        </div>
        <h1 class="user-display-name">{{ userInfo?.name }}</h1>
        <div class="user-meta">
          <span class="role-badge">{{ userInfo?.roleName }}</span>
          <span class="dept-badge">{{ userInfo?.college }}</span>
        </div>
        <div class="hero-actions">
          <button class="hero-btn primary" @click="showEditDialog = true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="btn-icon"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
            编辑资料
          </button>
          <button class="hero-btn secondary" @click="showPwdDialog = true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="btn-icon"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            修改密码
          </button>
        </div>
      </div>
      <div class="hero-wave">
        <svg viewBox="0 0 1440 120" preserveAspectRatio="none"><path d="M0,32L48,37.3C96,43,192,53,288,58.7C384,64,480,64,576,58.7C672,53,768,43,864,48C960,53,1056,75,1152,80C1248,85,1344,75,1392,69.3L1440,64L1440,120L1392,120C1344,120,1248,120,1152,120C1056,120,960,120,864,120C768,120,672,120,576,120C480,120,384,120,288,120C192,120,96,120,48,120L0,120Z" fill="rgba(10,31,68,1)"/></svg>
      </div>
    </div>

    <!-- 主体内容 -->
    <div class="profile-body">
      <div class="body-inner">
        <!-- 左侧：信息卡片 -->
        <div class="body-left">
          <!-- 基本信息 -->
          <div class="info-card">
            <div class="card-header">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="card-icon"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
              <span>基本信息</span>
            </div>
            <div class="card-body">
              <div class="info-row">
                <span class="info-label">用户名</span>
                <span class="info-value">{{ userInfo?.username }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">所属部门</span>
                <span class="info-value">{{ userInfo?.college }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">电子邮箱</span>
                <span class="info-value">{{ userInfo?.email || '未设置' }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">联系电话</span>
                <span class="info-value">{{ userInfo?.phone || '未设置' }}</span>
              </div>
            </div>
          </div>

          <!-- 教师工作信息 -->
          <div v-if="isTeacher" class="info-card">
            <div class="card-header">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="card-icon"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
              <span>工作信息</span>
            </div>
            <div class="card-body">
              <div class="info-row">
                <span class="info-label">办公室</span>
                <span class="info-value">{{ userInfo?.office || '未设置' }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">入职时间</span>
                <span class="info-value">{{ userInfo?.joinDate || '未设置' }}</span>
              </div>
            </div>
          </div>

          <!-- 学生学籍信息 -->
          <div v-if="isStudent" class="info-card">
            <div class="card-header">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="card-icon"><path d="M12 14l9-5-9-5-9 5 9 5z"/><path d="M12 14l6.16-3.422a12.083 12.083 0 0 1 .665 6.479A11.952 11.952 0 0 0 12 20.055a11.952 11.952 0 0 0-6.824-2.998 12.078 12.078 0 0 1 .665-6.479L12 14z"/><path d="M12 14l9-5-9-5-9 5 9 5z" opacity="0.3"/></svg>
              <span>学籍信息</span>
            </div>
            <div class="card-body">
              <div class="info-row">
                <span class="info-label">学号</span>
                <span class="info-value">{{ userInfo?.studentId }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">专业</span>
                <span class="info-value">{{ userInfo?.major }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">年级</span>
                <span class="info-value">{{ userInfo?.grade }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">导师</span>
                <span class="info-value">{{ userInfo?.advisor }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">宿舍</span>
                <span class="info-value">{{ userInfo?.dormitory }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">入学时间</span>
                <span class="info-value">{{ userInfo?.enrollmentDate }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧：学业/权限 -->
        <div class="body-right">
          <!-- 学业成绩（学生） -->
          <div v-if="isStudent" class="info-card stats-card">
            <div class="card-header">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="card-icon"><path d="M12 20V10"/><path d="M18 20V4"/><path d="M6 20v-4"/></svg>
              <span>学业成绩</span>
            </div>
            <div class="stats-grid">
              <div class="stat-item">
                <span class="stat-num">{{ userInfo?.gpa }}</span>
                <span class="stat-label">平均绩点</span>
                <div class="stat-bar"><div class="stat-fill" style="width: 85%"></div></div>
              </div>
              <div class="stat-item">
                <span class="stat-num">{{ userInfo?.credits }}</span>
                <span class="stat-label">已修学分</span>
                <div class="stat-bar"><div class="stat-fill" style="width: 68%"></div></div>
              </div>
              <div class="stat-item">
                <span class="stat-num">{{ userInfo?.coursesCompleted }}</span>
                <span class="stat-label">完成课程</span>
                <div class="stat-bar"><div class="stat-fill" style="width: 72%"></div></div>
              </div>
            </div>
          </div>

          <!-- 权限范围 -->
          <div class="info-card permission-card">
            <div class="card-header">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="card-icon"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
              <span>权限范围（{{ accessibleMenus.length }} 项）</span>
            </div>
            <div class="perm-grid">
              <div v-for="menu in accessibleMenus" :key="menu.path" class="perm-chip">
                <span class="perm-icon">{{ menu.icon }}</span>
                <span class="perm-name">{{ menu.title }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ============ 编辑资料弹窗 ============ -->
    <Teleport to="body">
      <div v-if="showEditDialog" class="dialog-overlay" @click.self="showEditDialog = false">
        <div class="dialog-box edit-dialog">
          <div class="dialog-header">
            <h3>编辑资料</h3>
            <button class="dialog-close" @click="showEditDialog = false">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
            </button>
          </div>
          <div class="dialog-body">
            <div class="form-group">
              <label>姓名</label>
              <input v-model="editForm.name" class="form-input" placeholder="请输入姓名" />
            </div>
            <div class="form-group">
              <label>电子邮箱</label>
              <input v-model="editForm.email" class="form-input" placeholder="请输入邮箱" type="email" />
            </div>
            <div class="form-group">
              <label>联系电话</label>
              <input v-model="editForm.phone" class="form-input" placeholder="请输入电话" />
            </div>
            <div v-if="isTeacher" class="form-group">
              <label>办公室</label>
              <input v-model="editForm.office" class="form-input" placeholder="请输入办公室" />
            </div>
            <div v-if="isStudent" class="form-group">
              <label>宿舍</label>
              <input v-model="editForm.dormitory" class="form-input" placeholder="请输入宿舍" />
            </div>
          </div>
          <div class="dialog-footer">
            <button class="form-btn cancel" @click="showEditDialog = false">取消</button>
            <button class="form-btn submit" @click="saveProfile" :disabled="saving">
              {{ saving ? '保存中...' : '保存修改' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ============ 修改密码弹窗 ============ -->
    <Teleport to="body">
      <div v-if="showPwdDialog" class="dialog-overlay" @click.self="showPwdDialog = false">
        <div class="dialog-box pwd-dialog">
          <div class="dialog-header">
            <h3>修改密码</h3>
            <button class="dialog-close" @click="showPwdDialog = false">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
            </button>
          </div>
          <div class="dialog-body">
            <div class="form-group">
              <label>当前密码</label>
              <input v-model="pwdForm.current" class="form-input" type="password" placeholder="请输入当前密码" />
            </div>
            <div class="form-group">
              <label>新密码</label>
              <input v-model="pwdForm.newPwd" class="form-input" type="password" placeholder="请输入新密码（至少6位）" />
            </div>
            <div class="form-group">
              <label>确认新密码</label>
              <input v-model="pwdForm.confirm" class="form-input" type="password" placeholder="请再次输入新密码" />
            </div>
            <p v-if="pwdError" class="form-error">{{ pwdError }}</p>
            <p v-if="pwdSuccess" class="form-success">{{ pwdSuccess }}</p>
          </div>
          <div class="dialog-footer">
            <button class="form-btn cancel" @click="showPwdDialog = false">取消</button>
            <button class="form-btn submit" @click="changePassword" :disabled="pwdSaving">
              {{ pwdSaving ? '修改中...' : '确认修改' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 成功 Toast -->
    <Teleport to="body">
      <transition name="toast-fade">
        <div v-if="toast.show" class="toast" :class="toast.type">
          <span class="toast-icon">{{ toast.type === 'success' ? '✅' : '❌' }}</span>
          <span>{{ toast.message }}</span>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

const userInfo = computed(() => authStore.userInfo)

const isStudent = computed(() => userInfo.value?.role === 'student')

const isTeacher = computed(() => {
  const roles = ['dean', 'admin', 'jw', 'ky', 'rs', 'yjs']
  return roles.includes(userInfo.value?.role)
})

const accessibleMenus = computed(() => authStore.menuList)

// Toast
const toast = ref({ show: false, message: '', type: 'success' })
let toastTimer = null

const showToast = (message, type = 'success') => {
  if (toastTimer) clearTimeout(toastTimer)
  toast.value = { show: true, message, type }
  toastTimer = setTimeout(() => {
    toast.value.show = false
  }, 2500)
}

// === 编辑资料 ===
const showEditDialog = ref(false)
const saving = ref(false)

const editForm = ref({
  name: '',
  email: '',
  phone: '',
  office: '',
  dormitory: ''
})

const openEditDialog = () => {
  editForm.value = {
    name: userInfo.value?.name || '',
    email: userInfo.value?.email || '',
    phone: userInfo.value?.phone || '',
    office: userInfo.value?.office || '',
    dormitory: userInfo.value?.dormitory || ''
  }
  showEditDialog.value = true
}

const saveProfile = () => {
  saving.value = true
  // 模拟保存
  setTimeout(() => {
    const updated = {
      ...userInfo.value,
      name: editForm.value.name,
      email: editForm.value.email,
      phone: editForm.value.phone,
      office: editForm.value.office,
      dormitory: editForm.value.dormitory
    }
    authStore.updateUserInfo(updated)
    showEditDialog.value = false
    saving.value = false
    showToast('资料修改成功！', 'success')
  }, 600)
}

// === 修改密码 ===
const showPwdDialog = ref(false)
const pwdSaving = ref(false)
const pwdError = ref('')
const pwdSuccess = ref('')

const pwdForm = ref({
  current: '',
  newPwd: '',
  confirm: ''
})

const openPwdDialog = () => {
  pwdForm.value = { current: '', newPwd: '', confirm: '' }
  pwdError.value = ''
  pwdSuccess.value = ''
  showPwdDialog.value = true
}

const changePassword = () => {
  pwdError.value = ''
  pwdSuccess.value = ''

  if (!pwdForm.value.current) {
    pwdError.value = '请输入当前密码'
    return
  }
  if (!pwdForm.value.newPwd || pwdForm.value.newPwd.length < 6) {
    pwdError.value = '新密码至少6位'
    return
  }
  if (pwdForm.value.newPwd !== pwdForm.value.confirm) {
    pwdError.value = '两次密码输入不一致'
    return
  }

  pwdSaving.value = true
  // 模拟修改
  setTimeout(() => {
    pwdSaving.value = false
    pwdSuccess.value = '密码修改成功！'
    showToast('密码修改成功！', 'success')
    setTimeout(() => {
      showPwdDialog.value = false
    }, 800)
  }, 600)
}

// 粒子样式
const particleStyle = (i) => {
  const left = Math.random() * 100
  const delay = Math.random() * 5
  const size = 2 + Math.random() * 4
  return {
    left: `${left}%`,
    width: `${size}px`,
    height: `${size}px`,
    animationDelay: `${delay}s`,
    animationDuration: `${3 + Math.random() * 4}s`
  }
}

// 用 watch 同步打开时的表单数据
watch(showEditDialog, (val) => {
  if (val) {
    editForm.value = {
      name: userInfo.value?.name || '',
      email: userInfo.value?.email || '',
      phone: userInfo.value?.phone || '',
      office: userInfo.value?.office || '',
      dormitory: userInfo.value?.dormitory || ''
    }
  }
})

watch(showPwdDialog, (val) => {
  if (val) {
    pwdForm.value = { current: '', newPwd: '', confirm: '' }
    pwdError.value = ''
    pwdSuccess.value = ''
  }
})
</script>

<style scoped>
/* ===== 全局 ===== */
.profile-page {
  min-height: 100%;
  background: #0a1f44;
  position: relative;
  overflow-x: hidden;
}

/* ===== Hero 头部 ===== */
.profile-hero {
  position: relative;
  min-height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: linear-gradient(135deg, #0a1f44 0%, #0d2a5e 30%, #1a0a3e 70%, #0a1f44 100%);
}

.hero-glow {
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(ellipse at 30% 40%, rgba(0, 212, 255, 0.08) 0%, transparent 50%),
              radial-gradient(ellipse at 70% 60%, rgba(123, 44, 191, 0.08) 0%, transparent 50%);
  animation: glow-drift 8s ease-in-out infinite alternate;
}

@keyframes glow-drift {
  0% { transform: translate(0, 0) rotate(0deg); }
  100% { transform: translate(2%, -2%) rotate(3deg); }
}

.hero-particles {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.particle {
  position: absolute;
  bottom: 40%;
  background: rgba(0, 212, 255, 0.5);
  border-radius: 50%;
  animation: float-up linear infinite;
}

@keyframes float-up {
  0% { transform: translateY(0) scale(1); opacity: 0.6; }
  100% { transform: translateY(-200px) scale(0); opacity: 0; }
}

.hero-content {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 50px 20px 30px;
}

.avatar-wrapper {
  position: relative;
  margin-bottom: 16px;
}

.avatar-emoji {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 90px;
  height: 90px;
  font-size: 48px;
  background: rgba(0, 212, 255, 0.1);
  border-radius: 50%;
  position: relative;
  z-index: 1;
}

.avatar-ring {
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  border: 2px solid transparent;
  background: linear-gradient(135deg, #00d4ff, #7b2cbf) border-box;
  -webkit-mask: linear-gradient(#fff 0 0) padding-box, linear-gradient(#fff 0 0);
  mask: linear-gradient(#fff 0 0) padding-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  animation: ring-spin 3s linear infinite;
}

@keyframes ring-spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.user-display-name {
  font-size: 32px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 10px;
  text-shadow: 0 2px 20px rgba(0, 212, 255, 0.3);
}

.user-meta {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.role-badge {
  padding: 4px 16px;
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.2), rgba(123, 44, 191, 0.2));
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 20px;
  font-size: 14px;
  color: #00d4ff;
}

.dept-badge {
  padding: 4px 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
}

.hero-actions {
  display: flex;
  gap: 12px;
}

.hero-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.hero-btn.primary {
  background: linear-gradient(135deg, #00d4ff, #0099cc);
  color: #fff;
  box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3);
}

.hero-btn.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 25px rgba(0, 212, 255, 0.4);
}

.hero-btn.secondary {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #fff;
}

.hero-btn.secondary:hover {
  background: rgba(255, 255, 255, 0.12);
  transform: translateY(-2px);
}

.btn-icon {
  width: 18px;
  height: 18px;
}

.hero-wave {
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  line-height: 0;
}

.hero-wave svg {
  width: 100%;
  height: 60px;
}

/* ===== 主体 ===== */
.profile-body {
  position: relative;
  z-index: 1;
  padding: 0 24px 40px;
  margin-top: -1px;
}

.body-inner {
  max-width: 1100px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  align-items: start;
}

.body-left, .body-right {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ===== 信息卡片 ===== */
.info-card {
  background: rgba(10, 31, 68, 0.85);
  border: 1px solid rgba(0, 212, 255, 0.12);
  border-radius: 14px;
  overflow: hidden;
  backdrop-filter: blur(10px);
  transition: border-color 0.3s;
}

.info-card:hover {
  border-color: rgba(0, 212, 255, 0.25);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(0, 212, 255, 0.08);
  font-size: 16px;
  font-weight: 600;
  color: #fff;
}

.card-icon {
  width: 20px;
  height: 20px;
  color: #00d4ff;
}

.card-body {
  padding: 6px 0;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  transition: background 0.2s;
}

.info-row:hover {
  background: rgba(0, 212, 255, 0.03);
}

.info-row + .info-row {
  border-top: 1px solid rgba(0, 212, 255, 0.05);
}

.info-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
}

.info-value {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
  text-align: right;
  max-width: 60%;
  word-break: break-all;
}

/* ===== 学业成绩 ===== */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  padding: 20px;
}

.stat-item {
  text-align: center;
}

.stat-num {
  display: block;
  font-size: 26px;
  font-weight: 700;
  color: #00d4ff;
  margin-bottom: 4px;
}

.stat-item .stat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.stat-bar {
  margin-top: 8px;
  height: 4px;
  background: rgba(0, 212, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.stat-fill {
  height: 100%;
  background: linear-gradient(90deg, #00d4ff, #7b2cbf);
  border-radius: 2px;
  transition: width 1s ease;
}

/* ===== 权限 ===== */
.perm-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  padding: 16px 20px 20px;
}

.perm-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: rgba(0, 212, 255, 0.04);
  border: 1px solid rgba(0, 212, 255, 0.08);
  border-radius: 8px;
  transition: all 0.3s;
}

.perm-chip:hover {
  background: rgba(0, 212, 255, 0.08);
  border-color: rgba(0, 212, 255, 0.2);
  transform: translateX(3px);
}

.perm-icon {
  font-size: 16px;
}

.perm-name {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.85);
}

/* ===== 弹窗 ===== */
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.dialog-box {
  width: 440px;
  max-width: 90vw;
  background: #0d2a5e;
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  animation: dialog-in 0.25s ease-out;
}

@keyframes dialog-in {
  from { opacity: 0; transform: scale(0.92) translateY(20px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 0;
}

.dialog-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #fff;
  margin: 0;
}

.dialog-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.05);
  border: none;
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  transition: all 0.2s;
}

.dialog-close:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.dialog-close svg {
  width: 18px;
  height: 18px;
}

.dialog-body {
  padding: 20px 24px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 6px;
}

.form-input {
  width: 100%;
  padding: 10px 14px;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(0, 212, 255, 0.15);
  border-radius: 8px;
  font-size: 14px;
  color: #fff;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.form-input:focus {
  border-color: rgba(0, 212, 255, 0.5);
  box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.08);
}

.form-input::placeholder {
  color: rgba(255, 255, 255, 0.25);
}

.form-error {
  margin: 8px 0 0;
  font-size: 13px;
  color: #ff4d4f;
}

.form-success {
  margin: 8px 0 0;
  font-size: 13px;
  color: #52c41a;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 0 24px 20px;
}

.form-btn {
  padding: 10px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.form-btn.cancel {
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.7);
}

.form-btn.cancel:hover {
  background: rgba(255, 255, 255, 0.1);
}

.form-btn.submit {
  background: linear-gradient(135deg, #00d4ff, #0099cc);
  color: #fff;
}

.form-btn.submit:hover {
  box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3);
}

.form-btn.submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ===== Toast ===== */
.toast {
  position: fixed;
  top: 30px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 28px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  z-index: 99999;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
}

.toast.success {
  background: #1a3a1a;
  border: 1px solid rgba(82, 196, 26, 0.4);
  color: #b7eb8f;
}

.toast.error {
  background: #3a1a1a;
  border: 1px solid rgba(255, 77, 79, 0.4);
  color: #ffa39e;
}

.toast-icon {
  font-size: 18px;
}

.toast-fade-enter-active,
.toast-fade-leave-active {
  transition: all 0.3s ease;
}

.toast-fade-enter-from,
.toast-fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px);
}

/* ===== 响应式 ===== */
@media (max-width: 768px) {
  .body-inner {
    grid-template-columns: 1fr;
  }
  .stats-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    padding: 16px;
  }
  .perm-grid {
    grid-template-columns: 1fr;
  }
  .hero-actions {
    flex-direction: column;
    width: 100%;
    max-width: 280px;
  }
  .hero-btn {
    justify-content: center;
  }
}
</style>
