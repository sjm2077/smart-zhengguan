// 数据加载器 - 从后端 API 获取 Excel 数据
// 启动方式: node server.js，然后打开 http://localhost:3000

let personnelData = [];
let personnelById = {};
let dataLoaded = false;
let dataLoading = false;
let loadCallbacks = [];

/**
 * 标准化单条人员数据，确保前端所有深层字段访问都有安全默认值（B-07 空值处理）
 * 后端仅需保证顶层字段存在，嵌套对象/数组缺失时在此统一兜底。
 */
function normalizePerson(p) {
  if (!p || typeof p !== 'object') return p;

  function asObj(v) { return (v && typeof v === 'object') ? v : {}; }
  function asArray(v) { return Array.isArray(v) ? v : []; }
  function asStr(v, fallback) { return (v === null || v === undefined || v === '') ? (fallback || '') : v; }
  function asNum(v) { var n = parseFloat(v); return isNaN(n) ? 0 : n; }

  p.id = asStr(p.id, '');
  p.name = asStr(p.name, '');

  p.retireInfo = asObj(p.retireInfo);
  p.retireInfo.isRetired = !!p.retireInfo.isRetired;
  p.retireInfo.retireDate = asStr(p.retireInfo.retireDate, '');

  p.staffingType = asObj(p.staffingType);
  p.staffingType.type = asStr(p.staffingType.type, '');
  p.staffingType.entryDate = asStr(p.staffingType.entryDate, '');

  p.positionInfo = asObj(p.positionInfo);
  p.positionInfo.title = asStr(p.positionInfo.title, '');
  p.positionInfo.level = asStr(p.positionInfo.level, '');
  p.positionInfo.hireDate = asStr(p.positionInfo.hireDate, '');

  p.partyPosition = asObj(p.partyPosition);
  p.partyPosition.title = asStr(p.partyPosition.title, '');
  p.partyPosition.dept = asStr(p.partyPosition.dept, '');
  p.partyPosition.startDate = asStr(p.partyPosition.startDate, '');

  p.professionalTitle = asObj(p.professionalTitle);
  p.professionalTitle.title = asStr(p.professionalTitle.title, '');
  p.professionalTitle.major = asStr(p.professionalTitle.major, '');
  p.professionalTitle.obtainDate = asStr(p.professionalTitle.obtainDate, '');

  p.skillLevel = asObj(p.skillLevel);
  p.skillLevel.level = asStr(p.skillLevel.level, '');
  p.skillLevel.trade = asStr(p.skillLevel.trade, '');
  p.skillLevel.cert = asStr(p.skillLevel.cert, '');

  p.dualEmployment = asObj(p.dualEmployment);
  p.dualEmployment.unit = asStr(p.dualEmployment.unit, '');
  p.dualEmployment.position = asStr(p.dualEmployment.position, '');
  p.dualEmployment.startDate = asStr(p.dualEmployment.startDate, '');

  p.abroadInfo = asObj(p.abroadInfo);
  p.abroadInfo.country = asStr(p.abroadInfo.country, '');
  p.abroadInfo.institution = asStr(p.abroadInfo.institution, '');
  p.abroadInfo.period = asStr(p.abroadInfo.period, '');

  p.teacherCert = asObj(p.teacherCert);
  p.teacherCert.type = asStr(p.teacherCert.type, '');
  p.teacherCert.subject = asStr(p.teacherCert.subject, '');
  p.teacherCert.issueDate = asStr(p.teacherCert.issueDate, '');

  p.contact = asObj(p.contact);
  p.contact.phone = asStr(p.contact.phone, '');
  p.contact.email = asStr(p.contact.email, '');
  p.contact.officePhone = asStr(p.contact.officePhone, '');
  p.contact.address = asStr(p.contact.address, '');

  p.educationList = asArray(p.educationList);
  p.workList = asArray(p.workList);
  p.familyMembers = asArray(p.familyMembers);
  p.annualAssessments = asArray(p.annualAssessments);
  p.internalTransfers = asArray(p.internalTransfers);
  p.trainings = asArray(p.trainings);
  p.honors = asArray(p.honors);
  p.socialPositions = asArray(p.socialPositions);
  p.promotionHistory = asArray(p.promotionHistory);

  p.performanceScore = asNum(p.performanceScore);
  p.teachingScore = asNum(p.teachingScore);
  p.researchScore = asNum(p.researchScore);
  p.serviceScore = asNum(p.serviceScore);
  p.promotionProbability = asNum(p.promotionProbability);

  return p;
}

/**
 * 标准化全部数据并建立 id -> person 索引
 */
function indexPersonnelData(data) {
  personnelData = (data || []).map(normalizePerson);
  personnelById = {};
  personnelData.forEach(function(p) {
    if (p.id) personnelById[p.id] = p;
  });
  return personnelData;
}

/**
 * 按 id 快速查找人员（O(1)，供各处 ID 关联使用）
 */
function findPersonById(id) {
  return personnelById[id] || null;
}

/**
 * 从服务器 API 加载数据
 * @param {Function} callback - 数据加载完成后的回调
 */
function loadPersonnelData(callback) {
  if (dataLoaded) {
    if (callback) callback(personnelData);
    return;
  }

  if (callback) loadCallbacks.push(callback);

  if (dataLoading) return;
  dataLoading = true;

  fetch('/api/personnel')
    .then(response => {
      if (!response.ok) throw new Error('HTTP ' + response.status);
      return response.json();
    })
    .then(data => {
      indexPersonnelData(data);
      dataLoaded = true;
      dataLoading = false;
      console.log(`已加载 ${personnelData.length} 名教职工数据`);
      loadCallbacks.forEach(cb => cb(personnelData));
      loadCallbacks = [];
    })
    .catch(err => {
      dataLoading = false;
      console.error('数据加载失败:', err.message);
      // 如果 API 不可用，尝试使用内嵌数据回退
      if (typeof personnelDataFallback !== 'undefined') {
        console.warn('使用内嵌回退数据');
        indexPersonnelData(personnelDataFallback);
        dataLoaded = true;
        loadCallbacks.forEach(cb => cb(personnelData));
        loadCallbacks = [];
      }
    });
}