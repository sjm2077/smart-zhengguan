<template>
  <div class="iframe-container">
    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner">
        <div class="spinner"></div>
        <p>正在加载页面...</p>
      </div>
    </div>

    <div v-if="error" class="error-overlay">
      <div class="error-content">
        <span class="error-icon">⚠️</span>
        <p>页面加载失败</p>
        <button @click="retry" class="retry-btn">重新加载</button>
      </div>
    </div>

    <iframe
      ref="iframeRef"
      :src="src"
      :title="title"
      frameborder="0"
      @load="handleLoad"
      @error="handleError"
    ></iframe>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useAuthStore } from '../stores/auth'

const props = defineProps({
  src: {
    type: String,
    required: true
  },
  title: {
    type: String,
    default: '子系统'
  }
})

const authStore = useAuthStore()
const iframeRef = ref(null)
const loading = ref(true)
const error = ref(false)

const handleLoad = () => {
  loading.value = false
  error.value = false
  sendAuthMessage()
}

const handleError = () => {
  loading.value = false
  error.value = true
}

const retry = () => {
  loading.value = true
  error.value = false
  if (iframeRef.value) {
    iframeRef.value.src = props.src
  }
}

const sendAuthMessage = () => {
  if (iframeRef.value && authStore.userInfo) {
    const message = {
      type: 'auth',
      payload: {
        token: authStore.token,
        role: authStore.userInfo.role,
        userId: authStore.userInfo.id,
        username: authStore.userInfo.username
      }
    }
    iframeRef.value.contentWindow?.postMessage(message, '*')
  }
}

const handleMessage = (event) => {
  console.log('收到子系统消息:', event.data)
}

onMounted(() => {
  window.addEventListener('message', handleMessage)
})

onUnmounted(() => {
  window.removeEventListener('message', handleMessage)
})

watch(() => props.src, () => {
  loading.value = true
  error.value = false
})
</script>

<style scoped>
.iframe-container {
  width: 100%;
  height: calc(100vh - 120px);
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.3);
}

iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.loading-overlay,
.error-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(10, 31, 68, 0.95);
  z-index: 10;
}

.loading-spinner {
  text-align: center;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 3px solid rgba(0, 212, 255, 0.2);
  border-top-color: #00d4ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

.loading-spinner p {
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
}

.error-content {
  text-align: center;
}

.error-icon {
  font-size: 60px;
  display: block;
  margin-bottom: 20px;
}

.error-content p {
  color: rgba(255, 255, 255, 0.8);
  font-size: 16px;
  margin-bottom: 20px;
}

.retry-btn {
  padding: 12px 30px;
  background: linear-gradient(135deg, #00d4ff, #0099cc);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.retry-btn:hover {
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
  transform: translateY(-2px);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
