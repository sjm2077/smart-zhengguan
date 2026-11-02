<template>
  <div class="login-page">
    <div class="login-overlay">
      <header class="login-header">
        <div class="brand-block">
          <img
            class="brand-logo-image"
            src="/branding/college-logo.png"
            alt="山东大学政治学与公共管理学院院徽"
          />
        </div>

        <button class="lang-btn" type="button" @click="showEnglishNotice">
          English
        </button>
      </header>

      <main class="login-main">
        <section class="login-card">
          <div class="login-card-tabs">
            <div class="login-tab active">账号登录</div>
          </div>

          <div class="login-card-body">
            <el-form :model="form" class="login-form" @submit.prevent>
              <el-form-item>
                <el-input
                  v-model="form.username"
                  size="large"
                  placeholder="用户名 / 工号 / 学号"
                />
              </el-form-item>

              <el-form-item>
                <el-input
                  v-model="form.password"
                  type="password"
                  show-password
                  size="large"
                  placeholder="请输入密码"
                />
              </el-form-item>

              <div class="login-options">
                <el-checkbox v-model="rememberMe">自动登录</el-checkbox>
                <button type="button" class="link-btn" @click="showForgotPassword">
                  忘记密码？
                </button>
              </div>

              <el-button
                type="primary"
                size="large"
                class="login-btn"
                @click="submitLogin"
              >
                账号登录
              </el-button>
            </el-form>

            <div class="login-tips">
              <div class="tip-title">温馨提示：</div>
              <div class="tip-line">1. 用户名为“工号 / 学号”，若忘记密码请先重置密码。</div>
              <div class="tip-line">2. 浏览器建议使用极速模式。</div>
              <div class="tip-line">3. 演示默认密码为 `123456`。</div>
              <div class="tip-line tip-danger">4. 本平台为校内业务演示页面，请勿输入真实敏感账号密码。</div>
            </div>
          </div>
        </section>
      </main>

      <footer class="login-footer">
        <div class="footer-left">山东大学 版权所有 Copyright@2017 数智化支撑研究院</div>
        <div class="footer-right">技术支持：talentwenwen66@gmail.com</div>
      </footer>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      form: {
        username: localStorage.getItem('remember-username') || 'admin',
        password: '',
        role: '教务秘书',
      },
      rememberMe: Boolean(localStorage.getItem('remember-username')),
    }
  },
  mounted() {
    if (this.$route.query.changed === '1' && this.$message) {
      this.$message.success('密码已更新，请重新登录')
    }
  },
  methods: {
    showEnglishNotice() {
      this.$message?.info('当前演示版本暂未提供英文界面')
    },
    showForgotPassword() {
      this.$message?.info('演示环境请使用默认密码 123456，正式环境可接入统一身份密码找回流程')
    },
    submitLogin() {
      const storedPassword = localStorage.getItem('mock-password') || '123456'

      if (!this.form.username || !this.form.password) {
        this.$message.warning('请输入账号和密码')
        return
      }

      if (this.form.password !== storedPassword) {
        this.$message.error('账号或密码不正确')
        return
      }

      if (this.rememberMe) {
        localStorage.setItem('remember-username', this.form.username)
      } else {
        localStorage.removeItem('remember-username')
      }

      localStorage.setItem('token', `mock-token-${Date.now()}`)
      localStorage.setItem('mock-user', JSON.stringify({
        name: this.form.username === 'admin' ? '张老师' : this.form.username,
        role: this.form.role,
      }))
      window.dispatchEvent(new Event('mock-user-updated'))

      const redirect = this.$route.query.redirect || '/home'
      this.$router.push(redirect)
    },
  },
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background-image:
    linear-gradient(180deg, rgba(44, 41, 30, 0.14) 0%, rgba(121, 95, 28, 0.05) 28%, rgba(18, 24, 12, 0.16) 100%),
    url('/login/login-bg.jpg'),
    url('/login/login-bg.svg');
  background-position: center 22%;
  background-repeat: no-repeat;
  background-size: cover;
}

.login-overlay {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 32px 36px 22px;
}

.login-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
}

.brand-block {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 14px;
  color: #fff;
  text-shadow: 0 2px 6px rgba(0, 0, 0, 0.16);
  max-width: min(84vw, 1120px);
}

.brand-logo-image {
  width: min(62vw, 820px);
  min-width: 360px;
  height: auto;
  filter: drop-shadow(0 8px 18px rgba(0, 0, 0, 0.2));
}

.lang-btn {
  min-width: 152px;
  height: 50px;
  border: 1px solid rgba(255, 255, 255, 0.75);
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
  font-size: 18px;
  border-radius: 8px;
  cursor: pointer;
  backdrop-filter: blur(2px);
}

.lang-btn:hover {
  background: rgba(255, 255, 255, 0.18);
}

.login-main {
  flex: 1;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding-right: 14%;
}

.login-card {
  width: 392px;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 20px 50px rgba(48, 38, 10, 0.16);
  overflow: hidden;
}

.login-card-tabs {
  display: grid;
  grid-template-columns: 1fr;
  background: rgba(242, 242, 242, 0.92);
  border-bottom: 1px solid #d7dce3;
}

.login-tab {
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 600;
  color: #5d5d5d;
}

.login-tab.active {
  background: rgba(255, 255, 255, 0.72);
}

.login-card-body {
  padding: 18px 26px 22px;
}

.login-form :deep(.el-input__wrapper) {
  min-height: 42px;
  background: #f1f5fb;
  box-shadow: inset 0 0 0 1px #d6dce6;
  border-radius: 0;
}

.login-form :deep(.el-input__inner) {
  color: #2b2b2b;
  font-size: 16px;
}

.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 4px 0 18px;
  color: #6f7782;
}

.link-btn {
  border: none;
  background: transparent;
  color: #2c79c9;
  font-size: 14px;
  cursor: pointer;
  padding: 0;
}

.login-btn {
  width: 100%;
  height: 48px;
  margin-top: 6px;
  background: #b50000 !important;
  border-color: #b50000 !important;
  border-radius: 6px;
  font-size: 18px;
  font-weight: 600;
}

.login-tips {
  margin-top: 18px;
  padding-top: 12px;
  border-top: 1px solid #e5e8ed;
  color: #666f7c;
  font-size: 13px;
  line-height: 1.9;
}

.tip-title {
  color: #4f5865;
  font-weight: 600;
}

.tip-danger {
  color: #d61717;
}

.login-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #fff;
  font-size: 15px;
  padding-top: 14px;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
  gap: 12px;
}

.footer-left,
.footer-right {
  opacity: 0.96;
}

@media (max-width: 1440px) {
  .login-main {
    padding-right: 8%;
  }
}

@media (max-width: 1100px) {
  .login-page {
    background-position: center 16%;
  }

  .login-overlay {
    padding: 24px 20px 18px;
  }

  .login-header {
    flex-direction: column;
    gap: 18px;
  }

  .brand-logo-image {
    width: min(76vw, 640px);
    min-width: 260px;
  }

  .login-main {
    justify-content: center;
    padding-right: 0;
    padding-top: 32px;
    padding-bottom: 24px;
  }

  .login-footer {
    flex-direction: column;
    gap: 8px;
    align-items: flex-start;
  }
}

@media (max-width: 640px) {
  .login-page {
    background-position: center 14%;
  }

  .brand-logo-image {
    width: 100%;
    min-width: 0;
  }

  .lang-btn {
    min-width: 124px;
    height: 42px;
    font-size: 16px;
  }

  .login-card {
    width: 100%;
  }

  .login-card-body {
    padding: 16px 16px 18px;
  }
}
</style>
