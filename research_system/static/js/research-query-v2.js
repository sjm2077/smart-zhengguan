
(function(){
'use strict';
const state={type:'project',page:1,pageSize:10,totalPages:1,fundYear:''};
const $=id=>document.getElementById(id);
const esc=v=>{const d=document.createElement('div');d.textContent=v==null?'':String(v);return d.innerHTML};
const fmt=n=>Number(n||0).toLocaleString('zh-CN',{maximumFractionDigits:2});

function optionFill(id,items,placeholder,get){
  const el=$(id), cur=el.value;
  el.innerHTML=`<option value="">${esc(placeholder)}</option>`;
  items.forEach(item=>{const x=get?get(item):{value:item,label:item};const o=document.createElement('option');o.value=x.value;o.textContent=x.label;el.appendChild(o)});
  el.value=cur;
}
function urlState(){
  const p=new URLSearchParams(location.search);
  return {
    type:p.get('type')||'project',keyword:p.get('keyword')||'',year:p.get('year')||'',
    fund_year:p.get('fund_year')||'',dept:p.get('dept')||'',subject:p.get('subject')||'',
    teacher_id:p.get('teacher_id')||'',status:p.get('status')||'',project_type:p.get('project_type')||'',
    fund_source:p.get('fund_source')||'',achievement_type:p.get('achievement_type')||'',
    achievement_level:p.get('achievement_level')||'',international:p.get('international')||''
  };
}
function params(){
  const p=new URLSearchParams();
  const map={
    keyword:$('rqKeyword').value.trim(),year:$('rqYear').value,fund_year:state.fundYear,
    dept:$('rqDept').value,subject:$('rqSubject').value,teacher_id:$('rqTeacher').value,
    status:$('rqStatus').value,project_type:$('rqProjectType').value,fund_source:$('rqFundSource').value,
    achievement_type:$('rqAchievementType').value,achievement_level:$('rqAchievementLevel').value,
    international:$('rqInternational').value
  };
  Object.entries(map).forEach(([k,v])=>{if(v)p.set(k,v)});
  p.set('type',state.type);p.set('page',state.page);p.set('page_size',state.pageSize);
  return p;
}
function applyType(){
  document.querySelectorAll('.rq-type-switch button').forEach(b=>b.classList.toggle('active',b.dataset.type===state.type));
  $('rqProjectFilters').hidden=state.type!=='project';
  $('rqAchievementFilters').hidden=state.type!=='achievement';
  $('rqResultTitle').textContent=state.type==='project'?'项目查询结果':state.type==='achievement'?'成果查询结果':'教师查询结果';
}
function applyUrl(){
  const q=urlState();state.type=['project','achievement','teacher'].includes(q.type)?q.type:'project';state.fundYear=q.fund_year;
  $('rqKeyword').value=q.keyword;$('rqYear').value=q.year;$('rqDept').value=q.dept;$('rqSubject').value=q.subject;
  $('rqTeacher').value=q.teacher_id;$('rqStatus').value=q.status;$('rqProjectType').value=q.project_type;
  $('rqFundSource').value=q.fund_source;$('rqAchievementType').value=q.achievement_type;
  $('rqAchievementLevel').value=q.achievement_level;$('rqInternational').value=q.international;
  applyType();renderDrillHint();
}
function renderDrillHint(){
  const parts=[];
  if(state.fundYear)parts.push(`经费年份：${state.fundYear}`);
  const box=$('rqDrilldownHint');
  if(parts.length){box.hidden=false;box.innerHTML=`<strong>下钻条件</strong> · ${parts.join(' · ')}`;}
  else box.hidden=true;
}
async function loadOptions(){
  const r=await fetch('/api/research-query/options2');if(!r.ok)throw new Error('查询选项加载失败');const d=await r.json();
  optionFill('rqYear',d.years||[],'全部年份',x=>({value:String(x),label:`${x}年`}));
  optionFill('rqDept',d.depts||[],'全部系别');
  optionFill('rqSubject',d.subjects||[],'全部学科');
  optionFill('rqTeacher',d.teachers||[],'全部教师',x=>({value:String(x.id),label:`${x.real_name}${x.dept__dept_name?' · '+x.dept__dept_name:''}`}));
  optionFill('rqStatus',d.project_statuses||[],'全部项目状态',x=>x);
  optionFill('rqProjectType',d.project_types||[],'全部项目类型',x=>x);
  optionFill('rqFundSource',d.fund_sources||[],'全部经费来源',x=>x);
  optionFill('rqAchievementType',d.achievement_types||[],'全部成果类型',x=>x);
  optionFill('rqAchievementLevel',d.achievement_levels||[],'全部成果级别');
  optionFill('rqInternational',d.international_options||[],'全部发表范围',x=>x);
}
function head(){
  if(state.type==='project')$('rqTableHead').innerHTML='<tr><th>项目</th><th>负责人</th><th>系别</th><th>学科</th><th>类型</th><th>状态</th><th>起止日期</th><th>进度</th><th>操作</th></tr>';
  else if(state.type==='achievement')$('rqTableHead').innerHTML='<tr><th>成果</th><th>作者</th><th>系别</th><th>学科</th><th>类型</th><th>级别</th><th>年份</th><th>发表范围</th><th>操作</th></tr>';
  else $('rqTableHead').innerHTML='<tr><th>教师</th><th>职称</th><th>系别</th><th>主持项目</th><th>科研成果</th><th>操作</th></tr>';
}
function rows(data){
  const b=$('rqTableBody');head();
  if(!data.length){b.innerHTML=`<tr><td colspan="${state.type==='teacher'?6:9}" class="rq-empty">当前条件下暂无真实记录</td></tr>`;return}
  if(state.type==='project')b.innerHTML=data.map(x=>`<tr><td><div class="rq-main-title">${esc(x.project_name)}</div><div class="rq-main-sub">${esc(x.project_no||'—')}</div></td><td>${esc(x.leader)}</td><td>${esc(x.dept||'—')}</td><td>${esc(x.subject||'未分类')}</td><td>${esc(x.project_type)}</td><td><span class="rq-tag">${esc(x.status)}</span></td><td>${esc(x.start_date)} 至 ${esc(x.end_date)}</td><td>${Number(x.actual_progress||0)}%</td><td><a class="rq-detail" href="${esc(x.url)}">查看详情</a></td></tr>`).join('');
  else if(state.type==='achievement')b.innerHTML=data.map(x=>`<tr><td><div class="rq-main-title">${esc(x.title)}</div></td><td>${esc(x.author)}</td><td>${esc(x.dept||'—')}</td><td>${esc(x.subject||'未分类')}</td><td>${esc(x.achievement_type)}</td><td>${esc(x.level||'—')}</td><td>${esc(x.publish_year)}</td><td>${x.is_international?'国际':'国内'}</td><td><a class="rq-detail" href="${esc(x.url)}">查看详情</a></td></tr>`).join('');
  else b.innerHTML=data.map(x=>`<tr><td><div class="rq-main-title">${esc(x.real_name)}</div></td><td>${esc(x.title||'—')}</td><td>${esc(x.dept||'未分配')}</td><td>${Number(x.project_count||0)}</td><td>${Number(x.achievement_count||0)}</td><td><a class="rq-detail" href="${esc(x.url)}">查看科研画像</a></td></tr>`).join('');
}
function condition(f){
  const a=[];if(f.keyword)a.push(`关键词“${f.keyword}”`);if(f.dept)a.push(f.dept);if(f.subject)a.push(f.subject);
  if(f.year)a.push(`${f.year}年`);if(f.fund_year)a.push(`经费年份${f.fund_year}`);
  if(f.project_type)a.push(f.project_type);if(f.status)a.push(f.status);if(f.fund_source)a.push(f.fund_source);
  if(f.achievement_type)a.push(f.achievement_type);if(f.achievement_level)a.push(f.achievement_level);
  if(f.international==='true')a.push('国际发表');if(f.international==='false')a.push('非国际发表');
  return a.length?'当前条件：'+a.join(' · '):'当前条件：全院科研数据';
}
async function load(){
  const p=params();history.replaceState(null,'',`${location.pathname}?${p.toString()}`);
  $('rqTableBody').innerHTML='<tr><td class="rq-empty">正在加载…</td></tr>';
  const r=await fetch(`/api/research-query/search2?${p.toString()}`),d=await r.json();if(!r.ok)throw new Error(d.error||'查询失败');
  $('rqSummaryProject').textContent=fmt(d.summary.project_count);$('rqSummaryAchievement').textContent=fmt(d.summary.achievement_count);
  $('rqSummaryTeacher').textContent=fmt(d.summary.teacher_count);$('rqSummaryFund').textContent=fmt(d.summary.fund_total);
  rows(d.rows||[]);state.page=d.pagination.page;state.totalPages=d.pagination.total_pages;
  $('rqConditionText').textContent=condition(d.filters||{});$('rqTotalText').textContent=`共 ${d.pagination.total} 条`;
  $('rqPageText').textContent=`第 ${state.page} / ${state.totalPages} 页`;$('rqPrev').disabled=state.page<=1;$('rqNext').disabled=state.page>=state.totalPages;
}
function reset(){
  ['rqKeyword','rqYear','rqDept','rqSubject','rqTeacher','rqStatus','rqProjectType','rqFundSource','rqAchievementType','rqAchievementLevel','rqInternational'].forEach(id=>$(id).value='');
  state.fundYear='';state.page=1;renderDrillHint();load().catch(show);
}
function show(e){console.error(e);head();$('rqTableBody').innerHTML=`<tr><td class="rq-empty">${esc(e.message||'查询失败')}</td></tr>`}
window.toggleSubmenu=el=>{const s=el.nextElementSibling;if(s)s.classList.toggle('open')};
window.goToSmartAnalysis=()=>{const role=localStorage.getItem('userRole')||'admin';location.href=role==='admin'?'/analysis/admin/':'/analysis/teacher/'};

document.addEventListener('DOMContentLoaded',async()=>{
  try{
    await loadOptions();applyUrl();
    document.querySelectorAll('.rq-type-switch button').forEach(b=>b.addEventListener('click',()=>{state.type=b.dataset.type;state.page=1;applyType();load().catch(show)}));
    $('rqSubmit').addEventListener('click',()=>{state.page=1;load().catch(show)});$('rqReset').addEventListener('click',reset);
    $('rqKeyword').addEventListener('keydown',e=>{if(e.key==='Enter'){state.page=1;load().catch(show)}});
    $('rqPrev').addEventListener('click',()=>{if(state.page>1){state.page--;load().catch(show)}});
    $('rqNext').addEventListener('click',()=>{if(state.page<state.totalPages){state.page++;load().catch(show)}});
    await load();
  }catch(e){show(e)}
});
})();