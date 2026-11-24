<template>
  <main class="login-page">
    <section class="login-container" aria-label="智慧教学平台登录">
      <!-- 左侧品牌区：保留学院标识与平台名称，不再展示功能列表 -->
      <aside class="login-brand">
        <div class="brand-decoration brand-decoration--top"></div>
        <div class="brand-decoration brand-decoration--bottom"></div>

        <div class="brand-content">
          <div class="brand-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"
              stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
              <path d="M6 12v5c0 1.1 2.7 2 6 2s6-.9 6-2v-5" />
            </svg>
          </div>

          <p class="brand-school">山东大学政治学与公共管理学院</p>
          <p class="brand-school-en">SCHOOL OF POLITICAL SCIENCE AND PUBLIC ADMINISTRATION</p>

          <div class="brand-divider" aria-hidden="true"></div>

          <h1 class="brand-title">智慧教学平台</h1>
          <p class="brand-desc">高校教学数据管理与分析系统</p>
        </div>

        <div class="brand-bottom-line" aria-hidden="true"></div>
      </aside>

      <!-- 右侧登录区 -->
      <section class="login-form-area">
        <div class="form-card">
          <div class="form-mark">
            <span class="form-mark-dot"></span>
            教学管理平台
          </div>

          <header class="form-header">
            <h2>账号登录</h2>
            <p>欢迎使用智慧教学平台，请输入您的账号信息</p>
          </header>

          <form class="form-body" @submit.prevent="handleLogin">
            <div class="input-group">
              <label class="input-label" for="login-username">账号</label>
              <div class="input-wrap">
                <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                  stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                  <circle cx="12" cy="7" r="4" />
                </svg>
                <input
                  id="login-username"
                  v-model.trim="username"
                  type="text"
                  name="username"
                  autocomplete="username"
                  placeholder="请输入账号"
                  class="form-input"
                  required
                />
              </div>
            </div>

            <div class="input-group">
              <label class="input-label" for="login-password">密码</label>
              <div class="input-wrap">
                <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                  stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
                <input
                  id="login-password"
                  v-model="password"
                  type="password"
                  name="password"
                  autocomplete="current-password"
                  placeholder="请输入密码"
                  class="form-input"
                  required
                />
              </div>
            </div>

            <p v-if="errorMsg" class="login-error" role="alert">{{ errorMsg }}</p>

            <button class="login-btn" type="submit" :disabled="loading">
              <span>{{ loading ? '正在登录…' : '登 录' }}</span>
              <svg v-if="!loading" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <line x1="5" y1="12" x2="19" y2="12" />
                <polyline points="12 5 19 12 12 19" />
              </svg>
              <span v-else class="loading-spinner" aria-hidden="true"></span>
            </button>
          </form>

          <div class="form-bottom-note">
            <span class="note-line"></span>
            <span>安全 · 规范 · 高效</span>
            <span class="note-line"></span>
          </div>
        </div>
      </section>
    </section>
  </main>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '@/api/auth'
import { setTokens } from '@/api/index'

const router = useRouter()
const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMsg = ref('')

const handleLogin = async (): Promise<void> => {
  if (loading.value) return

  if (!username.value || !password.value) {
    errorMsg.value = '请输入账号和密码'
    return
  }

  loading.value = true
  errorMsg.value = ''

  try {
    const res = await login({
      username: username.value,
      password: password.value,
    })

    // 保留现有认证流程：保存 JWT、记录登录用户信息并进入系统首页。
    setTokens(res.token, res.refresh)
    localStorage.setItem('user_info', JSON.stringify(res.user))
    await router.push('/dashboard')
  } catch (e: any) {
    errorMsg.value = e?.response?.data?.detail || '登录失败，请检查账号和密码'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  width: 100%;
  box-sizing: border-box;
  display: grid;
  place-items: center;
  padding: 24px;
  overflow: hidden;
  background:
    radial-gradient(circle at 8% 12%, rgba(59, 130, 246, 0.09), transparent 26%),
    radial-gradient(circle at 92% 88%, rgba(30, 58, 138, 0.07), transparent 28%),
    #f3f6fb;
}

.login-container {
  position: relative;
  display: flex;
  width: min(1180px, 100%);
  min-height: min(680px, calc(100vh - 48px));
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.9);
  border-radius: 26px;
  background: #fff;
  box-shadow:
    0 28px 80px rgba(20, 43, 91, 0.12),
    0 4px 14px rgba(20, 43, 91, 0.04);
}

/* 左侧学院品牌区 */
.login-brand {
  position: relative;
  isolation: isolate;
  display: flex;
  flex: 0 0 46%;
  align-items: center;
  justify-content: center;
  padding: 64px 44px;
  overflow: hidden;
  color: #fff;
  background: linear-gradient(145deg, #101d3e 0%, #18336f 54%, #24499b 100%);
}

.login-brand::before {
  position: absolute;
  z-index: -1;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background:
    linear-gradient(120deg, transparent 35%, rgba(255, 255, 255, 0.035) 35.2%, transparent 64%),
    linear-gradient(30deg, transparent 56%, rgba(255, 255, 255, 0.025) 56.2%, transparent 78%);
  content: '';
}

.brand-decoration {
  position: absolute;
  z-index: -1;
  border: 1px solid rgba(191, 219, 254, 0.12);
  border-radius: 50%;
  pointer-events: none;
}

.brand-decoration--top {
  top: -190px;
  right: -145px;
  width: 470px;
  height: 470px;
  box-shadow:
    0 0 0 38px rgba(191, 219, 254, 0.025),
    0 0 0 78px rgba(191, 219, 254, 0.02);
}

.brand-decoration--bottom {
  bottom: -250px;
  left: -170px;
  width: 500px;
  height: 500px;
  box-shadow:
    0 0 0 42px rgba(191, 219, 254, 0.025),
    0 0 0 86px rgba(191, 219, 254, 0.018);
}

.brand-content {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 430px;
  text-align: center;
}

.brand-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 78px;
  height: 78px;
  margin-bottom: 30px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.095);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(8px);
}

.brand-icon svg {
  width: 39px;
  height: 39px;
  color: #78b7ff;
}

.brand-school {
  margin: 0;
  color: #f8fbff;
  font-size: clamp(17px, 1.7vw, 21px);
  font-weight: 650;
  line-height: 1.7;
  letter-spacing: 1px;
}

.brand-school-en {
  max-width: 350px;
  margin: 7px auto 0;
  color: rgba(219, 234, 254, 0.68);
  font-size: 9px;
  line-height: 1.8;
  letter-spacing: 1.5px;
}

.brand-divider {
  width: 42px;
  height: 3px;
  margin: 28px auto 24px;
  border-radius: 10px;
  background: linear-gradient(90deg, #60a5fa, #a5d8ff);
}

.brand-title {
  margin: 0;
  color: #fff;
  font-size: clamp(30px, 3vw, 38px);
  font-weight: 750;
  line-height: 1.35;
  letter-spacing: 3px;
}

.brand-desc {
  margin: 17px 0 0;
  color: rgba(219, 234, 254, 0.82);
  font-size: 15px;
  line-height: 1.8;
  letter-spacing: 1px;
}

.brand-bottom-line {
  position: absolute;
  right: 48px;
  bottom: 32px;
  left: 48px;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(219, 234, 254, 0.2), transparent);
}

/* 右侧登录区 */
.login-form-area {
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: center;
  padding: 64px clamp(34px, 6vw, 88px);
  background:
    radial-gradient(circle at 100% 0%, rgba(219, 234, 254, 0.36), transparent 28%),
    #fff;
}

.form-card {
  width: 100%;
  max-width: 390px;
}

.form-mark {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  margin-bottom: 22px;
  color: #47628f;
  font-size: 12px;
  font-weight: 650;
  letter-spacing: 1px;
}

.form-mark-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #3b82f6;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
}

.form-header {
  margin-bottom: 34px;
}

.form-header h2 {
  margin: 0;
  color: #152544;
  font-size: 32px;
  font-weight: 750;
  line-height: 1.35;
  letter-spacing: 1px;
}

.form-header p {
  margin: 12px 0 0;
  color: #8b98ad;
  font-size: 14px;
  line-height: 1.8;
}

.form-body {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.input-label {
  color: #273956;
  font-size: 14px;
  font-weight: 650;
}

.input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 17px;
  width: 20px;
  height: 20px;
  color: #93a2b8;
  pointer-events: none;
  transition: color 0.2s ease;
}

.form-input {
  box-sizing: border-box;
  width: 100%;
  height: 58px;
  padding: 0 17px 0 49px;
  border: 1px solid #e1e8f2;
  border-radius: 12px;
  outline: none;
  background: #f7f9fc;
  color: #1f2d43;
  font: inherit;
  font-size: 15px;
  transition: border-color 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
}

.form-input::placeholder {
  color: #a5afbf;
}

.input-wrap:focus-within .input-icon {
  color: #3568c8;
}

.form-input:focus {
  border-color: #6c96e8;
  background: #fff;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
}

.login-error {
  margin: -8px 0 0;
  padding: 10px 12px;
  border: 1px solid #fee2e2;
  border-radius: 9px;
  background: #fff7f7;
  color: #c24141;
  font-size: 13px;
  line-height: 1.6;
}

.login-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 13px;
  width: 100%;
  height: 58px;
  margin-top: 6px;
  border: 0;
  border-radius: 12px;
  background: linear-gradient(105deg, #24458f 0%, #2f5ec0 100%);
  box-shadow: 0 10px 22px rgba(36, 69, 143, 0.18);
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 5px;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease;
}

.login-btn svg {
  width: 19px;
  height: 19px;
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 13px 27px rgba(36, 69, 143, 0.25);
  filter: brightness(1.05);
}

.login-btn:active:not(:disabled) {
  transform: translateY(0);
}

.login-btn:disabled {
  cursor: wait;
  opacity: 0.8;
}

.loading-spinner {
  width: 17px;
  height: 17px;
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

.form-bottom-note {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 34px;
  color: #a0aabd;
  font-size: 12px;
  letter-spacing: 2px;
}

.note-line {
  width: 28px;
  height: 1px;
  background: #e4eaf3;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 900px) {
  .login-page {
    padding: 18px;
  }

  .login-container {
    min-height: min(650px, calc(100vh - 36px));
  }

  .login-brand {
    flex-basis: 42%;
    padding: 48px 28px;
  }

  .login-form-area {
    padding: 48px 34px;
  }

  .brand-school {
    font-size: 17px;
  }

  .brand-school-en {
    font-size: 8px;
    letter-spacing: 0.8px;
  }

  .brand-title {
    font-size: 29px;
    letter-spacing: 2px;
  }

  .brand-desc {
    font-size: 13px;
  }
}

@media (max-width: 680px) {
  .login-page {
    display: block;
    min-height: 100vh;
    padding: 14px;
  }

  .login-container {
    display: block;
    width: 100%;
    min-height: 0;
    border-radius: 20px;
  }

  .login-brand {
    min-height: 265px;
    padding: 30px 22px 34px;
  }

  .brand-icon {
    width: 54px;
    height: 54px;
    margin-bottom: 16px;
    border-radius: 16px;
  }

  .brand-icon svg {
    width: 29px;
    height: 29px;
  }

  .brand-school {
    font-size: 16px;
  }

  .brand-school-en {
    max-width: 290px;
    font-size: 7px;
    letter-spacing: 0.5px;
  }

  .brand-divider {
    margin: 17px auto 13px;
  }

  .brand-title {
    font-size: 27px;
  }

  .brand-desc {
    margin-top: 7px;
    font-size: 12px;
  }

  .brand-bottom-line {
    right: 30px;
    bottom: 15px;
    left: 30px;
  }

  .login-form-area {
    padding: 36px 25px 32px;
  }

  .form-mark {
    margin-bottom: 15px;
  }

  .form-header {
    margin-bottom: 25px;
  }

  .form-header h2 {
    font-size: 27px;
  }

  .form-body {
    gap: 18px;
  }

  .form-input,
  .login-btn {
    height: 54px;
  }

  .form-bottom-note {
    margin-top: 26px;
  }
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
