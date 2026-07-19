<template>
  <div class="kpi-card" :class="{ disabled: isDisabled, hidden: isHidden }" :style="cardStyle">
    <div class="card-inner">
      <div class="card-left">
        <span class="card-title">{{ title }}</span>
        <div class="card-value-row">
          <span class="card-value" :style="valueStyle">
            <template v-if="isHidden">
              <span class="no-permission">无权限</span>
            </template>
            <template v-else-if="displayValue === '--'">
              <span class="masked">--</span>
            </template>
            <template v-else>
              <span class="number" ref="numberRef">{{ animatedValue }}</span>
              <span class="unit">{{ unit }}</span>
            </template>
          </span>
          <span v-if="showTrend" class="trend" :class="trendClass">
            <span class="trend-icon">{{ trendDirection === 'up' ? '▲' : '▼' }}</span>
            <span class="trend-value">{{ trend }}%</span>
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'

const props = defineProps({
  title: { type: String, required: true },
  value: { type: [Number, String], default: 0 },
  unit: { type: String, default: '' },
  trend: { type: Number, default: 0 },
  trendDirection: { type: String, default: 'up' },
  gradient: { type: String, default: 'linear-gradient(135deg, #00d4ff, #0099cc)' },
  color: { type: String, default: '#00d4ff' },
  permission: { type: String, default: 'full' }
})

const animatedValue = ref(props.value)

const isHidden = computed(() => props.permission === 'hidden')
const isDisabled = computed(() => props.permission === '--' || props.permission === 'hidden')
const showTrend = computed(() => !isHidden.value && props.permission !== '--' && props.trend !== 0)

const displayValue = computed(() => {
  if (isHidden.value) return 'hidden'
  if (props.permission === '--') return '--'
  return props.value
})

const trendClass = computed(() => ({
  'trend-up': props.trendDirection === 'up',
  'trend-down': props.trendDirection === 'down'
}))

const valueStyle = computed(() => ({
  background: props.gradient,
  '-webkit-background-clip': 'text',
  '-webkit-text-fill-color': 'transparent',
  'background-clip': 'text'
}))

const cardStyle = computed(() => ({
  '--bar-color': props.color
}))

watch(() => props.value, (newVal) => {
  animatedValue.value = newVal
}, { immediate: true })
</script>

<style scoped>
.kpi-card {
  background: rgba(16, 32, 64, 0.6);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 10px;
  padding: 12px 16px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s;
  min-width: 180px;
  height: 100%;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.kpi-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 60%;
  background: var(--bar-color, #00d4ff);
  border-radius: 0 2px 2px 0;
  box-shadow: 0 0 10px var(--bar-color, #00d4ff);
}

.kpi-card:hover {
  border-color: rgba(0, 212, 255, 0.45);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.08);
  transform: translateY(-2px);
}

.kpi-card.disabled {
  opacity: 0.5;
}

.kpi-card.hidden {
  display: none;
}

.card-inner {
  display: flex;
  flex-direction: column;
  justify-content: center;
  height: 100%;
  position: relative;
  z-index: 1;
  padding-left: 8px;
}

.card-left {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.card-title {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.65);
  font-weight: 500;
  letter-spacing: 0.5px;
}

.card-value-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
}

.card-value {
  font-size: 24px;
  font-weight: 700;
  font-family: 'Orbitron', 'DIN Alternate', monospace;
  line-height: 1;
  display: flex;
  align-items: baseline;
}

.number {
  display: inline-block;
}

.unit {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  -webkit-text-fill-color: rgba(255, 255, 255, 0.8);
  margin-left: 4px;
}

.trend {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  flex-shrink: 0;
  font-weight: 500;
}

.trend-up {
  background: rgba(82, 196, 26, 0.15);
  color: #52c41a;
  border: 1px solid rgba(82, 196, 26, 0.3);
}

.trend-down {
  background: rgba(255, 77, 79, 0.15);
  color: #ff4d4f;
  border: 1px solid rgba(255, 77, 79, 0.3);
}

.trend-icon {
  font-size: 9px;
}

.trend-value {
  font-weight: 600;
}

.masked,
.no-permission {
  background: rgba(255, 255, 255, 0.3);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
</style>
