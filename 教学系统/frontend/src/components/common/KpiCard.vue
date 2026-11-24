<template>
  <div class="kpi-card">
    <div class="title">{{ title }}</div>
    <div class="value">{{ value }}</div>
  </div>
</template>

<script setup lang="ts">
defineProps({
  title: String,
  value: Number,
})
</script>

<style scoped lang="scss">
.kpi-card {
  background: linear-gradient(135deg, #0d2342, #153b70);
  border-radius: 12px;
  padding: 20px;
  color: white;
  box-shadow: 0 0 15px rgba(0,0,0,0.4);
}

.title {
  font-size: 15px;
  color: #b5cfff;
}

.value {
  font-size: 34px;
  margin-top: 12px;
  font-weight: bold;
}
</style>