<template>
  <router-view v-if="hideLayout" />
  <div v-else class="app-layout">
    <Navbar />
    <div class="app-body">
      <Sidebar />
      <div class="app-main">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script>
import Navbar from './components/Navbar.vue'
import Sidebar from './components/Sidebar.vue'

export default {
  components: { Navbar, Sidebar },
  computed: {
    hideLayout() {
      return Boolean(this.$route.meta?.hideLayout)
    },
  },
}
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html {
  color-scheme: only light;
  background: #fff;
}
body {
  color-scheme: only light;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', sans-serif;
  background: #fff;
  color: #333;
}
#app {
  color-scheme: only light;
  background: #fff;
  color: #333;
}
.app-layout { display: flex; flex-direction: column; height: 100vh; background: #fff; color: #333; }
.app-body { display: flex; flex: 1; overflow: hidden; }
.app-main { flex: 1; min-width: 0; padding: 16px; overflow: auto; background: #fff; }
.app-main,
.app-main .page-header,
.app-main .filter-row,
.app-main .section-card,
.app-main .chart-card,
.app-main .stat-card,
.app-main .chart-box,
.app-main .el-table,
.app-main .el-table__inner-wrapper,
.app-main .el-table tr,
.app-main .el-table th.el-table__cell,
.app-main .el-table td.el-table__cell,
.app-main .el-input__wrapper,
.app-main .el-textarea__inner,
.app-main .el-select__wrapper,
.app-main .el-dialog,
.app-main .el-drawer,
.app-main .el-empty,
.app-main .el-pagination,
.app-main .el-pager li {
  color-scheme: only light;
}
.app-main .page-header,
.app-main .filter-row,
.app-main .section-card,
.app-main .chart-card,
.app-main .stat-card,
.app-main .el-table,
.app-main .el-table__inner-wrapper,
.app-main .el-table tr,
.app-main .el-table th.el-table__cell,
.app-main .el-table td.el-table__cell,
.app-main .el-input__wrapper,
.app-main .el-textarea__inner,
.app-main .el-select__wrapper,
.app-main .el-dialog,
.app-main .el-drawer,
.app-main .el-empty {
  background: #fff !important;
  color: #333 !important;
}
.app-main .el-row { min-width: 0; }
.app-main .stat-row,
.app-main .chart-row,
.app-main .bottom-row { row-gap: 16px; }
.app-main .stat-row > .el-col,
.app-main .chart-row > .el-col,
.app-main .bottom-row > .el-col { min-width: 0; }
.app-main .chart-card,
.app-main .info-card,
.app-main .stat-card,
.app-main .section-card { min-width: 0; }
.app-main .page-header,
.app-main .filter-row { min-width: 0; }
.app-main .header-right,
.app-main .filter-items { min-width: 0; flex-wrap: wrap; }
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #ccc; border-radius: 3px; }

@media (max-width: 1400px) {
  .app-main .stat-row > .el-col {
    flex: 0 0 50% !important;
    max-width: 50% !important;
  }

  .app-main .chart-row > .el-col,
  .app-main .bottom-row > .el-col {
    flex: 0 0 50% !important;
    max-width: 50% !important;
  }
}

@media (max-width: 1100px) {
  .app-main { padding: 12px; }

  .app-main .page-header,
  .app-main .filter-row {
    flex-direction: column;
    align-items: flex-start !important;
  }

  .app-main .header-right,
  .app-main .filter-btns {
    width: 100%;
  }

  .app-main .stat-row > .el-col,
  .app-main .chart-row > .el-col,
  .app-main .bottom-row > .el-col {
    flex: 0 0 100% !important;
    max-width: 100% !important;
  }

  .app-main .quick-grid {
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)) !important;
  }
}

@media (max-width: 768px) {
  .app-main { padding: 10px; }
}
</style>
