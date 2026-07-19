<template>
  <div class="verify-code" @click="refresh">
    <canvas ref="canvas" :width="width" :height="height"></canvas>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  width: { type: Number, default: 120 },
  height: { type: Number, default: 40 }
})

const emit = defineEmits(['update:value', 'change'])
const canvas = ref(null)
const code = ref('')

const generateCode = () => {
  const chars = '0123456789ABCDEFGHJKLMNPQRSTUVWXYZ'
  let result = ''
  for (let i = 0; i < 4; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  code.value = result
  emit('update:value', result)
  emit('change', result)
  drawCanvas()
}

const drawCanvas = () => {
  const ctx = canvas.value.getContext('2d')
  ctx.clearRect(0, 0, props.width, props.height)
  
  ctx.fillStyle = 'rgba(0, 20, 40, 0.9)'
  ctx.fillRect(0, 0, props.width, props.height)

  for (let i = 0; i < 30; i++) {
    ctx.beginPath()
    ctx.arc(
      Math.random() * props.width,
      Math.random() * props.height,
      Math.random() * 1.5,
      0,
      Math.PI * 2
    )
    ctx.fillStyle = `rgba(${Math.random() * 255}, ${Math.random() * 255}, ${Math.random() * 255}, 0.5)`
    ctx.fill()
  }

  ctx.font = 'bold 24px Orbitron, Arial'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  
  for (let i = 0; i < code.value.length; i++) {
    const x = (props.width / 5) * (i + 1)
    const y = props.height / 2 + (Math.random() - 0.5) * 10
    const angle = (Math.random() - 0.5) * 0.4
    
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(angle)
    
    const gradient = ctx.createLinearGradient(x - 10, y - 10, x + 10, y + 10)
    gradient.addColorStop(0, '#00d4ff')
    gradient.addColorStop(0.5, '#eb2f96')
    gradient.addColorStop(1, '#00d4ff')
    
    ctx.fillStyle = gradient
    ctx.fillText(code.value[i], 0, 0)
    ctx.restore()
  }

  for (let i = 0; i < 3; i++) {
    ctx.beginPath()
    ctx.moveTo(Math.random() * props.width, Math.random() * props.height)
    ctx.lineTo(Math.random() * props.width, Math.random() * props.height)
    ctx.strokeStyle = `rgba(${Math.random() * 255}, ${Math.random() * 255}, ${Math.random() * 255}, 0.3)`
    ctx.stroke()
  }
}

const refresh = () => {
  generateCode()
}

onMounted(() => {
  generateCode()
})

defineExpose({ refresh })
</script>

<style scoped>
.verify-code {
  cursor: pointer;
  border-radius: 8px;
  overflow: hidden;
  transition: transform 0.2s;
}

.verify-code:hover {
  transform: scale(1.02);
}

canvas {
  display: block;
  border-radius: 8px;
}
</style>
