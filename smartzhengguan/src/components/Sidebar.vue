<template>
  <div class="sidebar">
    <el-menu
      router
      :default-active="$route.path"
      background-color="#0A2463"
      text-color="rgba(255,255,255,0.75)"
      active-text-color="#fff"
      class="side-menu"
    >
      <el-menu-item index="/home">
        <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
          <polyline points="9 22 9 12 15 12 15 22" />
        </svg>
        <span>首页</span>
      </el-menu-item>

      <el-menu-item index="/admission">
        <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
          <rect x="8" y="2" width="8" height="4" rx="1" />
        </svg>
        <span>招生管理</span>
      </el-menu-item>

      <el-sub-menu index="academic-menu">
        <template #title>
          <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="8" r="4" />
            <path d="M4 20c0-4 4-7 8-7s8 3 8 7" />
          </svg>
          <span>学籍管理</span>
        </template>
        <el-menu-item index="/academic-status">学籍总览</el-menu-item>
        <el-menu-item index="/academic-change">学籍异动管理</el-menu-item>
      </el-sub-menu>

      <el-sub-menu index="training-menu">
        <template #title>
          <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
          </svg>
          <span>培养管理</span>
        </template>
        <el-menu-item index="/training">培养总览</el-menu-item>
        <el-menu-item index="/training-course">课程与培养环节管理</el-menu-item>
      </el-sub-menu>

      <el-sub-menu index="degree-menu">
        <template #title>
          <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
            <path d="M6 12v5c0 2 3 4 6 4s6-2 6-4v-5" />
          </svg>
          <span>学位管理</span>
        </template>
        <el-menu-item index="/degree">学位总览</el-menu-item>
        <el-menu-item index="/degree-defense">答辩管理</el-menu-item>
      </el-sub-menu>

      <el-menu-item index="/scholarship">
        <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="8" r="6" />
          <path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11" />
        </svg>
        <span>奖助管理</span>
      </el-menu-item>

      <el-menu-item index="/employment">
        <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="2" y="7" width="20" height="14" rx="2" />
          <path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2" />
          <circle cx="12" cy="14" r="2" />
        </svg>
        <span>就业管理</span>
      </el-menu-item>

      <el-menu-item index="/intelligent-prediction">
        <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 3v4" />
          <path d="M12 17v4" />
          <path d="M4.93 4.93l2.83 2.83" />
          <path d="M16.24 16.24l2.83 2.83" />
          <path d="M3 12h4" />
          <path d="M17 12h4" />
          <path d="M4.93 19.07l2.83-2.83" />
          <path d="M16.24 7.76l2.83-2.83" />
          <circle cx="12" cy="12" r="4" />
        </svg>
        <span>智能预测</span>
      </el-menu-item>

      <el-menu-item index="/data-management">
        <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
          <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
          <line x1="12" y1="22.08" x2="12" y2="12" />
        </svg>
        <span>数据管理</span>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<style scoped>
.sidebar { width: 200px; flex-shrink: 0; background: #0A2463; overflow-y: auto; }
.side-menu { border-right: none !important; height: 100%; }
.side-menu .el-menu-item,
.side-menu :deep(.el-sub-menu__title) { font-size: 15px; font-weight: 500; height: 46px; line-height: 46px; }
.side-menu .el-menu-item { padding-left: 20px !important; }
.side-menu :deep(.el-sub-menu__title) { padding-left: 20px !important; color: rgba(255,255,255,0.75) !important; }
.side-menu .el-menu-item:hover,
.side-menu :deep(.el-sub-menu__title:hover) { background: rgba(255,255,255,0.08) !important; }
.side-menu .el-menu-item.is-active { background: rgba(255,255,255,0.15) !important; border-left: 3px solid #409EFF; }
.side-menu :deep(.el-sub-menu.is-active > .el-sub-menu__title),
.side-menu :deep(.el-sub-menu.is-opened > .el-sub-menu__title) {
  color: #fff !important;
}
.side-menu :deep(.el-menu--inline) {
  background: rgba(255,255,255,0.04) !important;
}
.side-menu :deep(.el-menu--inline .el-menu-item) {
  min-width: auto;
  padding-left: 48px !important;
  font-size: 14px;
}
.menu-icon { width: 18px; height: 18px; margin-right: 8px; flex-shrink: 0; vertical-align: middle; opacity: 0.8; }

@media (max-width: 1200px) {
  .sidebar { width: 72px; }
  .side-menu .el-menu-item,
  .side-menu :deep(.el-sub-menu__title) { justify-content: center; padding-left: 0 !important; }
  .side-menu .el-menu-item span,
  .side-menu :deep(.el-sub-menu__title span) { display: none; }
  .menu-icon { margin-right: 0; }
}
</style>
