// ╔══════════════════════════════════════════════════════════╗
// ║     Excel 终端查询工具 - 像数据库一样查 Excel            ║
// ╚══════════════════════════════════════════════════════════╝
//
// 用法（在终端运行）：
//   node read-excel.js                                    → 显示帮助
//   node read-excel.js list                               → 列出所有工作表
//   node read-excel.js show 教职工主表                     → 显示前10条
//   node read-excel.js show 教职工主表 20                  → 显示前20条
//   node read-excel.js fields 教职工主表                   → 查看字段名
//   node read-excel.js find 教职工主表 姓名=张             → 模糊搜索
//   node read-excel.js find 教职工主表 姓名=王 性别=女     → 多条件AND
//   node read-excel.js count 教职工主表 性别=男            → 统计数量
//   node read-excel.js stats 教职工主表 性别               → 分组统计
//   node read-excel.js join 教职工主表 学习经历 工号        → 关联查询
//   node read-excel.js sql "SELECT * FROM 教职工主表 WHERE 姓名='张' LIMIT 5"
//
var XLSX = require('xlsx');
var path = require('path');
var EXCEL_PATH = path.join(__dirname, '人事平台虚拟数据.xlsx');

// ========== 读 Excel ==========
function loadExcel() {
  try {
    return XLSX.readFile(EXCEL_PATH);
  } catch (e) {
    console.error('❌ 读取Excel失败: ' + e.message);
    console.error('  路径: ' + EXCEL_PATH);
    process.exit(1);
  }
}

function readSheet(wb, name) {
  if (!wb.Sheets[name]) {
    console.error('❌ 工作表不存在: ' + name);
    console.error('  可用: ' + wb.SheetNames.join(', '));
    process.exit(1);
  }
  return XLSX.utils.sheet_to_json(wb.Sheets[name], { defval: '' });
}

// ========== 条件解析 ==========
function parseCondition(arg) {
  var parts = arg.split('==');
  if (parts.length === 2) return { field: parts[0], value: parts[1], fuzzy: false };
  parts = arg.split('=');
  if (parts.length === 2) return { field: parts[0], value: parts[1], fuzzy: true };
  return null;
}

// ========== 查询引擎 ==========
function queryData(data, conditions) {
  return data.filter(function(row) {
    return conditions.every(function(c) {
      var v = String(row[c.field] || '').toLowerCase();
      var s = c.value.toLowerCase();
      return c.fuzzy ? v.indexOf(s) >= 0 : v === s;
    });
  });
}

function getFields(data) {
  return data.length === 0 ? [] : Object.keys(data[0]);
}

function groupBy(data, field) {
  var m = {};
  data.forEach(function(r) {
    var k = r[field] || '(空)';
    m[k] = (m[k] || 0) + 1;
  });
  return m;
}

// ========== 格式化表格输出 ==========
var PRIORITY = ['工号', '姓名', '性别', '出生日期', '民族', '学历/学位', '毕业院校', '专业', '政治面貌', '身份证号'];

function pad(s, w) {
  var cn = 0;
  for (var i = 0; i < s.length; i++) { if (s.charCodeAt(i) > 127) cn++; }
  var p = w - s.length - cn;
  if (p <= 0) p = 1;
  return s + ' '.repeat(p);
}

function printTable(data, maxRows) {
  if (data.length === 0) { console.log('  (无匹配)'); return; }
  var show = maxRows ? data.slice(0, maxRows) : data;
  var fields = getFields(show);
  var cols = [];
  PRIORITY.forEach(function(f) { if (fields.indexOf(f) >= 0) cols.push(f); });
  if (cols.length === 0) cols = fields.slice(0, 6);
  var hdr = cols.map(function(f) { return pad(f, 14); }).join(' | ');
  console.log('  ' + hdr);
  console.log('  ' + '-'.repeat(hdr.length));
  show.forEach(function(r) {
    var line = cols.map(function(f) { return pad(String(r[f] || ''), 14); }).join(' | ');
    console.log('  ' + line);
  });
  if (maxRows && data.length > maxRows)
    console.log('  ... 共 ' + data.length + ' 条，仅显示前 ' + maxRows + ' 条');
  else
    console.log('  — 共 ' + data.length + ' 条');
}

// ========== SQL 解析 ==========
function parseSQL(sql) {
  sql = sql.trim();
  var fm = sql.match(/SELECT\s+\*\s+FROM\s+(.+?)(\s+WHERE|\s+LIMIT|\s+ORDER|\s*$)/i);
  if (!fm) return null;
  var sheet = fm[1].trim(), conds = [], limit = null;
  var wm = sql.match(/WHERE\s+(.+?)(\s+LIMIT|\s+ORDER|\s*$)/i);
  if (wm) {
    wm[1].split(/\s+AND\s+/i).forEach(function(p) {
      var m = p.match(/(\S+)\s*=\s*'([^']*)'/);
      if (m) conds.push({ field: m[1], value: m[2], fuzzy: true });
    });
  }
  var lm = sql.match(/LIMIT\s+(\d+)/i);
  if (lm) limit = parseInt(lm[1]);
  return { sheet: sheet, conds: conds, limit: limit };
}

// ========== 帮助 ==========
function help() {
  console.log(`
╔══════════════════════════════════════════════════════╗
║     Excel 数据库查询工具 - 命令参考                   ║
╚══════════════════════════════════════════════════════╝

  list                    列出所有工作表及其行数
  schema                  显示完整数据库表结构 (DDL)
  show <表> [条数]        显示工作表记录
  fields <表>             查看所有字段名
  find <表> <条件>...     多条件模糊查询 (AND)
  count <表> [条件]       统计记录数量
  stats <表> <字段>       按字段分组统计 (GROUP BY)
  join <表1> <表2> [字段]  关联两张表 (JOIN, 默认按工号)
  sql "<语句>"            类SQL查询

条件写法: 字段=值 → 模糊  字段==值 → 精确
示例:
  node read-excel.js find 教职工主表 姓名=张
  node read-excel.js find 教职工主表 姓名=王 性别=女
  node read-excel.js stats 教职工主表 政治面貌
  node read-excel.js sql "SELECT * FROM 教职工主表 WHERE 姓名='张' LIMIT 5"
`);
}

// ========== 主入口 ==========
function main() {
  var cmd = (process.argv[2] || '').toLowerCase();
  var wb = loadExcel();

  switch (cmd) {

    case '':
    case 'help':
      help();
      break;

    // ---------- schema ----------
    case 'schema':
      console.log('\n📋 完整数据库表结构 (DDL) - ' + EXCEL_PATH);
      console.log('═'.repeat(55));
      wb.SheetNames.forEach(function(name) {
        var d = XLSX.utils.sheet_to_json(wb.Sheets[name], { defval: '' });
        var fl = d.length > 0 ? Object.keys(d[0]) : [];
        var pk = fl[0] || '';  // 第一列即主键
        console.log('\n┌── ' + name + ' (' + d.length + '行, ' + fl.length + '列)');
        console.log('│  PRIMARY KEY: ' + pk);
        fl.forEach(function(c) { console.log('│  ├ ' + c); });
        console.log('└──');
      });
      break;

    // ---------- list ----------
    case 'list':
      console.log('\n📊 工作表列表 (' + EXCEL_PATH + ')');
      console.log('─'.repeat(45));
      wb.SheetNames.forEach(function(name) {
        var n = XLSX.utils.sheet_to_json(wb.Sheets[name], { defval: '' }).length;
        console.log('  📄 ' + pad(name, 22) + ' → ' + n + ' 行');
      });
      console.log('─'.repeat(45));
      break;

    // ---------- show ----------
    case 'show':
      var s = process.argv[3]; if (!s) { console.error('用法: node read-excel.js show <表名> [条数]'); process.exit(1); }
      var data = readSheet(wb, s);
      var limit = parseInt(process.argv[4]) || 10;
      console.log('\n📋 ' + s + ' (前 ' + limit + ' / 共 ' + data.length + ' 条)');
      printTable(data, limit);
      break;

    // ---------- fields ----------
    case 'fields':
      var s = process.argv[3]; if (!s) { console.error('用法: node read-excel.js fields <表名>'); process.exit(1); }
      var data = readSheet(wb, s);
      var fl = getFields(data);
      console.log('\n📋 ' + s + ' 字段 (' + fl.length + ' 个):');
      console.log('─'.repeat(35));
      fl.forEach(function(f, i) { console.log('  ' + (i + 1) + '. ' + f); });
      break;

    // ---------- find ----------
    case 'find':
      var s = process.argv[3]; if (!s) { console.error('用法: node read-excel.js find <表> <条件>...'); process.exit(1); }
      var conds = [];
      for (var i = 4; i < process.argv.length; i++) { var c = parseCondition(process.argv[i]); if (c) conds.push(c); }
      if (conds.length === 0) { console.error('至少一个条件，格式: 字段=值'); process.exit(1); }
      var data = readSheet(wb, s);
      var result = queryData(data, conds);
      var str = conds.map(function(c) { return c.field + (c.fuzzy ? '~=' : '==') + c.value; }).join(' AND ');
      console.log('\n🔍 ' + s + ' WHERE ' + str);
      printTable(result, 20);
      break;

    // ---------- count ----------
    case 'count':
      var s = process.argv[3]; if (!s) { console.error('用法: node read-excel.js count <表> [条件]'); process.exit(1); }
      var conds = [];
      for (var i = 4; i < process.argv.length; i++) { var c = parseCondition(process.argv[i]); if (c) conds.push(c); }
      var data = readSheet(wb, s);
      var result = conds.length > 0 ? queryData(data, conds) : data;
      console.log('\n📊 ' + s + ': ' + result.length + ' 条 (总 ' + data.length + ' 条)');
      break;

    // ---------- stats ----------
    case 'stats':
      var s = process.argv[3], f = process.argv[4];
      if (!s || !f) { console.error('用法: node read-excel.js stats <表> <字段>'); process.exit(1); }
      var data = readSheet(wb, s);
      var g = groupBy(data, f);
      console.log('\n📊 ' + s + ' 按 [' + f + '] 分组:');
      console.log('─'.repeat(45));
      var maxV = Math.max.apply(null, Object.values(g));
      Object.keys(g).sort(function(a, b) { return g[b] - g[a]; }).forEach(function(k) {
        var bar = '█'.repeat(Math.round(g[k] / maxV * 25));
        console.log('  ' + pad(k, 18) + ' ' + String(g[k]).padStart(4) + '  ' + bar);
      });
      console.log('─'.repeat(45) + '\n  总计: ' + data.length + ' 条');
      break;

    // ---------- join ----------
    case 'join':
      var t1 = process.argv[3], t2 = process.argv[4], jf = process.argv[5] || '工号';
      if (!t1 || !t2) { console.error('用法: node read-excel.js join <表1> <表2> [关联字段]'); process.exit(1); }
      var d1 = readSheet(wb, t1), d2 = readSheet(wb, t2);
      var idx = {};
      d2.forEach(function(r) { var k = r[jf]; if (k) { if (!idx[k]) idx[k] = []; idx[k].push(r); } });
      var joined = [];
      d1.forEach(function(r) {
        var k = r[jf], ms = idx[k];
        if (ms) ms.forEach(function(m) {
          var obj = {};
          Object.keys(r).forEach(function(kk) { obj[t1 + '.' + kk] = r[kk]; });
          Object.keys(m).forEach(function(kk) { obj[t2 + '.' + kk] = m[kk]; });
          joined.push(obj);
        });
      });
      console.log('\n🔗 JOIN ' + t1 + ' ⋈ ' + t2 + ' ON ' + jf);
      console.log('  ' + t1 + ': ' + d1.length + ' 行, ' + t2 + ': ' + d2.length + ' 行 → 匹配 ' + joined.length + ' 行');
      if (joined.length > 0) { console.log('─'.repeat(40)); printTable(joined, 10); }
      break;

    // ---------- sql ----------
    case 'sql':
      var sql = process.argv[3]; if (!sql) { console.error('用法: node read-excel.js sql "SELECT ..."'); process.exit(1); }
      var p = parseSQL(sql); if (!p) { console.error('SQL解析失败'); process.exit(1); }
      var data = readSheet(wb, p.sheet);
      var result = p.conds.length > 0 ? queryData(data, p.conds) : data;
      if (p.limit) result = result.slice(0, p.limit);
      console.log('\n🔍 SQL: ' + sql);
      printTable(result, p.limit || 20);
      break;

    // ---------- 兼容旧用法 ----------
    default:
      var arg = process.argv[2];
      var data = readSheet(wb, '教职工主表');
      var num = parseInt(arg);
      if (!isNaN(num) && num > 0) {
        console.log('\n📋 教职工主表 (前 ' + num + ' 条)');
        printTable(data, num);
      } else if (arg.length > 0) {
        var result = queryData(data, [{ field: '姓名', value: arg, fuzzy: true }]);
        console.log('\n🔍 教职工主表 WHERE 姓名~=' + arg);
        printTable(result, 20);
      } else {
        help();
      }
  }
}

main();