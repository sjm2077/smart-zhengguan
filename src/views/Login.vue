<template>
  <div class="login-container">
    <canvas ref="particleCanvas" class="particle-canvas"></canvas>
    
    <div class="login-content">
      <div class="login-left">
        <div class="platform-intro">
          <h1 class="platform-title">山东大学</h1>
          <h2 class="platform-subtitle">政治学与公共管理学院</h2>
          <p class="platform-desc">
            整合教务、科研、师资、研究生等多维度数据，<br>
            为学院管理层提供一站式数据可视化决策平台
          </p>
          <div class="feature-list">
            <div class="feature-item">
              <span class="feature-icon">📊</span>
              <span>数据可视化</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">🔐</span>
              <span>权限精细化</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">⚡</span>
              <span>实时动态</span>
            </div>
          </div>
        </div>
      </div>

      <div class="login-right">
        <div class="login-card" :class="{ shake: isShaking }">
          <div class="card-header">
            <h2>用户登录</h2>
            <p>请输入您的账号信息</p>
          </div>

          <form @submit.prevent="handleLogin" class="login-form">
            <div class="form-item">
              <label>用户名</label>
              <input 
                v-model="formData.username" 
                type="text" 
                placeholder="请输入用户名"
                :disabled="loading"
              />
            </div>

            <div class="form-item">
              <label>密码</label>
              <input 
                v-model="formData.password" 
                type="password" 
                placeholder="请输入密码"
                :disabled="loading"
              />
            </div>

            <div class="form-item captcha-item">
              <label>验证码</label>
              <div class="captcha-input-wrapper">
                <input 
                  v-model="formData.captcha" 
                  type="text" 
                  placeholder="请输入验证码"
                  maxlength="4"
                  :disabled="loading"
                />
                <VerifyCode ref="verifyCodeRef" @change="handleCaptchaChange" />
              </div>
            </div>

            <div v-if="errorMsg" class="error-message">
              {{ errorMsg }}
            </div>

            <button type="submit" class="login-btn" :disabled="loading">
              <span v-if="!loading">登 录</span>
              <span v-else class="loading-spinner"></span>
            </button>
          </form>

          <div class="demo-accounts">
            <p>演示账号：dean / admin / jw / ky / rs / yjs / student</p>
            <p>密码：123456</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import VerifyCode from '../components/VerifyCode.vue'

const router = useRouter()
const authStore = useAuthStore()

const particleCanvas = ref(null)
const verifyCodeRef = ref(null)
const isShaking = ref(false)
const loading = ref(false)
const errorMsg = ref('')
const captchaCode = ref('')

const formData = ref({
  username: '',
  password: '',
  captcha: ''
})

let animationId = null
let particles = []

class Particle {
  constructor(canvas) {
    this.canvas = canvas
    this.reset()
  }

  reset() {
    this.x = Math.random() * this.canvas.width
    this.y = Math.random() * this.canvas.height
    this.size = Math.random() * 2 + 0.5
    this.speedX = (Math.random() - 0.5) * 0.5
    this.speedY = (Math.random() - 0.5) * 0.5
    this.opacity = Math.random() * 0.5 + 0.2
    this.color = Math.random() > 0.5 ? '#00d4ff' : '#7b2cbf'
  }

  update() {
    this.x += this.speedX
    this.y += this.speedY

    if (this.x < 0 || this.x > this.canvas.width) this.speedX *= -1
    if (this.y < 0 || this.y > this.canvas.height) this.speedY *= -1

    this.opacity = Math.sin(Date.now() * 0.002 + this.x) * 0.3 + 0.3
  }

  draw(ctx) {
    ctx.beginPath()
    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2)
    ctx.fillStyle = this.color
    ctx.globalAlpha = this.opacity
    ctx.fill()
    ctx.globalAlpha = 1
  }
}

const initParticles = () => {
  const canvas = particleCanvas.value
  canvas.width = window.innerWidth
  canvas.height = window.innerHeight
  
  particles = []
  const particleCount = Math.floor((canvas.width * canvas.height) / 15000)
  
  for (let i = 0; i < particleCount; i++) {
    particles.push(new Particle(canvas))
  }
}

const animateParticles = () => {
  const canvas = particleCanvas.value
  const ctx = canvas.getContext('2d')
  
  ctx.fillStyle = 'rgba(10, 31, 68, 0.1)'
  ctx.fillRect(0, 0, canvas.width, canvas.height)

  particles.forEach(particle => {
    particle.update()
    particle.draw(ctx)
  })

  particles.forEach((p1, i) => {
    particles.slice(i + 1).forEach(p2 => {
      const dx = p1.x - p2.x
      const dy = p1.y - p2.y
      const dist = Math.sqrt(dx * dx + dy * dy)
      
      if (dist < 120) {
        ctx.beginPath()
        ctx.moveTo(p1.x, p1.y)
        ctx.lineTo(p2.x, p2.y)
        ctx.strokeStyle = `rgba(0, 212, 255, ${0.15 - dist / 800})`
        ctx.stroke()
      }
    })
  })

  animationId = requestAnimationFrame(animateParticles)
}

const handleCaptchaChange = (code) => {
  captchaCode.value = code
}

const handleLogin = async () => {
  errorMsg.value = ''

  if (!formData.value.username) {
    errorMsg.value = '请输入用户名'
    triggerShake()
    return
  }
  if (!formData.value.password) {
    errorMsg.value = '请输入密码'
    triggerShake()
    return
  }
  if (!formData.value.captcha) {
    errorMsg.value = '请输入验证码'
    triggerShake()
    return
  }
  if (formData.value.captcha.toUpperCase() !== captchaCode.value.toUpperCase()) {
    errorMsg.value = '验证码错误'
    verifyCodeRef.value.refresh()
    formData.value.captcha = ''
    triggerShake()
    return
  }

  loading.value = true
  
  try {
    await authStore.login(formData.value)
    router.push('/')
  } catch (error) {
    errorMsg.value = error.message
    triggerShake()
    verifyCodeRef.value.refresh()
    formData.value.captcha = ''
  } finally {
    loading.value = false
  }
}

const triggerShake = () => {
  isShaking.value = true
  setTimeout(() => {
    isShaking.value = false
  }, 500)
}

const handleResize = () => {
  initParticles()
}

onMounted(() => {
  if (authStore.isLoggedIn) {
    router.push('/')
    return
  }
  initParticles()
  animateParticles()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.login-container {
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #0a1f44 0%, #0d2a4d 50%, #050d1f 100%);
  overflow: hidden;
  position: relative;
}

.particle-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
}

.login-content {
  position: relative;
  z-index: 2;
  display: flex;
  width: 100%;
  height: 100%;
  padding: 60px;
  gap: 80px;
  align-items: center;
  justify-content: center;
}

.login-left {
  flex: 1;
  max-width: 500px;
}

.platform-intro {
  animation: fadeIn 0.8s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}



.platform-title {
  font-size: 42px;
  font-weight: 700;
  color: #00d4ff;
  margin-bottom: 8px;
  letter-spacing: 6px;
  font-family: 'SimHei', 'Microsoft YaHei', sans-serif;
}

.platform-subtitle {
  font-size: 22px;
  color: #00d4ff;
  margin-bottom: 30px;
  font-weight: 600;
  letter-spacing: 4px;
}

.platform-desc {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.8;
  margin-bottom: 40px;
}

.feature-list {
  display: flex;
  gap: 30px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 10px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
  padding: 12px 20px;
  background: rgba(0, 212, 255, 0.1);
  border-radius: 8px;
  border: 1px solid rgba(0, 212, 255, 0.2);
}

.feature-icon {
  font-size: 20px;
}

.login-right {
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-card {
  width: 420px;
  padding: 50px 40px;
  background: rgba(0, 20, 40, 0.6);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  border: 1px solid rgba(0, 212, 255, 0.3);
  box-shadow: 0 0 40px rgba(0, 212, 255, 0.15);
  animation: fadeIn 0.8s ease 0.2s both;
}

.login-card.shake {
  animation: shake 0.5s ease;
}

.card-header {
  text-align: center;
  margin-bottom: 40px;
}

.card-header h2 {
  font-size: 28px;
  color: #fff;
  margin-bottom: 10px;
}

.card-header p {
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.form-item label {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 500;
}

.form-item input {
  padding: 14px 16px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 8px;
  color: #fff;
  font-size: 15px;
  transition: all 0.3s;
  outline: none;
}

.form-item input:focus {
  border-color: #00d4ff;
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.2);
}

.form-item input::placeholder {
  color: rgba(255, 255, 255, 0.3);
}

.form-item input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.captcha-input-wrapper {
  display: flex;
  gap: 15px;
}

.captcha-input-wrapper input {
  flex: 1;
}

.error-message {
  color: #ff4d4f;
  font-size: 13px;
  text-align: center;
  padding: 10px;
  background: rgba(255, 77, 79, 0.1);
  border-radius: 6px;
  border: 1px solid rgba(255, 77, 79, 0.3);
}

.login-btn {
  padding: 16px;
  background: linear-gradient(135deg, #00d4ff, #0099cc);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  margin-top: 10px;
  letter-spacing: 4px;
}

.login-btn:hover:not(:disabled) {
  box-shadow: 0 0 30px rgba(0, 212, 255, 0.5);
  transform: translateY(-2px);
}

.login-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: rotate 0.8s linear infinite;
}

.demo-accounts {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid rgba(0, 212, 255, 0.1);
  text-align: center;
}

.demo-accounts p {
  color: rgba(255, 255, 255, 0.5);
  font-size: 12px;
  line-height: 1.8;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-8px); }
  20%, 40%, 60%, 80% { transform: translateX(8px); }
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes badgeGlow {
  0%, 100% { 
    filter: drop-shadow(0 0 15px rgba(196, 30, 58, 0.5)); 
    transform: scale(1);
  }
  50% { 
    filter: drop-shadow(0 0 25px rgba(196, 30, 58, 0.8)); 
    transform: scale(1.02);
  }
}
</style>
