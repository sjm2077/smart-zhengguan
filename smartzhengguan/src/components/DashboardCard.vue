<template>
  <div class="stat-card">
    <div class="stat-icon" :style="{ background: resolvedTheme.surface }">
      <MonoIcon
        :icon="icon"
        :size="22"
        :primary="resolvedTheme.primary"
        :secondary="resolvedTheme.secondary"
      />
    </div>
    <div class="stat-info">
      <div class="stat-number">{{ number }}</div>
      <div class="stat-title">{{ title }}</div>
      <div class="stat-change" :class="changeClass">{{ displayChange }}</div>
    </div>
  </div>
</template>

<script>
import MonoIcon from './MonoIcon.vue'
import { getIconTheme } from '../utils/iconThemes'

export default {
  components: { MonoIcon },
  props: ['title', 'number', 'change', 'icon', 'iconBg', 'changeLabel'],
  computed: {
    resolvedTheme() {
      return getIconTheme(this.icon)
    },
    numericChange() {
      const value = Number(this.change)
      return Number.isFinite(value) ? value : null
    },
    changeClass() {
      if (this.numericChange === null) return 'neutral'
      return this.numericChange >= 0 ? 'up' : 'down'
    },
    displayChange() {
      if (this.changeLabel) return this.changeLabel
      if (this.numericChange === null) return '暂无环比信息'
      const value = Math.abs(this.numericChange).toFixed(1).replace(/\.0$/, '')
      return `较上期 ${this.numericChange >= 0 ? '↑' : '↓'} ${value}%`
    },
  },
}
</script>

<style scoped>
.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  height: 100%;
}

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #165DFF;
  flex-shrink: 0;
}

.stat-number {
  font-size: 24px;
  font-weight: 700;
  color: #333;
  margin-bottom: 2px;
}

.stat-title {
  font-size: 14px;
  font-weight: 400;
  color: #666;
  margin-bottom: 2px;
}

.stat-change {
  font-size: 12px;
  font-weight: 400;
  color: #999;
}

.stat-change.up {
  color: #2ecc71;
}

.stat-change.down {
  color: #ff4d4f;
}

.stat-change.neutral {
  color: #999;
}
</style>
