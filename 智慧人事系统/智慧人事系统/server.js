var http = require('http');
var fs = require('fs');
var path = require('path');
var XLSX = require('xlsx');

var PORT = 3002;
var ROOT = __dirname;
var EXCEL_PATH = path.join(__dirname, '人事平台虚拟数据.xlsx');

var MIME = { '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'application/javascript; charset=utf-8', '.json': 'application/json; charset=utf-8', '.png': 'image/png', '.ico': 'image/x-icon' };

function readSheet(wb, name) { var s = wb.Sheets[name]; return s ? XLSX.utils.sheet_to_json(s, { defval: '' }) : []; }
function parseDate(val) { if (!val) return ''; if (typeof val === 'number') { var d = XLSX.SSF.parse_date_code(val); if (d) return d.y + '-' + String(d.m).padStart(2,'0') + '-' + String(d.d).padStart(2,'0'); } return String(val).trim(); }

function buildPersonnelData() {
  try {
    var wb = XLSX.readFile(EXCEL_PATH);
    var mainData = readSheet(wb, '教职工主表');
    var education = readSheet(wb, '学习经历');
    var work = readSheet(wb, '工作经历');
    var family = readSheet(wb, '家庭成员');
    var assessments = readSheet(wb, '年度考核');
    var transfers = readSheet(wb, '校内调动');
    var staffing = readSheet(wb, '编制记录');
    var positions = readSheet(wb, '岗位信息');
    var partyPos = readSheet(wb, '党政职务');
    var profTitles = readSheet(wb, '专业技术职务');
    var skills = readSheet(wb, '工勤技能');
    var dual = readSheet(wb, '双聘信息');
    var abroad = readSheet(wb, '公派出国');
    var teacherCerts = readSheet(wb, '教师资格证');
    var trainings = readSheet(wb, '培训记录');
    var honors = readSheet(wb, '荣誉称号');
    var social = readSheet(wb, '社会兼职');
    var contacts = readSheet(wb, '联系方式');
    var perfScores = readSheet(wb, '绩效得分');
    var promoHistory = readSheet(wb, '晋升历史');

    function groupBy(arr) { var m = {}; arr.forEach(function(r) { var id = r['工号']; if (!id) return; if (!m[id]) m[id] = []; m[id].push(r); }); return m; }
    function singleMap(arr) { var m = {}; arr.forEach(function(r) { var id = r['工号']; if (id && !m[id]) m[id] = r; }); return m; }

    var eduMap = groupBy(education); var workMap = groupBy(work); var familyMap = groupBy(family);
    var assessMap = groupBy(assessments); var transferMap = groupBy(transfers); var trainingMap = groupBy(trainings);
    var honorMap = groupBy(honors); var socialMap = groupBy(social); var perfMap = groupBy(perfScores); var promoMap = groupBy(promoHistory);
    var staffingMap = singleMap(staffing); var positionMap = singleMap(positions); var partyPosMap = singleMap(partyPos);
    var profTitleMap = singleMap(profTitles); var skillMap = singleMap(skills); var dualMap = singleMap(dual);
    var abroadMap = singleMap(abroad); var teacherCertMap = singleMap(teacherCerts); var contactMap = singleMap(contacts);

    var personnel = mainData.map(function(row) {
      var id = row['工号'], name = row['姓名'];

      var educationList = (eduMap[id] || []).map(function(e) { return { degree: e['学历/学位']||'', school: e['毕业院校']||'', major: e['专业']||'', start: parseDate(e['入学日期']), end: parseDate(e['毕业日期']) }; });
      var workList = (workMap[id] || []).map(function(w) { return { company: w['单位']||'', position: w['职务']||'', start: parseDate(w['开始日期']), end: parseDate(w['结束日期']) }; });
      var familyMembers = (familyMap[id] || []).map(function(f) { return { name: f['成员姓名']||'', relation: f['关系']||'', workplace: f['工作单位']||'', phone: f['联系方式']||'' }; });
      var annualAssessments = (assessMap[id] || []).map(function(a) { return { year: String(a['年度']||''), result: a['考核结果']||'' }; });
      var internalTransfers = (transferMap[id] || []).map(function(t) { return { fromDept: t['原部门']||'', toDept: t['新部门']||'', date: parseDate(t['调动日期']) }; });
      var retireStatus = row['离退休状态'] || '';
      var isRetired = retireStatus === '退休' || retireStatus === '离休';
      var s = staffingMap[id] || {}; var staffingType = { type: s['编制类型']||'', entryDate: parseDate(s['入编日期']) };
      var pos = positionMap[id] || {}; var positionInfo = { title: pos['岗位名称']||'', level: pos['岗位等级']||'', hireDate: parseDate(pos['聘用日期']) };
      var pp = partyPosMap[id] || {}; var partyPosition = { title: pp['职务名称']||'', dept: pp['任职部门']||'', startDate: parseDate(pp['任职开始日期']) };
      var pt = profTitleMap[id] || {}; var professionalTitle = { title: pt['职称']||'', major: pt['专业']||'', obtainDate: parseDate(pt['获得日期']) };
      var sk = skillMap[id] || {}; var skillLevel = { level: sk['技能等级']||'', trade: sk['工种']||'', cert: sk['证书编号']||'' };
      var du = dualMap[id] || {}; var dualEmployment = { unit: du['双聘单位']||'', position: du['岗位']||'', startDate: parseDate(du['开始日期']) };
      var ab = abroadMap[id] || {}; var abroadInfo = { country: ab['国家']||'', institution: ab['访学单位']||'', period: ab['起止时间']||'' };
      var tc = teacherCertMap[id] || {}; var teacherCert = { type: tc['资格种类']||'', subject: tc['学科']||'', issueDate: parseDate(tc['颁发日期']) };
      var trainingList = (trainingMap[id] || []).map(function(t) { return { name: t['培训名称']||'', date: parseDate(t['时间']), location: t['地点']||'' }; });
      var honorList = (honorMap[id] || []).map(function(h) { return { name: h['称号名称']||'', grantor: h['授予单位']||'', date: parseDate(h['授予日期']) }; });
      var socialList = (socialMap[id] || []).map(function(sp) { return { org: sp['组织名称']||'', title: sp['职务']||'' }; });
      var ct = contactMap[id] || {}; var contact = { phone: ct['手机']||'', email: ct['邮箱']||'', officePhone: ct['办公电话']||'', address: ct['地址']||'' };
      var perfRecords = (perfMap[id] || []).sort(function(a,b) { return String(b['年份']).localeCompare(String(a['年份'])); });
      var latestPerf = perfRecords[0] || {};
      var performanceScore = parseFloat(latestPerf['总分']) || 0;
      var teachingScore = parseFloat(latestPerf['教学得分']) || 0;
      var researchScore = parseFloat(latestPerf['科研得分']) || 0;
      var serviceScore = parseFloat(latestPerf['服务得分']) || 0;

      // ===== FIXED: Promotion history =====
      var promoRecords = promoMap[id] || [];
      var promoByYear = {};
      for (var i = 0; i < promoRecords.length; i++) {
        var year = parseInt(promoRecords[i]['年份']);
        if (isNaN(year)) continue;
        var str = promoRecords[i]['晋升概率（实际/预测）'] || '';
        if (str.indexOf('实际') >= 0) {
          promoByYear[year] = 1.0;
        } else if (str.indexOf('预测') >= 0) {
          var prob = parseFloat(str.replace('%', '')) / 100;
          if (!isNaN(prob)) promoByYear[year] = prob;
        }
      }
      var promoKeys = Object.keys(promoByYear).map(Number).sort(function(a,b) { return a-b; });
      var promotionHistory = [];
      if (promoKeys.length > 0) {
        var minY = promoKeys[0], maxY = promoKeys[promoKeys.length-1];
        for (var y = minY; y <= maxY; y++) {
          promotionHistory.push({ year: y, prob: promoByYear[y] !== undefined ? promoByYear[y] : 0 });
        }
      } else {
        for (var y = 2020; y <= 2025; y++) { promotionHistory.push({ year: y, prob: 0 }); }
      }
      var promotionProbability = promotionHistory.length > 0 ? promotionHistory[promotionHistory.length-1].prob : 0;

      return {
        id: id, name: name, gender: row['性别']||'', birthdate: parseDate(row['出生日期']), nation: row['民族']||'', nativePlace: row['籍贯']||'', idCard: row['身份证号']||'',
        politicalStatus: row['政治面貌']||'群众', partyJoinDate: parseDate(row['入党时间']), partyBranch: row['所属党支部']||'',
        educationList: educationList, workList: workList, familyMembers: familyMembers,
        annualAssessments: annualAssessments, internalTransfers: internalTransfers,
        retireInfo: { isRetired: isRetired, retireDate: parseDate(row['退休日期']) },
        staffingType: staffingType, positionInfo: positionInfo, partyPosition: partyPosition,
        professionalTitle: professionalTitle, skillLevel: skillLevel, dualEmployment: dualEmployment,
        abroadInfo: abroadInfo, teacherCert: teacherCert,
        trainings: trainingList, honors: honorList, socialPositions: socialList, contact: contact,
        performanceScore: performanceScore, teachingScore: teachingScore, researchScore: researchScore, serviceScore: serviceScore,
        promotionProbability: promotionProbability, promotionHistory: promotionHistory
      };
    });
    return personnel;
  } catch (e) { console.error('Error:', e.message); return null; }
}

var server = http.createServer(function(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  if (req.method === 'OPTIONS') { res.writeHead(204); res.end(); return; }
  if (req.url === '/api/personnel') {
    var data = buildPersonnelData();
    if (!data) { res.writeHead(500, { 'Content-Type': 'application/json; charset=utf-8' }); res.end(JSON.stringify({ error: 'Failed' })); return; }
    res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' }); res.end(JSON.stringify(data)); return;
  }
  var filePath = req.url === '/' ? '/index.html' : req.url;
  filePath = path.join(ROOT, filePath);
  if (!filePath.startsWith(ROOT)) { res.writeHead(403); res.end('Forbidden'); return; }
  var ext = path.extname(filePath);
  var ct = MIME[ext] || 'application/octet-stream';
  fs.readFile(filePath, function(err, content) {
    if (err) { res.writeHead(err.code === 'ENOENT' ? 404 : 500); res.end(err.code === 'ENOENT' ? 'Not Found' : 'Error'); return; }
    res.writeHead(200, { 'Content-Type': ct }); res.end(content);
  });
});

server.on('error', function(err) { if (err.code === 'EADDRINUSE') { console.error('端口 '+PORT+' 被占用'); process.exit(1); } else throw err; });
server.listen(PORT, function() {
  console.log('服务器已启动: http://localhost:' + PORT);
  console.log('数据来源: ' + EXCEL_PATH);
});