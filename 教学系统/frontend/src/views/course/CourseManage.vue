<template>
  <main class="course-hub">
    <header class="page-header">
      <div class="header-title">
        <h1><span class="head-glyph">▤</span> 课程资源与教学运行中心</h1>
        <p>山东大学政治学与公共管理学院 · 本学期课程安排、教学任务与课程数据维护</p>
      </div>
      <div class="header-actions">
        <span class="semester-pill">2026—2027学年 · 第一学期</span>
        <button class="btn btn-light" type="button" :disabled="loading" @click="loadData">↻ 刷新数据</button>
        <button class="btn btn-primary" type="button" @click="openCreateCourse">＋ 新增课程</button>
      </div>
    </header>

    <div v-if="errorMessage" class="alert alert-error" role="alert">
      <strong>数据读取失败：</strong>{{ errorMessage }}
      <button class="btn btn-text" type="button" @click="loadData">重新读取</button>
    </div>
    <div v-if="warningMessage" class="alert alert-warn" role="status">{{ warningMessage }}</div>
    <div v-if="loaded && !semesterId" class="alert alert-warn" role="status">
      后端未找到“2026—2027学年第一学期”对应的学期记录，因此暂不将其他学期课程误计入本学期。请先检查现有学期配置。
    </div>
    <div v-if="previewRows.length" class="alert alert-warn" role="status">
      当前页面有 {{ previewRows.length }} 条 Excel 临时预览记录，尚未写入数据库，不计入上方正式统计。
      <button class="btn btn-text" type="button" @click="clearPreview">清除临时预览</button>
    </div>
    <div class="data-note">
      <span class="note-bullet"></span>
      当前学期固定；统计来自现有教务接口。对于缺少明确专业、年级或选修类别字段的课程，标记为“待关联/待分类”，不自行推断。
    </div>

    <section class="overview" aria-label="本学期教学运行概览">
      <article v-for="card in summaryCards" :key="card.label" class="overview-card">
        <div class="overview-icon" :class="card.color">{{ card.icon }}</div>
        <div class="overview-content">
          <span>{{ card.label }}</span>
          <strong>{{ card.value }}</strong>
          <small>{{ card.detail }}</small>
        </div>
      </article>
    </section>

    <section id="module-required-courses" class="panel">
      <div class="panel-heading">
        <div>
          <h2><span class="blue-rail"></span> 专业与年级必修课程安排</h2>
          <p>覆盖六个专业的本学期公共必修与专业必修课。课程适用范围必须来自明确记录，不能用课程名称推定。</p>
        </div>
        <span class="count-chip">{{ filteredRequired.length }} 条记录</span>
      </div>
      <div class="filters">
        <label>所属专业
          <select v-model="requiredMajor" @change="onRequiredMajorChanged">
            <option value="">全部专业</option>
            <option v-for="m in MAJORS" :key="m.name" :value="m.name">{{ m.name }}</option>
          </select>
        </label>
        <label>入学年级
          <select v-model="requiredGrade" @change="resetRequiredPage">
            <option value="">全部年级</option>
            <option v-for="year in requiredGradeOptions" :key="year" :value="String(year)">{{ year }}级</option>
          </select>
        </label>
        <label>必修性质
          <select v-model="requiredCategory" @change="resetRequiredPage">
            <option value="">全部必修</option>
            <option value="公共必修">公共必修</option>
            <option value="专业必修">专业必修</option>
            <option value="必修（未细分）">未细分必修</option>
          </select>
        </label>
        <label class="filter-search">搜索课程
          <input v-model.trim="requiredKeyword" type="search" placeholder="课程名称 / 代码 / 教师 / 教学班" @input="resetRequiredPage" />
        </label>
      </div>
      <div class="panel-actions">
        <span class="helper-note">后端课程与教学班信息实时读取；Excel导入为待入库预览，不会自动修改数据库。</span>
        <div class="button-group">
          <button class="btn btn-light" type="button" @click="downloadTemplate('required')">下载模板</button>
          <button class="btn btn-light" type="button" @click="requiredFileInput?.click()">导入 Excel</button>
          <button class="btn btn-light" type="button" @click="exportExcel('required')">导出 Excel</button>
          <input ref="requiredFileInput" class="visually-hidden" type="file" accept=".xlsx,.csv" @change="onFileSelected($event, 'required')" />
        </div>
      </div>
      <div class="table-wrap">
        <table class="course-table">
          <thead><tr>
            <th>课程代码 / 课程名称</th><th>必修性质</th><th>适用专业 / 年级</th>
            <th>任课教师</th><th>学分 / 学时</th><th>上课时间 / 地点</th><th>来源</th><th>操作</th>
          </tr></thead>
          <tbody>
            <tr v-for="row in requiredVisible" :key="row.uid">
              <td><strong>{{ row.name }}</strong><small>{{ row.code }}<template v-if="row.className"> · {{ row.className }}</template></small></td>
              <td><span class="category-tag">{{ row.category }}</span></td>
              <td>
                <span v-if="row.major && row.grade" class="target-tag">{{ row.major }} · {{ row.grade }}级</span>
                <span v-else class="muted">待关联专业与年级</span>
              </td>
              <td>{{ row.teacher || '待分配' }}</td>
              <td>{{ displayNumber(row.credit) }} / {{ displayNumber(row.hours) }}</td>
              <td>{{ row.schedule || '待排课' }}<small>{{ row.location || '地点未录入' }}</small></td>
              <td><span class="source-tag" :class="row.source === 'preview' ? 'source-preview' : 'source-server'">{{ row.source === 'preview' ? '未入库' : '教务接口' }}</span></td>
              <td><button class="text-link" type="button" @click="detail = row">详情</button></td>
            </tr>
            <tr v-if="!loading && filteredRequired.length === 0"><td colspan="8" class="empty-cell">暂无符合条件的必修课程。请确认当前学期数据及课程类型，或通过 Excel 导入预览。</td></tr>
            <tr v-if="loading"><td colspan="8" class="empty-cell">正在读取课程数据…</td></tr>
          </tbody>
        </table>
      </div>
      <div class="pagination">
        <span>显示 {{ filteredRequired.length ? (requiredPage-1)*PAGE_SIZE+1 : 0 }}—{{ Math.min(requiredPage*PAGE_SIZE,filteredRequired.length) }} 条，共 {{ filteredRequired.length }} 条</span>
        <div><button type="button" :disabled="requiredPage<=1" @click="requiredPage--">上一页</button><span>{{ requiredPage }} / {{ requiredTotalPages }}</span><button type="button" :disabled="requiredPage>=requiredTotalPages" @click="requiredPage++">下一页</button></div>
      </div>
    </section>

    <section id="module-elective-courses" class="panel">
      <div class="panel-heading">
        <div>
          <h2><span class="blue-rail"></span> 本学期教师选修课程安排</h2>
          <p>包含本院教师开设的专业限选课，以及面向全校学生开设的公共选修课；不再使用虚构的热度排名。</p>
        </div>
        <span class="count-chip">{{ filteredElective.length }} 条记录</span>
      </div>
      <div class="filters">
        <label>任课教师
          <select v-model="electiveTeacher" @change="resetElectivePage">
            <option value="">全部教师</option>
            <option v-for="teacher in teacherNames" :key="teacher" :value="teacher">{{ teacher }}</option>
          </select>
        </label>
        <label>选修类别
          <select v-model="electiveCategory" @change="resetElectivePage">
            <option value="">全部选修</option>
            <option value="专业限选">专业限选</option>
            <option value="公共选修">公共选修</option>
            <option value="选修（未细分）">未细分选修</option>
          </select>
        </label>
        <label class="filter-search">搜索课程
          <input v-model.trim="electiveKeyword" type="search" placeholder="课程名称 / 代码 / 教师 / 教学班" @input="resetElectivePage" />
        </label>
      </div>
      <div class="panel-actions">
        <span class="helper-note">公共选修标注“面向全校”；没有选课人数和容量数据时保持空值，不估算。</span>
        <div class="button-group">
          <button class="btn btn-light" type="button" @click="downloadTemplate('elective')">下载模板</button>
          <button class="btn btn-light" type="button" @click="electiveFileInput?.click()">导入 Excel</button>
          <button class="btn btn-light" type="button" @click="exportExcel('elective')">导出 Excel</button>
          <input ref="electiveFileInput" class="visually-hidden" type="file" accept=".xlsx,.csv" @change="onFileSelected($event, 'elective')" />
        </div>
      </div>
      <div class="table-wrap">
        <table class="course-table">
          <thead><tr>
            <th>课程代码 / 课程名称</th><th>选修类别</th><th>任课教师</th>
            <th>面向对象</th><th>学分 / 学时</th><th>选课人数 / 容量</th><th>排课信息</th><th>来源</th><th>操作</th>
          </tr></thead>
          <tbody>
            <tr v-for="row in electiveVisible" :key="row.uid">
              <td><strong>{{ row.name }}</strong><small>{{ row.code }}<template v-if="row.className"> · {{ row.className }}</template></small></td>
              <td><span class="category-tag">{{ row.category }}</span></td>
              <td>{{ row.teacher || '待分配' }}</td>
              <td>{{ row.audience || (row.category === '公共选修' ? '面向全校' : '未录入') }}</td>
              <td>{{ displayNumber(row.credit) }} / {{ displayNumber(row.hours) }}</td>
              <td>
                <span v-if="row.enrolled !== null && row.capacity !== null">{{ row.enrolled }} / {{ row.capacity }}</span>
                <span v-else class="muted">未录入</span>
              </td>
              <td>{{ row.schedule || '待排课' }}<small>{{ row.location || '地点未录入' }}</small></td>
              <td><span class="source-tag" :class="row.source === 'preview' ? 'source-preview' : 'source-server'">{{ row.source === 'preview' ? '未入库' : '教务接口' }}</span></td>
              <td><button class="text-link" type="button" @click="detail = row">详情</button></td>
            </tr>
            <tr v-if="!loading && filteredElective.length === 0"><td colspan="9" class="empty-cell">暂无符合条件的选修课程。若后端只有“选修”大类，会在这里标记为“未细分选修”。</td></tr>
            <tr v-if="loading"><td colspan="9" class="empty-cell">正在读取课程数据…</td></tr>
          </tbody>
        </table>
      </div>
      <div class="pagination">
        <span>显示 {{ filteredElective.length ? (electivePage-1)*PAGE_SIZE+1 : 0 }}—{{ Math.min(electivePage*PAGE_SIZE,filteredElective.length) }} 条，共 {{ filteredElective.length }} 条</span>
        <div><button type="button" :disabled="electivePage<=1" @click="electivePage--">上一页</button><span>{{ electivePage }} / {{ electiveTotalPages }}</span><button type="button" :disabled="electivePage>=electiveTotalPages" @click="electivePage++">下一页</button></div>
      </div>
    </section>


    <!-- 原有第3行：课程分类树 + 教学计划进度 + 课程容量分析（保留布局，替换为本学期数据） -->
    <div class="legacy-region" aria-label="课程资源与运行概览">
      <div class="legacy-region-heading">
        <h2><span class="blue-rail"></span> 课程资源与教学进度</h2>
        <p>恢复原页面的三栏分析、课程封面和时间轴布局；数据取自本学期现有教务记录。</p>
      </div>
      <div class="hub-row-3col">
        <section id="module-course-category-tree" class="hub-panel">
          <div class="hub-panel-header">
            <span class="hub-panel-title">
              <svg class="panel-title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/></svg>
              课程分类树
            </span>
            <span class="hub-panel-badge">{{ legacyCategoryTotal }} 门</span>
          </div>
          <div v-if="legacyCategoryTree.length" class="category-tree">
            <div v-for="cat in legacyCategoryTree" :key="cat.name" class="tree-node">
              <button class="tree-parent" type="button" :aria-expanded="legacyCategoryIsOpen(cat.name)" @click="legacyToggleCategory(cat.name)">
                <svg class="tree-arrow" :class="{ expanded: legacyCategoryIsOpen(cat.name) }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
                <span class="tree-icon" :style="{ background: cat.color }"></span>
                <span class="tree-name">{{ cat.name }}</span>
                <span class="tree-count">{{ cat.children.length }}</span>
              </button>
              <div v-show="legacyCategoryIsOpen(cat.name)" class="tree-children">
                <div v-for="child in cat.children" :key="child" class="tree-child">
                  <span class="tree-child-dot" :style="{ background: cat.color }"></span>
                  <span class="tree-child-name">{{ child }}</span>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="legacy-empty">本学期暂无可分类的课程记录。</div>
        </section>

        <section id="module-teaching-plan-progress" class="hub-panel">
          <div class="hub-panel-header">
            <span class="hub-panel-title">
              <svg class="panel-title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              教学计划进度
            </span>
            <span class="hub-panel-badge">排课资料完整度</span>
          </div>
          <p class="legacy-panel-subtitle">展示教学班教师、上课时间、地点的录入进度，不代表实际授课周进度。</p>
          <div v-if="legacyTeachingPlans.length" class="plan-progress-list">
            <div v-for="plan in legacyTeachingPlans" :key="plan.uid" class="plan-item">
              <div class="plan-info"><span class="plan-name">{{ plan.name }}</span><span class="plan-meta">{{ plan.meta }}</span></div>
              <div class="plan-bar-wrap">
                <div class="plan-bar-bg"><div class="plan-bar-fill" :style="{ width: plan.progress + '%', background: plan.progress === 100 ? '#1E3A8A' : '#60A5FA' }"></div></div>
                <span class="plan-pct" :class="{ 'text-success': plan.progress === 100 }">{{ plan.progress }}%</span>
              </div>
              <div class="plan-milestones">
                <span v-for="step in plan.milestones" :key="step.label" class="milestone-dot" :class="{ done: step.done }" :title="step.label + (step.done ? '已录入' : '未录入')"></span>
              </div>
            </div>
          </div>
          <div v-else class="legacy-empty">暂无本学期教学班安排记录，暂不能计算资料完整度。</div>
        </section>

        <section id="module-course-capacity" class="hub-panel">
          <div class="hub-panel-header">
            <span class="hub-panel-title">
              <svg class="panel-title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
              课程容量分析
            </span>
            <span class="hub-panel-badge">{{ legacyHighLoadCount }} 门高负荷</span>
          </div>
          <div v-if="legacyCapacityCourses.length" class="capacity-list">
            <div v-for="c in legacyCapacityCourses" :key="c.uid" class="capacity-item">
              <div class="capacity-header"><span class="capacity-name" :title="c.name">{{ c.name }}</span><span class="capacity-rate" :class="legacyLoadClass(c.ratio)">{{ (c.ratio * 100).toFixed(0) }}%</span></div>
              <div class="capacity-bar-wrap"><div class="capacity-bar-bg"><div class="capacity-bar-fill" :style="{ width: Math.min(c.ratio * 100, 100) + '%', background: legacyLoadColor(c.ratio) }"></div></div></div>
              <div class="capacity-footer"><span class="capacity-nums">{{ c.enrolled }} / {{ c.capacity }} 人</span><button class="legacy-inline-btn" type="button" @click="detail = c.row">详情</button></div>
            </div>
          </div>
          <div v-else class="legacy-empty">当前教学班未同时录入有效容量和选课人数，暂不能展示容量占比。</div>
        </section>
      </div>

      <!-- 原有第4行：课程封面展示（横向滚动） -->
      <section id="module-course-cover" class="hub-panel hub-cover-panel">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg class="panel-title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
            课程封面展示
          </span>
          <div class="cover-nav">
            <button type="button" class="cover-nav-btn" aria-label="向左浏览课程" @click="legacyScrollCover('left')"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg></button>
            <button type="button" class="cover-nav-btn" aria-label="向右浏览课程" @click="legacyScrollCover('right')"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg></button>
          </div>
        </div>
        <div v-if="legacyFeaturedCourses.length" ref="legacyCoverScrollRef" class="cover-scroll-wrap">
          <button v-for="c in legacyFeaturedCourses" :key="c.uid" class="cover-card" type="button" @click="detail = c.row">
            <div class="cover-banner" :style="{ background: c.coverGradient }">
              <div class="cover-badge-row"><span class="cover-badge badge-active">{{ c.status }}</span><span class="cover-badge cover-badge-type">{{ c.category }}</span></div>
              <div class="cover-icon-wrap"><svg class="cover-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20 M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg></div>
            </div>
            <div class="cover-body">
              <h4 class="cover-name" :title="c.name">{{ c.name }}</h4>
              <p class="cover-college">{{ c.code }} · {{ c.teacher }}</p>
              <div class="cover-meta">
                <span class="cover-meta-item">{{ displayNumber(c.credit) }} 学分</span>
                <span class="cover-meta-item">{{ c.enrolled !== null && c.capacity !== null ? c.enrolled + ' / ' + c.capacity + ' 人' : '选课人数未录入' }}</span>
              </div>
              <div class="cover-rating"><span class="legacy-cover-hint">查看课程详情</span><span aria-hidden="true">›</span></div>
            </div>
          </button>
        </div>
        <div v-else class="legacy-empty">暂无本学期已登记的课程可展示。</div>
      </section>

      <!-- 原有第5行中的课程时间轴保留；热门趋势已替换为教学任务检查 -->
      <div class="hub-row-2col legacy-last-row">
        <section class="hub-panel legacy-operation-panel" id="module-course-operations">
          <div class="hub-panel-header">
            <span class="hub-panel-title">
              <svg class="panel-title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M12 7v5l3 2"/></svg>
              本学期教学任务检查
            </span>
            <span class="hub-panel-badge">{{ issues.length }} 条待完善事项</span>
          </div>
          <p class="legacy-panel-subtitle">基于已有课程与教学班接口，检查授课教师、时间、地点和容量缺项。</p>
          <div v-if="issues.length" class="legacy-issues-list">
            <button v-for="issue in issues.slice(0, 12)" :key="issue.key" class="issue-row" type="button" @click="detail = issue.row">
              <span class="issue-dot"></span><div><strong>{{ issue.row.name }}</strong><small>{{ issue.reason }}</small></div><span class="issue-action">详情 ›</span>
            </button>
            <p v-if="issues.length > 12" class="muted">另有 {{ issues.length - 12 }} 条待完善事项，可通过课程列表进一步查询。</p>
          </div>
          <div v-else class="legacy-empty">{{ loaded ? '可读取的课程记录中暂无已识别缺项，不代表所有排课冲突均已审计。' : '正在读取本学期教学任务。' }}</div>
        </section>
        <section class="hub-panel" id="module-course-timeline">
          <div class="hub-panel-header">
            <span class="hub-panel-title">
              <svg class="panel-title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              课程时间轴
            </span>
            <span class="hub-panel-badge">2026—2027第一学期</span>
          </div>
          <div class="timeline-wrap">
            <div v-for="(evt, i) in legacyTimeline" :key="evt.title" class="timeline-item" :class="{ 'timeline-active': evt.active }">
              <div class="timeline-marker"><div class="timeline-dot" :class="{ 'dot-active': evt.active, 'dot-done': evt.done }"></div><div v-if="i < legacyTimeline.length-1" class="timeline-line" :class="{ 'line-done': evt.done }"></div></div>
              <div class="timeline-content"><div class="timeline-date">{{ evt.date }}</div><div class="timeline-title">{{ evt.title }}</div><div class="timeline-desc">{{ evt.desc }}</div></div>
            </div>
          </div>
          <p class="legacy-panel-subtitle">此处为可核验的业务节点，不代表学校正式教学日历。</p>
        </section>
      </div>
    </div>

    <section v-if="unclassifiedCourses.length" class="panel compact-panel">
      <div class="panel-heading">
        <div><h2><span class="blue-rail"></span> 待分类课程</h2><p>本学期存在课程类型无法识别的真实记录，未擅自归入必修或选修。</p></div>
        <span class="count-chip">{{ unclassifiedCourses.length }} 条</span>
      </div>
      <div class="unclassified-list">
        <span v-for="row in unclassifiedCourses.slice(0,30)" :key="row.uid" class="unclassified-item">{{ row.code }} · {{ row.name }}</span>
      </div>
    </section>

    <div class="page-footnote">说明：本页展示的实时课程记录来自既有 `/api/courses/`、`/api/teaching-classes/` 等接口；新增课程只保存课程基础信息，专业年级开课关系的正式批量入库仍需相应后端字段/接口支持。</div>

    <!-- Excel导入结果：明确为前端校验预览，不冒充正式保存 -->
    <div v-if="importOpen" class="overlay" @click.self="closeImport" @keydown.esc.window="closeImport">
      <div class="dialog" role="dialog" aria-modal="true" aria-labelledby="import-title">
        <div class="dialog-header"><div><span class="eyebrow">EXCEL IMPORT VALIDATION</span><h3 id="import-title">{{ importSection === 'required' ? '必修课程' : '选修课程' }}导入预检</h3></div><button class="icon-close" type="button" @click="closeImport">×</button></div>
        <div class="dialog-content">
          <div class="alert alert-warn">当前版本只执行文件读取、字段校验与页面预览；<strong>不会写入 MySQL，也不会覆盖已有课程记录。</strong>正式批量保存需后端确认课程与专业、年级和教学任务的数据关系。</div>
          <p class="file-name">文件：{{ importFileName || '未选择' }}</p>
          <div class="import-stats"><div><small>有效记录</small><strong>{{ importedPending.length }}</strong></div><div><small>错误记录</small><strong>{{ importErrors.length }}</strong></div></div>
          <div v-if="importErrors.length" class="error-list"><p v-for="(err,i) in importErrors.slice(0,20)" :key="i">{{ err }}</p><p v-if="importErrors.length > 20">其余 {{ importErrors.length-20 }} 条错误请修正文件后重新导入。</p></div>
          <div v-else-if="!importedPending.length" class="empty-note">没有发现可预览的课程行，请检查工作表第一行表头及学期字段。</div>
          <div v-if="importedPending.length" class="sample-list"><div v-for="row in importedPending.slice(0,5)" :key="row.uid"><strong>{{ row.name }}</strong><span>{{ row.code }} · {{ row.teacher || '教师未填' }} · {{ row.category }}</span></div></div>
        </div>
        <div class="dialog-footer"><button class="btn btn-light" type="button" @click="closeImport">取消</button><button class="btn btn-primary" type="button" :disabled="!importedPending.length || importErrors.length > 0" @click="applyImportedPreview">加入本页预览（不入库）</button></div>
      </div>
    </div>

    <!-- 基础课程新增：使用既有 /api/courses/，不创建额外 Django 应用 -->
    <div v-if="createOpen" class="overlay" @click.self="createOpen=false" @keydown.esc.window="createOpen=false">
      <div class="dialog course-dialog" role="dialog" aria-modal="true" aria-labelledby="create-title">
        <div class="dialog-header"><div><span class="eyebrow">NEW COURSE</span><h3 id="create-title">新增基础课程</h3></div><button class="icon-close" type="button" @click="createOpen=false">×</button></div>
        <form class="dialog-content" @submit.prevent="createCourse">
          <div class="alert alert-warn">仅向现有课程接口创建基础课程，不会自动创建教学班或专业年级培养方案。保存后若缺少教学班，页面会提示待完善。</div>
          <div class="form-grid">
            <label>课程代码 *<input v-model.trim="courseForm.code" required placeholder="例如 SPPA101" /></label>
            <label>课程名称 *<input v-model.trim="courseForm.name" required placeholder="请输入课程名称" /></label>
            <label>所属学院 *<select v-model="courseForm.college" required><option value="">请选择学院</option><option v-for="c in colleges" :key="c.id" :value="String(c.id)">{{ c.name }}</option></select></label>
            <label>课程类型 *<select v-model="courseForm.course_type" required><option value="">请选择原系统课程类型</option><option v-for="type in availableCourseTypes" :key="type" :value="type">{{ type }}</option></select></label>
            <label>学分 *<input v-model.number="courseForm.credit" required type="number" min="0" step="0.5" /></label>
            <label>学时 *<input v-model.number="courseForm.hours" required type="number" min="0" step="1" /></label>
            <label class="form-span">课程简介<textarea v-model="courseForm.description" rows="3" placeholder="课程说明（选填）"></textarea></label>
          </div>
          <p v-if="createError" class="error-text" role="alert">{{ createError }}</p>
          <div class="dialog-footer"><button class="btn btn-light" type="button" @click="createOpen=false">取消</button><button class="btn btn-primary" type="submit" :disabled="creating || !semesterId">{{ creating ? '保存中…' : '保存至现有课程接口' }}</button></div>
        </form>
      </div>
    </div>

    <!-- 教学任务详情 -->
    <div v-if="detail" class="drawer-overlay" @click.self="detail = null" @keydown.esc.window="detail = null">
      <aside class="drawer" role="dialog" aria-modal="true" aria-label="课程开设详情">
        <div class="drawer-head"><div><span class="eyebrow">COURSE DETAILS</span><h3>{{ detail.name }}</h3><p>{{ detail.code }} · {{ detail.category }}</p></div><button class="icon-close" type="button" @click="detail = null">×</button></div>
        <div class="drawer-body">
          <div class="detail-grid">
            <div><small>学年学期</small><strong>2026—2027学年 第一学期</strong></div>
            <div><small>数据来源</small><strong>{{ detail.source === 'server' ? '教务数据库' : 'Excel临时预览（未入库）' }}</strong></div>
            <div><small>课程类型</small><strong>{{ detail.category }}</strong></div>
            <div><small>课程代码</small><strong>{{ detail.code }}</strong></div>
            <div><small>学分 / 学时</small><strong>{{ displayNumber(detail.credit) }} / {{ displayNumber(detail.hours) }}</strong></div>
            <div><small>任课教师</small><strong>{{ detail.teacher || '待分配' }}</strong></div>
            <div><small>所属专业</small><strong>{{ detail.major || '未建立关联' }}</strong></div>
            <div><small>适用年级</small><strong>{{ detail.grade ? detail.grade+'级' : '未建立关联' }}</strong></div>
            <div><small>教学班</small><strong>{{ detail.className || '未建立教学班' }}</strong></div>
            <div><small>教学周</small><strong>{{ detail.weeks || '未录入' }}</strong></div>
            <div><small>上课时间</small><strong>{{ detail.schedule || '未录入' }}</strong></div>
            <div><small>上课地点</small><strong>{{ detail.location || '未录入' }}</strong></div>
            <div><small>面向对象</small><strong>{{ detail.audience || '未录入' }}</strong></div>
            <div><small>已选人数 / 容量</small><strong>{{ displayNumber(detail.enrolled) }} / {{ displayNumber(detail.capacity) }}</strong></div>
            <div><small>开课状态</small><strong>{{ detail.status || '未录入' }}</strong></div>
          </div>
          <p v-if="detail.source==='preview'" class="preview-note">此条仅来自本次导入的预览文件，刷新或离开页面后将消失，不会影响任何数据库记录。</p>
        </div>
        <div class="drawer-footer"><button class="btn btn-light" type="button" @click="detail=null">关闭</button></div>
      </aside>
    </div>
  </main>
</template>
<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import api from '@/api/index'

/**
 * 课程管理单文件改造版。
 * 只使用已有 courses / teaching-classes / teachers / semesters / colleges 接口。
 * 不自创专业培养方案或数据库字段；文件导入仅供本页校验预览，不声称已保存。
 */
const CURRENT_SEMESTER = '2026-2027-1'
const PAGE_SIZE = 12
const MAJORS = [
  { name: '行政管理', years: 4 },
  { name: '政治学与行政学', years: 4 },
  { name: '国际政治', years: 4 },
  { name: '科学社会主义', years: 4 },
  { name: '行政管理+电子科学与技术双学位', years: 5 },
  { name: '国际政治＋英语双学位', years: 5 },
] as const

type Section = 'required' | 'elective'
type Origin = 'server' | 'preview'
type ApiObject = Record<string, unknown>
interface BasicItem { id: number; name: string }
interface Offering {
  uid: string
  id: number | null
  code: string
  name: string
  category: string
  major: string
  grade: number | null
  teacher: string
  credit: number | null
  hours: number | null
  className: string
  weeks: string
  schedule: string
  location: string
  audience: string
  enrolled: number | null
  capacity: number | null
  status: string
  source: Origin
}
interface Problem { key: string; row: Offering; reason: string }

const courses = ref<ApiObject[]>([])
const classes = ref<ApiObject[]>([])
const teachers = ref<ApiObject[]>([])
const semesters = ref<BasicItem[]>([])
const colleges = ref<BasicItem[]>([])
const classRequestSucceeded = ref(false)
const loaded = ref(false)
const loading = ref(false)
const errorMessage = ref('')
const warningMessage = ref('')
const previewRows = ref<Offering[]>([])
const detail = ref<Offering | null>(null)
const requiredMajor = ref('')
const requiredGrade = ref('')
const requiredCategory = ref('')
const requiredKeyword = ref('')
const electiveTeacher = ref('')
const electiveCategory = ref('')
const electiveKeyword = ref('')
const requiredPage = ref(1)
const electivePage = ref(1)
const requiredFileInput = ref<HTMLInputElement | null>(null)
const electiveFileInput = ref<HTMLInputElement | null>(null)

function str(value: unknown): string {
  return value === null || value === undefined ? '' : String(value).trim()
}
function num(value: unknown): number | null {
  if (value === null || value === undefined || value === '') return null
  const n = Number(value)
  return Number.isFinite(n) ? n : null
}
function obj(value: unknown): ApiObject {
  return typeof value === 'object' && value !== null && !Array.isArray(value) ? (value as ApiObject) : {}
}
function linkedId(value: unknown): number | null {
  return num(typeof value === 'object' && value !== null ? obj(value).id : value)
}
function displayNumber(value: number | null): string {
  return value === null ? '—' : String(value)
}
function errorText(err: unknown): string {
  const e = err as { response?: { status?: number; data?: { detail?: string; [key: string]: unknown } }; message?: string }
  const detail = e?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (e?.response?.status === 403) return '当前账号没有读取或修改该业务数据的权限。'
  if (e?.response?.status === 401) return '登录状态已失效，请重新登录。'
  if (e?.response?.status === 404) return '现有业务接口不存在，请核对已部署的后端。'
  const payload = e?.response?.data
  if (payload) return JSON.stringify(payload).slice(0,400)
  return e?.message || '请求失败，请检查接口与网络。'
}
function apiGet<T>(path: string, params?: ApiObject): Promise<T> {
  return api.get(path, params ? { params } : undefined) as unknown as Promise<T>
}
async function fetchAll(path: string): Promise<ApiObject[]> {
  const collected: ApiObject[] = []
  for (let page = 1; page <= 100; page++) {
    const payload = await apiGet<unknown>(path, { page, page_size: 100 })
    if (Array.isArray(payload)) return payload.map(obj)
    const response = obj(payload)
    const pageItems = Array.isArray(response.results) ? response.results.map(obj) : []
    collected.push(...pageItems)
    if (!pageItems.length) break
    const count = num(response.count)
    if (count !== null && collected.length >= count) break
    if (!response.next) break
  }
  return collected
}
function isCurrentSemester(name: string): boolean {
  const normalized = name.toLowerCase().replace(/[\s\u2014\u2013_]/g, '-').replace(/学年|学期|第|\s/g, '')
  return /2026[^0-9]*2027/.test(normalized) &&
    (/第一|一|秋|上/.test(name) || /(?:^|[^0-9])1(?:$|[^0-9])/.test(normalized) || /2027-1/.test(normalized))
}
const semesterId = computed<number | null>(() => {
  const found = semesters.value.find(s => isCurrentSemester(s.name))
  return found?.id ?? null
})
const academyCollegeIds = computed(() => {
  const values = colleges.value.filter(c => /政治学.*公共管理|公共管理.*政治学|政管学院/.test(c.name)).map(c => c.id)
  return new Set(values)
})
function isAcademyCourse(course: ApiObject): boolean {
  const id = linkedId(course.college)
  // 学院关系可识别时严格限定为政管学院；无法识别时不擅自推断。
  return id !== null && academyCollegeIds.value.has(id)
}
function academyTeacherInClass(cls: ApiObject): boolean {
  const teacherId = linkedId(cls.teacher)
  if (teacherId === null) return false
  const teacher = teachers.value.find(t => linkedId(t.id) === teacherId)
  return !!teacher && academyCollegeIds.value.has(linkedId(teacher.college) ?? -1)
}
function statusOfCourse(course: ApiObject): string {
  const active = course.is_active
  return active === false ? '停用' : str(course.status) || '已登记'
}
function classification(text: string): string {
  const t = text.trim().toLowerCase().replace(/[\s_-]/g, '')
  if (/公共必修|通识必修|publicrequired|generalrequired/.test(t)) return '公共必修'
  if (/专业必修|majorrequired|professionalrequired/.test(t)) return '专业必修'
  if (/必修|required|compulsory|mandatory/.test(t)) return '必修（未细分）'
  if (/专业限选|专业选修|majorelective|professionalelective|restrictedelective/.test(t)) return '专业限选'
  if (/公共选修|通识选修|公选|publicelective|generalelective/.test(t)) return '公共选修'
  if (/选修|elective/.test(t)) return '选修（未细分）'
  return '待分类'
}
function isRequired(category: string): boolean { return category.includes('必修') }
function isElective(category: string): boolean { return category.includes('选修') || category === '专业限选' }
function teacherFor(cls: ApiObject): string {
  const raw = str(cls.teacher_name || cls.teacher_display || cls.instructor_name)
  if (raw) return raw
  const teacherId = linkedId(cls.teacher)
  const teacher = teachers.value.find(t => linkedId(t.id) === teacherId)
  return str(teacher?.name || teacher?.full_name || (typeof cls.teacher === 'object' ? obj(cls.teacher).name : ''))
}
function courseForClass(cls: ApiObject): ApiObject | undefined {
  const courseId = linkedId(cls.course)
  return courses.value.find(c => linkedId(c.id) === courseId)
}
const realRows = computed<Offering[]>(() => {
  if (!semesterId.value) return []
  const id = semesterId.value
  const ownCourses = courses.value.filter(c => isAcademyCourse(c) || classes.value.some(cls => linkedId(cls.course) === linkedId(c.id) && academyTeacherInClass(cls)))
  const result: Offering[] = []
  for (const course of ownCourses) {
    const relatedClasses = classRequestSucceeded.value ? classes.value.filter(cls => {
      const belongs = linkedId(cls.course) === linkedId(course.id)
      const semester = linkedId(cls.semester)
      // 某教学班显式记载其他学期时不可算入本学期。
      return belongs && (semester === null || semester === id)
    }) : []
    const courseSemester = linkedId(course.semester)
    if (courseSemester !== id && !relatedClasses.some(cls => linkedId(cls.semester) === id)) continue
    const type = classification(str(course.course_type))
    const createRow = (cls?: ApiObject, index=0): Offering => ({
      uid: `db-${str(course.id)}-${cls ? str(cls.id) : 'course'}-${index}`,
      id: linkedId(course.id),
      code: str(course.code),
      name: str(course.name),
      category: type,
      // 当前 Course/TeachingClass 接口不提供稳定的培养方案目标关联；不猜测专业与入学年级。
      major: '', grade: null,
      teacher: cls ? teacherFor(cls) : '',
      credit: num(course.credit),
      hours: num(course.hours),
      className: cls ? str(cls.class_name || cls.name) : '',
      weeks: cls ? str(cls.weeks || cls.teaching_weeks) : '',
      schedule: cls ? str(cls.schedule || cls.class_time) : '',
      location: cls ? str(cls.location || cls.classroom) : '',
      audience: '',
      enrolled: cls ? num(cls.enrolled_count) : null,
      capacity: cls ? num(cls.capacity) : null,
      status: statusOfCourse(course),
      source: 'server',
    })
    if (!classRequestSucceeded.value || !relatedClasses.length) result.push(createRow())
    else relatedClasses.forEach((cls, i) => result.push(createRow(cls, i)))
  }
  return result
})
const allRows = computed(() => [...realRows.value, ...previewRows.value])
const serverOnlyRows = computed(() => realRows.value)
const summaryCards = computed(() => {
  const valid = loaded.value && semesterId.value !== null
  const uniqueCourses = new Set(serverOnlyRows.value.map(r => r.code || String(r.id)))
  const classesInPeriod = classRequestSucceeded.value ? classes.value.filter(c => {
    const sem = linkedId(c.semester)
    const course = courseForClass(c)
    if (!course || !(isAcademyCourse(course) || academyTeacherInClass(c))) return false
    if (sem !== null) return sem === semesterId.value
    return linkedId(course.semester) === semesterId.value
  }) : []
  const ready = classesInPeriod.filter(c => Boolean(teacherFor(c)) && Boolean(str(c.schedule || c.class_time)) && Boolean(str(c.location || c.classroom)))
  return [
    { label: '本学期课程', value: valid ? String(uniqueCourses.size) : '—', detail: '按课程代码去重（已登记）', icon: '▤', color: 'icon-blue' },
    { label: '本学期教学班', value: valid && classRequestSucceeded.value ? String(classesInPeriod.length) : '—', detail: '按已关联教学班记录统计', icon: '▦', color: 'icon-sky' },
    { label: '排课信息完整率', value: valid && classRequestSucceeded.value ? (classesInPeriod.length ? `${Math.round(ready.length/classesInPeriod.length*100)}%` : '—') : '—', detail: '教师、时间、地点均已录入', icon: '✓', color: 'icon-green' },
    { label: '待完善记录', value: valid && classRequestSucceeded.value ? String(issues.value.length) : '—', detail: '仅检查现有接口可判断的缺项', icon: '!', color: 'icon-orange' },
  ]
})
const issues = computed<Problem[]>(() => {
  if (!classRequestSucceeded.value || !semesterId.value) return []
  const records: Problem[] = []
  for (const row of realRows.value) {
    const reasons: string[] = []
    if (!row.className) reasons.push('未建立或未填写教学班')
    if (row.className && !row.teacher) reasons.push('尚未分配教师')
    if (row.className && !row.schedule) reasons.push('上课时间未录入')
    if (row.className && !row.location) reasons.push('上课地点未录入')
    if (row.enrolled !== null && row.capacity !== null && row.enrolled > row.capacity) reasons.push('实际选课人数超过计划容量')
    if (reasons.length) records.push({ key: row.uid, row, reason: reasons.join('；') })
  }
  return records
})
const unclassifiedCourses = computed(() => realRows.value.filter(r => r.category === '待分类'))
const requiredRows = computed(() => allRows.value.filter(r => isRequired(r.category)))
const electiveRows = computed(() => allRows.value.filter(r => isElective(r.category)))
const requiredGradeOptions = computed(() => {
  const major = MAJORS.find(m => m.name === requiredMajor.value)
  return major && major.years === 4 ? [2026,2025,2024,2023] : [2026,2025,2024,2023,2022]
})
function onRequiredMajorChanged(): void {
  if (requiredGrade.value && !requiredGradeOptions.value.includes(Number(requiredGrade.value))) requiredGrade.value = ''
  resetRequiredPage()
}
function resetRequiredPage(): void { requiredPage.value = 1 }
function resetElectivePage(): void { electivePage.value = 1 }
function matchesSearch(row: Offering, keyword: string): boolean {
  const k = keyword.trim().toLowerCase()
  return !k || [row.code,row.name,row.teacher,row.className].join(' ').toLowerCase().includes(k)
}
const filteredRequired = computed(() => requiredRows.value.filter(r =>
  (!requiredCategory.value || r.category === requiredCategory.value) &&
  (!requiredMajor.value || r.major === requiredMajor.value) &&
  (!requiredGrade.value || r.grade === Number(requiredGrade.value)) &&
  matchesSearch(r, requiredKeyword.value)
))
const filteredElective = computed(() => electiveRows.value.filter(r =>
  (!electiveCategory.value || r.category === electiveCategory.value) &&
  (!electiveTeacher.value || r.teacher === electiveTeacher.value) &&
  matchesSearch(r,electiveKeyword.value)
))
const requiredTotalPages = computed(() => Math.max(1, Math.ceil(filteredRequired.value.length/PAGE_SIZE)))
const electiveTotalPages = computed(() => Math.max(1, Math.ceil(filteredElective.value.length/PAGE_SIZE)))
const requiredVisible = computed(() => filteredRequired.value.slice((requiredPage.value-1)*PAGE_SIZE,requiredPage.value*PAGE_SIZE))
const electiveVisible = computed(() => filteredElective.value.slice((electivePage.value-1)*PAGE_SIZE,electivePage.value*PAGE_SIZE))
const teacherNames = computed(() => [...new Set([...teachers.value.map(t=>str(t.name||t.full_name)), ...electiveRows.value.map(r=>r.teacher)].filter(Boolean))].sort((a,b)=>a.localeCompare(b,'zh-CN')))


// 恢复原页面的课程分类树、教学计划进度、容量分析、课程封面和时间轴。
// 所有与具体课程有关的内容从本学期教务接口构建，不再复用旧版写死的统计数值。
const legacyCategoryExpanded = reactive<Record<string, boolean>>({})
const LEGACY_CATEGORY_COLORS = [
  '#1E3A8A', '#2563EB', '#3B82F6', '#5589DF', '#679FEA', '#85B5F3', '#8899AF',
]
const LEGACY_CATEGORY_NAMES = [
  '公共必修', '专业必修', '必修（未细分）', '专业限选',
  '公共选修', '选修（未细分）', '待分类',
]
const legacyCategoryTree = computed(() => LEGACY_CATEGORY_NAMES.map((name, i) => ({
  name,
  color: LEGACY_CATEGORY_COLORS[i] || '#2563EB',
  children: [...new Map(realRows.value.filter(row => row.category === name)
    .map(row => [row.code || row.name, row.name])).values()],
})).filter(group => group.children.length > 0))
const legacyCategoryTotal = computed(() => new Set(realRows.value.map(r => r.code || r.name)).size)
function legacyToggleCategory(name: string): void {
  legacyCategoryExpanded[name] = legacyCategoryExpanded[name] === false
}
function legacyCategoryIsOpen(name: string): boolean {
  return legacyCategoryExpanded[name] !== false
}

// 此处的“进度”仅指本学期教学任务信息是否完整，绝不冒充教学实际完成进度。
const legacyTeachingPlans = computed(() => realRows.value.filter(row => !!row.className).slice(0, 6).map(row => {
  const fields = [
    { label: '任课教师', done: !!row.teacher },
    { label: '上课时间', done: !!row.schedule },
    { label: '教学地点', done: !!row.location },
  ]
  const completed = fields.filter(f => f.done).length
  return {
    uid: row.uid, name: row.className || row.name,
    meta: `${row.name} · 已完善 ${completed}/3 项`,
    progress: Math.round((completed / 3) * 100),
    milestones: fields, row,
  }
}))

const legacyCapacityCourses = computed(() => realRows.value.filter(row =>
  row.capacity !== null && row.capacity > 0 && row.enrolled !== null
).map(row => ({
  uid: row.uid, name: row.className ? `${row.name} · ${row.className}` : row.name,
  enrolled: row.enrolled as number, capacity: row.capacity as number,
  ratio: (row.enrolled as number) / (row.capacity as number), row,
})).sort((a,b) => b.ratio-a.ratio).slice(0, 7))
const legacyHighLoadCount = computed(() => realRows.value.filter(row => row.capacity !== null && row.capacity > 0 && row.enrolled !== null && row.enrolled / row.capacity >= 0.9).length)
function legacyLoadClass(ratio: number): string {
  return ratio >= 0.95 ? 'load-danger' : ratio >= 0.8 ? 'load-warning' : 'load-safe'
}
function legacyLoadColor(ratio: number): string {
  return ratio >= 0.95 ? '#1E3A8A' : ratio >= 0.8 ? '#3B82F6' : '#93C5FD'
}
const legacyCoverScrollRef = ref<HTMLElement | null>(null)
const COVER_PALETTE = [
  'linear-gradient(135deg,#0F172A,#1E3A8A)',
  'linear-gradient(135deg,#1E3A8A,#2563EB)',
  'linear-gradient(135deg,#1E40AF,#60A5FA)',
  'linear-gradient(135deg,#243B72,#5D8CD8)',
  'linear-gradient(135deg,#2563EB,#93C5FD)',
]
const legacyFeaturedCourses = computed(() => [...new Map(realRows.value
  .filter(row => !!row.name).map(row => [row.code || row.name, row])).values()]
  .slice(0, 12).map((row, i) => ({
    uid: row.uid, row, name: row.name, code: row.code, teacher: row.teacher || '任课教师待分配',
    credit: row.credit, category: row.category, status: row.status,
    enrolled: row.enrolled, capacity: row.capacity,
    coverGradient: COVER_PALETTE[i % COVER_PALETTE.length],
  })))
function legacyScrollCover(direction: 'left' | 'right'): void {
  legacyCoverScrollRef.value?.scrollBy({ left: direction === 'left' ? -300 : 300, behavior: 'smooth' })
}

// 保留课程时间轴展示结构，改为根据现有教学任务形成业务节点；不伪造校历日期。
const legacyTimeline = computed(() => {
  const count = new Set(realRows.value.map(r => r.code || r.name)).size
  const classRows = realRows.value.filter(r => !!r.className)
  const assigned = classRows.filter(r => !!r.teacher).length
  const scheduled = classRows.filter(r => !!r.schedule && !!r.location).length
  return [
    { date: '课程建档', title: '本学期课程基础数据', desc: `已从教务接口识别 ${count} 门本学期课程。`, done: count > 0, active: false },
    { date: '教学班', title: '教学任务关联', desc: `已关联 ${classRows.length} 条教学班记录。`, done: classRows.length > 0, active: false },
    { date: '师资安排', title: '任课教师落实', desc: `已分配教师 ${assigned}/${classRows.length} 条教学班记录。`, done: classRows.length > 0 && assigned === classRows.length, active: false },
    { date: '排课安排', title: '时间与地点录入', desc: `已录入时间和地点 ${scheduled}/${classRows.length} 条教学班记录。`, done: classRows.length > 0 && scheduled === classRows.length, active: true },
    { date: '待接入', title: '课程考核与学期归档', desc: '具体考核、成绩归档日期需以学校正式教学日历和相关业务接口为准。', done: false, active: false },
  ]
})

async function loadData(): Promise<void> {
  if (loading.value) return
  loading.value = true
  loaded.value = false
  errorMessage.value = ''
  warningMessage.value = ''
  try {
    const [semesterData, collegeData] = await Promise.all([
      fetchAll('/dashboard/semesters/'),
      fetchAll('/dashboard/colleges/'),
    ])
    semesters.value = semesterData.map(x => ({ id: num(x.id) ?? 0, name: str(x.name || x.academic_year || x.term) }))
    colleges.value = collegeData.map(x => ({ id: num(x.id) ?? 0, name: str(x.name) }))
    const [courseResult,classResult,teacherResult] = await Promise.allSettled([
      fetchAll('/courses/'),fetchAll('/teaching-classes/'),fetchAll('/teachers/'),
    ])
    if (courseResult.status === 'rejected') throw courseResult.reason
    courses.value = courseResult.value
    classes.value = classResult.status === 'fulfilled' ? classResult.value : []
    teachers.value = teacherResult.status === 'fulfilled' ? teacherResult.value : []
    classRequestSucceeded.value = classResult.status === 'fulfilled'
    if (classResult.status === 'rejected') warningMessage.value = `教学班接口未能读取，排课统计暂不显示：${errorText(classResult.reason)}`
    if (teacherResult.status === 'rejected') warningMessage.value += ' 教师字典未能读取，部分任课教师名称可能缺失。'
    loaded.value = true
  } catch(err) {
    courses.value = []; classes.value = []; teachers.value = []
    classRequestSucceeded.value = false
    errorMessage.value = errorText(err)
  } finally {
    loading.value = false
    resetRequiredPage()
    resetElectivePage()
  }
}
onMounted(() => { void loadData() })

// ========== 基础课程新增（仅调用原有接口） ==========
const createOpen = ref(false)
const creating = ref(false)
const createError = ref('')
const courseForm = reactive({ code: '', name: '', college: '', course_type: '', credit: 3, hours: 48, description: '' })
const availableCourseTypes = computed(() => {
  const existing = [...new Set(courses.value.map(c => str(c.course_type)).filter(Boolean))]
  return existing.length ? existing : ['required', 'elective']
})
function openCreateCourse() {
  createError.value = ''
  Object.assign(courseForm, {code:'',name:'',college:'',course_type:'',credit:3,hours:48,description:''})
  const own = colleges.value.find(c => academyCollegeIds.value.has(c.id))
  if (own) courseForm.college = String(own.id)
  createOpen.value = true
}
async function createCourse() {
  if (creating.value) return
  createError.value = ''
  if (!semesterId.value) { createError.value = '当前学期不存在，无法保存课程。'; return }
  if (!courseForm.code || !courseForm.name || !courseForm.college || !courseForm.course_type) { createError.value = '请填写完整必填字段。'; return }
  creating.value = true
  try {
    await api.post('/courses/', {
      code: courseForm.code, name: courseForm.name,
      college: Number(courseForm.college), semester: semesterId.value,
      credit: courseForm.credit, hours: courseForm.hours,
      course_type: courseForm.course_type, description: courseForm.description,
    })
    createOpen.value = false
    await loadData()
  } catch (err) { createError.value = errorText(err) }
  finally { creating.value = false }
}

// ========== 纯浏览器 Excel（真实 XLSX，零额外依赖）工具 ==========
const REQUIRED_HEADERS = [
  '学年学期','专业','年级','课程代码','课程名称','课程性质','学分','学时','教学班','任课教师','上课周次','上课时间','上课地点','开课状态',
]
const ELECTIVE_HEADERS = [
  '学年学期','课程代码','课程名称','选修类别','任课教师','所属单位','学分','学时','教学班','面向对象','计划容量','已选人数','上课周次','上课时间','上课地点','开课状态',
]
const utf8 = new TextEncoder()
function escapeXml(value: string): string {
  return value.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&apos;')
}
function colLetter(index: number): string {
  let n = index + 1, text = ''
  while (n) { n--; text = String.fromCharCode(65 + n % 26) + text; n = Math.floor(n/26) }
  return text
}
function crc32(bytes: Uint8Array): number {
  let crc = 0xFFFFFFFF
  for (const b of bytes) {
    crc ^= b
    for (let i = 0; i < 8; i++) crc = (crc >>> 1) ^ (crc & 1 ? 0xEDB88320 : 0)
  }
  return (crc ^ 0xFFFFFFFF) >>> 0
}
function zipStored(files: Array<{name: string; data: Uint8Array}>): Uint8Array {
  const locals: Uint8Array[] = [], centrals: Uint8Array[] = []
  let offset = 0
  for (const file of files) {
    const name = utf8.encode(file.name)
    const len = file.data.byteLength, crc = crc32(file.data)
    const local = new Uint8Array(30 + name.length)
    const lv = new DataView(local.buffer)
    lv.setUint32(0,0x04034b50,true); lv.setUint16(4,20,true); lv.setUint16(6,0x0800,true)
    lv.setUint16(8,0,true); lv.setUint32(14,crc,true); lv.setUint32(18,len,true)
    lv.setUint32(22,len,true); lv.setUint16(26,name.length,true)
    local.set(name,30)
    locals.push(local,file.data)
    const central = new Uint8Array(46 + name.length)
    const cv = new DataView(central.buffer)
    cv.setUint32(0,0x02014b50,true); cv.setUint16(4,20,true); cv.setUint16(6,20,true)
    cv.setUint16(8,0x0800,true); cv.setUint32(16,crc,true)
    cv.setUint32(20,len,true); cv.setUint32(24,len,true); cv.setUint16(28,name.length,true)
    cv.setUint32(42,offset,true); central.set(name,46)
    centrals.push(central)
    offset += local.length + len
  }
  const centerLength = centrals.reduce((n,a)=>n+a.length,0)
  const end = new Uint8Array(22), ev = new DataView(end.buffer)
  ev.setUint32(0,0x06054b50,true)
  ev.setUint16(8,files.length,true); ev.setUint16(10,files.length,true)
  ev.setUint32(12,centerLength,true); ev.setUint32(16,offset,true)
  const total = offset + centerLength + end.length
  const result = new Uint8Array(total); let cursor = 0
  for (const block of [...locals,...centrals,end]) { result.set(block,cursor); cursor+=block.length }
  return result
}
function makeXlsx(rows: string[][]): Uint8Array {
  const sheetData = rows.map((row,ri) => {
    const cells = row.map((val,ci) => `<c r="${colLetter(ci)}${ri+1}" t="inlineStr"><is><t xml:space="preserve">${escapeXml(val)}</t></is></c>`).join('')
    return `<row r="${ri+1}">${cells}</row>`
  }).join('')
  const files = [
    {name:'[Content_Types].xml',text:'<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>'},
    {name:'_rels/.rels',text:'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'},
    {name:'xl/workbook.xml',text:'<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="课程安排" sheetId="1" r:id="rId1"/></sheets></workbook>'},
    {name:'xl/_rels/workbook.xml.rels',text:'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'},
    {name:'xl/worksheets/sheet1.xml',text:`<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>${sheetData}</sheetData></worksheet>`},
  ]
  return zipStored(files.map(f=>({name:f.name,data:utf8.encode(f.text)})))
}
function download(bytes: Uint8Array, name: string): void {
  const blob = new Blob([bytes.buffer as ArrayBuffer], {type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'})
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url; anchor.download = name; document.body.appendChild(anchor); anchor.click(); anchor.remove()
  window.setTimeout(()=>URL.revokeObjectURL(url),1000)
}
function downloadTemplate(section: Section): void {
  const headers = section==='required' ? REQUIRED_HEADERS : ELECTIVE_HEADERS
  download(makeXlsx([headers]), `${section==='required'?'专业必修':'教师选修'}_本学期导入模板.xlsx`)
}
function excelNumber(value: number | null): string { return value === null ? '' : String(value) }
function rowsForExport(section: Section): string[][] {
  const records = section === 'required' ? filteredRequired.value : filteredElective.value
  const headers = section === 'required' ? REQUIRED_HEADERS : ELECTIVE_HEADERS
  const data = records.map(row => section === 'required' ? [
    CURRENT_SEMESTER,row.major,row.grade===null?'':String(row.grade),row.code,row.name,row.category,
    excelNumber(row.credit),excelNumber(row.hours),row.className,row.teacher,row.weeks,row.schedule,row.location,row.status,
  ] : [
    CURRENT_SEMESTER,row.code,row.name,row.category,row.teacher,'',excelNumber(row.credit),excelNumber(row.hours),
    row.className,row.audience,excelNumber(row.capacity),excelNumber(row.enrolled),row.weeks,row.schedule,row.location,row.status,
  ])
  return [[...headers,'数据来源'],...data.map((cells,i)=>[...cells,records[i]?.source==='preview'?'临时预览-未入库':'教务接口'])]
}
function exportExcel(section: Section): void {
  download(makeXlsx(rowsForExport(section)), `${section==='required'?'专业必修课程':'教师选修课程'}_${CURRENT_SEMESTER}_筛选结果.xlsx`)
}

function csvParse(text: string): string[][] {
  const lines: string[][] = []; let row: string[] = [], cell = '', quoted = false
  const source = text.replace(/^\uFEFF/,'')
  for (let i=0;i<source.length;i++) {
    const ch=source[i]
    if (quoted) {
      if (ch==='"' && source[i+1]==='"') {cell+='"';i++}
      else if (ch==='"') quoted=false
      else cell+=ch
    } else if (ch==='"') quoted=true
    else if (ch===',') {row.push(cell);cell=''}
    else if (ch==='\n' || ch==='\r') {
      if (ch==='\r' && source[i+1]==='\n') i++
      row.push(cell); if (row.some(v=>v.trim())) lines.push(row)
      row=[];cell=''
    } else cell+=ch
  }
  if (quoted) throw new Error('CSV 引号未正确闭合')
  row.push(cell); if (row.some(v=>v.trim())) lines.push(row)
  return lines
}
function xmlDocument(xml: string): Document {
  const doc = new DOMParser().parseFromString(xml,'application/xml')
  if (doc.getElementsByTagName('parsererror').length) throw new Error('Excel XML 内容解析失败')
  return doc
}
function localElements(parent: Element | Document, tag: string): Element[] {
  return Array.from(parent.getElementsByTagName('*')).filter(el=>el.localName===tag)
}
async function readZipEntries(buffer: ArrayBuffer): Promise<Map<string,Uint8Array>> {
  const bytes = new Uint8Array(buffer), view = new DataView(buffer)
  let eocd = -1
  for (let i=bytes.length-22;i>=Math.max(0,bytes.length-65557);i--) {
    if (view.getUint32(i,true)===0x06054b50) {eocd=i;break}
  }
  if (eocd<0) throw new Error('不是有效的 XLSX/ZIP 文件')
  const size = view.getUint32(eocd+12,true)
  const offset = view.getUint32(eocd+16,true)
  if (offset+size>bytes.length || size>2_000_000) throw new Error('Excel目录长度异常')
  const total = view.getUint16(eocd+10,true)
  if (total>128) throw new Error('工作簿包含过多文件，不支持导入')
  const entries=new Map<string,Uint8Array>()
  let p=offset, totalUncompressed=0
  for(let i=0;i<total;i++) {
    if(view.getUint32(p,true)!==0x02014b50) throw new Error('Excel ZIP 目录损坏')
    const method=view.getUint16(p+10,true), compressedLength=view.getUint32(p+20,true)
    const uncompressedLength=view.getUint32(p+24,true)
    const nameLen=view.getUint16(p+28,true),extraLen=view.getUint16(p+30,true),commentLen=view.getUint16(p+32,true)
    const localOffset=view.getUint32(p+42,true)
    const name=new TextDecoder().decode(bytes.subarray(p+46,p+46+nameLen))
    p+=46+nameLen+extraLen+commentLen
    if (!/^xl\/(worksheets\/|_rels\/|workbook\.xml|sharedStrings\.xml)/.test(name)) continue
    if(uncompressedLength>12_000_000 || compressedLength>8_000_000) throw new Error('Excel表格过大')
    totalUncompressed+=uncompressedLength
    if(totalUncompressed>20_000_000) throw new Error('Excel解压后内容过大')
    if(view.getUint32(localOffset,true)!==0x04034b50) throw new Error('Excel ZIP 数据项损坏')
    const localNameLen=view.getUint16(localOffset+26,true),localExtraLen=view.getUint16(localOffset+28,true)
    const pos=localOffset+30+localNameLen+localExtraLen
    if(pos+compressedLength>bytes.length) throw new Error('Excel ZIP 数据越界')
    const raw=bytes.slice(pos,pos+compressedLength)
    let output: Uint8Array
    if (method===0) output=raw
    else if (method===8) {
      if (typeof DecompressionStream==='undefined') throw new Error('当前浏览器无法解压 XLSX，请将 Excel 另存为 CSV 后导入')
      const unzipped = await new Response(new Blob([raw.buffer as ArrayBuffer]).stream().pipeThrough(new DecompressionStream('deflate-raw'))).arrayBuffer()
      if (unzipped.byteLength>12_000_000) throw new Error('Excel解压内容超过上限')
      output=new Uint8Array(unzipped)
    } else throw new Error('不支持的 Excel ZIP 压缩格式')
    if(output.length!==uncompressedLength) throw new Error('Excel数据长度不一致')
    entries.set(name,output)
  }
  return entries
}
async function xlsxParse(file: File): Promise<string[][]> {
  const entries=await readZipEntries(await file.arrayBuffer())
  const decoder=new TextDecoder()
  const wbData=entries.get('xl/workbook.xml')
  if(!wbData) throw new Error('Excel缺少工作簿描述文件')
  const wb=xmlDocument(decoder.decode(wbData))
  const sheets=localElements(wb,'sheet')
  if(!sheets.length) throw new Error('Excel文件中没有工作表')
  const firstSheet=sheets[0]!
  const relId=firstSheet.getAttribute('r:id') || firstSheet.getAttributeNS('http://schemas.openxmlformats.org/officeDocument/2006/relationships','id')
  let sheetPath='xl/worksheets/sheet1.xml'
  const rels=entries.get('xl/_rels/workbook.xml.rels')
  if(rels && relId) {
    const links=localElements(xmlDocument(decoder.decode(rels)),'Relationship')
    const target=links.find(el=>el.getAttribute('Id')===relId)?.getAttribute('Target')
    if(target) sheetPath=target.startsWith('/')?target.slice(1):target.startsWith('xl/')?target:`xl/${target.replace(/^\.\//,'')}`
  }
  const sheetData=entries.get(sheetPath)
  if(!sheetData) throw new Error('无法读取首个 Excel 工作表')
  const strings: string[]=[]
  const shared=entries.get('xl/sharedStrings.xml')
  if(shared) {
    for(const el of localElements(xmlDocument(decoder.decode(shared)),'si'))
      strings.push(localElements(el,'t').map(t=>t.textContent||'').join(''))
  }
  const sheet=xmlDocument(decoder.decode(sheetData))
  const rowEls=localElements(sheet,'row')
  if(rowEls.length>3001) throw new Error('单次最多导入3000行课程数据')
  const table: string[][]=[]
  for(const rowEl of rowEls) {
    const cells: string[]=[]
    const cellEls=Array.from(rowEl.children).filter(el=>el.localName==='c')
    for(const c of cellEls) {
      const ref=c.getAttribute('r')||''
      const letters=(ref.match(/^[A-Z]+/i)||[])[0]||''
      let index=0
      for(const ch of letters.toUpperCase()) index=index*26+ch.charCodeAt(0)-64
      const column=letters?index-1:cells.length
      if(column<0||column>100) throw new Error('Excel列数超过支持范围')
      const typ=c.getAttribute('t')||''
      const v=localElements(c,typ==='inlineStr'?'t':'v').map(x=>x.textContent||'').join('')
      cells[column]=typ==='s'?(strings[Number(v)]||''):v
    }
    if(cells.some(s=>str(s))) table.push(cells.map(v=>v||''))
  }
  return table
}

const importOpen=ref(false)
const importSection=ref<Section>('required')
const importFileName=ref('')
const importErrors=ref<string[]>([])
const importedPending=ref<Offering[]>([])
function closeImport(): void { importOpen.value=false; importedPending.value=[]; importErrors.value=[] }
function validateHeaders(row: string[], expected: string[]): Map<string,number> {
  const names=row.map(v=>str(v).replace(/\s/g,''))
  const indices=new Map<string,number>()
  for(const key of expected) {
    const i=names.indexOf(key)
    if(i<0) throw new Error(`Excel缺少表头“${key}”，请先下载本页模板填写`)
    indices.set(key,i)
  }
  return indices
}
function formatSemester(value: string): boolean {
  return value.trim()===CURRENT_SEMESTER || isCurrentSemester(value)
}
async function onFileSelected(event: Event, section: Section): Promise<void> {
  const input=event.target as HTMLInputElement
  const file=input.files?.[0]
  input.value=''
  if(!file) return
  importOpen.value=true;importSection.value=section;importFileName.value=file.name
  importedPending.value=[];importErrors.value=[]
  if(file.size>8*1024*1024) {importErrors.value=['文件超过8MB，请分批导入'];return}
  try {
    const data=file.name.toLowerCase().endsWith('.csv') ? csvParse(await file.text()) :
      file.name.toLowerCase().endsWith('.xlsx') ? await xlsxParse(file) :
      (()=>{throw new Error('只支持 .xlsx 或 .csv 文件')})()
    if(!data.length) throw new Error('文件不包含任何数据')
    const expected=section==='required'?REQUIRED_HEADERS:ELECTIVE_HEADERS
    const index=validateHeaders(data[0]||[],expected)
    const seen=new Set<string>()
    for(let i=1;i<data.length;i++) {
      const values=data[i]||[]
      const field=(name: string)=>str(values[index.get(name)??-1])
      const errs: string[]=[]
      const semester=field('学年学期'),code=field('课程代码'),name=field('课程名称')
      const category=field(section==='required'?'课程性质':'选修类别')
      if(!formatSemester(semester)) errs.push('学期不是2026—2027学年第一学期')
      if(!code||!name) errs.push('课程代码和名称不能为空')
      if(section==='required' && !['公共必修','专业必修'].includes(category)) errs.push('课程性质只能为公共必修或专业必修')
      if(section==='elective' && !['专业限选','公共选修'].includes(category)) errs.push('选修类别只能为专业限选或公共选修')
      const major=section==='required'?field('专业'):''
      const grade=section==='required'?num(field('年级').replace('级','')):null
      if(section==='required') {
        const found=MAJORS.find(m=>m.name===major)
        if(!found) errs.push('专业不属于已确定的六个专业')
        if(grade===null||!Number.isInteger(grade)||grade<2022||grade>2026||(found?.years===4&&grade===2022)) errs.push('专业与年级组合不符合培养学制')
      }
      const teacher=field('任课教师')
      if(section==='elective' && !teacher) errs.push('必须填写任课教师')
      const creditValue=field('学分'),hoursValue=field('学时')
      const credit=num(creditValue),hours=num(hoursValue)
      if(credit===null||credit<0||hours===null||hours<0||!Number.isInteger(hours)) errs.push('学分或学时无效')
      const className=field('教学班')
      const key=section==='required'?`${code}|${major}|${grade}|${className}`:`${code}|${teacher}|${className}`
      if(seen.has(key)) errs.push('Excel内部存在重复课程与教学班组合')
      seen.add(key)
      const capacity=section==='elective'?num(field('计划容量')):null
      const enrolled=section==='elective'?num(field('已选人数')):null
      if((capacity!==null&&(!Number.isInteger(capacity)||capacity<0)) || (enrolled!==null&&(!Number.isInteger(enrolled)||enrolled<0))) errs.push('容量及已选人数必须是非负整数')
      if(errs.length) {importErrors.value.push(`第${i+1}行：${errs.join('；')}`);continue}
      importedPending.value.push({
        uid:`preview-${section}-${i}-${Date.now()}`,id:null,code,name,category,major,
        grade:section==='required'?grade:null,teacher,credit,hours,className,
        weeks:field('上课周次'),schedule:field('上课时间'),location:field('上课地点'),
        audience:section==='required'?'':field('面向对象'),capacity,enrolled,
        status:field('开课状态')||'待确认',source:'preview',
      })
    }
    if(data.length===1) importErrors.value.push('Excel只有表头，没有任何课程记录')
  } catch(err) {importErrors.value.push(errorText(err))}
}
function clearPreview(): void {
  previewRows.value = []
  resetRequiredPage(); resetElectivePage()
}
function applyImportedPreview(): void {
  const section=importSection.value
  // 按本次导入范围替换预览，避免重复点击导致统计重复；后端真实数据不受影响。
  previewRows.value=[...previewRows.value.filter(r=>section==='required'?!isRequired(r.category):!isElective(r.category)),...importedPending.value]
  closeImport()
  resetRequiredPage(); resetElectivePage()
}
</script>
<style scoped>
.course-hub { --ink:#172944; --blue:#254b9c; --muted:#8796ad; display:flex; flex-direction:column; gap:20px; padding:26px 26px 48px; max-width:1780px; margin:auto; color:var(--ink); font-family:inherit; box-sizing:border-box; }
.course-hub *, .course-hub *::before, .course-hub *::after { box-sizing:border-box; }
.page-header { display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:18px; padding:2px 0 0; }
.header-title h1 { display:flex; align-items:center; gap:12px; margin:0; font-size:25px; letter-spacing:.2px; font-weight:750; }
.head-glyph { color:#315db3; font-size:27px; }
.header-title p { margin:9px 0 0; color:#8e9bb0; font-size:12px; line-height:1.6; }
.header-actions { display:flex; align-items:center; flex-wrap:wrap; gap:9px; }
.semester-pill { display:inline-flex; align-items:center; min-height:37px; padding:8px 14px; border:1px solid #dce8f7; border-radius:9px; background:#edf4ff; color:#244b96; font-size:12px; font-weight:650; }
.btn { min-height:37px; padding:8px 14px; border:1px solid transparent; border-radius:9px; font-size:12px; font-weight:650; white-space:nowrap; cursor:pointer; transition:background .2s,border-color .2s,transform .2s; }
.btn:disabled { opacity:.5; cursor:not-allowed; }
.btn-primary { background:#24468e; color:#fff; }
.btn-primary:hover:not(:disabled) { background:#3160ba; }
.btn-light { background:#fff; color:#315a93; border-color:#dfe7f2; }
.btn-light:hover:not(:disabled) { background:#f1f6ff; border-color:#9fbbe1; }
.btn-text { background:transparent; color:#a64735; padding:4px 8px; }
.data-note { display:flex; align-items:flex-start; gap:9px; padding:12px 14px; border-radius:9px; background:#f0f5fd; color:#637996; font-size:11px; line-height:1.8; }
.note-bullet { flex:none; width:7px; height:7px; margin-top:7px; background:#4388e9; border-radius:50%; }
.alert { padding:12px 16px; border:1px solid; border-radius:9px; font-size:12px; line-height:1.9; }
.alert-warn { color:#8a601f; background:#fff9ed; border-color:#f2dfbd; }
.alert-error { color:#a14134; background:#fff7f6; border-color:#f4d5d0; }
.overview { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; }
.overview-card { display:flex; align-items:center; gap:15px; min-height:117px; padding:20px; border-radius:14px; border:1px solid #e5ebf3; background:#fff; box-shadow:0 9px 25px #15326408; }
.overview-icon { flex:none; display:grid; place-items:center; width:48px; height:48px; border-radius:13px; font-size:22px; font-weight:750; }
.icon-blue { background:#eaf2ff; color:#244b9b; }
.icon-sky { background:#e7f5ff; color:#3682c8; }
.icon-green { background:#e8f7f2; color:#18836b; }
.icon-orange { background:#fff2e4; color:#b37629; }
.overview-content { display:flex; flex-direction:column; gap:4px; min-width:0; }
.overview-content>span { color:#91a0b7; font-size:12px; }
.overview-content strong { font-size:28px; color:#1a2b43; line-height:1.25; }
.overview-content small { color:#9ba8b9; font-size:10px; line-height:1.7; }
.panel { min-width:0; padding:23px 24px; border:1px solid #e5ebf3; border-radius:15px; background:#fff; box-shadow:0 7px 24px #193d6906; }
.panel-heading { display:flex; justify-content:space-between; align-items:start; gap:13px; }
.panel-heading h2 { display:flex; align-items:center; gap:9px; margin:0; font-size:18px; color:#1b3150; }
.blue-rail { width:4px; height:19px; border-radius:4px; background:#3176d9; }
.panel-heading p { margin:8px 0 0 13px; color:#8e9eb2; font-size:11px; line-height:1.8; }
.count-chip { flex:none; padding:7px 11px; background:#ecf4ff; border-radius:8px; color:#315ca4; font-size:11px; white-space:nowrap; }
.filters { display:flex; align-items:end; flex-wrap:wrap; gap:11px; margin:20px 0 14px; padding:14px 15px; border:1px solid #eef2f8; border-radius:11px; background:#f8faff; }
.filters label { display:flex; flex-direction:column; gap:7px; min-width:145px; max-width:100%; color:#72829a; font-size:11px; }
.filters .filter-search { flex:1 1 250px; }
.filters select,.filters input,.form-grid input,.form-grid select,.form-grid textarea { min-height:38px; width:100%; border:1px solid #dfe7f1; background:#fff; border-radius:8px; padding:7px 10px; color:#384e6a; font-size:12px; font-family:inherit; outline:none; }
.filters select:focus,.filters input:focus,.form-grid :is(select,input,textarea):focus { border-color:#6497eb; box-shadow:0 0 0 3px #3e7bdb18; }
.panel-actions { display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; margin-bottom:14px; }
.helper-note { color:#98a5b5; font-size:10px; line-height:1.7; }
.button-group { display:flex; flex-wrap:wrap; gap:8px; }
.visually-hidden { position:absolute!important; width:1px!important; height:1px!important; overflow:hidden!important; clip:rect(0,0,0,0)!important; white-space:nowrap!important; }
.table-wrap { border:1px solid #ecf0f6; border-radius:11px; overflow-x:auto; }
.course-table { width:100%; border-collapse:collapse; min-width:1020px; }
.course-table thead { background:#f5f8fc; }
.course-table th { padding:15px 13px; text-align:left; white-space:nowrap; color:#8999ad; font-size:11px; font-weight:650; }
.course-table td { padding:15px 13px; border-top:1px solid #eef2f6; font-size:12px; color:#405773; line-height:1.6; vertical-align:middle; }
.course-table tbody tr:hover { background:#fbfdff; }
.course-table td strong { display:block; font-size:12px; color:#263e5c; }
.course-table td small { display:block; margin-top:4px; color:#98a6b9; font-size:10px; }
.course-table .muted,.muted { color:#9aa7b8; font-size:11px; }
.category-tag,.target-tag,.source-tag { display:inline-block; padding:5px 8px; border-radius:6px; font-size:11px; white-space:nowrap; }
.category-tag { color:#2b63b2; background:#eaf3ff; }
.target-tag { background:#f0f5ff; color:#335b98; white-space:normal; }
.source-server { background:#edf8f2; color:#228366; }
.source-preview { background:#fff4e3; color:#ac711d; }
.text-link { border:none; background:transparent; padding:5px 0; font-size:11px; color:#2a66bd; font-weight:650; cursor:pointer; }
.text-link:hover { text-decoration:underline; }
.empty-cell { text-align:center; padding:34px 10px!important; color:#95a3b5!important; }
.pagination { display:flex; align-items:center; justify-content:space-between; gap:10px; padding-top:16px; font-size:11px; color:#8b9aaf; }
.pagination div { display:flex; align-items:center; gap:10px; }
.pagination button { border:1px solid #e1e8f2; border-radius:7px; background:#fff; padding:7px 12px; color:#305f9c; cursor:pointer; font-size:11px; }
.pagination button:disabled { opacity:.45; cursor:not-allowed; }
.compact-panel { padding-bottom:26px; }
.issues-list { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; margin-top:18px; }
.issue-row { display:flex; gap:12px; align-items:center; width:100%; padding:13px 14px; border:1px solid #f1e2d2; border-radius:9px; background:#fffcf8; text-align:left; cursor:pointer; }
.issue-dot { flex:none; width:8px; height:8px; border-radius:50%; background:#d69c4a; }
.issue-row>div { flex:1; min-width:0; }
.issue-row strong { display:block; color:#3c4e64; font-size:12px; }
.issue-row small { display:block; color:#a17847; font-size:10px; line-height:1.6; margin-top:4px; }
.issue-action { color:#a26c27; font-size:10px; white-space:nowrap; }
.empty-note { margin-top:16px; padding:25px 18px; text-align:center; border-radius:10px; background:#f8fafe; color:#8d9db1; font-size:12px; line-height:1.8; }
.unclassified-list { display:flex; flex-wrap:wrap; gap:8px; margin-top:17px; }
.unclassified-item { padding:8px 11px; border:1px solid #e6ebf4; border-radius:7px; background:#f8faff; color:#6a7e9d; font-size:11px; }
.page-footnote { color:#9aa8bc; font-size:10px; line-height:1.8; }
.overlay { position:fixed; z-index:1300; inset:0; display:flex; align-items:center; justify-content:center; padding:20px; background:#0b1e3b7d; backdrop-filter:blur(3px); }
.dialog { display:flex; flex-direction:column; width:min(710px,100%); max-height:92vh; overflow:hidden; background:white; border-radius:17px; box-shadow:0 18px 70px #111e3f40; }
.dialog-header { display:flex; justify-content:space-between; gap:15px; align-items:flex-start; padding:22px 25px; border-bottom:1px solid #eaf0f6; }
.eyebrow { color:#7e94b1; font-size:10px; letter-spacing:1.3px; font-weight:650; }
.dialog-header h3,.drawer-head h3 { margin:7px 0 0; font-size:20px; color:#203b60; }
.icon-close { flex:none; display:grid; place-items:center; width:32px; height:32px; font-size:23px; border:1px solid #e4ebf4; border-radius:8px; background:white; color:#8395aa; cursor:pointer; }
.dialog-content { min-height:0; overflow-y:auto; padding:23px 25px; font-size:12px; color:#526881; }
.dialog-footer { display:flex; justify-content:flex-end; gap:10px; padding:16px 25px; border-top:1px solid #edf1f6; }
.file-name { color:#788da8; font-size:11px; }
.import-stats { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; margin:15px 0; }
.import-stats>div { border-radius:9px; padding:14px; background:#f4f8ff; }
.import-stats small { display:block; font-size:11px; color:#8b9db4; }
.import-stats strong { color:#2c5ca8; display:block; font-size:24px; margin-top:3px; }
.error-list { max-height:170px; overflow:auto; background:#fff8f5; padding:10px 13px; border:1px solid #f3d9cd; border-radius:8px; color:#ac5240; font-size:11px; }
.sample-list { margin-top:12px; border:1px solid #edf1f7; border-radius:10px; }
.sample-list>div { display:flex; justify-content:space-between; gap:12px; padding:10px 13px; border-bottom:1px solid #edf1f7; }
.sample-list>div:last-child { border-bottom:0; }
.sample-list strong { color:#263e5c; }
.sample-list span { color:#93a3b5; }
.form-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:15px; margin-top:17px; }
.form-grid label { display:flex; flex-direction:column; gap:8px; color:#4e6686; font-size:12px; font-weight:650; }
.form-span { grid-column:1/-1; }
.form-grid textarea { padding:10px; resize:vertical; }
.error-text { color:#bc4540; font-size:12px; line-height:1.7; }
.course-dialog .dialog-footer { margin:18px -25px -23px; }
.drawer-overlay { position:fixed; z-index:1350; inset:0; display:flex; justify-content:flex-end; background:#071d4077; backdrop-filter:blur(2px); }
.drawer { display:flex; flex-direction:column; width:min(515px,100%); height:100%; background:#fff; box-shadow:-18px 0 60px #101d3b30; }
.drawer-head { display:flex; justify-content:space-between; gap:12px; padding:25px 24px; border-bottom:1px solid #edf1f7; }
.drawer-head p { margin:7px 0 0; color:#8c9fb6; font-size:12px; }
.drawer-body { flex:1; overflow:auto; padding:23px 24px; }
.detail-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; }
.detail-grid>div { min-height:68px; padding:13px; background:#f6f9fd; border-radius:10px; }
.detail-grid small { display:block; color:#8598ae; font-size:10px; margin-bottom:6px; }
.detail-grid strong { overflow-wrap:anywhere; font-size:12px; color:#344b68; line-height:1.65; }
.preview-note { padding:13px; border-radius:8px; background:#fff7ec; color:#aa7427; font-size:11px; line-height:1.8; }
.drawer-footer { display:flex; justify-content:flex-end; padding:17px 24px; border-top:1px solid #edf1f7; }
@media(max-width:1230px) { .overview { grid-template-columns:repeat(2,minmax(0,1fr)); } .header-title h1 { font-size:23px; } .issues-list { grid-template-columns:1fr; } }
@media(max-width:760px) { .course-hub { padding:18px 13px 35px; gap:14px; } .page-header { align-items:flex-start; } .header-actions { width:100%; } .overview { gap:9px; } .overview-card { min-height:92px; padding:13px; gap:10px; } .overview-icon { width:37px; height:37px; font-size:18px; } .overview-content strong { font-size:23px; } .panel { padding:16px 13px; } .panel-heading h2 { font-size:15px; } .panel-heading p { margin-left:0; } .filters label { flex:1 1 145px; } .filters .filter-search { flex:1 1 100%; } .button-group { width:100%; } .form-grid,.detail-grid { grid-template-columns:1fr; } .dialog-header,.dialog-content { padding:17px; } .dialog-footer { padding:14px 17px; } .course-dialog .dialog-footer { margin:18px -17px -17px; } }

/* ===== 恢复原有课程分类树 / 计划进度 / 容量 / 封面 / 时间轴布局 ===== */
.legacy-region .hub-row-2col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.legacy-region .hub-row-3col {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 16px;
}
.legacy-region .hub-panel {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px 22px;
  display: flex;
  flex-direction: column;
}
.legacy-region .hub-cover-panel {
  overflow: hidden;
}
.legacy-region .hub-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-shrink: 0;
}
.legacy-region .hub-panel-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-title);
  display: flex;
  align-items: center;
  gap: 8px;
}
.legacy-region .panel-title-icon {
  width: 16px;
  height: 16px;
  color: var(--color-primary);
  flex-shrink: 0;
}
.legacy-region .hub-panel-badge {
  font-size: 11px;
  background: #EFF6FF;
  color: var(--color-primary);
  padding: 3px 10px;
  border-radius: 6px;
  font-weight: 500;
  white-space: nowrap;
}
.legacy-region .hub-panel-badge.hover-tip {
  cursor: help;
}
.legacy-region .capacity-alert-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #1E3A8A;
  margin-right: 2px;
  animation: pulse-dot 1.5s ease-in-out infinite;
}
.legacy-region .category-tree {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.legacy-region .tree-node {
  border-radius: 8px;
  overflow: hidden;
}
.legacy-region .tree-parent {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  cursor: pointer;
  border-radius: 6px;
  transition: background 0.15s;
  user-select: none;
}
.legacy-region .tree-parent:hover {
  background: #F9FAFB;
}
.legacy-region .tree-arrow {
  width: 14px;
  height: 14px;
  color: var(--text-muted);
  flex-shrink: 0;
  transition: transform 0.2s;
}
.legacy-region .tree-arrow.expanded {
  transform: rotate(90deg);
}
.legacy-region .tree-icon {
  width: 10px;
  height: 10px;
  border-radius: 3px;
  flex-shrink: 0;
}
.legacy-region .tree-name {
  flex: 1;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-title);
}
.legacy-region .tree-count {
  font-size: 11px;
  color: var(--text-muted);
  background: #F3F4F6;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}
.legacy-region .tree-children {
  margin-left: 32px;
  padding: 4px 0 4px 12px;
  border-left: 2px solid #F3F4F6;
}
.legacy-region .tree-child {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 0;
  font-size: 12px;
  color: var(--text-body);
}
.legacy-region .tree-child-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
.legacy-region .tree-child-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.legacy-region .plan-progress-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.legacy-region .plan-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.legacy-region .plan-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.legacy-region .plan-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-title);
}
.legacy-region .plan-meta {
  font-size: 11px;
  color: var(--text-muted);
}
.legacy-region .plan-bar-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
}
.legacy-region .plan-bar-bg {
  flex: 1;
  height: 10px;
  background: #F3F4F6;
  border-radius: 5px;
  overflow: hidden;
  position: relative;
}
.legacy-region .plan-bar-fill {
  height: 100%;
  border-radius: 5px;
  transition: width 0.5s ease;
  position: relative;
  min-width: 0;
}
.legacy-region .plan-bar-dot {
  position: absolute;
  right: -5px;
  top: 50%;
  transform: translateY(-50%);
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #FFF;
  border: 2px solid #3B82F6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}
.legacy-region .plan-pct {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-title);
  width: 36px;
  text-align: right;
  flex-shrink: 0;
}
.legacy-region .plan-pct.text-success {
  color: #1E3A8A;
}
.legacy-region .plan-pct.text-warning {
  color: #3B82F6;
}
.legacy-region .plan-milestones {
  display: flex;
  gap: 6px;
}
.legacy-region .milestone-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #E5E7EB;
  flex-shrink: 0;
  cursor: help;
  transition: background 0.2s;
}
.legacy-region .milestone-dot.done {
  background: #3B82F6;
}
.legacy-region .capacity-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.legacy-region .capacity-item {
  padding: 8px 0;
  border-bottom: 1px solid #F3F4F6;
}
.legacy-region .capacity-item:last-child {
  border-bottom: none;
}
.legacy-region .capacity-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.legacy-region .capacity-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-title);
}
.legacy-region .capacity-rate {
  font-size: 14px;
  font-weight: 700;
}
.legacy-region .capacity-rate.load-safe {
  color: #93C5FD;
}
.legacy-region .capacity-rate.load-warning {
  color: #3B82F6;
}
.legacy-region .capacity-rate.load-danger {
  color: #1E3A8A;
}
.legacy-region .capacity-bar-wrap {
  margin-bottom: 4px;
}
.legacy-region .capacity-bar-bg {
  height: 7px;
  background: #F3F4F6;
  border-radius: 4px;
  overflow: hidden;
}
.legacy-region .capacity-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}
.legacy-region .capacity-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.legacy-region .capacity-nums {
  font-size: 11px;
  color: var(--text-muted);
}
.legacy-region .capacity-wait {
  font-size: 11px;
  color: #1E3A8A;
  font-weight: 600;
  background: #EFF6FF;
  padding: 1px 6px;
  border-radius: 4px;
}
.legacy-region .cover-scroll-wrap {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  scroll-behavior: smooth;
  padding-bottom: 8px;
  scrollbar-width: thin;
  scrollbar-color: #D1D5DB transparent;
}
.legacy-region .cover-scroll-wrap::-webkit-scrollbar {
  height: 4px;
}
.legacy-region .cover-scroll-wrap::-webkit-scrollbar-track {
  background: transparent;
}
.legacy-region .cover-scroll-wrap::-webkit-scrollbar-thumb {
  background: #D1D5DB;
  border-radius: 2px;
}
.legacy-region .cover-nav {
  display: flex;
  gap: 6px;
}
.legacy-region .cover-nav-btn {
  width: 32px;
  height: 32px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: #FFF;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}
.legacy-region .cover-nav-btn svg {
  width: 16px;
  height: 16px;
  color: var(--text-secondary);
}
.legacy-region .cover-nav-btn:hover {
  background: #F9FAFB;
  border-color: #D1D5DB;
}
.legacy-region .cover-card {
  min-width: 240px;
  max-width: 240px;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;
  flex-shrink: 0;
  transition: all 0.25s;
  cursor: pointer;
  background: var(--bg-card);
}
.legacy-region .cover-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  transform: translateY(-3px);
  border-color: var(--color-primary-light);
}
.legacy-region .cover-banner {
  height: 110px;
  position: relative;
  display: flex;
  align-items: flex-end;
  justify-content: flex-end;
  padding: 14px;
}
.legacy-region .cover-badge-row {
  position: absolute;
  top: 10px;
  left: 10px;
  display: flex;
  gap: 6px;
}
.legacy-region .cover-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 4px;
  color: #FFF;
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(4px);
}
.legacy-region .cover-badge.badge-active {
  background: rgba(30, 58, 138, 0.85);
}
.legacy-region .cover-badge.badge-pending {
  background: rgba(147, 197, 253, 0.85);
  color: #1E3A8A;
}
.legacy-region .cover-badge.badge-ended {
  background: rgba(107, 114, 128, 0.85);
}
.legacy-region .cover-icon-wrap {
  opacity: 0.2;
}
.legacy-region .cover-icon {
  width: 48px;
  height: 48px;
  color: #FFF;
}
.legacy-region .cover-body {
  padding: 14px;
}
.legacy-region .cover-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-title);
  margin: 0 0 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.legacy-region .cover-college {
  font-size: 11px;
  color: var(--text-muted);
  margin: 0;
}
.legacy-region .cover-meta {
  display: flex;
  gap: 12px;
  margin-top: 10px;
}
.legacy-region .cover-meta-item {
  font-size: 11px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 4px;
}
.legacy-region .cover-meta-icon {
  width: 13px;
  height: 13px;
  color: var(--text-muted);
}
.legacy-region .cover-rating {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #F3F4F6;
}
.legacy-region .cover-stars {
  display: flex;
  gap: 1px;
}
.legacy-region .cover-star {
  font-size: 14px;
  color: #E5E7EB;
}
.legacy-region .cover-star.filled {
  color: #2563EB;
}
.legacy-region .cover-rating-num {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-primary);
}
.legacy-region .timeline-wrap {
  display: flex;
  flex-direction: column;
}
.legacy-region .timeline-item {
  display: flex;
  gap: 14px;
  position: relative;
}
.legacy-region .timeline-marker {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  width: 24px;
}
.legacy-region .timeline-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #E5E7EB;
  border: 2px solid #FFF;
  box-shadow: 0 0 0 2px #E5E7EB;
  flex-shrink: 0;
  margin-top: 4px;
  z-index: 1;
  transition: all 0.3s;
}
.legacy-region .timeline-dot.dot-active {
  background: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(30, 58, 138, 0.25);
  animation: pulse-ring 2s ease-in-out infinite;
}
.legacy-region .timeline-dot.dot-done {
  background: #3B82F6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3);
}
@keyframes pulse-ring {
  0%, 100% { box-shadow: 0 0 0 3px rgba(30, 58, 138, 0.25); }
  50% { box-shadow: 0 0 0 8px rgba(30, 58, 138, 0.05); }
}
.legacy-region .timeline-line {
  width: 2px;
  flex: 1;
  min-height: 28px;
  background: #E5E7EB;
  margin-top: 4px;
}
.legacy-region .timeline-line.line-done {
  background: #3B82F6;
}
.legacy-region .timeline-content {
  flex: 1;
  padding-bottom: 16px;
  min-width: 0;
}
.legacy-region .timeline-item:last-child .timeline-content {
  padding-bottom: 0;
}
.legacy-region .timeline-date {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 500;
}
.legacy-region .timeline-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-title);
  margin-top: 2px;
}
.legacy-region .timeline-desc {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 2px;
  line-height: 1.4;
}
.legacy-region .timeline-tags {
  display: flex;
  gap: 4px;
  margin-top: 4px;
  flex-wrap: wrap;
}
.legacy-region .timeline-tag {
  font-size: 10px;
  background: #EFF6FF;
  color: var(--color-primary);
  padding: 1px 7px;
  border-radius: 4px;
  font-weight: 500;
}
.legacy-region .timeline-active .timeline-title {
  color: var(--color-primary);
}
.legacy-region .timeline-active .timeline-content {
  background: linear-gradient(135deg, rgba(239, 246, 255, 0.6), transparent);
  border-radius: 8px;
  padding: 8px 10px;
  margin-left: -10px;
}
@media (max-width: 1600px){
.legacy-region .hub-row-3col {
    grid-template-columns: 1fr 1fr;
  }
}
@media (max-width: 1200px){
.legacy-region .hub-row-2col {
    grid-template-columns: 1fr;
  }
.legacy-region .hub-row-3col {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 768px){
.legacy-region .cover-card {
    min-width: 200px;
    max-width: 200px;
  }
}

.legacy-region { display:flex; flex-direction:column; gap:20px; }
.legacy-region-heading { padding:2px 0; }
.legacy-region-heading h2 { display:flex; align-items:center; gap:9px; font-size:18px; margin:0; color:#1b3150; }
.legacy-region-heading p { margin:9px 0 0; color:#8e9eb2; font-size:11px; }
.legacy-region .hub-panel { --bg-card:#fff; --border-color:#e5ebf3; --text-title:#1b3150; --text-muted:#93a0b2; --text-secondary:#61758e; --color-primary:#244b96; --color-primary-light:#9fc0f5; }
.legacy-region .hub-row-3col { grid-template-columns:repeat(3,minmax(0,1fr)); }
.legacy-region .hub-row-2col { grid-template-columns:repeat(2,minmax(0,1fr)); }
.legacy-region .hub-panel { min-width:0; background:#fff; border:1px solid #e5ebf3; border-radius:15px; box-shadow:0 7px 24px #193d6906; }
.legacy-region .legacy-empty { border-radius:9px; padding:24px 12px; text-align:center; background:#f7f9fc; color:#94a2b5; font-size:12px; line-height:1.8; }
.legacy-region .legacy-panel-subtitle { font-size:11px; color:#91a0b2; line-height:1.7; margin:1px 0 15px; }
.legacy-region .tree-parent { width:100%; border:0; text-align:left; font-family:inherit; }
.legacy-region .legacy-inline-btn { border:0; background:transparent; font-size:11px; color:#3067b5; cursor:pointer; }
.legacy-region .cover-card { flex:none; text-align:left; padding:0; cursor:pointer; font-family:inherit; }
.legacy-region .cover-card:focus-visible { outline:3px solid #93baf9; outline-offset:2px; }
.legacy-region .legacy-cover-hint { color:#3067b5; font-size:11px; }
.legacy-region .cover-rating { justify-content:space-between; }
.legacy-region .cover-meta { flex-wrap:wrap; }
.legacy-region .legacy-issues-list { display:flex; flex-direction:column; gap:9px; }
.legacy-region .legacy-issues-list .issue-row { padding:11px; }
.legacy-region .hub-panel { padding:20px; }
.legacy-region .hub-cover-panel { padding:20px; }
@media (max-width:1370px) { .legacy-region .hub-row-3col { grid-template-columns:repeat(2,minmax(0,1fr)); } }
@media (max-width:1050px) { .legacy-region .hub-row-3col, .legacy-region .hub-row-2col { grid-template-columns:minmax(0,1fr); } }
@media (max-width:760px) { .legacy-region .hub-row-3col, .legacy-region .hub-row-2col { grid-template-columns:minmax(0,1fr); } .legacy-region .hub-panel { padding:16px; } }

</style>
