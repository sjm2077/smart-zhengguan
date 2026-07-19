<template>
  <div class="not-found">
    <div class="content">
      <h1 class="code">404</h1>
      <h2 class="title">页面不存在</h2>
      <p class="desc">抱歉，您访问的页面不存在或已被删除</p>
      <button @click="goHome" class="home-btn">返回首页</button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/')
}
</script>

<style scoped>
.not-found {
  width: 100%;
  height: calc(100vh - 120px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.content {
  text-align: center;
}

.code {
  font-size: 120px;
  font-weight: 700;
  font-family: 'Orbitron', monospace;
  background: linear-gradient(135deg, #00d4ff, #7b2cbf);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 20px;
}

.title {
  font-size: 32px;
  color: #fff;
  margin-bottom: 15px;
}

.desc {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 40px;
}

.home-btn {
  padding: 14px 40px;
  background: linear-gradient(135deg, #00d4ff, #0099cc);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.3s;
}

.home-btn:hover {
  box-shadow: 0 0 30px rgba(0, 212, 255, 0.5);
  transform: translateY(-2px);
}
</style>
