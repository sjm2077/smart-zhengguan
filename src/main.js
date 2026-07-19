import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './styles/global.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.mount('#app')

if (window.echarts) {
  console.log('ECharts loaded successfully')
} else {
  console.error('ECharts not loaded')
}
