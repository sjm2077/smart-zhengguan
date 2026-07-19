// 菜单配置
const menuItems = [
  { key: 'dashboard', label: '数据概览', icon: 'fa-chart-pie', parent: false },
  { key: 'basic', label: '基本信息', icon: 'fa-address-card', parent: false },
  {
    key: 'personnel', label: '人事信息', icon: 'fa-users', parent: true, children: [
      { key: 'political', label: '政治面貌' }, { key: 'education', label: '学习经历' }, { key: 'work', label: '工作经历' },
      { key: 'family', label: '家庭成员' }, { key: 'assessment', label: '年度考核' }, { key: 'transfer', label: '校内调动' },
      { key: 'retire', label: '离退休信息' }, { key: 'staffing', label: '编制类型记录' }
    ]
  },
  {
    key: 'position', label: '职务/岗位', icon: 'fa-briefcase', parent: true, children: [
      { key: 'positionInfo', label: '岗位信息' }, { key: 'partyPos', label: '党政职务' }, { key: 'professional', label: '专业技术职务' },
      { key: 'skill', label: '工勤技能' }, { key: 'dual', label: '双聘单位' }
    ]
  },
  {
    key: 'teacher', label: '师资信息', icon: 'fa-graduation-cap', parent: true, children: [
      { key: 'abroad', label: '公派出国' }, { key: 'teacherCert', label: '教师资格证' }, { key: 'training', label: '教师培训' },
      { key: 'honor', label: '荣誉称号' }, { key: 'social', label: '学术与社会兼职' }
    ]
  },
  {
    key: 'analysis', label: '统计分析', icon: 'fa-chart-line', parent: true, children: [
      { key: 'performance', label: '绩效统计' }, { key: 'promotion', label: '晋升预测' }
    ]
  },
  { key: 'contact', label: '其他信息', icon: 'fa-address-book', parent: false },
  { key: 'portrait', label: '全景画像', icon: 'fa-id-card', parent: false }
];

const pageTitles = {
  dashboard: '数据概览', basic: '基本信息', political: '政治面貌', education: '学习经历', work: '工作经历',
  family: '家庭成员', assessment: '年度考核', transfer: '校内调动', retire: '离退休信息', staffing: '编制类型记录',
  positionInfo: '岗位信息', partyPos: '党政职务', professional: '专业技术职务', skill: '工勤技能', dual: '双聘单位',
  abroad: '公派出国', teacherCert: '教师资格证', training: '教师培训', honor: '荣誉称号', social: '学术与社会兼职',
  contact: '联系方式', performance: '绩效统计', promotion: '晋升预测', portrait: '全景画像'
};

var currentPage = 'dashboard';
var currentParent = '';
var portraitSelectedPerson = null;

// ===== 分页与排序全局状态 =====
var tableSortState = { col: -1, dir: 1 }; // col索引, dir: 1=asc, -1=desc
var tablePageState = { page: 1, pageSize: 15 };

// ===== 面包屑 =====
function getBreadcrumbPath(pageKey, parentKey) {
  var path = [{ label: '首页', key: 'dashboard' }];
  if (pageKey === 'dashboard') return path;
  if (parentKey) {
    for (var i = 0; i < menuItems.length; i++) {
      if (menuItems[i].parent && menuItems[i].key === parentKey) {
        path.push({ label: menuItems[i].label, key: null });
        break;
      }
    }
  }
  path.push({ label: pageTitles[pageKey] || pageKey, key: null });
  return path;
}

function renderBreadcrumb(pageKey, parentKey) {
  if (pageKey === 'dashboard') return '';
  var path = getBreadcrumbPath(pageKey, parentKey);
  var html = '<div class="breadcrumb">';
  for (var i = 0; i < path.length; i++) {
    if (i > 0) html += '<span class="breadcrumb-sep"><i class="fas fa-chevron-right"></i></span>';
    if (path[i].key) {
      html += '<span class="breadcrumb-item breadcrumb-link" data-page="' + path[i].key + '">' + path[i].label + '</span>';
    } else {
      html += '<span class="breadcrumb-item breadcrumb-current">' + path[i].label + '</span>';
    }
  }
  html += '</div>';
  return html;
}

function renderSidebar() {
  var nav = document.getElementById('sidebarNav');
  var html = '';
  menuItems.forEach(function(item) {
    if (item.parent) {
      html += '<div class="nav-item parent-menu" data-parent="'+item.key+'"><span class="menu-text"><i class="fas '+item.icon+'"></i> '+item.label+'</span><i class="fas fa-chevron-down"></i></div>';
      html += '<div class="submenu" id="sub_'+item.key+'">';
      item.children.forEach(function(child) {
        html += '<div class="nav-item sub-item" data-page="'+child.key+'" data-parent="'+item.key+'"><i class="fas fa-circle" style="font-size:0.4rem;"></i> '+child.label+'</div>';
      });
      html += '</div>';
    } else {
      html += '<div class="nav-item" data-page="'+item.key+'"><i class="fas '+item.icon+'"></i> '+item.label+'</div>';
    }
  });
  nav.innerHTML = html;
}

function setActiveMenu(pageKey, parentKey) {
  parentKey = parentKey || null;
  document.querySelectorAll('.nav-item').forEach(function(el) { el.classList.remove('active'); });
  var selector = parentKey ? '.sub-item[data-page="'+pageKey+'"]' : '.nav-item[data-page="'+pageKey+'"]';
  var el = document.querySelector(selector);
  if (el) el.classList.add('active');
  if (parentKey) {
    var parentEl = document.querySelector('.parent-menu[data-parent="'+parentKey+'"]');
    if (parentEl) parentEl.classList.add('active');
  }
}

function toggleSubmenu(parentKey) {
  var sub = document.getElementById('sub_' + parentKey);
  if (sub) sub.classList.toggle('open');
}

function updatePageTitle(key) {
  // 页面标题已改为静态品牌文字，此函数仅保留兼容性
}

function getIconForPage(key) {
  var map = {
    dashboard: 'fa-chart-pie', basic: 'fa-address-card', political: 'fa-flag', education: 'fa-graduation-cap',
    work: 'fa-briefcase', family: 'fa-people-roof', assessment: 'fa-clipboard-check', transfer: 'fa-arrows-left-right',
    retire: 'fa-person-cane', staffing: 'fa-file-lines', positionInfo: 'fa-briefcase', partyPos: 'fa-building-columns',
    professional: 'fa-certificate', skill: 'fa-gears', dual: 'fa-building', abroad: 'fa-plane-departure',
    teacherCert: 'fa-chalkboard-user', training: 'fa-chalkboard', honor: 'fa-medal', social: 'fa-handshake',
    contact: 'fa-address-book', performance: 'fa-chart-bar', promotion: 'fa-arrow-trend-up', portrait: 'fa-id-card'
  };
  return map[key] || 'fa-file';
}

function toggleSearchBox(visible) {
  // 搜索栏始终显示，此函数仅用于清空输入
  if (!visible) document.getElementById('searchInput').value = '';
}

// ===== 全局模糊查找 =====
function highlightMatch(text, keyword) {
  if (!keyword || !text) return text;
  var lowText = String(text).toLowerCase();
  var lowKw = keyword.toLowerCase();
  var idx = lowText.indexOf(lowKw);
  if (idx === -1) return text;
  return String(text).substring(0, idx) + '<span class="search-highlight">' + String(text).substring(idx, idx + keyword.length) + '</span>' + String(text).substring(idx + keyword.length);
}

function fuzzySearchPersonnel(keyword) {
  var kw = keyword.toLowerCase().trim();
  if (kw === '') return [];
  var results = [];
  for (var i = 0; i < personnelData.length; i++) {
    var p = personnelData[i];
    var score = 0;
    
    // 姓名完全匹配 +100
    if (p.name.toLowerCase() === kw) score += 100;
    // 姓名包含 +50
    else if (p.name.toLowerCase().indexOf(kw) !== -1) score += 50;
    
    // 工号匹配 +40
    if (p.id.toLowerCase().indexOf(kw) !== -1) score += 40;
    
    // 手机号匹配 +35
    if (p.contact.phone && p.contact.phone.indexOf(kw) !== -1) score += 35;
    
    // 邮箱匹配 +30
    if (p.contact.email && p.contact.email.toLowerCase().indexOf(kw) !== -1) score += 30;
    
    // 部门/党支部匹配 +25
    if (p.partyBranch && p.partyBranch.toLowerCase().indexOf(kw) !== -1) score += 25;
    
    // 办公电话匹配 +20
    if (p.contact.officePhone && p.contact.officePhone.indexOf(kw) !== -1) score += 20;
    
    // 地址匹配 +15
    if (p.contact.address && p.contact.address.toLowerCase().indexOf(kw) !== -1) score += 15;
    
    // 党政职务匹配 +10
    if (p.partyPosition.title && p.partyPosition.title.toLowerCase().indexOf(kw) !== -1) score += 10;
    
    // 专业匹配 +10
    if (p.professionalTitle.major && p.professionalTitle.major.toLowerCase().indexOf(kw) !== -1) score += 10;
    
    // 岗位名称匹配 +10
    if (p.positionInfo.title && p.positionInfo.title.toLowerCase().indexOf(kw) !== -1) score += 10;
    
    if (score > 0) {
      results.push({ person: p, score: score, keyword: kw });
    }
  }
  results.sort(function(a, b) { return b.score - a.score; });
  return results.slice(0, 15);
}

function renderSearchSuggestions(results) {
  var container = document.getElementById('searchSuggestions');
  if (!container) return;
  
  if (results.length === 0) {
    container.innerHTML = '<div class="search-suggestion-item no-match">未找到匹配的人员</div>';
    container.style.display = 'block';
    return;
  }
  
  // 顶部的统计信息
  var html = '<div style="padding:8px 18px;font-size:0.72rem;color:var(--text-secondary);border-bottom:1px solid var(--border-light);background:#F8FAFC;">找到 <strong>' + results.length + '</strong> 个匹配结果</div>';
  
  results.forEach(function(r) {
    var p = r.person;
    var kw = r.keyword;
    var initials = p.name.charAt(0);
    html += '<div class="search-suggestion-item" data-id="' + p.id + '">';
    html += '<div class="search-suggestion-avatar">' + initials + '</div>';
    html += '<div class="search-suggestion-info">';
    html += '<span class="search-suggestion-name">' + highlightMatch(p.name, kw) + '</span>';
    html += '<div class="search-suggestion-detail">';
    html += '<span><i class="fas fa-id-badge"></i> ' + highlightMatch(p.id, kw) + '</span>';
    if (p.partyBranch) html += '<span><i class="fas fa-building"></i> ' + highlightMatch(p.partyBranch, kw) + '</span>';
    html += '<span><i class="fas fa-phone"></i> ' + highlightMatch(p.contact.phone, kw) + '</span>';
    html += '</div></div>';
    html += '<span class="search-suggestion-link"><i class="fas fa-arrow-right"></i> 查看</span>';
    html += '</div>';
  });
  
  container.innerHTML = html;
  container.style.display = 'block';
  
  // 绑定点击
  container.querySelectorAll('.search-suggestion-item').forEach(function(item) {
    item.addEventListener('click', function() {
      var id = this.getAttribute('data-id');
      if (id) {
        // 跳转到全景画像
        for (var i = 0; i < personnelData.length; i++) {
          if (personnelData[i].id === id) {
            portraitSelectedPerson = personnelData[i];
            break;
          }
        }
        document.getElementById('searchInput').value = '';
        container.style.display = 'none';
        if (portraitSelectedPerson) {
          // 直接刷新全景画像视图，避免 renderPage('portrait') 重置选中状态
          setActiveMenu('portrait');
          currentPage = 'portrait';
          currentParent = '';
          refreshPortraitView();
        }
      }
    });
  });
}

function bindGlobalSearch() {
  var input = document.getElementById('searchInput');
  var suggestions = document.getElementById('searchSuggestions');
  if (!input || !suggestions) return;
  
  input.addEventListener('input', function() {
    var keyword = this.value.trim();
    if (keyword === '') {
      suggestions.style.display = 'none';
      // 如果在表格页面，恢复表格显示
      document.querySelectorAll('table tbody tr').forEach(function(row) {
        row.style.display = '';
      });
      return;
    }
    // 如果在非仪表盘/全景画像/绩效统计/晋升预测页面，同时过滤当前表格
    var tablePages = ['basic','political','education','work','family','assessment','transfer','retire','staffing','positionInfo','partyPos','professional','skill','dual','abroad','teacherCert','training','honor','social','contact'];
    if (tablePages.indexOf(currentPage) !== -1) {
      var kw = keyword.toLowerCase();
      document.querySelectorAll('table tbody tr').forEach(function(row) {
        row.style.display = row.innerText.toLowerCase().indexOf(kw) !== -1 ? '' : 'none';
      });
    }
    // 显示全局搜索下拉
    var results = fuzzySearchPersonnel(keyword);
    renderSearchSuggestions(results);
  });
  
  // Enter 键：跳转到第一个匹配结果
  input.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
      var keyword = this.value.trim();
      if (keyword === '') return;
      var results = fuzzySearchPersonnel(keyword);
      if (results.length > 0) {
        var p = results[0].person;
        for (var i = 0; i < personnelData.length; i++) {
          if (personnelData[i].id === p.id) { portraitSelectedPerson = personnelData[i]; break; }
        }
        this.value = '';
        suggestions.style.display = 'none';
        if (portraitSelectedPerson) {
          setActiveMenu('portrait');
          currentPage = 'portrait';
          currentParent = '';
          refreshPortraitView();
        }
      }
    }
  });
  
  // 点击外部关闭下拉
  document.addEventListener('click', function(e) {
    if (!e.target.closest('.topbar-search-wrapper')) {
      suggestions.style.display = 'none';
    }
  });
  
  // 初始状态：搜索栏始终显示
  document.getElementById('globalSearchWrapper').style.display = '';
}

// ===== 分页渲染 =====
function renderPagination(totalRows, containerEl) {
  tablePageState.page = Math.max(1, Math.min(tablePageState.page, Math.ceil(totalRows / tablePageState.pageSize)));
  var totalPages = Math.ceil(totalRows / tablePageState.pageSize);
  if (totalPages <= 1) return '';
  
  var html = '<div class="pagination-bar">';
  html += '<div class="pagination-info">共 ' + totalRows + ' 条记录，第 ' + tablePageState.page + '/' + totalPages + ' 页</div>';
  html += '<div class="pagination-controls">';
  html += '<select class="page-size-select" id="pageSizeSelect">';
  [10, 15, 20, 30, 50].forEach(function(s) {
    html += '<option value="' + s + '"' + (tablePageState.pageSize === s ? ' selected' : '') + '>' + s + ' 条/页</option>';
  });
  html += '</select>';
  html += '<button class="page-btn' + (tablePageState.page <= 1 ? ' disabled' : '') + '" data-page="1" title="首页"><i class="fas fa-angles-left"></i></button>';
  html += '<button class="page-btn' + (tablePageState.page <= 1 ? ' disabled' : '') + '" data-page="' + (tablePageState.page - 1) + '" title="上一页"><i class="fas fa-chevron-left"></i></button>';
  
  var startP = Math.max(1, tablePageState.page - 2);
  var endP = Math.min(totalPages, tablePageState.page + 2);
  if (startP > 1) html += '<span class="page-ellipsis">…</span>';
  for (var p = startP; p <= endP; p++) {
    html += '<button class="page-btn' + (p === tablePageState.page ? ' active' : '') + '" data-page="' + p + '">' + p + '</button>';
  }
  if (endP < totalPages) html += '<span class="page-ellipsis">…</span>';
  
  html += '<button class="page-btn' + (tablePageState.page >= totalPages ? ' disabled' : '') + '" data-page="' + (tablePageState.page + 1) + '" title="下一页"><i class="fas fa-chevron-right"></i></button>';
  html += '<button class="page-btn' + (tablePageState.page >= totalPages ? ' disabled' : '') + '" data-page="' + totalPages + '" title="末页"><i class="fas fa-angles-right"></i></button>';
  html += '</div></div>';
  return html;
}

// ===== 真实 CSV 导出 =====
function realExportTable(columns, rows) {
  var title = pageTitles[currentPage] || '数据导出';
  
  // Build CSV content with BOM for Excel UTF-8 compatibility
  var csvContent = '\uFEFF';
  
  // Header
  var headerCols = columns.slice();
  if (headerCols[headerCols.length - 1] !== '操作') headerCols.push('操作');
  csvContent += headerCols.map(function(c) { return '"' + (c || '').replace(/"/g, '""') + '"'; }).join(',') + '\n';
  
  // Data rows (strip HTML tags for CSV)
  rows.forEach(function(row) {
    var csvRow = row.map(function(cell) {
      var text = String(cell || '').replace(/<[^>]*>/g, '').replace(/"/g, '""');
      return '"' + text + '"';
    });
    csvContent += csvRow.join(',') + '\n';
  });
  
  var blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  var url = URL.createObjectURL(blob);
  var a = document.createElement('a');
  a.href = url;
  a.download = title + '_' + new Date().toISOString().slice(0, 10) + '.csv';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  
  var toast = document.getElementById('toast');
  toast.textContent = '已成功导出 ' + rows.length + ' 条记录';
  toast.style.display = 'block';
  setTimeout(function() { toast.style.display = 'none'; }, 2000);
}

// ===== 生成带排序和分页的表格 =====
function generateTableHTML(columns, rows, rawRows) {
  rawRows = rawRows || rows;
  
  var sortCol = tableSortState.col;
  var sortDir = tableSortState.dir;
  
  // 排序
  if (sortCol >= 0 && sortCol < columns.length && rows.length > 0) {
    rows.sort(function(a, b) {
      var va = (a[sortCol] || '').toString().replace(/<[^>]*>/g, '');
      var vb = (b[sortCol] || '').toString().replace(/<[^>]*>/g, '');
      var na = parseFloat(va), nb = parseFloat(vb);
      if (!isNaN(na) && !isNaN(nb)) { va = na; vb = nb; }
      if (va < vb) return -1 * sortDir;
      if (va > vb) return 1 * sortDir;
      return 0;
    });
  }
  
  // 分页
  var totalRows = rows.length;
  var startIdx = (tablePageState.page - 1) * tablePageState.pageSize;
  var pagedRows = rows.slice(startIdx, startIdx + tablePageState.pageSize);
  
  var html = '<div class="card"><div class="card-header"><h3>'+(pageTitles[currentPage] || '')+'</h3><button class="btn btn-outline" onclick="window.exportTable()"><i class="fas fa-download"></i> 导出</button></div><div class="table-responsive"><table><thead><tr>';
  
  columns.forEach(function(col, idx) {
    var sortIcon = '';
    if (idx === sortCol) {
      sortIcon = ' <i class="fas fa-sort-' + (sortDir === 1 ? 'up' : 'down') + ' sort-icon-active"></i>';
    } else {
      sortIcon = ' <i class="fas fa-sort sort-icon"></i>';
    }
    html += '<th class="sortable-th" data-col="'+idx+'">'+col+sortIcon+'</th>';
  });
  html += '<th>操作</th></tr></thead><tbody>';
  
  pagedRows.forEach(function(row) {
    html += '<tr>';
    row.forEach(function(cell, idx) {
      if (idx === 1) {
        var pid = null;
        for (var i = 0; i < personnelData.length; i++) { if (personnelData[i].name === cell) { pid = personnelData[i].id; break; } }
        html += '<td><span class="clickable-name" data-id="'+(pid||'')+'">'+cell+'</span></td>';
      } else { html += '<td>'+cell+'</td>'; }
    });
    var did = null;
    for (var j = 0; j < personnelData.length; j++) { if (personnelData[j].name === row[1]) { did = personnelData[j].id; break; } }
    html += '<td><button class="btn btn-outline" style="padding:4px 12px;" onclick="window.showDetailById(\''+(did||'')+'\')"><i class="fas fa-eye"></i> 详情</button></td>';
    html += '</tr>';
  });
  html += '</tbody></table></div>';
  html += renderPagination(totalRows);
  html += '</div>';
  
  // 存储原始数据供导出使用
  html += '<script type="application/json" class="export-data" style="display:none;">' + JSON.stringify({ columns: columns, rows: rawRows }) + '</sc' + 'ript>';
  return html;
}

function renderSimpleTable(type, columns, rowMapper) {
  var rows = personnelData.map(function(p) { return rowMapper(p); }).filter(function(r) { return r; });
  return generateTableHTML(columns, rows);
}

function renderListTable(field, columns, rowMapper) {
  var rows = [];
  personnelData.forEach(function(p) {
    var list = p[field];
    if (list && list.length > 0) { list.forEach(function(item) { rows.push(rowMapper(p, item)); }); }
  });
  return generateTableHTML(columns, rows);
}

function renderBasicTable() {
  var columns = ['工号','姓名','性别','出生日期','民族','籍贯','身份证号'];
  var rows = personnelData.map(function(p) { return [p.id, p.name, p.gender, p.birthdate, p.nation, p.nativePlace, p.idCard]; });
  return generateTableHTML(columns, rows);
}

// ============ ECharts 仪表盘 ============
var COLORS = ['#1E3A8A','#2563EB','#3B82F6','#60A5FA','#93C5FD','#BFDBFE','#DBEAFE','#EFF6FF'];
var SEC_COLORS = ['#1E3A8A','#10B981','#6366F1','#F59E0B','#EF4444'];

function cc(title, icon, id, extraClass) { return '<div class="chart-card'+(extraClass?' '+extraClass:'')+'"><div class="chart-title"><i class="fas '+icon+'"></i> '+title+'</div><div class="chart-wrap" id="'+id+'"></div></div>'; }
function section(title, subtitle, icon, bgColor, content) { return '<div class="dash-section"><div class="dash-section-header"><div class="section-icon" style="background:'+bgColor+';"><i class="fas '+icon+'"></i></div><div><span class="section-title">'+title+'</span><span class="section-subtitle">'+subtitle+'</span></div></div>'+content+'</div>'; }

function getPromoYears() {
  var years = {};
  for (var i = 0; i < personnelData.length; i++) {
    var ph = personnelData[i].promotionHistory;
    if (!ph) continue;
    for (var j = 0; j < ph.length; j++) { years[ph[j].year] = true; }
  }
  return Object.keys(years).map(Number).sort(function(a,b) { return a-b; });
}

function renderDashboardHTML() {
  var total = personnelData.length;
  var active = 0, retired = 0, partyMembers = 0, maleCount = 0;
  for (var i = 0; i < personnelData.length; i++) { var p = personnelData[i]; if (!p.retireInfo.isRetired) active++; else retired++; if (p.politicalStatus === '中共党员') partyMembers++; if (p.gender === '男') maleCount++; }

  var html = '<div class="stats-grid">'+
    '<div class="stat-card" data-filter="all"><div class="stat-icon" style="background:#1E3A8A;"><i class="fas fa-user-group"></i></div><div><div class="stat-value">'+total+'</div><div class="stat-label">教职工总数</div></div></div>'+
    '<div class="stat-card"><div class="stat-icon" style="background:#3B82F6;"><i class="fas fa-user-check"></i></div><div><div class="stat-value">'+active+'</div><div class="stat-label">在职人数</div></div></div>'+
    '<div class="stat-card"><div class="stat-icon" style="background:#F59E0B;"><i class="fas fa-person-cane"></i></div><div><div class="stat-value">'+retired+'</div><div class="stat-label">离退休</div></div></div>'+
    '<div class="stat-card"><div class="stat-icon" style="background:#10B981;"><i class="fas fa-flag"></i></div><div><div class="stat-value">'+partyMembers+'</div><div class="stat-label">党员人数</div></div></div>'+
    '<div class="stat-card"><div class="stat-icon" style="background:#6366F1;"><i class="fas fa-mars"></i></div><div><div class="stat-value">'+maleCount+' / '+(total-maleCount)+'</div><div class="stat-label">男 / 女</div></div></div>'+
  '</div>';

  html += section('组织架构', '学院支部体系与人员构成', 'fa-sitemap', '#1E3A8A',
    '<div class="dash-grid">'+cc('组织架构旭日图', 'fa-sitemap', 'chart-tree')+cc('编制 → 岗位 → 性别 桑基图', 'fa-diagram-project', 'chart-sankey')+'</div>');

  html += section('队伍结构', '职称、学历与绩效面面观', 'fa-layer-group', '#10B981',
    '<div class="dash-grid-3">'+cc('职称分布', 'fa-chart-pie', 'chart-pie-title')+cc('学历分布', 'fa-graduation-cap', 'chart-pie-degree')+cc('绩效雷达图', 'fa-crosshairs', 'chart-radar')+'</div>');

  html += section('学科与人才', '教师专业分布与科研能力', 'fa-microscope', '#6366F1',
    '<div class="dash-grid">'+cc('各学科教师人数', 'fa-chart-bar', 'chart-bar-major')+cc('年龄 vs 科研得分散点图', 'fa-circle-dot', 'chart-scatter')+'</div>');

  html += section('党建与荣誉', '党支部、培训及荣誉词云', 'fa-award', '#F59E0B',
    '<div class="dash-grid-3">'+cc('培训与荣誉词云', 'fa-cloud', 'chart-wordcloud')+cc('绩效气泡图', 'fa-chart-bubble', 'chart-bubble')+cc('各党支部人数', 'fa-building-columns', 'chart-bar-party')+'</div>');

  html += section('考核与晋升', '历年考核趋势与晋升预测', 'fa-chart-line', '#EF4444',
    '<div class="dash-grid">'+cc('历年考核堆叠面积图', 'fa-chart-area', 'chart-area')+cc('历年晋升概率折线图', 'fa-chart-line', 'chart-line')+'</div>'+
    '<div class="dash-grid"><div class="chart-card full-width tall"><div class="chart-title"><i class="fas fa-table-cells"></i> 晋升概率热力图</div><div class="chart-wrap" id="chart-heatmap" style="min-height:380px;"></div></div></div>');

  return html;
}

// ===== 图表点击联动：跳转到基本信息页并筛选 =====
function navigateToFilteredList(keyword) {
  renderPage('basic');
  setTimeout(function() {
    var searchInput = document.getElementById('searchInput');
    if (searchInput) {
      searchInput.value = keyword;
      searchInput.dispatchEvent(new Event('input'));
    }
  }, 300);
}

function bindChartClick(chart, dataMapFn) {
  if (!chart) return;
  chart.off('click');
  chart.on('click', function(params) {
    var keyword = dataMapFn(params);
    if (keyword) navigateToFilteredList(keyword);
  });
}

function initAllCharts() {
  try { initTreeChart(); } catch(e) { console.warn('tree', e); }
  try { initSankeyChart(); } catch(e) { console.warn('sankey', e); }
  try { initPieTitle(); } catch(e) { console.warn('pie-title', e); }
  try { initPieDegree(); } catch(e) { console.warn('pie-degree', e); }
  try { initRadarChart(); } catch(e) { console.warn('radar', e); }
  try { initBarMajor(); } catch(e) { console.warn('bar-major', e); }
  try { initScatterChart(); } catch(e) { console.warn('scatter', e); }
  try { initWordCloud(); } catch(e) { console.warn('wordcloud', e); }
  try { initBubbleChart(); } catch(e) { console.warn('bubble', e); }
  try { initBarParty(); } catch(e) { console.warn('bar-party', e); }
  try { initStackedArea(); } catch(e) { console.warn('area', e); }
  try { initLineChart(); } catch(e) { console.warn('line', e); }
  try { initHeatmap(); } catch(e) { console.warn('heatmap', e); }
}

function initTreeChart() {
  var el = document.getElementById('chart-tree'); if (!el) return;
  var chart = echarts.init(el);
  var branches = {};
  for (var i = 0; i < personnelData.length; i++) {
    var d = personnelData[i].partyBranch || '其他';
    if (!branches[d]) branches[d] = [];
    branches[d].push(personnelData[i].name);
  }
  var sortedKeys = Object.keys(branches).sort(function(a,b) { return branches[b].length - branches[a].length; });
  var othersCount = 0;
  var children = [];
  for (var k = 0; k < sortedKeys.length; k++) {
    var cnt = branches[sortedKeys[k]].length;
    if (k < 12) {
      var shortName = sortedKeys[k].length > 12 ? sortedKeys[k].substring(0,12)+'…' : sortedKeys[k];
      children.push({
        name: shortName + ' (' + cnt + '人)',
        value: cnt,
        _branch: sortedKeys[k],
        itemStyle: { color: COLORS[k % COLORS.length] }
      });
    } else {
      othersCount += cnt;
    }
  }
  if (othersCount > 0) {
    children.push({ name: '其他支部 (' + othersCount + '人)', value: othersCount, itemStyle: { color: '#94a3b8' } });
  }
  var sunburstData = {
    name: '政管学院 (' + personnelData.length + '人)',
    value: personnelData.length,
    itemStyle: { color: '#0b2b5a' },
    children: children
  };
  chart.setOption({
    tooltip: { trigger: 'item', formatter: function(p) { return p.name + (p.value ? '<br/>' + p.value + '人' : ''); } },
    series: [{
      type: 'sunburst',
      data: [sunburstData],
      radius: ['22%', '92%'],
      nodeClick: false,
      sort: 'desc',
      emphasis: { focus: 'ancestor' },
      label: { rotate: 0, fontSize: 9, minAngle: 5 },
      levels: [
        { label: { fontSize: 17, fontWeight: 'bold', color: '#fff' }, itemStyle: { borderWidth: 4, borderColor: '#fff' } },
        { label: { fontSize: 11, fontWeight: 'bold' }, itemStyle: { borderWidth: 2, borderColor: '#fff' } }
      ]
    }]
  });
  // 点击联动：点击支部跳转到基本信息
  bindChartClick(chart, function(params) {
    if (params.data && params.data._branch) return params.data._branch;
    return null;
  });
  window.addEventListener('resize', function() { chart.resize(); });
}

function initSankeyChart() {
  var el = document.getElementById('chart-sankey'); if (!el) return;
  var chart = echarts.init(el);
  var levelGroups = {};
  personnelData.forEach(function(p) {
    var l = (p.positionInfo.level || '其他').trim();
    var cat = l;
    if (/^正高/.test(l) || /^副高/.test(l)) cat = '高级职称';
    else if (/^中级/.test(l) || /^初级/.test(l)) cat = '中初级职称';
    else if (/^正科/.test(l) || /^副科/.test(l) || /^正处/.test(l) || /^副处/.test(l) || /^科员/.test(l)) cat = '管理岗';
    else cat = '其他岗位';
    if (!levelGroups[cat]) levelGroups[cat] = { male: 0, female: 0 };
    var g = p.gender;
    if (g === '男') levelGroups[cat].male++; else levelGroups[cat].female++;
  });
  var nodes = [
    { name: '高级职称' }, { name: '中初级职称' }, { name: '管理岗' }, { name: '其他岗位' },
    { name: '男' }, { name: '女' }
  ];
  var links = [];
  for (var cat in levelGroups) {
    var g = levelGroups[cat];
    if (g.male > 0) links.push({ source: cat, target: '男', value: g.male });
    if (g.female > 0) links.push({ source: cat, target: '女', value: g.female });
  }
  var staffingGroups = {};
  personnelData.forEach(function(p) {
    var s = (p.staffingType.type || '其他').trim();
    var l = (p.positionInfo.level || '其他').trim();
    var cat = l;
    if (/^正高/.test(l) || /^副高/.test(l)) cat = '高级职称';
    else if (/^中级/.test(l) || /^初级/.test(l)) cat = '中初级职称';
    else if (/^正科/.test(l) || /^副科/.test(l) || /^正处/.test(l) || /^副处/.test(l) || /^科员/.test(l)) cat = '管理岗';
    else cat = '其他岗位';
    var key = s + '|' + cat;
    if (!staffingGroups[key]) staffingGroups[key] = 0;
    staffingGroups[key]++;
  });
  var staffingTypes = { '事业编': true, '人事代理': true, '合同工': true, '劳务派遣': true };
  for (var key in staffingGroups) {
    var parts = key.split('|');
    if (staffingTypes[parts[0]]) {
      if (!nodes.find(function(n) { return n.name === parts[0]; })) nodes.unshift({ name: parts[0] });
      links.push({ source: parts[0], target: parts[1], value: staffingGroups[key] });
    }
  }
  chart.setOption({ tooltip: { trigger: 'item', formatter: function(p) { return p.data.source ? p.data.source + ' → ' + p.data.target + ' : ' + p.data.value + '人' : p.name + ' : ' + (p.value||''); } }, series: [{ type: 'sankey', nodeAlign: 'left', layoutIterations: 0, lineStyle: { color: 'gradient', curveness: 0.5 }, data: nodes, links: links, label: { fontSize: 12, fontWeight: 'bold' }, emphasis: { focus: 'adjacency' } }] });
  bindChartClick(chart, function(params) { return params.name; });
  window.addEventListener('resize', function() { chart.resize(); });
}

function initPieTitle() {
  var el = document.getElementById('chart-pie-title'); if (!el) return;
  var chart = echarts.init(el);
  var map = {};
  for (var i = 0; i < personnelData.length; i++) { var t = personnelData[i].professionalTitle.title || '无'; map[t] = (map[t] || 0) + 1; }
  var data = Object.keys(map).map(function(k) { return { name: k, value: map[k] }; });
  chart.setOption({ tooltip: { trigger: 'item' }, series: [{ type: 'pie', radius: ['40%','70%'], itemStyle: { borderRadius: 6 }, label: { fontSize: 10, formatter: '{b}\n{d}%' }, data: data }], color: COLORS });
  bindChartClick(chart, function(params) { return params.name; });
  window.addEventListener('resize', function() { chart.resize(); });
}

function initPieDegree() {
  var el = document.getElementById('chart-pie-degree'); if (!el) return;
  var chart = echarts.init(el);
  var map = {};
  for (var i = 0; i < personnelData.length; i++) { var list = personnelData[i].educationList; for (var j = 0; j < list.length; j++) { var d = list[j].degree || '其他'; map[d] = (map[d] || 0) + 1; } }
  var data = Object.keys(map).map(function(k) { return { name: k, value: map[k] }; });
  chart.setOption({ tooltip: { trigger: 'item' }, series: [{ type: 'pie', radius: ['40%','70%'], roseType: 'area', label: { fontSize: 10 }, data: data }], color: COLORS });
  bindChartClick(chart, function(params) { return params.name; });
  window.addEventListener('resize', function() { chart.resize(); });
}

function initRadarChart() {
  var el = document.getElementById('chart-radar'); if (!el) return;
  var chart = echarts.init(el);
  var sums = [0,0,0,0]; for (var i = 0; i < personnelData.length; i++) { sums[0] += personnelData[i].performanceScore; sums[1] += personnelData[i].teachingScore; sums[2] += personnelData[i].researchScore; sums[3] += personnelData[i].serviceScore; }
  var n = personnelData.length; var avg = [+(sums[0]/n).toFixed(1), +(sums[1]/n).toFixed(1), +(sums[2]/n).toFixed(1), +(sums[3]/n).toFixed(1)];
  var max = Math.max.apply(null, avg) * 1.2;
  chart.setOption({ radar: { indicator: [{name:'综合',max:Math.round(max)},{name:'教学',max:Math.round(max)},{name:'科研',max:Math.round(max)},{name:'服务',max:Math.round(max)}], shape:'circle', center:['50%','50%'], radius:'65%', axisName:{fontSize:10} }, series: [{ type: 'radar', data: [{ value: avg, name: '全校均值', areaStyle: { opacity: 0.3 }, lineStyle: { color:'#2563eb' }, itemStyle: { color:'#2563eb' } }], symbol: 'circle', symbolSize: 5 }] });
  window.addEventListener('resize', function() { chart.resize(); });
}

function initBarMajor() {
  var el = document.getElementById('chart-bar-major'); if (!el) return;
  var chart = echarts.init(el);
  var map = {}; for (var i = 0; i < personnelData.length; i++) { var m = personnelData[i].professionalTitle.major || '其他'; map[m] = (map[m]||0)+1; }
  var keys = Object.keys(map); var pairs = keys.map(function(k){return[k,map[k]]}).sort(function(a,b){return b[1]-a[1]});
  var topN = 12;
  var topPairs = pairs.slice(0, topN);
  var othersCount = 0;
  for (var i = topN; i < pairs.length; i++) { othersCount += pairs[i][1]; }
  if (othersCount > 0) topPairs.push(['其他', othersCount]);
  var xData = topPairs.map(function(e){return e[0]}); var yData = topPairs.map(function(e){return e[1]});
  chart.setOption({ tooltip: { trigger: 'axis' }, xAxis: { type: 'category', data: xData, axisLabel: { fontSize: 10, rotate: 30, interval: 0 } }, yAxis: { type: 'value' }, series: [{ type: 'bar', data: yData, barWidth: '60%', borderRadius: [6,6,0,0], itemStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'#6366f1'},{offset:1,color:'#2563eb'}]) } }], grid: { left: '8%', right: '5%', bottom: '22%', top: '5%' } });
  bindChartClick(chart, function(params) { return params.name; });
  window.addEventListener('resize', function() { chart.resize(); });
}

function initScatterChart() {
  var el = document.getElementById('chart-scatter'); if (!el) return;
  var chart = echarts.init(el);
  var allData = [];
  for (var i = 0; i < personnelData.length; i++) { var birth = personnelData[i].birthdate; var age = birth ? 2025-parseInt(birth.split('-')[0]):40; allData.push([age, personnelData[i].researchScore||0, personnelData[i].name, personnelData[i].id]); }
  function shuffle(arr) { for (var i = arr.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var tmp = arr[i]; arr[i] = arr[j]; arr[j] = tmp; } return arr; }
  var data = shuffle(allData).slice(0, 80);
  chart.setOption({ tooltip: { formatter: function(p){return p.value[2]+'<br/>年龄:'+p.value[0]+'<br/>科研:'+p.value[1];} }, xAxis: { type: 'value', name: '年龄', nameTextStyle: { fontSize: 11 } }, yAxis: { type: 'value', name: '科研得分', nameTextStyle: { fontSize: 11 } }, series: [{ type: 'scatter', data: data, symbolSize: function(v){return 8+v[1]/6;}, itemStyle: { color: '#2563eb', opacity: 0.6 } }], grid: { left: '12%', right: '5%', bottom: '10%', top: '5%' } });
  // 散点图点击：跳转到全景画像
  bindChartClick(chart, function(params) {
    if (params.value && params.value[3]) {
      portraitSelectedPerson = null;
      for (var i = 0; i < personnelData.length; i++) {
        if (personnelData[i].id === params.value[3]) { portraitSelectedPerson = personnelData[i]; break; }
      }
      if (portraitSelectedPerson) {
        renderPage('portrait');
        return null;
      }
    }
    return null;
  });
  window.addEventListener('resize', function() { chart.resize(); });
}

function initWordCloud() {
  var el = document.getElementById('chart-wordcloud'); if (!el) return;
  var chart = echarts.init(el);
  var words = {};
  for (var i = 0; i < personnelData.length; i++) {
    var tr = personnelData[i].trainings;
    for (var j = 0; j < tr.length; j++) {
      var w = (tr[j].name || '').trim();
      if (w) words[w] = (words[w] || 0) + 1;
    }
    var ho = personnelData[i].honors;
    for (var k = 0; k < ho.length; k++) {
      var h = (ho[k].name || '').trim();
      if (h) words[h] = (words[h] || 0) + 3;
    }
  }
  var data = Object.keys(words).map(function(w){return{name:w,value:words[w]}}).sort(function(a,b){return b.value-a.value}).slice(0, 60);
  if (data.length === 0) {
    el.innerHTML = '<p style="text-align:center;padding-top:80px;color:#999;">暂无培训与荣誉数据</p>';
    return;
  }
  try {
    chart.setOption({
      series: [{
        type: 'wordCloud',
        shape: 'circle',
        sizeRange: [12, 32],
        rotationRange: [-30, 30],
        gridSize: 8,
        textStyle: { fontFamily: 'sans-serif', fontWeight: 'bold' },
        data: data
      }]
    });
    bindChartClick(chart, function(params) { return params.name; });
  } catch(e) {
    el.innerHTML = '<p style="text-align:center;padding-top:80px;color:#999;">词云组件加载失败</p>';
  }
  window.addEventListener('resize', function() { chart.resize(); });
}

function initBubbleChart() {
  var el = document.getElementById('chart-bubble'); if (!el) return;
  var chart = echarts.init(el); var data = []; var limit = Math.min(personnelData.length, 40);
  for (var i = 0; i < limit; i++) { data.push([personnelData[i].teachingScore||0, personnelData[i].researchScore||0, personnelData[i].serviceScore||0, personnelData[i].name, personnelData[i].id]); }
  chart.setOption({ tooltip: { formatter: function(p){return p.value[3]+'<br/>教学:'+p.value[0]+' 科研:'+p.value[1]+'<br/>服务:'+p.value[2];} }, xAxis: { type: 'value', name: '教学', splitLine: { lineStyle: { type: 'dashed' } } }, yAxis: { type: 'value', name: '科研', splitLine: { lineStyle: { type: 'dashed' } } }, series: [{ type: 'scatter', data: data, symbolSize: function(v){return 6+v[2]/5;}, itemStyle: { opacity: 0.5, color: '#2563eb' } }], grid: { left: '12%', right: '8%', bottom: '10%', top: '5%' } });
  bindChartClick(chart, function(params) {
    if (params.value && params.value[4]) {
      for (var i = 0; i < personnelData.length; i++) {
        if (personnelData[i].id === params.value[4]) { portraitSelectedPerson = personnelData[i]; break; }
      }
      if (portraitSelectedPerson) { renderPage('portrait'); return null; }
    }
    return null;
  });
  window.addEventListener('resize', function() { chart.resize(); });
}

function initBarParty() {
  var el = document.getElementById('chart-bar-party'); if (!el) return;
  var chart = echarts.init(el); var map = {}; for (var i = 0; i < personnelData.length; i++) { var b = personnelData[i].partyBranch||'未知'; map[b]=(map[b]||0)+1; }
  var keys = Object.keys(map); var pairs = keys.map(function(k){return[k,map[k]]}).sort(function(a,b){return b[1]-a[1]});
  var topN = 10;
  var topPairs = pairs.slice(0, topN);
  var othersCount = 0;
  for (var i = topN; i < pairs.length; i++) { othersCount += pairs[i][1]; }
  if (othersCount > 0) topPairs.push(['其他支部', othersCount]);
  var xData = topPairs.map(function(e){ return e[0].length > 10 ? e[0].substring(0,10)+'...' : e[0]; });
  chart.setOption({ tooltip: { trigger: 'axis', formatter: function(params) { var origName = topPairs[params[0].dataIndex][0]; return origName + ': ' + params[0].value + '人'; } }, xAxis: { type: 'category', data: xData, axisLabel: { fontSize: 10, rotate: 30, interval: 0 } }, yAxis: { type: 'value' }, series: [{ type: 'bar', data: topPairs.map(function(e){return e[1]}), barWidth: '60%', borderRadius: [6,6,0,0], itemStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'#8b5cf6'},{offset:1,color:'#6366f1'}]) } }], grid: { left: '8%', right: '5%', bottom: '22%', top: '5%' } });
  bindChartClick(chart, function(params) {
    var origName = topPairs[params.dataIndex][0];
    return origName !== '其他支部' ? origName : null;
  });
  window.addEventListener('resize', function() { chart.resize(); });
}

function initStackedArea() {
  var el = document.getElementById('chart-area'); if (!el) return;
  var chart = echarts.init(el);
  var years = ['2020','2021','2022','2023','2024'];
  var results = { '优秀': [0,0,0,0,0], '合格': [0,0,0,0,0], '基本合格': [0,0,0,0,0], '不合格': [0,0,0,0,0] };
  for (var i = 0; i < personnelData.length; i++) { var as = personnelData[i].annualAssessments; for (var j = 0; j < as.length; j++) { var idx = years.indexOf(as[j].year); if (idx >= 0 && results[as[j].result]) { results[as[j].result][idx]++; } } }
  var series = ['优秀','合格','基本合格','不合格'].map(function(name) { return { name: name, type: 'line', stack: 'Total', areaStyle: {}, data: results[name] }; });
  chart.setOption({ tooltip: { trigger: 'axis' }, legend: { data: ['优秀','合格','基本合格','不合格'], bottom: 0, textStyle: { fontSize: 10 } }, xAxis: { type: 'category', data: years }, yAxis: { type: 'value' }, series: series, color: ['#2563eb','#10b981','#f59e0b','#ef4444'], grid: { left: '8%', right: '5%', bottom: '12%', top: '5%' } });
  window.addEventListener('resize', function() { chart.resize(); });
}

function initLineChart() {
  var el = document.getElementById('chart-line'); if (!el) return;
  var chart = echarts.init(el);
  var years = getPromoYears();
  if (years.length === 0) years = [2020,2021,2022,2023,2024,2025];
  var staff = personnelData.filter(function(p) { return !p.retireInfo.isRetired; }).slice(0, 8);
  var staffIds = staff.map(function(p){ return p.id; });
  var series = staff.map(function(p) {
    var data = [];
    for (var y = years[0]; y <= years[years.length-1]; y++) {
      var v = 0;
      for (var j = 0; j < p.promotionHistory.length; j++) { if (p.promotionHistory[j].year === y) { v = p.promotionHistory[j].prob * 100; break; } }
      data.push(v);
    }
    return { name: p.name, type: 'line', smooth: true, data: data, _id: p.id };
  });
  chart.setOption({ tooltip: { trigger: 'axis' }, legend: { bottom: 0, textStyle: { fontSize: 10 } }, xAxis: { type: 'category', data: years.map(String) }, yAxis: { type: 'value', name: '概率(%)' }, series: series, color: COLORS, grid: { left: '10%', right: '5%', bottom: '14%', top: '5%' } });
  bindChartClick(chart, function(params) {
    if (params.seriesName) {
      for (var i = 0; i < personnelData.length; i++) {
        if (personnelData[i].name === params.seriesName && !personnelData[i].retireInfo.isRetired) {
          portraitSelectedPerson = personnelData[i];
          renderPage('portrait');
          return null;
        }
      }
    }
    return null;
  });
  window.addEventListener('resize', function() { chart.resize(); });
}

function initHeatmap() {
  var el = document.getElementById('chart-heatmap'); if (!el) return;
  var chart = echarts.init(el);
  var years = getPromoYears();
  if (years.length === 0) years = [2020,2021,2022,2023,2024,2025];

  var active = personnelData.filter(function(p) { return !p.retireInfo.isRetired; });
  function sample(arr, n) {
    if (arr.length <= n) return arr.slice();
    var shuffled = arr.slice();
    for (var i = shuffled.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var tmp = shuffled[i]; shuffled[i] = shuffled[j]; shuffled[j] = tmp;
    }
    return shuffled.slice(0, n);
  }
  var sampled = sample(active, 25);
  var data = [];
  var yData = [];
  var yIds = [];
  for (var i = 0; i < sampled.length; i++) {
    yData.push(sampled[i].name);
    yIds.push(sampled[i].id);
    for (var j = 0; j < years.length; j++) {
      var prob = 0;
      for (var k = 0; k < sampled[i].promotionHistory.length; k++) {
        if (sampled[i].promotionHistory[k].year === years[j]) { prob = sampled[i].promotionHistory[k].prob; break; }
      }
      data.push([j, i, prob]);
    }
  }
  chart.setOption({
    tooltip: { formatter: function(p) { return yData[p.value[1]] + ' (' + years[p.value[0]] + '): ' + (p.value[2]*100).toFixed(0)+'%'; } },
    xAxis: { type: 'category', data: years.map(String), position: 'top', axisLabel: { fontSize: 11 } },
    yAxis: { type: 'category', data: yData, axisLabel: { fontSize: 10 } },
    visualMap: { min: 0, max: 1, calculable: true, orient: 'vertical', right: 5, top: 'center', inRange: { color: ['#e2e8f0','#f59e0b','#6366f1','#2563eb'] } },
    series: [{ type: 'heatmap', data: data, label: { show: true, fontSize: 9, formatter: function(p) { return (p.value[2]*100).toFixed(0); } } }],
    grid: { left: '6%', right: '12%', bottom: '3%', top: '8%' }
  });
  bindChartClick(chart, function(params) {
    if (params.value && yIds[params.value[1]]) {
      var id = yIds[params.value[1]];
      for (var i = 0; i < personnelData.length; i++) {
        if (personnelData[i].id === id) { portraitSelectedPerson = personnelData[i]; break; }
      }
      if (portraitSelectedPerson) { renderPage('portrait'); return null; }
    }
    return null;
  });
  window.addEventListener('resize', function() { chart.resize(); });
}

function renderPerformanceStats() {
  var sorted = personnelData.slice().sort(function(a,b) { return b.performanceScore - a.performanceScore; });
  var total = personnelData.length;
  var excellent = 0, good = 0, fair = 0;
  for (var i = 0; i < total; i++) {
    var s = sorted[i].performanceScore;
    if (s >= 85) excellent++; else if (s >= 70) good++; else fair++;
  }
  var html = '<div class="stats-grid">'+
    '<div class="stat-card"><div class="stat-icon" style="background:#2563eb;"><i class="fas fa-star"></i></div><div><div class="stat-value">'+(sorted[0]?sorted[0].performanceScore.toFixed(1):'—')+'</div><div class="stat-label">最高得分 ('+(sorted[0]?sorted[0].name:'')+')</div></div></div>'+
    '<div class="stat-card"><div class="stat-icon" style="background:#10b981;"><i class="fas fa-medal"></i></div><div><div class="stat-value">'+excellent+'</div><div class="stat-label">优秀 (≥85分)</div></div></div>'+
    '<div class="stat-card"><div class="stat-icon" style="background:#f59e0b;"><i class="fas fa-thumbs-up"></i></div><div><div class="stat-value">'+good+'</div><div class="stat-label">良好 (70~84分)</div></div></div>'+
    '<div class="stat-card"><div class="stat-icon" style="background:#ef4444;"><i class="fas fa-chart-simple"></i></div><div><div class="stat-value">'+fair+'</div><div class="stat-label">待提升 (<70分)</div></div></div>'+
  '</div>';
  var top20 = sorted.slice(0, 20);
  html += '<div class="card"><div class="card-header"><h3><i class="fas fa-trophy"></i> 绩效 Top 20</h3></div><div class="table-responsive"><table><thead><tr><th>排名</th><th>姓名</th><th>综合得分</th><th>教学</th><th>科研</th><th>服务</th></tr></thead><tbody>';
  top20.forEach(function(p, idx) {
    html += '<tr><td><strong>#'+(idx+1)+'</strong></td><td><span class="clickable-name" data-id="'+p.id+'">'+p.name+'</span></td><td style="font-weight:700;color:#2563eb;">'+p.performanceScore+'</td><td>'+p.teachingScore+'</td><td>'+p.researchScore+'</td><td>'+p.serviceScore+'</td></tr>';
  });
  html += '</tbody></table></div></div>';
  return html;
}

function renderPromotionPrediction() {
  var activeStaff = personnelData.filter(function(p){return !p.retireInfo.isRetired;});
  var promoYears = getPromoYears();
  var latestYear = promoYears.length > 0 ? promoYears[promoYears.length - 1] : 2025;
  var candidates = activeStaff.map(function(p) {
    var prob = 0;
    for (var i = 0; i < p.promotionHistory.length; i++) {
      if (p.promotionHistory[i].year === latestYear) { prob = p.promotionHistory[i].prob; break; }
    }
    return { name: p.name, id: p.id, prob: prob };
  }).sort(function(a,b) { return b.prob - a.prob; });
  var highCount = candidates.filter(function(c){return c.prob>=0.8;}).length;
  var midCount = candidates.filter(function(c){return c.prob>=0.5&&c.prob<0.8;}).length;
  var lowCount = candidates.filter(function(c){return c.prob>0&&c.prob<0.5;}).length;
  var zeroCount = candidates.filter(function(c){return c.prob===0;}).length;
  var html = '<div class="stats-grid">'+
    '<div class="stat-card"><div class="stat-icon" style="background:#2563eb;"><i class="fas fa-arrow-trend-up"></i></div><div><div class="stat-value">'+highCount+'</div><div class="stat-label">高概率晋升 (≥80%)</div></div></div>'+
    '<div class="stat-card"><div class="stat-icon" style="background:#6366f1;"><i class="fas fa-chart-line"></i></div><div><div class="stat-value">'+midCount+'</div><div class="stat-label">中等概率 (50~79%)</div></div></div>'+
    '<div class="stat-card"><div class="stat-icon" style="background:#f59e0b;"><i class="fas fa-circle-question"></i></div><div><div class="stat-value">'+lowCount+'</div><div class="stat-label">较低概率 (<50%)</div></div></div>'+
    '<div class="stat-card"><div class="stat-icon" style="background:#94a3b8;"><i class="fas fa-circle-xmark"></i></div><div><div class="stat-value">'+zeroCount+'</div><div class="stat-label">暂无概率数据</div></div></div>'+
  '</div>';
  var top15 = candidates.filter(function(c){return c.prob>0;}).slice(0, 15);
  if (top15.length > 0) {
    var maxP = top15[0].prob;
    html += '<div class="card"><div class="card-header"><h3><i class="fas fa-ranking-star"></i> '+latestYear+'年 晋升预测 Top 15</h3></div><div class="table-responsive"><table><thead><tr><th>姓名</th><th>晋升概率</th><th>进度条</th></tr></thead><tbody>';
    top15.forEach(function(c) {
      var pct = (c.prob*100).toFixed(0);
      var barColor = c.prob>=0.8?'#2563eb':(c.prob>=0.6?'#6366f1':'#f59e0b');
      html += '<tr><td><span class="clickable-name" data-id="'+c.id+'">'+c.name+'</span></td><td style="font-weight:700;">'+pct+'%</td><td><div style="background:#e2e8f0;border-radius:10px;height:18px;overflow:hidden;"><div style="background:'+barColor+';width:'+pct+'%;height:100%;border-radius:10px;transition:width 0.6s ease;"></div></div></td></tr>';
    });
    html += '</tbody></table></div></div>';
  } else {
    html += '<div class="card"><div class="card-header"><h3><i class="fas fa-ranking-star"></i> 晋升预测</h3></div><p style="color:#94a3b8;text-align:center;padding:40px 0;">暂无晋升概率数据</p></div>';
  }
  return html;
}

function showDetailModal(personId) {
  var p = null; for (var i = 0; i < personnelData.length; i++) { if (personnelData[i].id === personId) { p = personnelData[i]; break; } } if (!p) return;
  var html = '<div class="modal-header"><h2><i class="fas fa-user"></i> '+p.name+' 全景档案</h2><button class="close-btn" onclick="window.closeModal()">&times;</button></div><div class="detail-grid"><div class="detail-item"><span class="label">工号</span><span class="value">'+p.id+'</span></div><div class="detail-item"><span class="label">性别 / 民族</span><span class="value">'+p.gender+' / '+p.nation+'</span></div><div class="detail-item"><span class="label">出生日期</span><span class="value">'+p.birthdate+'</span></div><div class="detail-item"><span class="label">籍贯</span><span class="value">'+p.nativePlace+'</span></div><div class="detail-item"><span class="label">政治面貌</span><span class="value">'+(p.politicalStatus||'群众')+'</span></div><div class="detail-item"><span class="label">入党时间</span><span class="value">'+(p.partyJoinDate||'-')+'</span></div><div class="detail-item"><span class="label">编制类型</span><span class="value">'+p.staffingType.type+' ('+p.staffingType.entryDate+')</span></div><div class="detail-item"><span class="label">岗位</span><span class="value">'+p.positionInfo.title+' '+p.positionInfo.level+'</span></div><div class="detail-item"><span class="label">职称</span><span class="value">'+(p.professionalTitle.title||'-')+'</span></div><div class="detail-item"><span class="label">离退休</span><span class="value">'+(p.retireInfo.isRetired?'是':'否')+'</span></div><div class="detail-item"><span class="label">联系方式</span><span class="value">'+p.contact.phone+' / '+p.contact.email+'</span></div></div><hr style="margin:20px 0;opacity:0.3;"><h4>学习经历</h4>'+(p.educationList.map(function(e){return '<p>'+e.degree+' - '+e.school+' '+e.major+' ('+e.start+'~'+e.end+')</p>';}).join('')||'<p>无</p>')+'<h4>工作经历</h4>'+(p.workList.map(function(w){return '<p>'+w.company+' '+w.position+' ('+w.start+'~'+w.end+')</p>';}).join('')||'<p>无</p>')+'<h4>家庭成员</h4>'+(p.familyMembers.map(function(f){return '<p>'+f.name+' ('+f.relation+') '+f.workplace+'</p>';}).join('')||'<p>无</p>')+'<h4>年度考核</h4>'+(p.annualAssessments.map(function(a){return '<span style="margin-right:12px;">'+a.year+':'+a.result+'</span>';}).join('')||'无')+'<h4>荣誉称号</h4>'+(p.honors.map(function(h){return '<p>'+h.name+' ('+h.grantor+','+h.date+')</p>';}).join('')||'<p>无</p>');
  document.getElementById('modalContent').innerHTML = html; document.getElementById('modalOverlay').style.display = 'flex';
}

// ============ 全景画像功能 ============

function renderPortraitSearch() {
  var html = '<div class="portrait-header">';
  html += '<div class="portrait-header-content">';
  html += '<h2><i class="fas fa-id-card"></i> 教职工全景画像</h2>';
  html += '<p>搜索教师姓名或工号，全方位查看教师个人信息与专属分析图表</p>';
  html += '<div class="portrait-search-wrap">';
  html += '<div class="portrait-search-box">';
  html += '<i class="fas fa-search"></i>';
  html += '<input type="text" id="portraitSearchInput" placeholder="输入教师姓名或工号进行搜索..." autocomplete="off">';
  html += '</div>';
  html += '<div class="portrait-suggestions" id="portraitSuggestions" style="display:none;"></div>';
  html += '</div>';
  html += '</div></div>';
  return html;
}

function renderPortraitPageHTML() {
  var p = portraitSelectedPerson;
  if (!p) { return renderPortraitSearch() + '<div class="card"><p style="text-align:center;color:#94a3b8;padding:40px 0;">请在上方搜索框中输入教师姓名或工号</p></div>'; }

  var n = personnelData.length;
  var sums = [0,0,0,0];
  for (var i = 0; i < n; i++) {
    sums[0] += personnelData[i].performanceScore;
    sums[1] += personnelData[i].teachingScore;
    sums[2] += personnelData[i].researchScore;
    sums[3] += personnelData[i].serviceScore;
  }
  var avg = [+(sums[0]/n).toFixed(1), +(sums[1]/n).toFixed(1), +(sums[2]/n).toFixed(1), +(sums[3]/n).toFixed(1)];

  var sorted = personnelData.slice().sort(function(a,b) { return b.performanceScore - a.performanceScore; });
  var rank = 0;
  for (var r = 0; r < sorted.length; r++) { if (sorted[r].id === p.id) { rank = r + 1; break; } }

  var html = renderPortraitSearch();

  html += '<div class="stats-grid">'+
    '<div class="stat-card"><div class="stat-icon" style="background:#1E3A8A;"><i class="fas fa-hashtag"></i></div><div><div class="stat-value">'+p.id+'</div><div class="stat-label">工号</div></div></div>'+
    '<div class="stat-card"><div class="stat-icon" style="background:#3B82F6;"><i class="fas fa-ranking-star"></i></div><div><div class="stat-value">第 '+(rank||'—')+' 名</div><div class="stat-label">综合得分排名（共'+n+'人）</div></div></div>'+
    '<div class="stat-card"><div class="stat-icon" style="background:#10B981;"><i class="fas fa-chart-line"></i></div><div><div class="stat-value">'+p.performanceScore.toFixed(1)+'</div><div class="stat-label">综合绩效得分</div></div></div>'+
    '<div class="stat-card"><div class="stat-icon" style="background:#6366F1;"><i class="fas fa-percent"></i></div><div><div class="stat-value">'+(p.promotionProbability*100).toFixed(0)+'%</div><div class="stat-label">晋升概率</div></div></div>'+
    '<div class="stat-card"><div class="stat-icon" style="background:#F59E0B;"><i class="fas fa-calendar-check"></i></div><div><div class="stat-value">'+(p.annualAssessments.filter(function(a){return a.result==='优秀';}).length)+'次</div><div class="stat-label">考核优秀次数</div></div></div>'+
  '</div>';

  html += section('基本信息', p.name+' · '+p.id, 'fa-address-card', '#1E3A8A',
    '<div class="card"><div class="detail-grid">'+
    '<div class="detail-item"><span class="label">姓名</span><span class="value" style="font-size:1.1rem;color:#1E3A8A;">'+p.name+'</span></div>'+
    '<div class="detail-item"><span class="label">工号</span><span class="value">'+p.id+'</span></div>'+
    '<div class="detail-item"><span class="label">性别 / 民族</span><span class="value">'+p.gender+' / '+p.nation+'</span></div>'+
    '<div class="detail-item"><span class="label">出生日期</span><span class="value">'+p.birthdate+'</span></div>'+
    '<div class="detail-item"><span class="label">籍贯</span><span class="value">'+p.nativePlace+'</span></div>'+
    '<div class="detail-item"><span class="label">身份证号</span><span class="value">'+p.idCard+'</span></div>'+
    '<div class="detail-item"><span class="label">政治面貌</span><span class="value">'+(p.politicalStatus||'群众')+'</span></div>'+
    '<div class="detail-item"><span class="label">入党时间</span><span class="value">'+(p.partyJoinDate||'-')+'</span></div>'+
    '<div class="detail-item"><span class="label">所属党支部</span><span class="value">'+(p.partyBranch||'-')+'</span></div>'+
    '<div class="detail-item"><span class="label">编制类型</span><span class="value">'+p.staffingType.type+' ('+p.staffingType.entryDate+')</span></div>'+
    '<div class="detail-item"><span class="label">岗位</span><span class="value">'+p.positionInfo.title+' · '+p.positionInfo.level+'</span></div>'+
    '<div class="detail-item"><span class="label">聘用时间</span><span class="value">'+(p.positionInfo.hireDate||'-')+'</span></div>'+
    '<div class="detail-item"><span class="label">职称</span><span class="value">'+(p.professionalTitle.title||'-')+' · '+(p.professionalTitle.major||'')+'</span></div>'+
    '<div class="detail-item"><span class="label">职称获取时间</span><span class="value">'+(p.professionalTitle.obtainDate||'-')+'</span></div>'+
    '<div class="detail-item"><span class="label">党政职务</span><span class="value">'+(p.partyPosition.title||'无')+'</span></div>'+
    '<div class="detail-item"><span class="label">离退休状态</span><span class="value">'+(p.retireInfo.isRetired?'是':'否')+'</span></div>'+
    '<div class="detail-item"><span class="label">联系方式</span><span class="value">'+p.contact.phone+' / '+p.contact.email+'</span></div>'+
    '<div class="detail-item"><span class="label">办公电话</span><span class="value">'+(p.contact.officePhone||'-')+'</span></div>'+
    '</div></div>');

  html += section('绩效分析', '个人绩效雷达图与各项得分对比', 'fa-chart-pie', '#10B981',
    '<div class="dash-grid-3">'+
    cc('个人 vs 全校均值 雷达图', 'fa-crosshairs', 'chart-portrait-radar')+
    cc('绩效四维柱状图', 'fa-chart-bar', 'chart-portrait-bar')+
    cc('绩效得分仪表盘', 'fa-gauge-high', 'chart-portrait-gauge')+
    '</div>');

  html += section('年度考核', '历年考核结果与变化趋势', 'fa-clipboard-check', '#6366F1',
    '<div class="dash-grid">'+
    cc('历年考核结果环形图', 'fa-chart-pie', 'chart-portrait-assess')+
    cc('历年考核时间线', 'fa-timeline', 'chart-portrait-timeline')+
    '</div>');

  html += section('晋升与发展', '历年晋升概率变化趋势', 'fa-arrow-trend-up', '#F59E0B',
    '<div class="dash-grid">'+
    cc('晋升概率折线图', 'fa-chart-line', 'chart-portrait-promo')+
    cc('累计荣誉/培训统计', 'fa-award', 'chart-portrait-honor')+
    '</div>');

  html += section('详细记录', '学习经历、工作经历、家庭成员、年度考核、荣誉、培训、社会兼职', 'fa-list-check', '#EF4444',
    '<div class="card"><div class="card-header"><h3><i class="fas fa-graduation-cap"></i> 学习经历 ('+(p.educationList.length)+'条)</h3></div>'+
    (p.educationList.length > 0 ? '<div class="table-responsive"><table><thead><tr><th>学历</th><th>毕业院校</th><th>专业</th><th>入学时间</th><th>毕业时间</th></tr></thead><tbody>'+
    p.educationList.map(function(e){ return '<tr><td>'+e.degree+'</td><td>'+e.school+'</td><td>'+e.major+'</td><td>'+e.start+'</td><td>'+e.end+'</td></tr>'; }).join('')+
    '</tbody></table></div>' : '<p style="color:#94a3b8;text-align:center;padding:20px;">暂无数据</p>')+
    '</div>'+

    '<div class="card"><div class="card-header"><h3><i class="fas fa-briefcase"></i> 工作经历 ('+(p.workList.length)+'条)</h3></div>'+
    (p.workList.length > 0 ? '<div class="table-responsive"><table><thead><tr><th>单位</th><th>职务</th><th>开始时间</th><th>结束时间</th></tr></thead><tbody>'+
    p.workList.map(function(w){ return '<tr><td>'+w.company+'</td><td>'+w.position+'</td><td>'+w.start+'</td><td>'+w.end+'</td></tr>'; }).join('')+
    '</tbody></table></div>' : '<p style="color:#94a3b8;text-align:center;padding:20px;">暂无数据</p>')+
    '</div>'+

    '<div class="card"><div class="card-header"><h3><i class="fas fa-people-roof"></i> 家庭成员 ('+(p.familyMembers.length)+'人)</h3></div>'+
    (p.familyMembers.length > 0 ? '<div class="table-responsive"><table><thead><tr><th>姓名</th><th>关系</th><th>工作单位</th><th>联系方式</th></tr></thead><tbody>'+
    p.familyMembers.map(function(f){ return '<tr><td>'+f.name+'</td><td>'+f.relation+'</td><td>'+f.workplace+'</td><td>'+f.phone+'</td></tr>'; }).join('')+
    '</tbody></table></div>' : '<p style="color:#94a3b8;text-align:center;padding:20px;">暂无数据</p>')+
    '</div>'+

    '<div class="card"><div class="card-header"><h3><i class="fas fa-clipboard-check"></i> 年度考核</h3></div>'+
    (p.annualAssessments.length > 0 ? '<div class="table-responsive"><table><thead><tr><th>年度</th><th>考核结果</th></tr></thead><tbody>'+
    p.annualAssessments.map(function(a){ var color=a.result==='优秀'?'#10B981':(a.result==='合格'?'#2563EB':(a.result==='基本合格'?'#F59E0B':'#EF4444')); return '<tr><td>'+a.year+'</td><td><span style="font-weight:700;color:'+color+';">'+a.result+'</span></td></tr>'; }).join('')+
    '</tbody></table></div>' : '<p style="color:#94a3b8;text-align:center;padding:20px;">暂无数据</p>')+
    '</div>'+

    '<div class="card"><div class="card-header"><h3><i class="fas fa-medal"></i> 荣誉称号 ('+(p.honors.length)+'项)</h3></div>'+
    (p.honors.length > 0 ? '<div class="table-responsive"><table><thead><tr><th>称号名称</th><th>授予单位</th><th>授予日期</th></tr></thead><tbody>'+
    p.honors.map(function(h){ return '<tr><td>'+h.name+'</td><td>'+h.grantor+'</td><td>'+h.date+'</td></tr>'; }).join('')+
    '</tbody></table></div>' : '<p style="color:#94a3b8;text-align:center;padding:20px;">暂无数据</p>')+
    '</div>'+

    '<div class="card"><div class="card-header"><h3><i class="fas fa-chalkboard"></i> 培训记录 ('+(p.trainings.length)+'次)</h3></div>'+
    (p.trainings.length > 0 ? '<div class="table-responsive"><table><thead><tr><th>培训名称</th><th>时间</th><th>地点</th></tr></thead><tbody>'+
    p.trainings.map(function(t){ return '<tr><td>'+t.name+'</td><td>'+t.date+'</td><td>'+t.location+'</td></tr>'; }).join('')+
    '</tbody></table></div>' : '<p style="color:#94a3b8;text-align:center;padding:20px;">暂无数据</p>')+
    '</div>'+

    '<div class="card"><div class="card-header"><h3><i class="fas fa-handshake"></i> 社会兼职 ('+(p.socialPositions.length)+'项)</h3></div>'+
    (p.socialPositions.length > 0 ? '<div class="table-responsive"><table><thead><tr><th>组织名称</th><th>职务</th></tr></thead><tbody>'+
    p.socialPositions.map(function(s){ return '<tr><td>'+s.org+'</td><td>'+s.title+'</td></tr>'; }).join('')+
    '</tbody></table></div>' : '<p style="color:#94a3b8;text-align:center;padding:20px;">暂无数据</p>')+
    '</div>');

  return html;
}

function initPortraitCharts() {
  try { initPortraitRadar(); } catch(e) { console.warn('portrait-radar', e); }
  try { initPortraitBar(); } catch(e) { console.warn('portrait-bar', e); }
  try { initPortraitGauge(); } catch(e) { console.warn('portrait-gauge', e); }
  try { initPortraitAssess(); } catch(e) { console.warn('portrait-assess', e); }
  try { initPortraitTimeline(); } catch(e) { console.warn('portrait-timeline', e); }
  try { initPortraitPromo(); } catch(e) { console.warn('portrait-promo', e); }
  try { initPortraitHonor(); } catch(e) { console.warn('portrait-honor', e); }
}

function initPortraitRadar() {
  var el = document.getElementById('chart-portrait-radar'); if (!el) return;
  var p = portraitSelectedPerson; if (!p) return;
  var chart = echarts.init(el);
  var sums = [0,0,0,0];
  for (var i = 0; i < personnelData.length; i++) {
    sums[0] += personnelData[i].performanceScore;
    sums[1] += personnelData[i].teachingScore;
    sums[2] += personnelData[i].researchScore;
    sums[3] += personnelData[i].serviceScore;
  }
  var n = personnelData.length;
  var avgVals = [+(sums[0]/n).toFixed(1), +(sums[1]/n).toFixed(1), +(sums[2]/n).toFixed(1), +(sums[3]/n).toFixed(1)];
  var personVals = [p.performanceScore, p.teachingScore, p.researchScore, p.serviceScore];
  var allVals = avgVals.concat(personVals);
  var maxVal = Math.max.apply(null, allVals) * 1.2;
  chart.setOption({
    legend: { data: ['全校均值', p.name], bottom: 0, textStyle: { fontSize: 11 } },
    radar: {
      indicator: [
        { name: '综合', max: Math.round(maxVal) },
        { name: '教学', max: Math.round(maxVal) },
        { name: '科研', max: Math.round(maxVal) },
        { name: '服务', max: Math.round(maxVal) }
      ],
      shape: 'circle', center: ['50%', '48%'], radius: '60%'
    },
    series: [{
      type: 'radar',
      data: [
        { value: avgVals, name: '全校均值', areaStyle: { opacity: 0.15 }, lineStyle: { color: '#94a3b8', type: 'dashed' }, itemStyle: { color: '#94a3b8' } },
        { value: personVals, name: p.name, areaStyle: { opacity: 0.35 }, lineStyle: { color: '#2563eb', width: 2 }, itemStyle: { color: '#2563eb' } }
      ],
      symbol: 'circle', symbolSize: 6
    }]
  });
  window.addEventListener('resize', function() { chart.resize(); });
}

function initPortraitBar() {
  var el = document.getElementById('chart-portrait-bar'); if (!el) return;
  var p = portraitSelectedPerson; if (!p) return;
  var chart = echarts.init(el);
  var categories = ['综合得分', '教学得分', '科研得分', '服务得分'];
  var personData = [p.performanceScore, p.teachingScore, p.researchScore, p.serviceScore];
  var sums = [0,0,0,0];
  for (var i = 0; i < personnelData.length; i++) {
    sums[0] += personnelData[i].performanceScore;
    sums[1] += personnelData[i].teachingScore;
    sums[2] += personnelData[i].researchScore;
    sums[3] += personnelData[i].serviceScore;
  }
  var n = personnelData.length;
  var avgData = [+(sums[0]/n).toFixed(1), +(sums[1]/n).toFixed(1), +(sums[2]/n).toFixed(1), +(sums[3]/n).toFixed(1)];
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: [p.name, '全校均值'], bottom: 0, textStyle: { fontSize: 11 } },
    xAxis: { type: 'category', data: categories, axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', name: '得分' },
    series: [
      { name: p.name, type: 'bar', data: personData, barWidth: '35%', itemStyle: { borderRadius: [6,6,0,0], color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'#2563eb'},{offset:1,color:'#1E3A8A'}]) } },
      { name: '全校均值', type: 'bar', data: avgData, barWidth: '35%', itemStyle: { borderRadius: [6,6,0,0], color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'#94a3b8'},{offset:1,color:'#cbd5e1'}]) } }
    ],
    grid: { left: '10%', right: '5%', bottom: '14%', top: '5%' }
  });
  window.addEventListener('resize', function() { chart.resize(); });
}

function initPortraitGauge() {
  var el = document.getElementById('chart-portrait-gauge'); if (!el) return;
  var p = portraitSelectedPerson; if (!p) return;
  var chart = echarts.init(el);
  var score = p.performanceScore;
  var level = score >= 85 ? '优秀' : (score >= 70 ? '良好' : '待提升');
  var color = score >= 85 ? '#10B981' : (score >= 70 ? '#2563EB' : '#EF4444');
  chart.setOption({
    series: [{
      type: 'gauge', startAngle: 210, endAngle: -30, center: ['50%', '55%'], radius: '85%', min: 0, max: 100,
      axisLine: { lineStyle: { width: 18, color: [[0.7, '#2563EB'], [0.85, '#10B981'], [1, '#93C5FD']] } },
      pointer: { length: '65%', width: 6, itemStyle: { color: color } },
      axisTick: { distance: -18, length: 5, lineStyle: { width: 1, color: '#999' } },
      splitLine: { distance: -20, length: 14, lineStyle: { width: 2, color: '#999' } },
      axisLabel: { color: '#464646', fontSize: 10, distance: 25 },
      detail: { valueAnimation: true, formatter: function(v) { return v.toFixed(1) + '\n' + level; }, color: color, fontSize: 18, offsetCenter: [0, '65%'] },
      data: [{ value: score, name: '综合绩效' }]
    }]
  });
  window.addEventListener('resize', function() { chart.resize(); });
}

function initPortraitAssess() {
  var el = document.getElementById('chart-portrait-assess'); if (!el) return;
  var p = portraitSelectedPerson; if (!p) return;
  var chart = echarts.init(el);
  var counts = { '优秀': 0, '合格': 0, '基本合格': 0, '不合格': 0 };
  for (var i = 0; i < p.annualAssessments.length; i++) {
    var r = p.annualAssessments[i].result;
    if (counts[r] !== undefined) counts[r]++;
  }
  if (p.annualAssessments.length === 0) {
    el.innerHTML = '<p style="text-align:center;padding-top:80px;color:#999;">暂无考核数据</p>';
    return;
  }
  var data = Object.keys(counts).filter(function(k){return counts[k]>0;}).map(function(k) {
    return { name: k, value: counts[k] };
  });
  chart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c}次 ({d}%)' },
    series: [{ type: 'pie', radius: ['45%', '75%'], center: ['50%', '50%'], itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 3 }, label: { fontSize: 11, formatter: '{b}\n{d}%' }, data: data }],
    color: ['#10B981', '#2563EB', '#F59E0B', '#EF4444']
  });
  window.addEventListener('resize', function() { chart.resize(); });
}

function initPortraitTimeline() {
  var el = document.getElementById('chart-portrait-timeline'); if (!el) return;
  var p = portraitSelectedPerson; if (!p) return;
  var chart = echarts.init(el);
  var sorted = p.annualAssessments.slice().sort(function(a,b) { return a.year.localeCompare(b.year); });
  if (sorted.length === 0) {
    el.innerHTML = '<p style="text-align:center;padding-top:80px;color:#999;">暂无考核数据</p>';
    return;
  }
  var xData = sorted.map(function(a){ return a.year; });
  var yData = sorted.map(function(a) {
    if (a.result === '优秀') return 4;
    if (a.result === '合格') return 3;
    if (a.result === '基本合格') return 2;
    return 1;
  });
  var yLabels = { 1: '不合格', 2: '基本合格', 3: '合格', 4: '优秀' };
  chart.setOption({
    tooltip: { trigger: 'axis', formatter: function(params) { var v = params[0].value; return params[0].axisValue + '年: ' + (yLabels[v] || '未知'); } },
    xAxis: { type: 'category', data: xData, axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', min: 0, max: 5, interval: 1, axisLabel: { formatter: function(v) { return yLabels[v] || ''; } } },
    series: [{
      type: 'line', data: yData, smooth: true, symbol: 'circle', symbolSize: 10,
      lineStyle: { color: '#2563eb', width: 3 },
      itemStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'#2563eb'},{offset:1,color:'#10B981'}]) },
      areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(37,99,235,0.3)'},{offset:1,color:'rgba(16,185,129,0.1)'}]) },
      markLine: { silent: true, lineStyle: { color: '#94a3b8', type: 'dashed' }, data: [{ yAxis: 3, label: { formatter: '合格线' } }] }
    }],
    grid: { left: '8%', right: '5%', bottom: '8%', top: '8%' }
  });
  window.addEventListener('resize', function() { chart.resize(); });
}

function initPortraitPromo() {
  var el = document.getElementById('chart-portrait-promo'); if (!el) return;
  var p = portraitSelectedPerson; if (!p) return;
  var chart = echarts.init(el);
  var promoData = p.promotionHistory;
  if (!promoData || promoData.length === 0) {
    el.innerHTML = '<p style="text-align:center;padding-top:80px;color:#999;">暂无晋升数据</p>';
    return;
  }
  var xData = promoData.map(function(ph){ return ph.year; });
  var yData = promoData.map(function(ph){ return +(ph.prob * 100).toFixed(0); });
  chart.setOption({
    tooltip: { trigger: 'axis', formatter: function(params) { return params[0].axisValue + '年: ' + params[0].value + '%'; } },
    xAxis: { type: 'category', data: xData, axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', name: '概率(%)', max: 100 },
    series: [{ type: 'line', data: yData, smooth: true, symbol: 'circle', symbolSize: 8, lineStyle: { color: '#F59E0B', width: 3 }, itemStyle: { color: '#F59E0B' }, areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(245,158,11,0.4)'},{offset:1,color:'rgba(245,158,11,0)'}]) } }],
    grid: { left: '10%', right: '5%', bottom: '8%', top: '8%' }
  });
  window.addEventListener('resize', function() { chart.resize(); });
}

function initPortraitHonor() {
  var el = document.getElementById('chart-portrait-honor'); if (!el) return;
  var p = portraitSelectedPerson; if (!p) return;
  var chart = echarts.init(el);
  var honorCount = p.honors.length;
  var trainingCount = p.trainings.length;
  var socialCount = p.socialPositions.length;
  if (honorCount + trainingCount + socialCount === 0) {
    el.innerHTML = '<p style="text-align:center;padding-top:80px;color:#999;">暂无荣誉/培训/兼职数据</p>';
    return;
  }
  chart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: ['荣誉称号', '培训记录', '社会兼职'], axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', name: '数量', minInterval: 1 },
    series: [{
      type: 'bar', data: [
        { value: honorCount, itemStyle: { color: '#F59E0B' } },
        { value: trainingCount, itemStyle: { color: '#2563EB' } },
        { value: socialCount, itemStyle: { color: '#10B981' } }
      ], barWidth: '50%', borderRadius: [8,8,0,0], label: { show: true, position: 'top', fontSize: 12, fontWeight: 'bold' }
    }],
    grid: { left: '10%', right: '5%', bottom: '8%', top: '12%' }
  });
  window.addEventListener('resize', function() { chart.resize(); });
}

// ============ 全景画像 - 搜索绑定 ============

function bindPortraitSearch() {
  var input = document.getElementById('portraitSearchInput');
  var suggestions = document.getElementById('portraitSuggestions');
  if (!input || !suggestions) return;

  input.addEventListener('input', function() {
    var keyword = this.value.trim().toLowerCase();
    if (keyword === '') { suggestions.style.display = 'none'; return; }
    var matches = personnelData.filter(function(p) {
      return p.name.toLowerCase().includes(keyword) || p.id.toLowerCase().includes(keyword);
    }).slice(0, 10);
    if (matches.length === 0) {
      suggestions.innerHTML = '<div class="portrait-suggestion-item no-match">未找到匹配的教师</div>';
      suggestions.style.display = 'block';
      return;
    }
    var html = '';
    matches.forEach(function(p) {
      html += '<div class="portrait-suggestion-item" data-id="'+p.id+'">'+
        '<span class="sug-name">'+p.name+'</span>'+
        '<span class="sug-id">'+p.id+'</span>'+
        '<span class="sug-dept">'+(p.partyBranch||'')+'</span>'+
      '</div>';
    });
    suggestions.innerHTML = html;
    suggestions.style.display = 'block';
    suggestions.querySelectorAll('.portrait-suggestion-item').forEach(function(item) {
      item.addEventListener('click', function() {
        var id = this.getAttribute('data-id');
        if (id) { selectPortraitPerson(id); input.value = ''; suggestions.style.display = 'none'; }
      });
    });
  });

  input.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
      var keyword = this.value.trim().toLowerCase();
      if (keyword === '') return;
      var match = personnelData.filter(function(p) {
        return p.name.toLowerCase().includes(keyword) || p.id.toLowerCase().includes(keyword);
      })[0];
      if (match) { selectPortraitPerson(match.id); this.value = ''; suggestions.style.display = 'none'; }
    }
  });

  document.addEventListener('click', function(e) {
    if (!e.target.closest('.portrait-search-wrap')) { suggestions.style.display = 'none'; }
  });
}

function selectPortraitPerson(id) {
  for (var i = 0; i < personnelData.length; i++) {
    if (personnelData[i].id === id) { portraitSelectedPerson = personnelData[i]; break; }
  }
  if (!portraitSelectedPerson) return;
  refreshPortraitView();
}

function refreshPortraitView() {
  var container = document.getElementById('contentArea');
  container.innerHTML = renderBreadcrumb('portrait') + renderPortraitPageHTML();
  bindPortraitSearch();
  setTimeout(function() { initPortraitCharts(); }, 200);
}

// ============ 页面路由 ============

function renderPage(pageKey, parentKey) {
  parentKey = parentKey || null;
  currentPage = pageKey;
  currentParent = parentKey;
  
  // 重置分页和排序状态
  tableSortState = { col: -1, dir: 1 };
  tablePageState = { page: 1, pageSize: 15 };
  
  updatePageTitle(pageKey);
  setActiveMenu(pageKey, parentKey);
  
  var container = document.getElementById('contentArea');
  var breadcrumbHtml = renderBreadcrumb(pageKey, parentKey);
  var html = '';
  
  switch (pageKey) {
    case 'dashboard':
      if (personnelData.length === 0) { html = breadcrumbHtml + '<div class="card"><p>数据加载中...</p></div>'; break; }
      html = breadcrumbHtml + renderDashboardHTML(); toggleSearchBox(false);
      container.innerHTML = html;
      setTimeout(function() { initAllCharts(); }, 200);
      return;
    case 'portrait':
      toggleSearchBox(false);
      portraitSelectedPerson = null;
      container.innerHTML = renderBreadcrumb('portrait') + renderPortraitPageHTML();
      bindPortraitSearch();
      return;
    case 'basic': html = renderBasicTable(); toggleSearchBox(true); break;
    case 'political': html = renderSimpleTable('political', ['工号','姓名','政治面貌','入党时间','所属党支部'], function(p) { return [p.id, p.name, p.politicalStatus||'群众', p.partyJoinDate||'-', p.partyBranch||'-']; }); toggleSearchBox(true); break;
    case 'education': html = renderListTable('educationList', ['工号','姓名','学历','毕业院校','专业','入学时间','毕业时间'], function(p,i) { return [p.id,p.name,i.degree,i.school,i.major,i.start,i.end]; }); toggleSearchBox(true); break;
    case 'work': html = renderListTable('workList', ['工号','姓名','单位','职务','开始时间','结束时间'], function(p,i) { return [p.id,p.name,i.company,i.position,i.start,i.end]; }); toggleSearchBox(true); break;
    case 'family': html = renderListTable('familyMembers', ['工号','姓名','成员姓名','关系','工作单位','联系方式'], function(p,i) { return [p.id,p.name,i.name,i.relation,i.workplace,i.phone]; }); toggleSearchBox(true); break;
    case 'assessment': html = renderListTable('annualAssessments', ['工号','姓名','年度','考核结果'], function(p,i) { return [p.id,p.name,i.year,i.result]; }); toggleSearchBox(true); break;
    case 'transfer': html = renderListTable('internalTransfers', ['工号','姓名','原部门','新部门','调动时间'], function(p,i) { return [p.id,p.name,i.fromDept,i.toDept,i.date]; }); toggleSearchBox(true); break;
    case 'retire': html = renderSimpleTable('retire', ['工号','姓名','是否离退休','退休时间'], function(p) { return [p.id,p.name,p.retireInfo.isRetired?'是':'否',p.retireInfo.retireDate||'-']; }); toggleSearchBox(true); break;
    case 'staffing': html = renderSimpleTable('staffing', ['工号','姓名','编制类型','入编时间'], function(p) { return [p.id,p.name,p.staffingType.type,p.staffingType.entryDate]; }); toggleSearchBox(true); break;
    case 'positionInfo': html = renderSimpleTable('positionInfo', ['工号','姓名','岗位名称','岗位等级','聘用时间'], function(p) { return [p.id,p.name,p.positionInfo.title,p.positionInfo.level,p.positionInfo.hireDate]; }); toggleSearchBox(true); break;
    case 'partyPos': html = renderSimpleTable('partyPos', ['工号','姓名','党政职务','任职部门','任职时间'], function(p) { return [p.id,p.name,p.partyPosition.title||'-',p.partyPosition.dept||'-',p.partyPosition.startDate||'-']; }); toggleSearchBox(true); break;
    case 'professional': html = renderSimpleTable('professional', ['工号','姓名','职称','专业','获取时间'], function(p) { return [p.id,p.name,p.professionalTitle.title||'-',p.professionalTitle.major||'-',p.professionalTitle.obtainDate||'-']; }); toggleSearchBox(true); break;
    case 'skill': html = renderSimpleTable('skill', ['工号','姓名','技能等级','工种','证书'], function(p) { return [p.id,p.name,p.skillLevel.level||'-',p.skillLevel.trade||'-',p.skillLevel.cert||'-']; }); toggleSearchBox(true); break;
    case 'dual': html = renderSimpleTable('dual', ['工号','姓名','双聘单位','岗位','开始时间'], function(p) { return [p.id,p.name,p.dualEmployment.unit||'无',p.dualEmployment.position||'-',p.dualEmployment.startDate||'-']; }); toggleSearchBox(true); break;
    case 'abroad': html = renderSimpleTable('abroad', ['工号','姓名','国家','访学单位','时间'], function(p) { return [p.id,p.name,p.abroadInfo.country||'-',p.abroadInfo.institution||'-',p.abroadInfo.period||'-']; }); toggleSearchBox(true); break;
    case 'teacherCert': html = renderSimpleTable('teacherCert', ['工号','姓名','资格种类','学科','颁发时间'], function(p) { return [p.id,p.name,p.teacherCert.type||'-',p.teacherCert.subject||'-',p.teacherCert.issueDate||'-']; }); toggleSearchBox(true); break;
    case 'training': html = renderListTable('trainings', ['工号','姓名','培训名称','时间','地点'], function(p,i) { return [p.id,p.name,i.name,i.date,i.location]; }); toggleSearchBox(true); break;
    case 'honor': html = renderListTable('honors', ['工号','姓名','称号','授予单位','时间'], function(p,i) { return [p.id,p.name,i.name,i.grantor,i.date]; }); toggleSearchBox(true); break;
    case 'social': html = renderListTable('socialPositions', ['工号','姓名','兼职组织','职务'], function(p,i) { return [p.id,p.name,i.org,i.title]; }); toggleSearchBox(true); break;
    case 'contact': html = renderSimpleTable('contact', ['工号','姓名','手机','邮箱','办公电话','地址'], function(p) { return [p.id,p.name,p.contact.phone,p.contact.email,p.contact.officePhone||'-',p.contact.address||'-']; }); toggleSearchBox(true); break;
    case 'performance': html = renderPerformanceStats(); toggleSearchBox(false); break;
    case 'promotion': html = renderPromotionPrediction(); toggleSearchBox(false); break;
    default: html = breadcrumbHtml + '<div class="card">页面开发中...</div>'; toggleSearchBox(false);
  }
  
  container.innerHTML = breadcrumbHtml + html;
  
  // 绑定可点击名称
  container.querySelectorAll('.clickable-name').forEach(function(el) {
    el.addEventListener('click', function() { showDetailModal(this.getAttribute('data-id')); });
  });
  
  // 绑定表头排序
  container.querySelectorAll('.sortable-th').forEach(function(th) {
    th.addEventListener('click', function() {
      var col = parseInt(this.getAttribute('data-col'));
      if (tableSortState.col === col) {
        tableSortState.dir = tableSortState.dir * -1;
      } else {
        tableSortState.col = col;
        tableSortState.dir = 1;
      }
      tablePageState.page = 1;
      renderPage(currentPage, currentParent);
    });
  });
  
  // 绑定分页按钮
  container.querySelectorAll('.page-btn:not(.disabled)').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var page = parseInt(this.getAttribute('data-page'));
      if (!isNaN(page)) {
        tablePageState.page = page;
        renderPage(currentPage, currentParent);
      }
    });
  });
  
  // 绑定每页条数
  var pageSizeSelect = container.querySelector('#pageSizeSelect');
  if (pageSizeSelect) {
    pageSizeSelect.addEventListener('change', function() {
      tablePageState.pageSize = parseInt(this.value);
      tablePageState.page = 1;
      renderPage(currentPage, currentParent);
    });
  }
  
  // 绑定面包屑导航
  container.querySelectorAll('.breadcrumb-link').forEach(function(el) {
    el.addEventListener('click', function() {
      var page = this.getAttribute('data-page');
      if (page) renderPage(page);
    });
  });
}

window.closeModal = function() { document.getElementById('modalOverlay').style.display = 'none'; };
window.showDetailById = function(id) { if(id) showDetailModal(id); };

window.exportTable = function() {
  // 尝试从卡片中提取表格数据
  var card = document.querySelector('.card');
  if (!card) {
    var toast = document.getElementById('toast');
    toast.textContent = '未找到可导出的表格数据';
    toast.style.display = 'block';
    setTimeout(function() { toast.style.display = 'none'; }, 2000);
    return;
  }

  // 尝试获取存储的导出数据
  var exportScript = card.querySelector('.export-data');
  if (exportScript) {
    try {
      var exportInfo = JSON.parse(exportScript.textContent);
      realExportTable(exportInfo.columns, exportInfo.rows);
      return;
    } catch(e) { /* fallback */ }
  }

  // Fallback: 从当前页面 DOM 表格提取
  var table = card.querySelector('table');
  if (!table) {
    var toast = document.getElementById('toast');
    toast.textContent = '当前页面无可导出表格';
    toast.style.display = 'block';
    setTimeout(function() { toast.style.display = 'none'; }, 2000);
    return;
  }

  var columns = [];
  var rows = [];
  var headers = table.querySelectorAll('thead th');
  headers.forEach(function(th, idx) {
    if (idx < headers.length - 1 || th.textContent.trim() !== '操作') {
      columns.push(th.textContent.replace(/[\s\ufeff]+/g, '').trim() || ('列' + (idx + 1)));
    }
  });

  var trs = table.querySelectorAll('tbody tr');
  trs.forEach(function(tr) {
    var row = [];
    var tds = tr.querySelectorAll('td');
    tds.forEach(function(td) {
      row.push(td.textContent.trim());
    });
    if (row.length > columns.length) row = row.slice(0, columns.length);
    rows.push(row);
  });

  realExportTable(columns, rows);
};

function bindEvents() {
  document.getElementById('sidebarNav').addEventListener('click', function(e) {
    var target = e.target.closest('.nav-item');
    if (!target) return;
    var page = target.getAttribute('data-page');
    var parent = target.getAttribute('data-parent');
    if (target.classList.contains('parent-menu')) {
      toggleSubmenu(target.getAttribute('data-parent'));
      return;
    }
    if (page) {
      renderPage(page, parent || null);
      if (parent) document.getElementById('sub_' + parent).classList.add('open');
    }
  });
  
  document.getElementById('modalOverlay').addEventListener('click', function(e) {
    if (e.target === this) window.closeModal();
  });
  
  // 初始化全局模糊搜索
  bindGlobalSearch();
}

function init() {
  renderSidebar();
  bindEvents();
  document.getElementById('contentArea').innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:300px;flex-direction:column;gap:16px;"><i class="fas fa-spinner fa-spin" style="font-size:3rem;color:#2563eb;"></i><p style="color:#64748b;font-size:1rem;">正在读取 Excel 数据...</p></div>';
  loadPersonnelData(function() { renderPage('dashboard'); });
}
init();