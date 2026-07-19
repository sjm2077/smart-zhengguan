<template>
  <aside class="sidebar" :class="{ collapsed: isCollapsed }">
    <div class="sidebar-header">
      <div class="logo" v-if="!isCollapsed">
        <span class="logo-icon">🏛️</span>
        <span class="logo-text">综合管理</span>
      </div>
      <div class="logo collapsed-logo" v-else>
        <span class="logo-icon">🏛️</span>
      </div>
    </div>

    <div class="sidebar-footer">
      <div class="version" v-if="!isCollapsed">
        <span>V1.0.0</span>
      </div>
      <button class="collapse-btn" @click="toggleCollapse">
        <span>{{ isCollapsed ? '→' : '←' }}</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
const props = defineProps({
  isCollapsed: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:isCollapsed'])

const toggleCollapse = () => {
  emit('update:isCollapsed', !props.isCollapsed)
}
</script>

<style scoped>
.sidebar {
  width: 220px;
  height: 100%;
  background: linear-gradient(180deg, rgba(5, 13, 31, 0.95) 0%, rgba(10, 31, 68, 0.9) 100%);
  border-right: 1px solid rgba(0, 212, 255, 0.2);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: width 0.3s ease;
  position: relative;
  z-index: 50;
}

.sidebar.collapsed {
  width: 60px;
}

.sidebar-header {
  height: 70px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 15px;
  border-bottom: 1px solid rgba(0, 212, 255, 0.1);
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  font-size: 28px;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: #00d4ff;
  letter-spacing: 2px;
}

.collapsed-logo {
  justify-content: center;
}

.sidebar-footer {
  padding: 15px;
  border-top: 1px solid rgba(0, 212, 255, 0.1);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.version {
  text-align: center;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

.collapse-btn {
  width: 100%;
  padding: 10px;
  background: rgba(0, 212, 255, 0.1);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 8px;
  color: #00d4ff;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.collapse-btn:hover {
  background: rgba(0, 212, 255, 0.2);
}

.sidebar.collapsed .collapse-btn {
  font-size: 12px;
}
</style>
